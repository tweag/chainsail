"""
Asynchronous tasks run using celery
"""
import logging
import os
import zipfile
from datetime import datetime
from io import BytesIO
from tempfile import NamedTemporaryFile

import boto3
import yaml
from botocore.exceptions import ClientError
from celery.utils.log import get_task_logger
from chainsail.common.configs import ControllerConfigSchema
from chainsail.common.custom_logging import configure_logging
from chainsail.scheduler.config import SchedulerConfig, load_scheduler_config
from chainsail.scheduler.core import celery, db
from chainsail.scheduler.db import TblJobs
from chainsail.scheduler.errors import JobError
from chainsail.scheduler.jobs import Job, JobStatus
from cloudstorage.drivers.google import GoogleStorageDriver
from sqlalchemy.exc import OperationalError

RESULTS_ARCHIVE_FILENAME = "results.zip"

logger_name = "chainsail.scheduler.tasks"
logger = get_task_logger(logger_name)
scheduler_config = load_scheduler_config()
configure_logging(logger_name, "DEBUG", scheduler_config.remote_logging_config_path)

# FIXME: Results retrieval logic and storage backend logic should be homogenized


def get_storage_driver_container(scheduler_config: SchedulerConfig):
    """Gets the cloudstorage driver and results container"""
    s3 = boto3.client(
        "s3",
        endpoint_url=scheduler_config.results_endpoint_url,
        aws_access_key_id=scheduler_config.results_access_key_id,
        aws_secret_access_key=scheduler_config.results_secret_key,
    )

    return s3, scheduler_config.results_bucket


def get_job_blob_root(scheduler_config: SchedulerConfig, job_id: int):
    storage_basename = scheduler_config.results_basename
    if storage_basename.startswith("/"):
        storage_basename = storage_basename[1:]
    return f"{storage_basename}/{job_id}"


def sanitize_object_name(object_name: str) -> str:
    return object_name.strip("/")


@celery.task()
def start_job_task(job_id):
    """Starts a job

    Args:
        job_id: The id of the job to start

    Raises:
        JobError: If the job failed to start
    """
    # Load Job object from database entry and lock its row using FOR UPDATE
    # to avoid the job being started multiple times. If the row is locked then
    # we can just ditch this start request.
    try:
        job_rep = TblJobs.query.with_for_update(of=TblJobs, nowait=True).filter_by(id=job_id).one()
    except OperationalError:
        # TODO: Log that the row could not be queried
        return
    job = Job.from_representation(job_rep, scheduler_config)
    try:
        job.start()
        job.representation.started_at = datetime.utcnow()
        logger.info(f"Started job #{job_id}.", extra={"job_id": job_id})
    except JobError as e:
        db.session.commit()
        logger.error(f"Failed to start job #{job_id}.", extra={"job_id": job_id})
        raise e
    else:
        db.session.commit()


@celery.task()
def stop_job_task(job_id, exit_status=None):
    """Stops a job

    Args:
        job_id: The id of the job to stop

    Raises:
        JobError: If the job failed to stop
    """
    # Load Job object from database entry
    job = Job.from_representation(TblJobs.query.filter_by(id=job_id).one(), scheduler_config)
    if exit_status:
        exit_status = JobStatus(exit_status)
    try:
        job.stop()
        job.representation.finished_at = datetime.utcnow()
        logger.info(f"Stopped job #{job_id}.", extra={"job_id": job_id})
        if exit_status:
            job.status = exit_status
    except JobError as e:
        db.session.commit()
        logger.error(f"Failed to stop stop job #{job_id}.", extra={"job_id": job_id})
        raise e
    else:
        db.session.commit()


@celery.task(autoretry_for=(Exception,), max_retries=5, retry_backoff=2)
def watch_job_task(job_id):
    """Watches a running job until it completes and updates its status in the database

    Args:
        job_id: The id of the job to start

    Raises:
        JobError: If the job failed to start
    """
    logger.info(f"Watching job {job_id}")
    job_rep = TblJobs.query.filter_by(id=job_id).one()
    job = Job.from_representation(job_rep, scheduler_config)
    try:
        job.watch()
        job.sync_representation()
        job.representation.finished_at = datetime.utcnow()
    # TODO: Make this a more specific exception
    except Exception as e:
        logger.exception(e)
        # Flag job as failed
        job.status = JobStatus.FAILED
        job.sync_representation()
        job.representation.finished_at = datetime.utcnow()
        db.session.commit()
        raise e
    else:
        db.session.commit()


@celery.task()
def scale_job_task(job_id, n_replicas) -> bool:
    """Scales a running job to have size `n_replicas`

    Args:
        job_id: The id of the job to scale
        n_replicas: The number of replicas to scale to

    Raises:
        JobError: If the job failed to be scaled
    """
    try:
        logger.info(f"Attempting to aquire lock for job {job_id}")
        job_rep = TblJobs.query.filter_by(id=job_id).one()
    except OperationalError:
        # Another process is already scaling this job
        logger.error(f"Failed to aquire lock for job {job_id} in scale_job_task")
        return False
    logger.info(f"Successfully aquired lock for job {job_id}")
    # Load Job object from database entry
    job = Job.from_representation(job_rep, scheduler_config)
    try:
        job.scale_to(n_replicas)
        logger.info(f"Scaled job #{job_id} to {n_replicas} replicas.", extra={"job_id": job_id})
    except JobError as e:
        logger.error(f"Failed to scale #{job_id}.", extra={"job_id": job_id})
        logger.exception(e)
        db.session.commit()
        raise e
    else:
        db.session.commit()
        return True


def get_signed_url(job_id):
    logger.info(f"Getting signed URL for results of job #{job_id}...", extra={"job_id": job_id})
    # FIXME: new implementation
    s3_client, container = get_storage_driver_container(scheduler_config)
    job_blob_root = get_job_blob_root(scheduler_config, job_id)
    response = s3_client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": container,
            "Key": sanitize_object_name(f"{job_blob_root}/{RESULTS_ARCHIVE_FILENAME}"),
        },
        ExpiresIn=scheduler_config.results_url_expiry_time,
    )
    logger.info(f"Obtained signed URL for results of job #{job_id}.", extra={"job_id": job_id})
    # TODO: Remove debugging statement here
    logger.warn(response)
    return response


@celery.task()
def update_signed_url_task(job_id, signed_url=None):
    if signed_url is None:
        signed_url = get_signed_url(job_id)
    job_rep = TblJobs.query.filter_by(id=job_id).one()
    job_rep.signed_url = signed_url
    db.session.commit()


@celery.task()
def zip_results_task(job_id):
    """Make zip archive of all results for a given job.

    Args:
        job_id: The id of the job the results of which to zip and link to
    """
    logger.info(f"Zipping results of job #{job_id}...", extra={"job_id": job_id})
    # FIXME: new implementation
    s3_client, container = get_storage_driver_container(scheduler_config)
    job_blob_root = get_job_blob_root(scheduler_config, job_id)

    objects = s3_client.list_objects(Bucket=scheduler_config.results_bucket, Prefix=job_blob_root)
    if "Contents" not in objects:
        raise JobError("No results files found in results backend.")

    archive_contents = BytesIO(b"")
    with zipfile.ZipFile(archive_contents, "w", zipfile.ZIP_DEFLATED) as zipf:
        for blob in objects["Contents"]:
            key = blob["Key"]
            is_results_archive = key.endswith(RESULTS_ARCHIVE_FILENAME)
            # Ignore existing results archives
            if is_results_archive:
                continue
            # Note: Loading entire object into memory here
            blob_name_no_root = key[len(job_blob_root) :]
            contents = s3_client.get_object(Bucket=container, Key=key)["Body"].read()
            zipf.writestr(blob_name_no_root, contents)
    archive_contents.seek(0)
    blob_name = sanitize_object_name(f"{job_blob_root}/{RESULTS_ARCHIVE_FILENAME}")
    s3_client.put_object(Body=archive_contents, Bucket=container, Key=blob_name)
    logger.info(f"Zipped results of job #{job_id}.", extra={"job_id": job_id})

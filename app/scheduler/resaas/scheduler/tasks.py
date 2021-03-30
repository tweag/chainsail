"""
Asynchronous tasks run using celery
"""
import os
from datetime import datetime
import logging
from tempfile import NamedTemporaryFile

import yaml
import zipfile

from resaas.common.configs import ControllerConfigSchema
from resaas.common.logging import configure_logging
from resaas.scheduler.config import load_scheduler_config
from resaas.scheduler.core import celery, db
from resaas.scheduler.db import TblJobs
from resaas.scheduler.errors import JobError
from resaas.scheduler.jobs import Job, JobStatus
from sqlalchemy.exc import OperationalError
from cloudstorage.drivers.google import GoogleStorageDriver


RESULTS_ARCHIVE_FILENAME = "results.zip"
logger = logging.getLogger("resaas.scheduler")

scheduler_config = load_scheduler_config()
configure_logging("resaas.scheduler", "DEBUG", scheduler_config.remote_logging_config_path)


def get_storage_driver_container(scheduler_config):
    """Gets the cloudstorage driver and results container.

    TODO: make this cloud provider-agnostic.
    """
    storage_config_path = scheduler_config.node_config.storage_config_path

    with open(storage_config_path) as f:
        storage_config = yaml.load(f, Loader=yaml.FullLoader)

    backend_config = storage_config["backend_config"]
    container_name = backend_config["cloud"]["container_name"]

    storage_driver = GoogleStorageDriver(key=backend_config["cloud"]["storage_key_path"])
    container = storage_driver.get_container(container_name)

    return storage_driver, container


def get_job_blob_root(scheduler_config, job_id):
    controller_config_path = scheduler_config.node_config.controller_config_path
    with open(controller_config_path) as f:
        raw_controller_config = yaml.load(f, Loader=yaml.FullLoader)
    storage_basename = ControllerConfigSchema().load(raw_controller_config).storage_basename
    if storage_basename.startswith("/"):
        storage_basename = storage_basename[1:]
    return os.path.join(storage_basename, str(job_id)) + "/"


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


@celery.task(autoretry_for=(Exception,), max_retries=3, retry_backoff=2)
def watch_job_task(job_id):
    """Watches a running job until it completes and updates its status in the database

    Args:
        job_id: The id of the job to start

    Raises:
        JobError: If the job failed to start
    """
    # Load Job object from database entry and lock its row using FOR UPDATE
    # to avoid the job being started multiple times. If the row is locked then
    # we can just ditch this start request.
    job_rep = TblJobs.query.filter_by(id=job_id).one()
    job = Job.from_representation(job_rep, scheduler_config)
    try:
        job.watch()
        job.sync_representation()
        job.representation.finished_at = datetime.utcnow()
    # TODO: Make this a more specific exception
    except Exception as e:
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
        job_id: The id of the job to stop
        n_replicas: The number of replicas to scale to

    Raises:
        JobError: If the job failed to stop
    """
    try:
        job_rep = TblJobs.query.with_for_update(of=TblJobs, nowait=True).filter_by(id=job_id).one()
    except OperationalError:
        # Another process is already scaling this job
        return False
    # Load Job object from database entry
    job = Job.from_representation(job_rep, scheduler_config)
    try:
        job.scale_to(n_replicas)
        logger.info(f"Scaled job #{job_id} to {n_replicas} replicas.", extra={"job_id": job_id})
    except JobError as e:
        db.session.commit()
        logger.error(f"Failed to stop #{job_id}.", extra={"job_id": job_id})
        raise e
    else:
        db.session.commit()
        return True


def get_signed_url(job_id):
    logger.info(f"Getting signed URL for results of job #{job_id}...", extra={"job_id": job_id})
    storage_driver, container = get_storage_driver_container(scheduler_config)
    job_blob_root = get_job_blob_root(scheduler_config, job_id)
    zip_blob = container.get_blob(os.path.join(job_blob_root, RESULTS_ARCHIVE_FILENAME))
    signed_url = storage_driver.generate_blob_download_url(
        zip_blob, expires=scheduler_config.results_url_expiry_time
    )
    logger.info(f"Obtained signed URL for results of job #{job_id}.", extra={"job_id": job_id})

    return signed_url


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
    storage_driver, container = get_storage_driver_container(scheduler_config)
    job_blob_root = get_job_blob_root(scheduler_config, job_id)

    tmpfiles = []
    for blob in storage_driver.get_blobs(container):
        is_results_archive = blob.name.endswith(RESULTS_ARCHIVE_FILENAME)
        in_job_root = blob.name.startswith(job_blob_root)
        if is_results_archive or not in_job_root:
            continue
        tmpfile = NamedTemporaryFile()
        storage_driver.download_blob(blob, tmpfile.name)
        tmpfiles.append((tmpfile, blob.name[len(job_blob_root) :]))

    # Put all downloaded blobs in a zip file
    with NamedTemporaryFile() as tmpzipfile:
        zipf = zipfile.ZipFile(tmpzipfile, "w", zipfile.ZIP_DEFLATED)
        for tmpfile, blob_name_no_root in tmpfiles:
            zipf.write(tmpfile.name, blob_name_no_root)
            tmpfile.close()
        zipf.close()
        tmpzipfile.seek(0)
        blob_name = os.path.join(job_blob_root, RESULTS_ARCHIVE_FILENAME)
        storage_driver.upload_blob(container, tmpzipfile, blob_name=blob_name)

    logger.info(f"Zipped results of job #{job_id}.", extra={"job_id": job_id})

"""
Asynchronous tasks run using celery
"""

from resaas.scheduler.core import celery, db
from resaas.scheduler.db import TblJobs
from resaas.scheduler.jobs import Job
from resaas.scheduler.config import load_scheduler_config
from resaas.scheduler.errors import JobError


@celery.task()
def start_job_task(job_id):
    """Starts a job

    Args:
        job_id: The id of the job to start

    Raises:
        JobError: If the job failed to start
    """
    # Load Job object from database entry
    job = Job.from_representation(
        TblJobs.query.filter_by(id=job_id).first(), load_scheduler_config()
    )
    try:
        job.start()
    except JobError as e:
        db.session.commit()
        raise e
    else:
        db.session.commit()


@celery.task()
def stop_job_task(job_id):
    """Stops a job

    Args:
        job_id: The id of the job to stop

    Raises:
        JobError: If the job failed to stop
    """
    # Load Job object from database entry
    job = Job.from_representation(
        TblJobs.query.filter_by(id=job_id).first(), load_scheduler_config()
    )
    try:
        job.stop()
    except JobError as e:
        db.session.commit()
        raise e
    else:
        db.session.commit()

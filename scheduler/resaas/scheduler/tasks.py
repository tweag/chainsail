"""
Asynchronous tasks run using celery
"""

# Our own pre-configured version of celery
from datetime import datetime
from resaas.scheduler.core import celery, db
from resaas.scheduler.db import TblJobs


@celery.task(time_limit=3)
def echo_job():
    print("welcome to the task")
    print("blarg")


@celery.task()
def update_job_finished_time(job_id):
    print("welcome to the task")
    job = TblJobs.query.filter_by(id=job_id).first()
    job.finished_at = datetime.utcnow()
    db.session.commit()
    return True

"""
Scheduler REST API and endpoint specifications
"""
from datetime import datetime

from flask import jsonify, request

from resaas.scheduler.core import app, db
from resaas.scheduler.config import load_scheduler_config
from resaas.scheduler.db import JobViewSchema, NodeViewSchema, TblJobs, TblNodes
from resaas.scheduler.jobs import Job
from resaas.scheduler.spec import JobSpecSchema
from resaas.scheduler.tasks import start_job_task

config = load_scheduler_config()


# @app.route("/job/test_update_time/<job_id>", methods=["POST"])
# def celery_dev_test(job_id):
#     """Call celery"""
#     job = TblJobs.query.filter_by(id=job_id).first()
#     if not job:
#         raise Exception
#     app.logger.info("Calling job update task")
#     result = update_job_finished_time.apply_async((job_id,), {})
#     if not result.get():
#         raise Exception
#     db.session.refresh(job)
#     return JobViewSchema().jsonify(job, many=False)


@app.route("/job/<job_id>", methods=["GET"])
def get_job(job_id):
    """List a single job"""
    job = TblJobs.query.filter_by(id=job_id).first()
    return JobViewSchema().jsonify(job, many=False)


@app.route("/job", methods=["POST"])
def create_job():
    """Create a job"""
    # Validate the provided job spec
    schema = JobSpecSchema()
    job_spec = schema.load(request.json)
    job = TblJobs(status="created", created_at=datetime.utcnow(), spec=schema.dumps(job_spec))
    db.session.add(job)
    db.session.commit()
    return jsonify({"job_id": job.id})


@app.route("/job/start/<job_id>", methods=["POST"])
def start_job(job_id):
    """Start a single job"""
    job = TblJobs.query.filter_by(id=job_id).first()
    if not job:
        raise ValueError("Job does not exist yet")
    start_job_task.apply_async((job_id,), {})
    # ("message", status_code)
    return ("message", 200)


@app.route("/jobs", methods=["GET"])
def get_jobs():
    """List all jobs"""
    jobs = TblJobs.query.all()
    return JobViewSchema().jsonify(jobs, many=True)


@app.route("/job/<job_id>/nodes", methods=["GET"])
def job_nodes(job_id):
    """List all nodes for a given job"""
    nodes = TblNodes.query.filter_by(job_id=job_id)
    return NodeViewSchema().jsonify(nodes, many=True)


@app.route("/internal/job/<job_id>/scale/<n_replicas>", methods=["GET"])
def scale_job(job_id, n_replicas):
    """Cheap and dirty way to allow for jobs to be scaled"""
    # TODO
    # Call celery task function which performs scaling. Can include redirect link to
    # await status of scaling.
    return


if __name__ == "__main__":
    # Development server
    db.create_all()
    app.run(debug=True)

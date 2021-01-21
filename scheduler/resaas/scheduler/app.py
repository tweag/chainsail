"""
Scheduler REST API and endpoint specifications
"""
from datetime import datetime

from flask import jsonify, request, abort

from resaas.scheduler.core import app, db
from resaas.scheduler.config import load_scheduler_config
from resaas.scheduler.db import JobViewSchema, NodeViewSchema, TblJobs, TblNodes
from resaas.scheduler.jobs import Job, JobStatus
from resaas.scheduler.spec import JobSpecSchema
from resaas.scheduler.tasks import scale_job_task, start_job_task, stop_job_task

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
    job = TblJobs(
        status=JobStatus.INITIALIZED.value,
        created_at=datetime.utcnow(),
        spec=schema.dumps(job_spec),
    )
    db.session.add(job)
    db.session.commit()
    return jsonify({"job_id": job.id})


@app.route("/job/<job_id>/start", methods=["POST"])
def start_job(job_id):
    """Start a single job"""
    job = TblJobs.query.filter_by(id=job_id).first()
    if not job:
        abort(404, "job does not exist")
    job.status = JobStatus.STARTING.value
    db.session.commit()
    start_job_task.apply_async((job_id,), {})
    return ("ok", 200)


@app.route("/job/<job_id>/stop", methods=["POST"])
def stop_job(job_id):
    """Start a single job"""
    job = TblJobs.query.filter_by(id=job_id).first()
    if not job:
        abort(404, "job does not exist")
    job.status = JobStatus.STOPPING.value
    db.session.commit()
    stop_job_task.apply_async((job_id,), {})
    return ("ok", 200)


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


@app.route("/internal/job/<job_id>/scale/<n_replicas>", methods=["POST"])
def scale_job(job_id, n_replicas):
    """Cheap and dirty way to allow for jobs to be scaled"""
    # TODO
    # Call celery task function which performs scaling. Can include redirect link to
    # await status of scaling.
    n_replicas = int(n_replicas)
    job = TblJobs.query.filter_by(id=job_id).first()
    if not job:
        abort(404, "job does not exist")
    scale_job_task.apply_async((job_id, n_replicas), {})
    return ("ok", 200)


if __name__ == "__main__":
    # Development server
    db.create_all()
    app.run(debug=True)

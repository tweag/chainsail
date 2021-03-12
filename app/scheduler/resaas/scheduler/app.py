"""
Scheduler REST API and endpoint specifications
"""
from datetime import datetime
import os

import functools
from flask import abort, jsonify, request
from firebase_admin.auth import verify_id_token
from resaas.common.spec import JobSpecSchema
from resaas.scheduler.config import load_scheduler_config
from resaas.scheduler.core import app, db, firebase_app
from resaas.scheduler.db import JobViewSchema, NodeViewSchema, TblJobs, TblNodes
from resaas.scheduler.jobs import JobStatus
from resaas.scheduler.tasks import scale_job_task, start_job_task, stop_job_task, watch_job_task

config = load_scheduler_config()


def _is_dev_mode():
    try:
        is_dev = os.environ["PYTHON_ENV"] == "development" or os.environ["PYTHON_ENV"] == "dev"
        return is_dev
    except:
        return False


def check_user(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            id_token = request.headers["Authorization"].split(" ").pop()
            claims = verify_id_token(id_token, app=firebase_app)
            user_id = claims.get("user_id", None)
        except:
            user_id = None
            claims = None
        user_not_found = not claims or not user_id
        # Verify user id token in non dev mode
        if (not _is_dev_mode()) and user_not_found:
            return "Unauthorized", 401
        kwargs.update(user_id=user_id)
        value = func(*args, **kwargs)
        return value

    return wrapper


def find_job(job_id, user_id=None):
    if not _is_dev_mode():
        if user_id is None:
            job = TblJobs.query.filter_by(id=job_id).first()
            if not job:
                abort(404, "job does not exist")
        else:
            job = TblJobs.query.filter_by(id=job_id, user_id=user_id).first()
            if not job:
                abort(404, "job does not exist for this user")
    else:
        job = TblJobs.query.filter_by(id=job_id).first()
        if not job:
            abort(404, "job does not exist")
    return job


@app.route("/job/<job_id>", methods=["GET"])
@check_user
def get_job(job_id, user_id):
    """List a single job"""
    job = find_job(job_id, user_id)
    return JobViewSchema().jsonify(job, many=False)


@app.route("/job", methods=["POST"])
@check_user
def create_job(user_id):
    """Create a job"""
    # Validate the provided job spec
    schema = JobSpecSchema()
    job_spec = schema.load(request.json)
    job = TblJobs(
        user_id=user_id,
        status=JobStatus.INITIALIZED.value,
        created_at=datetime.utcnow(),
        spec=schema.dumps(job_spec),
    )
    db.session.add(job)
    db.session.commit()
    return jsonify({"job_id": job.id})


@app.route("/job/<job_id>/start", methods=["POST"])
@check_user
def start_job(job_id, user_id):
    """Start a single job"""
    job = find_job(job_id, user_id)
    job.status = JobStatus.STARTING.value
    db.session.commit()
    # Starts the watch process once the job is successfully started
    # The watch process will stop the job once it either succeeds or fails.
    start_job_task.apply_async(
        (job_id,),
        {},
        link=watch_job_task.si(job_id).set(
            link=stop_job_task.si(job_id, exit_status="success"),
            link_error=stop_job_task.si(job_id, exit_status="failed"),
        ),
    )
    return ("ok", 200)


@app.route("/job/<job_id>/stop", methods=["POST"])
@check_user
def stop_job(job_id, user_id):
    """Start a single job"""
    job = find_job(job_id, user_id)
    job.status = JobStatus.STOPPING.value
    db.session.commit()
    stop_job_task.apply_async((job_id,), {})
    return ("ok", 200)


@app.route("/jobs", methods=["GET"])
@check_user
def get_jobs(user_id):
    """List all jobs"""
    if not _is_dev_mode():
        jobs = TblJobs.query.filter_by(user_id=user_id)
    else:
        jobs = TblJobs.query.all()
    return JobViewSchema().jsonify(jobs, many=True)


@app.route("/job/<job_id>/nodes", methods=["GET"])
def job_nodes(job_id):
    """List all nodes for a given job"""
    nodes = TblNodes.query.filter_by(job_id=job_id)
    return NodeViewSchema().jsonify(nodes, many=True)


@app.route("/internal/job/<job_id>/scale/<n_replicas>", methods=["POST"])
def scale_job(job_id, n_replicas):
    """Cheap and dirty way to allow for jobs to be scaled."""
    n_replicas = int(n_replicas)
    job = find_job(job_id)
    scaling_task = scale_job_task.apply_async((job_id, n_replicas), {})
    # Await the result, raising any exceptions that get thrown
    scaled = scaling_task.get()
    if not scaled:
        abort(409, "job is currently being scaled")
    return ("ok", 200)


@app.route("/internal/job/<job_id>/add_iteration/<iteration>", methods=["POST"])
def add_iteration(job_id, iteration):
    """Adds an iteration entry to a job's list of controller iterations"""
    job = find_job(job_id)
    if job.controller_iterations is None:
        job.controller_iterations = []
    # .append(iteration) does not work, probably b/c lists are a mutable data type
    # or something like that
    job.controller_iterations = job.controller_iterations + [iteration]
    db.session.commit()
    return ("ok", 200)


if __name__ == "__main__":
    # Development server
    if _is_dev_mode():
        print("dev mode: user authentication switched off")
    db.create_all()
    app.run("0.0.0.0", debug=True)

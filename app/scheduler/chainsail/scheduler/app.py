"""
Scheduler REST API and endpoint specifications
"""
import functools
import os
from datetime import datetime
import os

from celery import chain
from cloudstorage.exceptions import NotFoundError
import functools
from flask import abort, jsonify, request
from firebase_admin.auth import (
    verify_id_token,
    InvalidIdTokenError,
    ExpiredIdTokenError,
    RevokedIdTokenError,
)
from chainsail.common.spec import JobSpecSchema
from chainsail.scheduler.core import app, db, firebase_app
from chainsail.scheduler.db import (
    JobViewSchema,
    NodeViewSchema,
    TblJobs,
    TblNodes,
    TblUsers,
)
from chainsail.scheduler.jobs import JobStatus
from chainsail.scheduler.tasks import (
    check_job_task,
    scale_job_task,
    start_job_task,
    stop_job_task,
    watch_job_task,
    zip_results_task,
    get_signed_url,
    update_signed_url_task,
    logger,
)


def _is_dev_mode():
    try:
        is_dev = (
            os.environ["PYTHON_ENV"] == "development"
            or os.environ["PYTHON_ENV"] == "dev"
        )
        return is_dev
    except:
        return False


def check_user(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        is_dev = _is_dev_mode()  # Verify user id token in non dev mode
        try:
            id_token = request.headers["Authorization"].split(" ").pop()
            claims = verify_id_token(id_token, app=firebase_app)
        except (InvalidIdTokenError, ExpiredIdTokenError, RevokedIdTokenError) as e:
            if not is_dev:
                return {"message": f"Unauthorized. Error: {e}"}, 401
            else:
                claims = None

        user_id = claims.get("user_id", None)
        if not is_dev and not user_id:
            # empty uid
            return {"message": "Unauthorized"}, 401

        email = claims.get("email", None)
        if not is_dev and not email:
            # empty email
            return {"message": "Unauthorized. No email found in token claim."}, 403

        user = TblUsers.query.filter_by(email=email).first()
        if not is_dev and not user:
            # unregistered user
            return (
                {
                    "message": f"User with id {user_id} and email {email} is not registered. Please contact our supporting team."
                },
                403,
            )

        if not is_dev and not user.is_allowed:
            # user not allowed
            return {
                "message": "User with id {user_id} and email {email} is not allowed to use services."
            }, 403

        kwargs.update(user_id=user_id)
        value = func(*args, **kwargs)
        return value

    return wrapper


def find_job(job_id, user_id=None):
    if _is_dev_mode() or user_id is None:
        job = TblJobs.query.filter_by(id=job_id).first()
        if not job:
            abort(404, "job does not exist")
    elif not _is_dev_mode():
        job = TblJobs.query.filter_by(id=job_id, user_id=user_id).first()
        if not job:
            abort(404, "job does not exist for this user")
    return job


def get_zip_chain(job_id):
    return chain(zip_results_task.si(job_id), update_signed_url_task.si(job_id))


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
        status=JobStatus.CHECKING.value,
        created_at=datetime.utcnow(),
        spec=schema.dumps(job_spec),
    )
    db.session.add(job)
    db.session.commit()
    logger.info(f"Created job #{job.id}.", extra={"job_id": job.id})
    # Starts the watch process once the job checks are successfully started
    # The watch process will stop the job once it either succeeds or fails.
    job_id = str(job.id)
    try:
        check_job_task.apply_async(
            (job_id,),
            {},
        )
    except:
        logger.error(
            f"Failed to launch checks for job #{job.id}.", extra={"job_id": job.id}
        )
        job.status = JobStatus.FAILED
        db.session.commit()

    return jsonify({"job_id": job.id})


@app.route("/job/<job_id>/start", methods=["POST"])
@check_user
def start_job(job_id, user_id):
    """Start a single job"""
    job = find_job(job_id, user_id)
    job.status = JobStatus.STARTING.value
    logger.info(f"Starting job #{job_id}...", extra={"job_id": job_id})
    db.session.commit()
    # Starts the watch process once the job is successfully started
    # The watch process will stop the job once it either succeeds or fails.
    zip_chain = get_zip_chain(job_id)
    start_job_task.apply_async(
        (job_id,),
        {},
        link=watch_job_task.si(job_id).set(
            link=stop_job_task.si(job_id, exit_status="success").set(link=zip_chain),
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

    zip_chain = get_zip_chain(job_id)
    stop_job_task.apply_async((job_id,), link=zip_chain)
    logger.info(f"Stopping job #{job_id}...", extra={"job_id": job_id})

    return ("ok", 200)


@app.route("/job/<job_id>/update_signed_url", methods=["POST"])
@check_user
def get_job_signed_url(job_id, user_id):
    find_job(job_id, user_id)
    try:
        signed_url = get_signed_url(job_id)
    except NotFoundError:
        return ("Results not zipped yet", 404)
    update_signed_url_task.apply_async((job_id, signed_url), {})
    return (signed_url, 200)


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
    find_job(job_id)
    logger.info(
        f"Scaling up job #{job_id} to {n_replicas} replicas...",
        extra={"job_id": job_id},
    )
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

"""
Scheduler REST API and endpoint specifications
"""
import functools
import json
import logging
import os

from datetime import datetime

import shortuuid
from celery import chain
from cloudstorage.exceptions import NotFoundError
from firebase_admin.auth import (
    ExpiredIdTokenError,
    InvalidIdTokenError,
    RevokedIdTokenError,
    verify_id_token,
)
from flask import abort, jsonify, request

from chainsail.common.custom_logging import configure_logging
from chainsail.common.spec import JobSpecSchema
from chainsail.scheduler.config import load_scheduler_config
from chainsail.scheduler.core import app, db, firebase_app, use_dev_user
from chainsail.scheduler.db import (
    JobViewSchema,
    NodeViewSchema,
    TblJobs,
    TblNodes,
    TblUsers,
)
from chainsail.scheduler.jobs import JobStatus
from chainsail.scheduler.tasks import (
    scale_job_task,
    start_job_task,
    stop_job_task,
    watch_job_task,
    zip_results_task,
    update_signed_url_task,
)
from chainsail.scheduler.utils import (
    get_signed_url,
    get_s3_client_and_container,
)

logger = logging.getLogger("chainsail.scheduler")

scheduler_config = load_scheduler_config()
configure_logging("chainsail.scheduler", "INFO", scheduler_config.remote_logging_config_path)

USER_PROB_BLOB_ROOT = "user_probs/"
USER_PROB_URL_EXPIRY_TIME = 31540000  # in seconds; approximately a year


def _is_dev_mode():
    try:
        is_dev = os.environ["PYTHON_ENV"] == "development" or os.environ["PYTHON_ENV"] == "dev"
        return is_dev
    except:
        return False


def check_user(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Get the current users email address
        # If firebase is enabled, verify the users using the token provided in the authorization header
        if firebase_app is not None:
            try:
                id_token = request.headers["Authorization"].split(" ").pop()
                claims = verify_id_token(id_token, app=firebase_app)
            except (
                KeyError,
                InvalidIdTokenError,
                ExpiredIdTokenError,
                RevokedIdTokenError,
            ) as e:
                return {
                    "message": f"Invalid/Expired/Revoked account token. Logging out and in again may refresh the token. If the problem persists, please contact support@chainsail.io. Error: {e}"
                }, 401
            user_id = claims.get("user_id", None)
            if not user_id:
                # empty uid
                return {
                    "message": "Unauthorized access: No user ID found in token claim. Logging out and in again may solve this issue. If the problem persists, please contact support@chainsail.io."
                }, 401
            email = claims.get("email", None)
            if not email:
                # empty email
                return {
                    "message": "Unauthorized access: No email found in token claim. Logging out and in again may solve this issue. If the problem persists, please contact support@chainsail.io."
                }, 401
            user = TblUsers.query.filter_by(email=email).first()
            if not user:
                # unregistered user
                return (
                    {
                        "message": f"Unauthorized access. Please contact support@chainsail.io to be granted access to Chainsail. Error: User with email {email} not found in database."
                    },
                    403,
                )
            if not user.is_allowed:
                # user not allowed
                return {
                    "message": f"Unauthorized access. Please contact support@chainsail.io to be granted access to Chainsail. Error: User with email {email} is not allowed to use the services."
                }, 403
        # If firebase is disabled, we assume we are in "dev" mode with a specific user and
        # do NOT check if the user exists in our internal auth table.
        else:
            user_id = use_dev_user
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


def validate_uploaded_files(flask_file_objs):
    # No use using logger here as the user won't be able to see it (no user ID).
    # Include user id in error message to be able to associate this with a user.
    # No check whether the single file uploaded is a valid zip file, as this is
    # being done on the frontend side.
    if len(flask_file_objs) == 0:
        raise FileNotFoundError("No file uploaded by user with id {user_id}")
    elif len(flask_file_objs) > 1:
        raise ValueError("More than one file uploaded by user with id {user_id}")


def save_uploaded_user_prob(flask_file_obj, user_id):
    """Saves a werkzeug FileStorage object to a blob with a random name
    that contains the user ID
    """
    s3, container = get_s3_client_and_container()
    blob_name = os.path.join(USER_PROB_BLOB_ROOT, f"{user_id}_{shortuuid.uuid()}.zip")
    s3.upload_fileobj(flask_file_obj, container, blob_name)
    return blob_name


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
    uploaded_files = list(request.files.values())
    validate_uploaded_files(uploaded_files)
    user_prob_blob_name = save_uploaded_user_prob(uploaded_files[0], user_id)
    signed_url = get_signed_url(user_prob_blob_name, USER_PROB_URL_EXPIRY_TIME)
    form_data = {
        "probability_definition": signed_url,
        **dict(((k, json.loads(v)) for k, v in request.form.items())),
    }
    print(form_data)
    # Validate the provided job spec
    schema = JobSpecSchema()
    job_spec = schema.load(form_data)
    job = TblJobs(
        user_id=user_id,
        status=JobStatus.INITIALIZED.value,
        created_at=datetime.utcnow(),
        spec=schema.dumps(job_spec),
    )
    db.session.add(job)
    db.session.commit()
    logger.info(f"Created job #{job.id}.", extra={"job_id": job.id})
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
    # FIXME: Ideally we could check authorization for internal endpoints
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
    # FIXME: Ideally we could check authorization for internal endpoints
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

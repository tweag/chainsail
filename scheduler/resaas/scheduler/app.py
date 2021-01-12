"""
Scheduler REST API and endpoint specifications
"""
from datetime import datetime
from resaas.scheduler.core import app, db, get_config
from flask import jsonify, request
from resaas.scheduler.db import Job, Node, JobViewSchema, NodeViewSchema
from resaas.scheduler.spec import JobSpecSchema

config = get_config()


@app.route("/job/<job_id>", methods=["GET"])
def get_job(job_id):
    """List a single job"""
    job = Job.query.filter_by(id=job_id).first()
    return JobViewSchema().jsonify(job, many=False)


@app.route("/job", methods=["POST"])
def create_job():
    """Create a job"""
    # Validate the provided job spec
    schema = JobSpecSchema()
    job_spec = schema.load(request.json)
    job = Job(status="created", created_at=datetime.utcnow(), spec=schema.dumps(job_spec))
    db.session.add(job)
    db.session.commit()
    # TODO: Submit Job's celery task here
    return jsonify({"job_id": job.id})


@app.route("/jobs", methods=["GET"])
def get_jobs():
    """List all jobs"""
    jobs = Job.query.all()
    return JobViewSchema().jsonify(jobs, many=True)


@app.route("/job/<job_id>/nodes", methods=["GET"])
def job_nodes(job_id):
    """List all nodes for a given job"""
    nodes = Node.query.filter_by(job_id=job_id)
    return NodeViewSchema().jsonify(nodes, many=True)


if __name__ == "__main__":
    # Development server
    db.create_all()
    app.run(debug=True)

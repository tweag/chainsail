from sqlalchemy.types import ARRAY

from chainsail.scheduler.core import db, ma


class TblJobs(db.Model):
    """
    Persistent job state and metadata
    """

    __tablename__ = "jobs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False)
    spec = db.Column(db.Unicode(), nullable=True)
    status = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime(), nullable=False)
    started_at = db.Column(db.DateTime(), nullable=True)
    finished_at = db.Column(db.DateTime(), nullable=True)
    # the ARRAY type limits us to postgresql databases
    controller_iterations = db.Column(ARRAY(db.String(50)), nullable=True)
    signed_url = db.Column(db.String(1000), nullable=True)


class TblNodes(db.Model):
    """
    Persistent node state
    """

    __tablename__ = "nodes"
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False)
    # e.g. VM or pod identifier
    name = db.Column(db.String(50), nullable=False)
    # Node type for object loading e.g. VMNode
    node_type = db.Column(db.String(50), nullable=False)
    entrypoint = db.Column(db.String(250), nullable=True)
    status = db.Column(db.String(50), nullable=True)
    address = db.Column(db.String(50), nullable=True)
    ports = db.Column(db.String(50), nullable=True)
    # Flag for indicating whether the node is currently used by the job
    # nodes which have been removed as a part of restarts, scaling, etc.
    # are flagged as in_use=False.
    in_use = db.Column(db.Boolean(), nullable=True)
    # Flag for indicating whether worker processes can be scheduled on this node
    is_worker = db.Column(db.Boolean(), nullable=True)
    job = db.relationship("TblJobs", backref="nodes", lazy=True)


class TblUsers(db.Model):
    """
    Users info
    """

    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), nullable=False)
    # whether a user is allowed to use our services
    is_allowed = db.Column(db.Boolean(), default=False)
    ## TODO: Add user quotas


class JobViewSchema(ma.SQLAlchemyAutoSchema):
    """Schema for returning jobs"""

    class Meta:
        model = TblJobs


class NodeViewSchema(ma.SQLAlchemyAutoSchema):
    """Schema for returning nodes"""

    class Meta:
        model = TblNodes

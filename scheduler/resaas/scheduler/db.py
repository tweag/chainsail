from resaas.scheduler.core import db, ma


class TblJobs(db.Model):
    """
    Persistent job state and metadata
    """

    __tablename__ = "jobs"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=True)
    spec = db.Column(db.Unicode(), nullable=True)
    status = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime(), nullable=False)
    started_at = db.Column(db.DateTime(), nullable=True)
    finished_at = db.Column(db.DateTime(), nullable=True)
    nodes = db.relationship("TblNodes", backref="jobs", lazy=True)


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


class JobViewSchema(ma.SQLAlchemyAutoSchema):
    """Schema for returning jobs"""

    class Meta:
        model = TblJobs


class NodeViewSchema(ma.SQLAlchemyAutoSchema):
    """Schema for returning nodes"""

    class Meta:
        model = TblNodes

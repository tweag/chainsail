# Config loading, sqlalchemy/flask declarations, etc.

from flask import Flask
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# TODO: Logger setup

# TODO: Dev-only
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////tmp/test.db"

# Flask-SQLAlchemy support
db = SQLAlchemy(app)
# Flask-marshmallow support
ma = Marshmallow(app)


def get_config():
    # TODO
    return {}

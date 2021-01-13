# Config loading, sqlalchemy/flask declarations, etc.

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

app = Flask(__name__)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


# TODO: Dev-only
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////tmp/test.db"

# Flask-SQLAlchemy support
db = SQLAlchemy(app)
# Flask-marshmallow support
ma = Marshmallow(app)


def get_config():
    # TODO
    return {}

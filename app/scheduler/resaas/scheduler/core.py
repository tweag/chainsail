# Config loading, sqlalchemy/flask declarations, etc.
import os
from pathlib import Path

import yaml
from celery import Celery
from flask import Flask, has_app_context
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import firebase_admin


class FlaskCelery(Celery):
    """
    Wrapper for adding flask application context to celery tasks.
    Modified from: https://stackoverflow.com/questions/12044776/how-to-use-flask-sqlalchemy-in-a-celery-task
    """

    def __init__(self, *args, **kwargs):

        super(FlaskCelery, self).__init__(*args, **kwargs)
        self.patch_task()

        if "app" in kwargs:
            print("initializing celery + flask app")
            self.init_app(kwargs["app"])
            # Hook into flask app's config for getting celery configurations
            self.conf.update(kwargs["app"].config, namespace="CELERY_")

    def patch_task(self):
        TaskBase = self.Task
        _celery = self

        class ContextTask(TaskBase):
            """
            Wraps celery tasks in a Flask app context
            """

            abstract = True

            def __call__(self, *args, **kwargs):
                if has_app_context():
                    print("Using app context which already is included")
                    return TaskBase.__call__(self, *args, **kwargs)
                else:
                    print("Making a new app context")
                    with _celery.app.app_context():
                        return TaskBase.__call__(self, *args, **kwargs)

        self.Task = ContextTask

    def init_app(self, app):
        self.app = app
        self.config_from_object(app.config)


app = Flask(__name__)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:"
)
# TODO: Logger setup

# In the simplest case, initialize the Flask-Cors extension with default arguments in order to
# allow CORS for all domains on all routes. See the full list of options in the documentation:
# https://flask-cors.corydolphin.com/en/latest/api.html#extension
CORS(app)


# Flask-SQLAlchemy support
db = SQLAlchemy(app)
# Flask-marshmallow support
ma = Marshmallow(app)
# Celery support
celery = FlaskCelery(app=app)

# Set the environment variable GOOGLE_APPLICATION_CREDENTIALS to the file path of the JSON file
# that contains your service account key.
firebase_app_name = "resaas"
try:
    firebase_app = firebase_admin.get_app(name=firebase_app_name)
except:
    firebase_app = firebase_admin.initialize_app(name=firebase_app_name)

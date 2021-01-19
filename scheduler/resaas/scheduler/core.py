# Config loading, sqlalchemy/flask declarations, etc.
import os
from pathlib import Path
from flask import Flask, has_app_context
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from celery import Celery
import yaml


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


# Flask-SQLAlchemy support
db = SQLAlchemy(app)
# Flask-marshmallow support
ma = Marshmallow(app)
# Celery support
celery = FlaskCelery(app=app)

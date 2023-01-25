# Scheduler

The Chainsail scheduler handles spinning up new sampling job clusters, tearing them down, and querying their metadata.
It is a single application with two main components:

1. A flask REST API ([chainsail/scheduler/app.py](chainsail/scheduler/app.py)) which is what clients use to interact with the Chainsail system.
2. A celery task runner for processing asynchronous tasks spawned by the flask application

The Chainsail scheduler is designed to work with Postgres (for flask) and Redis (for celery). An example docker-compose file can be found in the [example directory](./example) along with
an example configuration file. The configuration file's schema is defined in [chainsail/scheduler/config.py](chainsail/scheduler/config.py).

## Running locally
:warning: this is outdated and will likely not immediately work, e.g. we don't use `docker-compose` anymore, YAML files in `./examples/` are outdated and the AWS part is specific to an early Chainsail development deployment.
The job specification also has evolved since.
The easiest way to run Chainsail locally is using Minikube + Terraform + Helm, as described in `../../doc/deployment.md`.
Unfortunately, this entails building Docker images and makes for slow iteration.

There are a few steps to running the Chainsail scheduler locally. Make sure that you
are in a nix-shell environment.

1.  Enter a nix and poetry shell
    1. `nix-shell ../../shell.nix`
    1. `poetry install` (if you haven't already)
    1. `poetry shell`
1.  Update the example scheduler.yaml file
    1. Create a public/private key pair and fill in the relevent fields in the example config file.
    1. Request a temporary AWS key for making dev requests: `aws sts get-session-token` and fill in the info in the config file. Note that for AWS
       we already have the necessary security group created in the eu-central-1 region,
       so you should leave the region to that setting for development.
1.  Boot up docker and redis using docker-compose: `docker-compose --file example/docker-compose.yaml up`
1.  Start the celery task worker:

    ```shell
    # Its easiest to run things from the repository root directory
    $ cd ../..
    $ PYTHONPATH="PYTHONPATH:$PWD/app/scheduler" \
      CELERY_BROKER_URL="redis://localhost:6379/0" \
      CELERY_RESULT_BACKEND="redis://localhost:6379/1" \
      SQLALCHEMY_DATABASE_URI="postgresql://postgres:resaas-dev@localhost:5432/postgres" \
      CHAINSAIL_SCHEDULER_CONFIG="$PWD/app/scheduler/example/scheduler.yaml" \
        celery --app "chainsail.scheduler.tasks.celery" worker --task-events --pool gevent --concurrency=1
    ```

1.  Download the JSON file that contains your firebase service account key by following [this instruction](https://firebase.google.com/docs/admin/setup/#initialize-sdk) and set the environment variable `GOOGLE_APPLICATION_CREDENTIALS` to it:

    ```shell
    export GOOGLE_APPLICATION_CREDENTIALS="/home/user/Downloads/service-account-file.json"
    ```

1.  Start the flask dev server:

    ```shell
    $ PYTHONPATH="PYTHONPATH:$PWD/app/scheduler" \
      CELERY_BROKER_URL="redis://localhost:6379/0" \
      CELERY_RESULT_BACKEND="redis://localhost:6379/1" \
      SQLALCHEMY_DATABASE_URI="postgresql://postgres:resaas-dev@localhost:5432/postgres" \
      CHAINSAIL_SCHEDULER_CONFIG="$PWD/app/scheduler/example/scheduler.yaml" \
      PYTHON_ENV=dev \
          python -m 'chainsail.scheduler.app'
    ```

    Make sure to drop `PYTHON_ENV=dev` for production.

With that you can start making requests, for example:

```shell
curl --request POST \
     --header "Content-Type: application/json" \
     --data '{"probability_definition": "gs://foo/bar", "initial_number_of_replicas": "2"}' \
     http://127.0.0.1:5000/job
```

## Tests

(assuming you have already run `poetry install`)

```shell
$ nix-shell ../../shell.nix
$ poetry shell
$ PYTHONPATH="$PYTHONPATH:$PWD" pytest --cov-report html --cov=chainsail
```

## Endpoints

The Flask endpoints are listed in `./chainsail/scheduler/apps.py` and, while sparsely documented, it should be pretty clear what they do.

## Resources:

**User Manuals:**

https://flask.palletsprojects.com/en/1.1.x/quickstart/
https://flask-sqlalchemy.palletsprojects.com/en/2.x/
https://marshmallow.readthedocs.io/en/stable/
https://docs.celeryproject.org/en/latest/getting-started/first-steps-with-celery.html

**Config:**

https://flask-sqlalchemy.palletsprojects.com/en/2.x/config/
https://docs.celeryproject.org/en/stable/userguide/configuration.html

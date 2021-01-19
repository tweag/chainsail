# scheduler dev example

Running the scheduler and async task worker locally:

First enter the poetry shell:

```shell
$ nix-shell
$ cd ./scheduler
$ poetry install
$ poetry shell
```


```shell
$ cd example
$ docker-compose up
# Move to repo root for next commands
$ cd ../..
```

```shell
# Start a celery worker
$ PYTHONPATH="PYTHONPATH:$PWD/scheduler \
  CELERY_BROKER_URL="redis://localhost:6379/0" \
  CELERY_RESULT_BACKEND="redis://localhost:6379/1" \
  SQLALCHEMY_DATABASE_URI="postgresql://postgres:resaas-dev@localhost:5432/postgres" \
      celery --app "resaas.scheduler.core.celery" worker --task-events --pool gevent --concurrency=1
```


```shell

# Start the flask app
$ PYTHONPATH="PYTHONPATH:$PWD/scheduler" \
  CELERY_BROKER_URL="redis://localhost:6379/0" \
  CELERY_RESULT_BACKEND="redis://localhost:6379/1" \
  SQLALCHEMY_DATABASE_URI="postgresql://postgres:resaas-dev@localhost:5432/postgres" \
  RESAAS_SCHEDULER_CONFIG="$PWD/scheduler/example/scheduler.yaml" \
      python -m 'resaas.scheduler.app'

```

Also see for extra celery config options: 
https://docs.celeryproject.org/en/stable/userguide/configuration.html

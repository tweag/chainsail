#!/bin/bash

celery --app "resaas.scheduler.tasks.celery" worker --task-events --pool gevent --concurrency=1 -D
status=$?
if [ $status -ne 0 ]; then
  echo "Failed to start celery worker: $status"
  exit $status
fi


python -m 'resaas.scheduler.app' -D
status=$?
if [ $status -ne 0 ]; then
  echo "Failed to start scheduler flask app: $status"
  exit $status
fi

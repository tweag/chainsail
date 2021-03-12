##############################################################################
# BASE
##############################################################################
FROM python:3.8.7-slim as base

# Set up required directories
RUN mkdir -p /app/deps && mkdir -p /run/sshd
WORKDIR /app

##############################################################################
# SYSTEM DEPENDENCIES
##############################################################################
FROM base as system-deps

RUN apt-get update && \
    apt-get install -y curl wget unzip openssh-client openssh-server && \
    rm -rf /var/lib/apt/lists/*


##############################################################################
# BUILD
##############################################################################
FROM base as builder-common

RUN apt-get update && apt-get install -y wget unzip git build-essential libffi-dev libssl-dev zlib1g-dev

# Python package managers
RUN pip install --upgrade pip && pip install "poetry~=1.1"

##############################################################################
FROM builder-common as builder

# Install the scheduler
COPY ./lib/common /app/lib/common
COPY ./lib/grpc /app/lib/grpc
COPY ./app/scheduler /app/app/scheduler

RUN cd /app/app/scheduler && \
    poetry config virtualenvs.in-project true && \
    poetry run pip install --upgrade pip && \
    poetry install --no-dev


##############################################################################
# FINAL
##############################################################################
FROM system-deps as app

COPY --from=builder /app /app

ENV PYTHONPATH=$PYTHONPATH:/app/app/scheduler

# Adding the app venv bin to the front of path so it is the default pip, etc.
ENV PATH=/app/app/scheduler/.venv/bin:$PATH

# This didn't work - I wasn't able to retrieve the value for $CONCURRENCY in the CMD
# ARG CONCURRENCY=10

CMD celery --app "resaas.scheduler.tasks.celery" worker --task-events --pool gevent --concurrency=5
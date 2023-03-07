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
    apt-get install -y curl wget unzip openssh-client openssh-server libmagic1 && \
    rm -rf /var/lib/apt/lists/*


##############################################################################
# BUILD
##############################################################################
FROM base as builder-common

RUN apt-get update && apt-get install -y wget unzip git build-essential libffi-dev libssl-dev zlib1g-dev

# Python package managers
RUN pip install --upgrade pip && pip install "poetry==1.3.0"

##############################################################################
FROM builder-common as builder

# Install scheduler dependencies:

# Path dependencies
COPY ./lib/common /app/lib/common
COPY ./lib/grpc /app/lib/grpc

RUN mkdir -p /app/app/scheduler
COPY ./app/scheduler/pyproject.toml /app/app/scheduler
COPY ./app/scheduler/poetry.lock /app/app/scheduler

RUN cd /app/app/scheduler && \
    poetry config virtualenvs.in-project true && \
    poetry run pip install --upgrade pip && \
    poetry install --no-dev --no-root

COPY ./app/scheduler /app/app/scheduler
RUN cd /app/app/scheduler && \
    poetry install --no-dev

##############################################################################
# FINAL
##############################################################################
FROM system-deps as app

COPY --from=builder /app /app

ENV PYTHONPATH=$PYTHONPATH:/app/app/scheduler

# Adding the app venv bin to the front of path so it is the default pip, etc.
ENV PATH=/app/app/scheduler/.venv/bin:$PATH

ENV CONCURRENCY=10

CMD celery --app "chainsail.scheduler.tasks.celery" worker --task-events --pool gevent --concurrency=$CONCURRENCY

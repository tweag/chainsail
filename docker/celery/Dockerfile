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
    apt-get install -y curl wget unzip openssh-client openssh-server libmagic1 apt-transport-https ca-certificates curl gnupg2 software-properties-common && \
    rm -rf /var/lib/apt/lists/*

# RUN apt-get -y install apt-transport-https ca-certificates curl gnupg2 software-properties-common
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add -
RUN add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable"

RUN apt-get update
RUN apt-get -y install docker-ce

##############################################################################
# BUILD
##############################################################################
FROM base as builder-common

RUN apt-get update && apt-get install -y wget unzip git build-essential libffi-dev libssl-dev zlib1g-dev

# Python package managers
RUN pip install --upgrade pip && pip install "poetry==1.1.10"

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

ENV CONCURRENCY=10

CMD celery --app "chainsail.scheduler.tasks.celery" worker --task-events --pool gevent --concurrency=$CONCURRENCY

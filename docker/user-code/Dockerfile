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
    apt-get install -y curl wget unzip && \
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

# Install the controller
COPY ./lib/common /app/lib/common
COPY ./lib/grpc /app/lib/grpc
COPY ./app/user_code_server /app/app/user_code_server

RUN cd /app/app/user_code_server && \
    poetry config virtualenvs.in-project true && \
    poetry run pip install --upgrade pip && \
    poetry install --no-dev


##############################################################################
# FINAL
##############################################################################
FROM system-deps as app

COPY --from=builder /app /app

# Directory for user data
RUN mkdir -p /probability

# User-defined functions and data
ENV PATH=$PATH:/probability
ENV PYTHONPATH=$PYTHONPATH:/probability

# Adding the app venv bin to the front of path so it is the default pip, etc.
ENV PATH=/app/app/user_code_server/.venv/bin:$PATH

WORKDIR /probability

EXPOSE 50052

ENTRYPOINT ["/app/entrypoint.sh"]
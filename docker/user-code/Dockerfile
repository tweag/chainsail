##############################################################################
# BASE
##############################################################################
FROM python:3.9-slim as base

# Set up required directories
RUN mkdir -p /app/deps && mkdir -p /run/sshd
WORKDIR /app

##############################################################################
# SYSTEM DEPENDENCIES
##############################################################################
FROM base as system-deps

# up-to-date GCC
RUN echo 'deb http://deb.debian.org/debian stable main' >> /etc/apt/sources.list
RUN apt update -y
RUN apt-get install -y gcc build-essential curl wget unzip libopenblas-dev && \
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

# Install the controller
COPY ./lib/grpc /app/lib/grpc
COPY ./lib/common /app/lib/common
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

COPY docker/user-code/entrypoint.sh /app/entrypoint.sh
RUN chmod 555 /app/entrypoint.sh
# Adding the app venv bin to the front of path so it is the default pip, etc.
ENV PATH=/app/app/user_code_server/.venv/bin:$PATH
RUN pip install scipy==1.9.1 numpy==1.23.2 pymc==4.1.7 requests==2.28.1 chainsail-helpers==0.1.4

WORKDIR /probability

ENV USER_CODE_SERVER_PORT=50052
EXPOSE $USER_CODE_SERVER_PORT

ENTRYPOINT ["/app/entrypoint.sh"]

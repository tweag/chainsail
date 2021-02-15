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

# Global SSH configurations
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
# Disable password authentication
RUN sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
# Listen on a non-default port to avoid clashing with the host's ssh
RUN sed -i 's/#Port 22/Port 26/' /etc/ssh/sshd_config
# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd


##############################################################################
# BUILD
##############################################################################
FROM base as builder-common

RUN apt-get update && apt-get install -y wget unzip git build-essential libffi-dev libssl-dev zlib1g-dev

# Python package managers
RUN pip install --upgrade pip && pip install "poetry~=1.1"

##############################################################################
FROM builder-common as builder

# Open-MPI
ENV OPENMPI_VERSION 3.1.6
RUN mkdir /tmp/openmpi && \
    cd /tmp/openmpi && \
    wget https://download.open-mpi.org/release/open-mpi/v3.1/openmpi-${OPENMPI_VERSION}.tar.gz && \
    tar zxf openmpi-${OPENMPI_VERSION}.tar.gz && \
    cd openmpi-${OPENMPI_VERSION} && \
    ./configure --enable-orterun-prefix-by-default --prefix=/app/deps/openmpi && \
    make -j $(nproc) all && \
    make install && \
    ldconfig && \
    rm -rf /tmp/openmpi


# Append OpenMPI installation path so rexfw can find it during install
ENV PATH=$PATH:/app/deps/openmpi/bin
ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/app/deps/openmpi/lib


# Install the controller
COPY ./lib/common /app/lib/common
COPY ./lib/schedule_estimation /app/lib/schedule_estimation
COPY ./lib/runners /app/lib/runners
COPY ./lib/grpc /app/lib/grpc
COPY ./app/controller /app/app/controller

# --extras input for poetry install
ARG RUNNERS="rexfw"

RUN cd /app/app/controller && \
    poetry config virtualenvs.in-project true && \
    poetry run pip install --upgrade pip && \
    poetry install --no-dev --extras ${RUNNERS}


##############################################################################
# FINAL
##############################################################################
FROM system-deps as app

COPY --from=builder /app /app

# Extra configuration
ADD docker/node/.openmpi /root/.openmpi
ADD docker/node/ssh/known_hosts /etc/ssh/ssh_config
ADD docker/node/entrypoint.sh /app/entrypoint.sh

# Directory for user data
RUN mkdir -p /probability

# Append OpenMPI installation path
ENV PATH=$PATH:/app/deps/openmpi/bin
ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/app/deps/openmpi/lib

# User-defined functions and data
ENV PATH=$PATH:/probability
ENV PYTHONPATH=$PYTHONPATH:/probability

# Adding the app venv bin to the front of path so it is the default pip, etc.
ENV PATH=/app/app/controller/.venv/bin:$PATH


# For SSH. Using non-default ssh port.
EXPOSE 26

WORKDIR /probability

ENTRYPOINT ["/app/entrypoint.sh"]

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
    apt-get install -y curl openssh-client openssh-server
# # Clear cache
#  && \  rm -rf /var/lib/apt/lists/*


##############################################################################
# BUILD
##############################################################################
FROM base as builder-common

RUN apt-get update && apt-get install -y wget build-essential libffi-dev libssl-dev zlib1g-dev

# Python package managers
RUN pip install --upgrade pip && pip install "poetry~=1.1"

##############################################################################
FROM builder-common as builder-rexfw

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


# Append OpenMPI installation path
ENV PATH=$PATH:/app/deps/openmpi/bin
ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/app/deps/openmpi/lib

RUN python -m venv /app/deps/rexfw && \
    /app/deps/rexfw/bin/pip install https://github.com/tweag/rexfw/archive/78d92fd7e34aefd3b857ae7e0b1f6fb90d631f80.zip

##############################################################################
FROM system-deps as base-node 

# COPY --from=builder /app/code/pipelines/dag-triggers/.venv /app/venv
# COPY --from=builder /app/code/mlinfra /app/code/mlinfra
# Open-MPI

# The rexfw app
COPY --from=builder-rexfw /app /app

# Extra configuration
ADD docker/node/.openmpi /root/.openmpi

EXPOSE 22

# Append OpenMPI installation path
ENV PATH=$PATH:/app/deps/openmpi/bin
ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/app/deps/openmpi/lib

# TODO move this above

# TODO: We might be able to restrict this to 'prohibit-password' for the actual deployment
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
# Disable password authentication
RUN sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
# Listen on a non-default port to avoid clashing with the host's ssh
RUN sed -i 's/#Port 22/Port 26/' /etc/ssh/sshd_config
# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

COPY docker/node/base/entrypoint.sh /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

# rexfw executable and modeling virtual environment. User defined functions are built here

# # Note: we need to build in the app dir to ensure the eggs for the local dependencies
# #   match our final environment.
# RUN mkdir /app/code
# COPY code /app/code

# WORKDIR /app/code/pipelines/dag-triggers
# RUN poetry config virtualenvs.in-project true && poetry run pip install --upgrade pip
# RUN poetry install

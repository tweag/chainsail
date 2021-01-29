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
    apt-get install -y curl openssh-client openssh-server && \
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


# Append OpenMPI installation path so rexfw can find it during install
ENV PATH=$PATH:/app/deps/openmpi/bin
ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/app/deps/openmpi/lib

# Add ssh entry for Github
# See: https://help.github.com/en/github/authenticating-to-github/githubs-ssh-key-fingerprints
RUN echo "github.com ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAq2A7hRGmdnm9tUD\
    bO9IDSwBK6TbQa+PXYPCPy6rbTrTtw7PHkccKrpp0yVhp5HdEIcKr6pLlVDBfO\
    LX9QUsyCOV0wzfjIJNlGEYsdlLJizHhbn2mUjvSAHQqZETYP81eFzLQNnPHt4E\
    VVUh7VfDESU84KezmD5QlWpXLmvU31/yMf+Se8xhHTvKSCZIFImWwoG6mbUoWf\
    9nzpIoaSjB+weqqUUmpaaasXVal72J+UX2B+2RPW3RcT0eOzQgqlJL3RKrTJvd\
    sjE3JEAvGq3lGHSZXy28G3skua2SmVi/w4yCE6gbODqnTWlg7+wC604ydGXA8V\
    JiS5ap43JXiUFFAaQ==" \
    >> /etc/ssh/ssh_known_hosts

# Install rexfw. Need to clone instead of fetching the zip archive
# to ensure that we can also check out the required submodules.
ARG REXFW_BRANCH="start-script"
ARG REXFW_COMMIT="01e7b035ad4b41aeda03b31701253de075b99a59"
RUN cd /app/deps && \
    git clone --recurse-submodules git@github.com:tweag/rexfw.git && \
    cd /app/deps/rexfw && \
    echo $(ls -lah /app/deps/rexfw/resaas/ ) && \
    git checkout "${REXFW_BRANCH}" && \
    poetry config virtualenvs.in-project true && \
    poetry run pip install --upgrade pip && \
    poetry install
##############################################################################
# FROM system-deps as base-node 

# # COPY --from=builder /app/code/pipelines/dag-triggers/.venv /app/venv
# # COPY --from=builder /app/code/mlinfra /app/code/mlinfra
# # Open-MPI

# # The rexfw app
# COPY --from=builder-rexfw /app /app

# # Extra configuration
# ADD docker/node/.openmpi /root/.openmpi

# EXPOSE 22

# # Append OpenMPI installation path
# ENV PATH=$PATH:/app/deps/openmpi/bin
# ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/app/deps/openmpi/lib

# # TODO move this above


# COPY docker/node/base/entrypoint.sh /entrypoint.sh

# ENTRYPOINT ["/entrypoint.sh"]

# # rexfw executable and modeling virtual environment. User defined functions are built here

# # # Note: we need to build in the app dir to ensure the eggs for the local dependencies
# # #   match our final environment.
# # RUN mkdir /app/code
# # COPY code /app/code

# # WORKDIR /app/code/pipelines/dag-triggers
# # RUN poetry config virtualenvs.in-project true && poetry run pip install --upgrade pip
# # RUN poetry install
# RUN poetry config virtualenvs.in-project true && poetry run pip install --upgrade pip
# RUN poetry install

# ##############################################################################
# # OUTPUT
# ##############################################################################
# FROM system-deps as final
# RUN mkdir /app/venv && mkdir -p /app/code/mlinfra
# COPY --from=builder /app/code/pipelines/dag-triggers/.venv /app/venv
# COPY --from=builder /app/code/mlinfra /app/code/mlinfra

# WORKDIR /app
# ENV PATH=/app/venv/bin:$PATH

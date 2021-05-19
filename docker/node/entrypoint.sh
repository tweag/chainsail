#!/usr/bin/env bash

set -ex

mkdir -p /root/.ssh

# Copy over ssh public key(s) for ssh server and adjust permissions
if [ -f /app/config/ssh/authorized_keys ]; then
    echo "Found ssh keys for server. Installing."
    cp /app/config/ssh/authorized_keys /root/.ssh/authorized_keys
    chown root /root/.ssh/authorized_keys
    chmod 600 /root/.ssh/authorized_keys
else
    echo "No ssh public keys found for server."
fi

# wait up to 5 minutes for user code server to be ready
# during that time, the user code server can install dependencies
if wait-for-it -t 300 localhost:50052; then
    echo User code gRPC server is ready
    exec "$@"
else
    echo User code gRPC server unreachable
    exit 1
fi

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

exec "$@"

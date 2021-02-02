#!/usr/bin/env bash

set -e

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

# Allow for the specification of an additional install script
# for fetching and installing user dependencies.
if [ -z "$USER_INSTALL_SCRIPT" ]
then
      echo 'USER_INSTALL_SCRIPT not specified. No extra install steps.'
else
      echo "Executing additional install script at $USER_INSTALL_SCRIPT"
      bash "$USER_INSTALL_SCRIPT"
fi

exec "$@"

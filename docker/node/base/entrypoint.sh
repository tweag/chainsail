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

# if [ -z "$USER_DATA_URL" ]
# then
#       echo 'USER_DATA_URL not specified. Not fetching any data.'
# else
#       echo "Downloading user data from $USER_DATA_URL"
#       curl -L 
# fi

exec "$@"

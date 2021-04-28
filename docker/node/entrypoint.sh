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

# Allow for fetching of user-defined zip file with data / PDF 
if [ -z "$USER_PROB_URL" ]
then
      echo 'USER_PROB_URL not specified. No user defined data to fetch.'
else
      echo "Fetching user probability definition zipfile at $USER_PROB_URL"
      mkdir -p /probability
      wget -O /probability/prob_def.zip "$USER_PROB_URL"
      # Flattening directory structure (-j flag) on unzip for initial prototype. This
      # means that nested directory structures in the zipfile are NOT 
      # supported.
      echo $(ls -lah /probability)
      unzip -o -j /probability/prob_def.zip -d /probability
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

# wait up to 30 seconds for user code server to be ready
if wait-for-it -t 30 localhost:50052; then
    echo User code gRPC server is ready
    exec "$@"
else
    echo User code gRPC server unreachable
    exit 1
fi

#!/usr/bin/env bash

set -ex

mkdir -p /root/.ssh
cp /app/config/ssh/authorized_keys /root/.ssh/authorized_keys
chown root /root/.ssh/authorized_keys
chmod 600 /root/.ssh/authorized_keys

exec "$@"

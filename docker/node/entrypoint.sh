#!/usr/bin/env bash

set -ex

mkdir -p /root/.ssh

# wait up to 5 minutes for user code server to be ready
# during that time, the user code server can install dependencies
if wait-for-it -t 300 localhost:50052; then
    echo User code gRPC server is ready
    exec "$@"
else
    echo User code gRPC server unreachable
    exit 1
fi

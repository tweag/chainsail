#!/usr/bin/env bash

set -ex

mkdir -p /root/.ssh

exec "$@"

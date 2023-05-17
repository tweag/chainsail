#!/usr/bin/env bash

set -euo pipefail

SCHEDULER_URL=$(minikube service scheduler --url)
MCMC_STATS_URL=$(minikube service mcmc-stats-server --url)
GRAPHITE_URL=$(minikube service graphite --url | head -n1)

export SCHEDULER_URL
export GRAPHITE_URL
export MCMC_STATS_URL
yarn run dev

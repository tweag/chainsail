#!/usr/bin/env bash
cd $1
poetry run run_simulation "${@:2}"

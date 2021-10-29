#!/usr/bin/env bash

set -ex

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

# Allow to run some command for checks
if [ "$DO_USER_CODE_CHECK" -eq "1" ]
then
      echo "Running checks on user code"
      python /app/app/user_code_server/chainsail/user_code_server/check_user_code.py
else
      echo "Skipping checks on user code"
fi

# Allow to run only user code check
if [ "$NO_SERVER" -eq "1" ]
then
      echo 'Skipping user code server startup'
else
      echo 'Starting user code server'
      # TODO: bash interprets the Python + args command as a single command "python arg1 arg2", I think :-(
      # So hardcoding this for now
      # exec "$@"
      python /app/app/user_code_server/chainsail/user_code_server/__init__.py --port $USER_CODE_SERVER_PORT --remote_logging_config $REMOTE_LOGGING_CONFIG_PATH
fi

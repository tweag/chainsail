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

# TODO: bash interprets the Python + args command as a single command "python arg1 arg2", I think :-(
# So hardcoding this for now
# exec "$@"
python /app/app/user_code_server/resaas/user_code_server/__init__.py --port $USER_CODE_SERVER_PORT

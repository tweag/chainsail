#!/usr/bin/env bash
# 1 argument to provide : the bucket name to store the results of the chainsail runs.

# Arguments
if [ "$#" -ne 1 ]; then
    echo "Illegal number of parameters."
    exit 1
fi
BUCKET_NAME=$1
INTERNAL_IP=$(gcloud compute instances list --filter="name=('$(hostname)')" --format='[no-heading](INTERNAL_IP)')

# Fetch secret config files
rm -rf config_dpl
cp -r config/ config_dpl
cd config_dpl || exit

echo "Fetching docker/config_dpl/storage.yaml"
gcloud secrets versions access 1 --secret="storage-yaml" > storage.yaml
sed -ri "s/(container_name:).*/\1 $BUCKET_NAME/" storage.yaml

echo "Fetching docker/config_dpl/controller.yaml"
gcloud secrets versions access 2 --secret="controller-yaml" > controller.yaml
sed -ri "s/(scheduler_address:).*/\1 $INTERNAL_IP/" controller.yaml
sed -ri "s/(metrics_address:).*/\1 $INTERNAL_IP/" controller.yaml

echo "Fetching docker/config_dpl/scheduler.yaml"
gcloud secrets versions access 2 --secret="scheduler-yaml" > scheduler.yaml

echo "Fetching docker/config_dpl/remote_logging.yaml"
gcloud secrets versions access 2 --secret="remote-logging-yaml" > remote_logging.yaml
sed -ri "s/(address:).*/\1 $INTERNAL_IP/" remote_logging.yaml

echo "Fetching docker/config_dpl/firebase_service_account.json"
gcloud secrets versions access 1 --secret="firebase-sa" > firebase_service_account.json

# Fetch .env.local
cd ../../app/client || exit
echo "Fetching app/client/.env.local"
gcloud secrets versions access 1 --secret="env-local" > .env.local

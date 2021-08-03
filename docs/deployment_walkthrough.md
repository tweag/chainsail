# Setup guide for hybrid deployment : local apps, cloud resources
This guide describes step by step how to deploy the service from scratch, with the client run locally but using Google Cloud Platform (GCP) resources.

## Storage bucket setup
Create a bucket to hold results of the sampling jobs from the [Google cloud console](https://console.cloud.google.com/). In **Cloud Storage**, click **Create bucket**, and set a *name* for the bucket.

## Virtual machine setup
- Create a virtual machine (VM) instance from the [Google cloud console](https://console.cloud.google.com/).
  - In **Compute Engine**, click **Create an instance**
  - In **Identity and API access** :
    - in **Service account**, select **"resaas-gce"**
    - select **Allow full access to all Cloud APIs**
- On your local machine, install the [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
- Connect to the instance and bind the ports for the scheduler (5000) and graphite (8080)
  ```bash
  gcloud compute config-ssh
  ssh <vm-instance-name>.<region-name>.resaas-simeon-dev -L 5000:localhost:5000 -L 8080:localhost:8080
  # for example : resaas-dev.europe-west3-c.resaas-simeon-dev
  ```

## Run the service on the cloud VM
On the newly created VM :
- Install [Docker](https://docs.docker.com/get-docker/)
- Install [Docker Compose](https://docs.docker.com/compose/install/)
- Clone this repository
  ```bash
  git clone https://github.com/tweag/resaas/
  ```
- Fetch config files from the secret manager
  ```bash
  cd resaas/docker/
  ./setup-cloud-config.sh <bucket-name-for-results>  # Bucket must already exist
  ```
- Fetch the deployment version of `docker-compose.yaml` from the secret manager
  ```bash
  gcloud secrets versions access latest --secret="docker-compose-yaml" > docker-compose.yaml
  ```
- Build docker images
  ```bash
  docker build -t "chainsail-celery-worker:latest" -f ./celery/Dockerfile ../
  docker build -t "chainsail-scheduler:latest" -f ./scheduler/Dockerfile ../
  docker build -t "chainsail-nginx:latest" -f ./nginx/Dockerfile ../
  ```
- launch docker-compose up
  ```bash
  docker-compose -f docker-compose.yaml up
  ```

## Run the client locally
See instructions [here](https://github.com/tweag/resaas/tree/etienne/use-secret-manager/app/client#develop).

## Access the app
The app can then be accessed through a browser, at [http://localhost:3000/]()

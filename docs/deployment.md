# Deploying chainsail

Chainsail is designed to be run on a kubernetes cluster either locally or in the cloud. We use the following set of tools for deploying chainsail:

  * Terraform - Used for provisioning cloud resources and base k8s cluster resources
  * Docker - For building chainsail images
  * Helm - For installing chainsail itself

This guide describes how to set up a chainsail environment from scratch, either locally or in the cloud.
#
## Table of Contents
- [Deploying chainsail](#deploying-chainsail)
  - [Table of Contents](#table-of-contents)
  - [Local deployment](#local-deployment)
    - [Initial Setup](#initial-setup)
    - [Deploying changes](#deploying-changes)
  - [Cloud deployment](#cloud-deployment)
    - [1. Provision the cloud environment on Google Cloud](#1-provision-the-cloud-environment-on-google-cloud)
    - [2. Provision the kubernetes cluster](#2-provision-the-kubernetes-cluster)
    - [3. Deploy chainsail back-end](#3-deploy-chainsail-back-end)
    - [4. Deploy chainsail front-end](#4-deploy-chainsail-front-end)
    - [5. Additional steps](#5-additional-steps)
  - [Maintenance / Development](#maintenance--development)
    - [Upgrading chainsail](#upgrading-chainsail)
    - [Allowing / disallowing application users](#allowing--disallowing-application-users)
#
## Local deployment

### Initial Setup

To deploy locally, you need to start a local cluster using minikube:

```console
minikube start
```

Then you can provision cluster resources with:

```console
cd ./terraform/clusters/local

# The first time you run terraform you need to run an init command:
terraform init

terraform apply
```

The local cluster uses `minio` for local object storage.

Note: Minikube has its own Docker registry, so if you want to deploy *local* versions
of chainsail you will need to build the latest version of its Docker images
and add them to Minikube's Docker registry. One way to do this is:

```console
# This makes docker commands use Minikube's Docker daemon
eval $(minikube docker-env)

HUB_NAMESPACE="eu.gcr.io/resaas-simeon-dev/" make images
```
The hub namespace environment variable has to match the value of the `imageHubNamespace` property in `helm/values.yaml`, but with a trailing slash (`/`).

Then, you can install Chainsail with Helm:

```console
helm install -f helm/values-local.yaml chainsail ./helm
```

### Running the client locally

For development purposes, you can run the frontend web app locally.
But to get access to your minikube services, you need to create service tunnels.
To do that, first get a list of all services with
```console
kubectl get svc
```
For each service (`scheduler` / `graphite` / `mcmc-stats-server`) you now need to establish a service tunnel via
```console
minikube service <service> --url &
```
. That command will print the URL and port at which the respective service will be reachable.

With that in hand, you can follow the instruction in the [`frontend README`](app/client/README#Develop), but skip the SSH tunneling part.
In the final call to `yarn run dev`, adapt the URLs in the environment variables to match the output of the service tunnel commands.

### Deploying changes

Each time you make local changes to the chainsail back-end, re-build the Docker image(s) for the services you have modified and run a Helm upgrade to deploy them locally:

```console
eval $(minikube docker-env)
make images
helm upgrade -f helm/values-local.yaml chainsail ./helm
```

## Cloud deployment

### Prerequisites
You need to make sure that your local Google Cloud credentials are set correctly.
To that end, run
```console
gcloud auth application-default login --project resaas-simeon-dev
``` 
.

### 1. Provision the cloud environment on Google Cloud

The first step in preparing a new chainsail environment is ensuring that (1) a Google Cloud Project already exists, (2) you have adequate access rights in the project to deploy infrastructure, and (3) the GCS bucket for storing the Terraform state has already been created. If you try running the commands in this guide without these pre-requisites, you'll likely run into some error messages.

```console
cd ./terraform/base/dev

# The first time you run terraform you need to run an init command:
terraform init

terraform apply
```

### 2. Provision the kubernetes cluster

With the base Google Cloud environment created, we can now provision the kubernetes cluster. This step creates things like k8s service accounts and the k8s secrets required to run chainsail.

```console
cd ./terraform/clusters/dev

# The first time you run terraform you need to run an init command:
terraform init

terraform apply
```

### 3. Deploy chainsail back-end

If Docker images have not already been built and pushed to the Google Cloud Container Registry for your desired version of chainsail, you should go ahead and build those now.
In order to be able to push the images to the container registry, your user needs to have access to the `eu.artifacts.resaas-simeon-dev` bucket.
The name of the bucket might vary depending on the `zone` and `node_location` entries in the `chainsail_gcp` Terraform module in `terraform/base/dev/main.tf`.

To build and push images, run
```console
HUB_NAMESPACE="eu.gcr.io/resaas-simeon-dev/" make push-images
```

The first time you deploy chainsail, you will need to fetch the cluster's kubernetes access credentials using `gcloud`:

```console
gcloud container clusters get-credentials --region $GCP_REGION chainsail
```
The GCP region can be found in `terraform/base/dev/main.tf` in the `node_location` entry of the `chainsail_gcp` module.

Once all of the desired images are published, you can install chainsail with:

```console
helm install -f helm/values-dev.yaml chainsail ./helm
```

### 4. Deploy chainsail front-end

The chainsail front-end is currently deployed separately using App Engine:

> **Note: The App Engine app.yaml is generated by Terraform. Run the `terraform/base/<env-name>` module to recreate it.

```console
cd app/client
npm run deploy
```
### 5. Additional steps

There are a couple of additional steps which need to be configured manually:

1. A Firebase project must exist which corresponds to your Google Cloud Project.

2. The app engine domain created in (4) must manually set as an authorized domain in Firebase at https://console.firebase.google.com

3. A VPC Connector must be created for the region in which you have deployed chainsail (See https://cloud.google.com/vpc/docs/configure-serverless-vpc-access)


## Maintenance / Development
### Upgrading chainsail

To upgrade an already running chainsail cluster to a newer version of the chart. Use:

```console
helm upgrade -f helm/values-dev.yaml chainsail ./helm
```

If using the `latest` tag for images in the helm chart, you will also need to restart the services so that
the latest image is pulled:

```console
kubectl rollout restart deployment scheduler-worker
kubectl rollout restart deployment scheduler
kubectl rollout restart deployment mcmc-stats-server
```

### Allowing / disallowing application users

The scheduler pod supports adding / removing user email addresses from the allowed users whitelist.

To add a user:

```console
export SCHEDULER_POD=$(kubectl get pods -l chainsail.io.service=scheduler -o jsonpath='{.items[0]..metadata.name}')

kubectl exec $SCHEDULER_POD -- scheduler-add-user --email someone@tweag.io
```

To remove a user:

```console
kubectl exec $SCHEDULER_POD -- scheduler-remove-user --email someone@tweag.io
```

# Deploying Chainsail

Chainsail is designed to be run on a Kubernetes cluster either locally or in the cloud. We use the following set of tools for deploying chainsail:

  * Terraform - Used for provisioning cloud resources and base k8s cluster resources
  * Docker - For building Chainsail images
  * Helm - For installing Chainsail itself

This guide describes how to set up a Chainsail environment from scratch, either locally or in the cloud.
#
## Table of Contents
- [Deploying Chainsail](#deploying-chainsail)
  - [Table of Contents](#table-of-contents)
  - [Prerequisites](#prerequisites-for-both-minikube-and-google-cloud-deployment)
  - [Local deployment](#local-deployment)
    - [Initial Setup](#initial-setup)
    - [Deploying changes](#deploying-changes)
  - [Cloud deployment](#cloud-deployment)
    - [1. Provision the cloud environment on Google Cloud](#1-provision-the-cloud-environment-on-google-cloud)
    - [2. Provision the Kubernetes cluster](#2-provision-the-kubernetes-cluster)
    - [3. Deploy Chainsail back-end](#3-deploy-chainsail-back-end)
    - [4. Deploy Chainsail front-end](#4-deploy-chainsail-front-end)
    - [5. Additional steps](#5-additional-steps)
  - [Maintenance / Development](#maintenance--development)
    - [Upgrading Chainsail](#upgrading-chainsail)
    - [Allowing / disallowing application users](#allowing--disallowing-application-users)
#

## Prerequisites for both Minikube and Google Cloud deployment
Make sure that you correctly edit the Terraform and Helm files.
Specifically, you'll want to make sure that you have matching container registry in
the following files / environment variables:
- `/terraform/cluster/local/main.tf` (`container_registry` in the `locals` block),
- `/helm/values.yaml` (`imageHubNamespace`),
- `/helm/values-local.yaml` (`imageHubNamespace`),
- `/helm/values-dev.yaml` (`imageHubNamespace`),if you're considering a Google Cloud deployment,
- and the `HUB_NAMESPACE` environment variable later.

## Local deployment

### Initial Setup

To deploy locally, you first need to start a local cluster using Minikube:

```bash
minikube start
```

Then you can provision cluster resources with:

```bash
cd ./terraform/cluster/local

# The first time you run terraform you need to run an init command:
terraform init

terraform apply
```

The local cluster uses `minio` for local object storage.

Note: Minikube has its own Docker registry, so if you want to deploy *local* versions
of Chainsail you will need to build the latest version of its Docker images
and add them to Minikube's Docker registry. One way to do this is:

```bash
# This makes docker commands use Minikube's Docker daemon
eval $(minikube docker-env)

HUB_NAMESPACE="<container registry>/" make images
```
The hub namespace environment variable has to match the value of the `imageHubNamespace` property in `helm/values.yaml` and the `container_registry` value in the `locals` block of `terraform/cluster/local/main.tf`.

Then, you can install Chainsail with Helm:

```bash
helm install -f helm/values-local.yaml chainsail ./helm
```

### Running the client locally

For development purposes, you can run the frontend web app locally.
But to get access to your Minikube services, you need to create service tunnels.
To do that, first get a list of all services with
```bash
kubectl get svc
```
For each service (`scheduler` / `graphite` / `mcmc-stats-server`) you now need to establish a service tunnel via
```bash
minikube service <service> --url &
```
. That command will print the URL and port at which the respective service will be reachable.

With that in hand, you can follow the instruction in the [`frontend README`](app/client/README#Develop), but skip the SSH tunneling part.
In the final call to `yarn run dev`, adapt the URLs in the environment variables to match the output of the service tunnel commands.

:warning: the link provided by the client to download samples won't work when Chainsail is deployed via Minikube, the reason being that the host machine does not see the Minikube-internal DNS server by default. To download sampling results, use the following command:
```bash
kubectl exec minio-0 -- curl --output - '<URL from download button>' >results.zip
```

### Deploying changes

Each time you make local changes to the Chainsail back-end, re-build the Docker image(s) for the services you have modified and run a Helm upgrade to deploy them locally:

```bash
eval $(minikube docker-env)
make images
helm upgrade -f helm/values-local.yaml chainsail ./helm
```

## Cloud deployment

### Prerequisites
In addition to the general [Prerequisites](#prerequisites-for-both-minikube-and-google-cloud-deployment),
- Make sure that your local Google Cloud credentials are set correctly.
  To that end, run
  ```bash
  gcloud auth application-default login --project <project name>
  ```
  .
- Fill in your Google Cloud project name and -region in `terraform/base/dev/main.tf` and `terraform/cluster/dev/main.tf`
- Manually provision a Google Cloud Storage bucket `chainsail-dev-terraform-state` that holds the Terraform state.

### 1. Provision the cloud environment on Google Cloud

The first step in preparing a new Chainsail environment is ensuring that (1) a Google Cloud Project already exists, (2) you have adequate access rights in the project to deploy infrastructure, and (3) the GCS bucket for storing the Terraform state has already been created. If you try running the commands in this guide without these pre-requisites, you'll likely run into some error messages.

```bash
cd ./terraform/base/dev

# The first time you run terraform you need to run an init command:
terraform init

terraform apply
```

### 2. Provision the Kubernetes cluster

With the base Google Cloud environment created, we can now provision the Kubernetes cluster. This step creates things like k8s service accounts and the k8s secrets required to run chainsail.

```bash
cd ./terraform/clusters/dev

# The first time you run terraform you need to run an init command:
terraform init

terraform apply
```

### 3. Deploy Chainsail back-end

If Docker images have not already been built and pushed to the Google Cloud Container Registry for your desired version of chainsail, you should go ahead and build those now.
In order to be able to push the images to the container registry, the Google Cloud credentials you use for the following need to have access to the container registry bucket created by Terraform.
It is called something like `<eu, ...>.artifacts.<project name>` bucket.
The name of the bucket might vary depending on the `zone` and `node_location` entries in the `chainsail_gcp` Terraform module in `terraform/base/dev/main.tf`.

To build and push images, run
```bash
HUB_NAMESPACE="<container registry>/" make push-images
```

The hub namespace environment variable has to match the value of the `imageHubNamespace` property in `helm/values.yaml`.

The first time you deploy Chainsail, you will need to fetch the cluster's Kubernetes access credentials using `gcloud`:

```bash
gcloud container clusters get-credentials --region $GCP_REGION chainsail
```
The GCP region can be found in `terraform/base/dev/main.tf` in the `node_location` entry of the `chainsail_gcp` module.

Once all of the desired images are published, you can install Chainsail with:

```bash
helm install -f helm/values-dev.yaml chainsail ./helm
```

### 4. Deploy Chainsail front-end

The Chainsail front-end is currently deployed separately using App Engine:

> **Note: The App Engine app.yaml is generated by Terraform. Run the `terraform/base/<env-name>` module to recreate it.

```bash
cd app/client
npm run deploy
```
### 5. Additional steps

There are a couple of additional steps which need to be configured manually:

1. A Firebase project must exist which corresponds to your Google Cloud Project.

2. The app engine domain created in (4) must manually set as an authorized domain in Firebase at https://console.firebase.google.com

3. A VPC Connector must be created for the region in which you have deployed Chainsail (See https://cloud.google.com/vpc/docs/configure-serverless-vpc-access)


## Maintenance / Development
### Upgrading Chainsail

To upgrade an already running Chainsail cluster to a newer version of the chart. Use:

```bash
helm upgrade -f helm/values-dev.yaml chainsail ./helm
```

If using the `latest` tag for images in the helm chart, you will also need to restart the services so that
the latest image is pulled:

```bash
kubectl rollout restart deployment scheduler-worker
kubectl rollout restart deployment scheduler
kubectl rollout restart deployment mcmc-stats-server
```

### Allowing / disallowing application users

The scheduler pod supports adding / removing user email addresses from the allowed users whitelist.

To add a user:

```bash
export SCHEDULER_POD=$(kubectl get pods -l chainsail.io.service=scheduler -o jsonpath='{.items[0]..metadata.name}')

kubectl exec $SCHEDULER_POD -- scheduler-add-user --email someone@provider.com
```

To remove a user:

```bash
kubectl exec $SCHEDULER_POD -- scheduler-remove-user --email someone@provider.com
```

## Stand-alone deployment of the controller

See the instructions in [/app/controller/README.md])(app/controller/README.md).

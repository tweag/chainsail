# terraform

Infrastructure as code for `chainsail`

## Overview

Resources are separated into base environments and cluster-specific resouces
within the `cluster/` and `base/` directories. Base environments must be
deployed prior to application-specific resources.

* `dev` - The chainsail dev environment on Google Cloud
  * `./base/dev` - Base GCP resources
  * `./cluster/dev`  - Application-specific resources

* `./cluster/local` - A local environment for testing out changes which is
  powered by [Minikube](https://minikube.sigs.k8s.io/docs/)

## Workflow

## Local

Local deployments assume that `minikube` is already running:

```console
minikube start
```

With `minikube` started you can provision the cluster by running:

```console
$ cd ./cluster/local
$ terraform terraform apply
```

Note that for local deployments the Terraform state only lives locally on your
machine.

## Cloud

For each environment, the deployment workflow is to enter the environment's
directories and run Terraform commands from there. For example:

```console
$ cd ./base/<env>
$ terraform apply
```

then

```
$ cd ./cluster/<env>
$ terraform apply
```

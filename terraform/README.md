# terraform

Infrastructure as code for `chainsail`

## Overview

Terraform config covers the following scope:
  1. Base resources (buckets, etc.), defined in `./base`
  2. Cluster resources (secrets, SAs, etc.), defined in `./clusters`. These do **not**
     include the application services themselves. Those are defined as a helm chart in [../helm](../helm).

The Terraform config does **not** include definitions for the client, which is instead
managed via the App Engine CLI. See [../app/client](../app/client) for more details.

Resources are separated into base environments and cluster-specific resouces
within the `cluster/` and `base/` directories. Base environments must be
deployed prior to application-specific resources.

* `dev` - The chainsail dev environment on Google Cloud
  * `./base/dev` - Base GCP resources
  * `./cluster/dev`  - Application-specific resources

* `./cluster/local` - A local environment for testing out changes which is
  powered by [Minikube](https://minikube.sigs.k8s.io/docs/)

## Workflow

See the deployment docs at [../docs/deployment.md](../docs/deployment.md).

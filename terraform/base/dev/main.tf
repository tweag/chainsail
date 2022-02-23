###############################################################################
# Providers
###############################################################################

terraform {
  required_version = ">=1.1.5"
  backend "gcs" {
    # Note: Bucket must be manually provisioned if it doesn't exist
    bucket = "chainsail-dev-terraform-state"
    prefix = "terraform/state/dev-base"
  }
}

locals {
  project = "resaas-simeon-dev"
  region  = "europe-west3"
}

provider "google" {
  project = local.project
  region  = local.region
}

data "google_client_config" "default" {}
data "google_project" "project" {}

###############################################################################
# Modules
###############################################################################


module "chainsail_gcp" {
  source              = "../../modules/chainsail-gcp"
  storage_location    = "EU"
  node_location       = "europe-west3-a"
  core_node_type      = "e2-standard-8"
  job_node_type       = "e2-standard-8"
  ssh_pem_secret_name = "chainsail_job_ssh_pem"
  ssh_pub_secret_name = "chainsail_job_ssh_pub"
}

###############################################################################
# Local files
###############################################################################

# Generate app engine yaml file for convenience
# TODO: This should probably live as a secret on Google Cloud eventually
resource "local_file" "app_yaml" {
  filename = "../../../app/client/app.yaml"
  content  = <<EOT
env: standard
runtime: nodejs12
service: default

env_variables:
  GRAPHITE_URL: http://${trim(module.chainsail_gcp.ingress_fqdn, ".")}/graphite
  SCHEDULER_URL: http://${trim(module.chainsail_gcp.ingress_fqdn, ".")}/scheduler
  MCMC_STATS_URL: http://${trim(module.chainsail_gcp.ingress_fqdn, ".")}/mcmc-stats

vpc_access_connector:
  name: projects/${data.google_project.project.number}/locations/${local.region}/connectors/client-vm-connector

handlers:
  - url: /.*
    secure: always
    script: auto

EOT
}

###############################################################################
# Providers
###############################################################################

terraform {
  required_version = "=1.1.5"
  backend "gcs" {
    # Note: Bucket must be manually provisioned if it doesn't exist
    bucket = "chainsail-dev-terraform-state"
    prefix = "terraform/state/dev-base"
  }
}

provider "google" {
  project = "resaas-simeon-dev"
  region  = "europe-west3"
}

data "google_client_config" "default" {}
data "google_project" "project" {}

###############################################################################
# Modules
###############################################################################


module "chainsail_gcp" {
  source              = "../../modules/chainsail-gcp"
  storage_location    = "EU"
  node_location       = "europe-west6-a"
  core_node_type      = "e2-standard-8"
  job_node_type       = "e2-standard-8"
  ssh_pem_secret_name = "chainsail_job_ssh_pem"
  ssh_pub_secret_name = "chainsail_job_ssh_pub"
}

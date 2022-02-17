
###############################################################################
# Providers
###############################################################################

terraform {
  required_version = "=1.1.5"
  backend "gcs" {
    # Note: Bucket must be manually provisioned if it doesn't exist
    bucket = "chainsail-dev-terraform-state"
    prefix = "terraform/state/dev-app"
  }
}

provider "google" {
  project = "resaas-simeon-dev"
  region  = "europe-west6"
}

data "google_client_config" "default" {}
data "google_project" "project" {}

# Fetch pre-populated environment config

data "google_secret_manager_secret_version" "chainsail_environment_config" {
  // Note: using latest secret version
  secret = "chainsail-environment-config"
}

locals {
  env_config = jsondecode(data.google_secret_manager_secret_version.chainsail_environment_config.secret_data)
}

data "google_container_cluster" "chainsail" {
  name     = local.env_config.cluster_name
  location = local.env_config.cluster_location
}

data "google_secret_manager_secret_version" "ssh_pem" {
  // Note: using latest secret version
  secret = "chainsail_job_ssh_pem"
}

data "google_secret_manager_secret_version" "ssh_pub" {
  // Note: using latest secret version
  secret = "chainsail_job_ssh_pub"
}

provider "kubernetes" {
  host                   = "https://${data.google_container_cluster.chainsail.endpoint}"
  token                  = data.google_client_config.default.access_token
  cluster_ca_certificate = base64decode(data.google_container_cluster.chainsail.master_auth[0].cluster_ca_certificate)
}

###############################################################################
# Modules
###############################################################################

locals {
  storage_yaml = yamlencode({
    backend = "cloud"
    backend_config = {
      local = {}
      cloud = {
        libcloud_provider = "GOOGLE_STORAGE"
        container_name    = local.env_config.storage_bucket
        driver_kwargs = {
          key     = local.env_config.storage_access_id
          secret  = local.env_config.storage_secret_key
          project = data.google_project.project.name
        }
      }
    }
    }
  )
}

module "chainsail_k8s" {
  source             = "../../modules/chainsail-k8s"
  job_ssh_pem        = base64encode(data.google_secret_manager_secret_version.ssh_pem.secret_data)
  job_ssh_pub        = base64encode(data.google_secret_manager_secret_version.ssh_pub.secret_data)
  storage_yaml       = local.storage_yaml
  storage_url        = "https://storage.googleapis.com"
  storage_access_key = local.env_config.storage_access_id
  storage_secret_key = local.env_config.storage_secret_key
  storage_bucket     = local.env_config.storage_bucket
  image_controller   = "${local.env_config.container_registry}/chainsail-mpi-node-k8s:latest"
  image_worker       = "${local.env_config.container_registry}/chainsail-mpi-node-k8s:latest"
  image_httpstan     = "${local.env_config.container_registry}/httpstan-server:latest"
  image_user_code    = "${local.env_config.container_registry}/chainsail-user-code:latest"
  image_pull_policy  = "Always"
}

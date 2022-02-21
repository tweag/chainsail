
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
  region  = "europe-west3"
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
provider "helm" {
  kubernetes {
    host                   = "https://${data.google_container_cluster.chainsail.endpoint}"
    token                  = data.google_client_config.default.access_token
    cluster_ca_certificate = base64decode(data.google_container_cluster.chainsail.master_auth[0].cluster_ca_certificate)
  }
}
###############################################################################
# Modules
###############################################################################

locals {
  scheduler_service_name = "scheduler"
  scheduler_service_port = "5001"

  graphite_service_name = "graphite"
  graphite_service_port = "8080"

  mcmc_stats_service_name = "mcmc-stats-server"
  mcmc_stats_service_port = "5002"

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
# https://kubernetes.github.io/ingress-nginx

resource "helm_release" "ingress_nginx" {
  name       = "ingress-nginx"
  repository = "https://kubernetes.github.io/ingress-nginx"
  chart      = "ingress-nginx"
  version    = "4.0.16"
  values = [<<EOT
controller:
  service:
    external:
      enabled: false
    internal:
      enabled: true
      # Assign static IP
      loadBalancerIP: ${local.env_config.backend_address}
      annotations:
        # Create internal LB
        cloud.google.com/load-balancer-type: 'Internal'
EOT
  ]
}


# This ingress is the primary way the chainsail backend should be accessed via the internal network
resource "kubernetes_ingress" "chainsail_backend" {
  depends_on = [helm_release.ingress_nginx]
  # Note: setting this to false so that Terraform will return even if the services
  # aren't available. This allows us to install those later via Helm.
  wait_for_load_balancer = false
  metadata {
    name = "chainsail-backend-ingress"
    annotations = {
      "kubernetes.io/ingress.class" = "nginx",
      "nginx.ingress.kubernetes.io/rewrite-target" : "/$2"
    }
  }
  # Note: since we have multiple services exposed under different routes we need to re-write the prefix
  # so that the requested url matches the one actually exposed by the service (e.g. some.address/scheduler/jobs should map to some.address/jobs)
  # See this doc for more details: https://github.com/kubernetes/ingress-nginx/tree/main/docs/examples/rewrite
  spec {
    rule {
      http {
        path {
          path = "/scheduler(/|$)(.*)"
          backend {
            service_name = local.scheduler_service_name
            service_port = local.scheduler_service_port
          }
        }
        path {
          path = "/graphite(/|$)(.*)"
          backend {
            service_name = local.graphite_service_name
            service_port = local.graphite_service_port
          }
        }
        path {
          path = "/mcmc-stats(/|$)(.*)"
          backend {
            service_name = local.mcmc_stats_service_name
            service_port = local.mcmc_stats_service_port
          }
        }
      }
    }
  }
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
  image_httpstan     = "${local.env_config.container_registry}/chainsail-httpstan-server:latest"
  image_user_code    = "${local.env_config.container_registry}/chainsail-user-code:latest"
  image_pull_policy  = "Always"
}

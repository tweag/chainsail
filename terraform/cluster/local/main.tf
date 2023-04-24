###############################################################################
# Providers
###############################################################################
terraform {
  required_version = ">=1.0.11"
  backend "local" {
    path = "terraform.tfstate"
  }
  required_providers {
    kubernetes = {
      version = ">= 2.16.1"
      source  = "hashicorp/kubernetes"
    }
  }
}

provider "kubernetes" {
  config_path    = "~/.kube/config"
  config_context = "minikube"
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
        libcloud_provider = "MINIO"
        container_name    = "chainsail-samples"
        driver_kwargs = {
          key    = "chainsail"
          secret = "chainsail"
          host   = "minio.default.svc.cluster.local"
          port   = 9000
          secure = false
        }
      }
    }
    }
  )
}

variable "image_prefix" {
  type    = string
  default = ""
}

module "chainsail-k8s" {
  source             = "../../modules/chainsail-k8s"
  job_ssh_pem        = filebase64("${path.module}/config/unsafe_dev_key_rsa.pem")
  job_ssh_pub        = filebase64("${path.module}/config/unsafe_dev_key_rsa.pub")
  storage_yaml       = local.storage_yaml
  storage_url        = "http://minio.default.svc.cluster.local:9000"
  storage_access_key = "chainsail"
  storage_secret_key = "chainsail"
  storage_bucket     = "chainsail-samples"
  image_controller   = "${var.image_prefix}chainsail-mpi-node-k8s:latest"
  image_worker       = "${var.image_prefix}chainsail-mpi-node-k8s:latest"
  image_httpstan     = "${var.image_prefix}chainsail-httpstan-server:latest"
  image_user_code    = "${var.image_prefix}chainsail-user-code:latest"
}

###############################################################################
# Local object storage
###############################################################################
provider "helm" {
  kubernetes {
    config_path = "~/.kube/config"
  }
}

resource "helm_release" "minio" {
  name       = "minio"
  repository = "https://charts.min.io"
  chart      = "minio"
  version    = "3.4.3"

  values = ["${file("config/values.yaml")}"]
}

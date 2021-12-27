###############################################################################
# Providers
###############################################################################
terraform {
  required_version = "=1.1.2"
  backend "local" {
    path = "terraform.tfstate"
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
          host   = "${data.kubernetes_service.minio.metadata[0].name}.${data.kubernetes_service.minio.metadata[0].namespace}.svc.cluster.local"
          port   = 9000
          secure = false
        }
      }
    }
    }
  )
}


module "chainsail-k8s" {
  source             = "../../modules/chainsail-k8s"
  job_ssh_pem        = filebase64("${path.module}/config/unsafe_dev_key_rsa.pem")
  job_ssh_pub        = filebase64("${path.module}/config/unsafe_dev_key_rsa.pub")
  storage_yaml       = local.storage_yaml
  storage_url        = "http://${data.kubernetes_service.minio.metadata[0].name}.${data.kubernetes_service.minio.metadata[0].namespace}.svc.cluster.local:9000"
  storage_access_key = "chainsail"
  storage_secret_key = "chainsail"
  storage_bucket     = "chainsail-samples"
  # TODO: Make these images match whatever local build script we use
  # for rebuilding images
  image_controller = "chainsail-mpi-node-k8s:latest"
  image_worker     = "chainsail-mpi-node-k8s:latest"
  image_httpstan   = "httpstan-server:latest"
  image_user_code  = "chainsail-user-code:latest"
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

data "kubernetes_service" "minio" {
  metadata {
    name = "minio"
  }
}

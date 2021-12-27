###############################################################################
# Secrets
###############################################################################
resource "kubernetes_secret_v1" "job_ssh_key" {
  metadata {
    name = "job-ssh-key"
  }
  data = {
    pub = "${var.job_ssh_pub}"
    pem = "${var.job_ssh_pem}"
  }
}

resource "kubernetes_secret_v1" "storage_yaml" {
  metadata {
    name = "storage-yaml"
  }
  data = {
    "storage.yaml" = "${var.storage_yaml}"
  }
}

resource "kubernetes_secret_v1" "scheduler_yaml" {
  metadata {
    name = "scheduler-yaml"
  }
  data = {
    "scheduler.yaml" = yamlencode(local.scheduler_yaml)
  }
}

resource "kubernetes_secret_v1" "controller_yaml" {
  metadata {
    name = "controller-yaml"
  }
  data = {
    "controller.yaml" = yamlencode(local.controller_yaml)
  }
}

resource "kubernetes_secret_v1" "remote_logging_yaml" {
  metadata {
    name = "remote-logging-yaml"
  }
  data = {
    "remote_logging.yaml" = yamlencode(local.remote_logging_yaml)
  }
}

# FIXME: This should also be a secret. Need to update the chainsail k8s node implementation
# to use a secret instead of a configmap for this to be possible though.
resource "kubernetes_config_map_v1" "worker_node_config" {
  metadata {
    name = "worker-node-config"
  }
  data = {
    "storage.yaml"        = "${var.storage_yaml}"
    "scheduler.yaml"      = yamlencode(local.scheduler_yaml)
    "controller.yaml"     = yamlencode(local.controller_yaml)
    "remote_logging.yaml" = yamlencode(local.remote_logging_yaml)
  }
}

locals {
  scheduler_yaml = {
    controller = {
      image = "${var.image_controller}"
      cmd   = "chainsail-controller"
      args = [
        "--job",
        "{job_id}",
        # FIXME: Might need to ensure that these paths match the helm chart as well
        "--storage",
        "/chainsail/storage.yaml",
        "--hostsfile",
        "/chainsail-hostfile/hostfile",
        "--job-spec",
        "/chainsail-jobspec/job.json",
        "--config",
        "/chainsail/controller.yaml"
      ]
      ports           = [50051, 26]
      user_code_image = "${var.image_user_code}"
      httpstan_image  = "${var.image_httpstan}"
    }
    worker = {
      image           = "${var.image_worker}"
      cmd             = "/usr/sbin/sshd"
      args            = ["-D"]
      ports           = [26]
      user_code_image = "${var.image_user_code}"
      httpstan_image  = "${var.image_httpstan}"
    }
    # FIXME: Ensure that this path matches helm chart
    remote_logging_config_path = "/config/remote_logging.yaml"
    results_url_expiry_time    = 604800
    node_type                  = "KubernetesPod"
    node_config = {
      # FIXME: Had to hard-code this name to avoid a cyclical dependency
      config_configmap_name = "worker-node-config"
      ssh_public_key        = "${var.job_ssh_pub}"
      # FIXME: These paths need to match in the helm chart values as well
      ssh_private_key_path   = "/config/unsafe_dev_key_rsa"
      storage_config_path    = "/config/storage.yaml"
      controller_config_path = "/config/controller.yaml"
      # TODO: Might want to make these variables in order to allow different values
      # in different environments
      pod_cpu    = "500m"
      pod_memory = "100Mi"
    }
  }

  remote_logging_yaml = {
    enabled     = true
    log_level   = "DEBUG"
    address     = "graphite.default.svc.cluster.local"
    port        = 8080
    buffer_size = 0
  }

  controller_yaml = {
    scheduler_address = "scheduler.default.svc.cluster.local"
    scheduler_port    = 5000
    metrics_address   = "graphite.default.svc.cluster.local"
    metrics_port      = 2004
    runner            = "chainsail.runners.rexfw:MPIRERunner"
    storage_basename  = "/storage"
    log_level         = "DEBUG"
    # FIXME: ensure that this path matches helm chart
    remote_logging_config_path = "/chainsail/remote_logging.yaml"
  }

}

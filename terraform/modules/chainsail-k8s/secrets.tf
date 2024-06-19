###############################################################################
# Secrets
###############################################################################
resource "kubernetes_secret_v1" "job_ssh_key" {
  metadata {
    name = "job-ssh-key"
  }
  binary_data = {
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


# FIXME: This should also be a secret. Need to update the Chainsail k8s node implementation
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
        # FIXME: Might need to ensure that these paths match the Helm chart as well
        "--storage",
        "/chainsail/storage.yaml",
        "--hostfile",
        "/chainsail-hostfile/hostfile",
        "--job-spec",
        "/chainsail-jobspec/job.json",
        "--config",
        "/chainsail/controller.yaml"
      ]
      ports           = [50051, 26]
      user_code_image = "${var.image_user_code}"
    }
    worker = {
      image           = "${var.image_worker}"
      cmd             = "/usr/sbin/sshd"
      args            = ["-D"]
      ports           = [26]
      user_code_image = "${var.image_user_code}"
    }
    # FIXME: Ensure that this path matches helm chart
    remote_logging_config_path = "/config/remote_logging.yaml"
    results_endpoint_url       = var.storage_url
    results_access_key_id      = var.storage_access_key
    results_secret_key         = var.storage_secret_key
    results_bucket             = var.storage_bucket
    results_dirname           = "/storage"
    results_url_expiry_time    = 604800
    node_type                  = "KubernetesPod"
    node_config = {
      # FIXME: Had to hard-code this name to avoid a cyclical dependency
      config_configmap_name = "worker-node-config"
      ssh_key_secret        = kubernetes_secret_v1.job_ssh_key.metadata[0].name
      # FIXME: These paths need to match in the helm chart values as well
      storage_config_path    = "/config/storage.yaml"
      controller_config_path = "/config/controller.yaml"
      # TODO: Might want to make these variables in order to allow different values
      # in different environments
      pod_cpu           = "500m"
      pod_memory        = "100Mi"
      image_pull_policy = var.image_pull_policy
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
    scheduler_port    = 5001
    metrics_address   = "graphite.default.svc.cluster.local"
    metrics_port      = 2004
    runner            = "chainsail.runners.rexfw:MPIRERunner"
    storage_dirname  = "/storage"
    log_level         = "DEBUG"
    # FIXME: ensure that this path matches helm chart
    remote_logging_config_path = "/chainsail/remote_logging.yaml"
  }

}

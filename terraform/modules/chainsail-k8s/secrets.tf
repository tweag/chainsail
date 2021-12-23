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
      config_configmap_name = "config-dpl-configmap" # FIXME
      ssh_public_key        = "${var.job_ssh_pub}"
      # FIXME: These paths need to match in the helm chart values as well
      ssh_private_key_path   = "/config/unsafe_dev_key_rsa"
      storage_config_path    = "/config/storage.yaml"
      controller_config_path = "/config/controller.yaml"
      # TODO: Might want to make these variables in order to allow different values
      # in different environments
      pod_cpu    = "1600m"
      pod_memory = "5000000Ki"
    }
  }
}

# FIXME: need to create the `config-dpl-configmap` since the current k8s implementation
# relies on it.
###############################################################################
# Scheduler
###############################################################################

resource "kubernetes_role" "chainsail_scheduler" {
  metadata {
    name = "chainsail-scheduler"
  }

  rule {
    # TODO: Might want to further restrict api groups here as well
    #  See: https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.21/#-strong-api-groups-strong-
    api_groups = [""]
    resources  = ["pods"]
    verbs      = ["get", "list", "watch", "create", "update", "patch", "delete"]
  }
}


resource "kubernetes_service_account" "chainsail_scheduler" {
  metadata {
    name = "chainsail-scheduler"
  }
  secret {
    name = kubernetes_secret_v1.scheduler_yaml.metadata.0.name
  }
}

resource "kubernetes_role_binding" "chainsail_scheduler" {
  metadata {
    name      = "chainsail-scheduler"
    namespace = "default"
  }
  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "Role"
    name      = kubernetes_role.chainsail_scheduler.metadata[0].name
  }


  subject {
    kind = "ServiceAccount"
    name = kubernetes_service_account.chainsail_scheduler.metadata[0].name
    # TODO: Confirm that this namespace is correct
    namespace = "kube-system"
  }
}

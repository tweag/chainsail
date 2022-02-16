data "google_project" "project" {}

resource "google_service_account" "chainsail" {
  account_id   = "chainsail"
  display_name = "Chainsail services"
}

resource "google_storage_hmac_key" "key" {
  service_account_email = google_service_account.chainsail.email
}

resource "google_storage_bucket" "results" {
  name           = "${data.google_project.project.name}-job-results"
  project        = data.google_project.project.name
  force_destroy  = false
  labels         = {}
  location       = var.storage_location
  storage_class  = "MULTI_REGIONAL"
  requester_pays = false
  versioning {
    enabled = false
  }
}

resource "google_container_registry" "registry" {
  project  = data.google_project.project.name
  location = var.storage_location
}

resource "google_storage_bucket_iam_member" "chainsail-registry" {
  bucket = google_container_registry.registry.id
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.chainsail.email}"
}

resource "google_storage_bucket_iam_member" "tasks-staging-objectAdmin" {
  bucket = google_storage_bucket.results.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.chainsail.email}"
}

resource "google_container_cluster" "chainsail" {
  name     = "chainsail"
  location = var.node_location
  # Note: removing the default node pool in favor of an explicitely managed one
  remove_default_node_pool = true
  initial_node_count       = 1
}

resource "google_container_node_pool" "core_nodes" {
  name     = "core-pool"
  location = var.node_location
  cluster  = google_container_cluster.chainsail.name

  autoscaling {
    max_node_count = 5
    min_node_count = 0
  }

  node_config {
    preemptible  = false
    machine_type = var.core_node_type
    # Labeling these nodes so that core services can be configured
    # to only be scheduled in this node pool
    labels = {
      for_core_services = "true"
    }
    # Tainting these nodes so that only "core" services can run on them
    taint {
      key    = "for_core_services"
      value  = "true"
      effect = "NO_SCHEDULE"
    }
    service_account = google_service_account.chainsail.email
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
  }
}

resource "google_container_node_pool" "job_nodes" {
  name     = "job-pool"
  location = var.node_location
  cluster  = google_container_cluster.chainsail.name

  autoscaling {
    max_node_count = 10
    min_node_count = 0
  }

  node_config {
    preemptible     = false
    machine_type    = var.job_node_type
    service_account = google_service_account.chainsail.email
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
  }
}

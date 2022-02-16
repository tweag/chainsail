locals {
  chainsail_environment_config = {
    storage_url        = "https://storage.googleapis.com"
    storage_access_id  = google_storage_hmac_key.key.access_id
    storage_secret_key = google_storage_hmac_key.key.secret
    storage_bucket     = google_storage_bucket.results.name
    container_registry = "${lower(google_container_registry.registry.location)}.gcr.io/${data.google_project.project.name}"
    cluster_name       = google_container_cluster.chainsail.name
    cluster_location   = google_container_cluster.chainsail.location
  }
}

resource "google_secret_manager_secret" "chainsail_environment_config" {
  secret_id = "chainsail-environment-config"
  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "chainsail_environment_config" {
  secret      = google_secret_manager_secret.chainsail_environment_config.id
  secret_data = jsonencode(local.chainsail_environment_config)
}

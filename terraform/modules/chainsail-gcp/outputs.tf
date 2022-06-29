output "container_registry" {
  value     = "${lower(google_container_registry.registry.location)}.gcr.io/${data.google_project.project.name}"
  sensitive = false
}

output "ingress_fqdn" {
  value = google_dns_record_set.chainsail_backend.name
}
output "ingress_address" {
  value = google_compute_address.chainsail_backend.address
}

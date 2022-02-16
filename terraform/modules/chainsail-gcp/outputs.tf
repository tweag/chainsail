output "container_registry" {
  value     = "${lower(google_container_registry.registry.location)}.gcr.io/${data.google_project.project.name}"
  sensitive = true
}

# resource "google_project_service" "compute" {
#   project = data.google_project.project.project_id
#   service = "compute.googleapis.com"
# }

# resource "google_project_service" "compute" {
#   project = data.google_project.project.project_id
#   service = "compute.googleapis.com"
# }

# resource "google_project_service" "servicenetworking" {
#   project = google_project.airflow.project_id
#   service = "servicenetworking.googleapis.com"
# }

# resource "google_project_service" "cloudkms" {
#   project = google_project.airflow.project_id
#   service = "cloudkms.googleapis.com"
# }

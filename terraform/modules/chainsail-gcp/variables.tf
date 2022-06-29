variable "storage_location" {
  description = "GCP location where storage buckets will be created"
  type        = string
}

variable "node_location" {
  description = "GCP location where compute resources will be created"
  type        = string
}

variable "core_node_type" {
  description = "GCE instance type for node pool running core services"
  type        = string
}

variable "job_node_type" {
  description = "GCE instance type for node pool where jobs are run"
  type        = string
}

variable "ssh_pem_secret_name" {
  description = "GCP secret manager secret name containing the ssh private key used for running jobs. Must already exist."
  type        = string
}


variable "ssh_pub_secret_name" {
  description = "GCP secret manager secret name containing the ssh public key used for running jobs. Must already exist."
  type        = string
}

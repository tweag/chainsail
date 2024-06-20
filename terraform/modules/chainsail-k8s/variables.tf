variable "job_ssh_pem" {
  description = "private ssh key used in MPI jobs"
  type        = string
  sensitive   = true
}

variable "job_ssh_pub" {
  description = "public ssh key used in MPI jobs"
  type        = string
  sensitive   = true
}

variable "storage_yaml" {
  description = "storage.yaml config file contents"
  type        = string
  sensitive   = true
}

variable "storage_url" {
  description = "Object storage backend url"
  type        = string
  default     = null
  sensitive   = true
}

variable "storage_access_key" {
  description = "Object storage HMAC access key"
  type        = string
  sensitive   = true
}

variable "storage_secret_key" {
  description = "Object storage HMAC secret key"
  type        = string
  sensitive   = true
}

variable "storage_bucket" {
  description = "Object storage bucket name"
  type        = string
}

variable "image_controller" {
  description = "Docker image used for creating controller nodes"
  type        = string
}

variable "image_worker" {
  description = "Docker image used for creating worker nodes"
  type        = string
}

variable "image_user_code" {
  description = "Docker image used for executing user code"
  type        = string
}

variable "image_pull_policy" {
  description = "Image pull policy to go in scheduler.yaml"
  type        = string
  default     = "IfNotPresent"
}

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

variable "image_httpstan" {
  description = "Docker image for httpstan"
  type        = string
}

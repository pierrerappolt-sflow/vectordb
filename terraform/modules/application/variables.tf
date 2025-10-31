/**
 * Application Module Variables
 */

variable "app_image" {
  description = "Docker image for FastAPI application"
  type        = string
}

variable "app_replicas" {
  description = "Number of FastAPI replicas"
  type        = number
  default     = 2
}

variable "app_db_host" {
  description = "Application database host"
  type        = string
}

variable "app_db_name" {
  description = "Application database name"
  type        = string
  default     = "vectordb"
}

variable "app_db_user" {
  description = "Application database user"
  type        = string
  default     = "vdbuser"
}

variable "app_db_password" {
  description = "Application database password"
  type        = string
  sensitive   = true
}

variable "temporal_host" {
  description = "Temporal gRPC host"
  type        = string
}

variable "temporal_port" {
  description = "Temporal gRPC port"
  type        = number
  default     = 7233
}

variable "temporal_namespace" {
  description = "Temporal namespace"
  type        = string
  default     = "default"
}

variable "worker_task_queue" {
  description = "Temporal worker task queue name"
  type        = string
  default     = "vdb-tasks"
}

variable "expose_api_publicly" {
  description = "Expose FastAPI via public LoadBalancer"
  type        = bool
  default     = true
}

variable "api_domain" {
  description = "Domain for FastAPI backend (optional, for DNS/SSL)"
  type        = string
  default     = ""
}

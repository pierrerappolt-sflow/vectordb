variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "production"
}

variable "cohere_api_key" {
  description = "Cohere API key for embeddings"
  type        = string
  sensitive   = true
}

variable "ingress_ip_name" {
  description = "Name of the reserved static IP for ingress"
  type        = string
}

variable "domain" {
  description = "Base domain for the application"
  type        = string
}

variable "api_subdomain" {
  description = "Subdomain for API"
  type        = string
  default     = "api"
}

variable "app_subdomain" {
  description = "Subdomain for app/UI"
  type        = string
  default     = "app"
}

variable "temporal_subdomain" {
  description = "Subdomain for Temporal UI"
  type        = string
  default     = "temporal"
}

variable "container_registry" {
  description = "Container registry URL (e.g., gcr.io/project-id or us-central1-docker.pkg.dev/project-id/vdb-images)"
  type        = string
}

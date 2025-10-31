/**
 * Terraform variables for VectorDB GKE deployment
 */

# ==================== GCP Configuration ====================
variable "gcp_project_id" {
  description = "GCP project ID"
  type        = string
}

variable "gcp_region" {
  description = "GCP region"
  type        = string
  default     = "us-west1"
}

variable "gcp_zone" {
  description = "GCP zone (zonal cluster for cost savings)"
  type        = string
  default     = "us-west1-a"
}

variable "cluster_name" {
  description = "GKE cluster name"
  type        = string
  default     = "vdb-cluster"
}

# ==================== GKE Node Configuration ====================
variable "machine_type" {
  description = "GKE node machine type (e2-medium for cost optimization)"
  type        = string
  default     = "e2-medium"
}

variable "min_nodes" {
  description = "Minimum number of nodes in the cluster"
  type        = number
  default     = 2
}

variable "max_nodes" {
  description = "Maximum number of nodes for autoscaling"
  type        = number
  default     = 4
}

variable "disk_size_gb" {
  description = "Boot disk size for GKE nodes"
  type        = number
  default     = 50
}

variable "use_preemptible_nodes" {
  description = "Use preemptible nodes for additional cost savings (~60% cheaper)"
  type        = bool
  default     = false  # Set to true for dev/staging environments
}

# ==================== PostgreSQL Configuration ====================
variable "postgres_storage_size_gb" {
  description = "Storage size for PostgreSQL instances"
  type        = number
  default     = 10
}

# ==================== Temporal Configuration ====================
variable "temporal_version" {
  description = "Temporal server version"
  type        = string
  default     = "1.22.4"
}

variable "temporal_ui_version" {
  description = "Temporal UI version"
  type        = string
  default     = "2.21.3"
}

variable "temporal_ui_domain" {
  description = "Domain for Temporal UI (optional, for SSL/HTTPS)"
  type        = string
  default     = ""
}

# ==================== FastAPI Configuration ====================
variable "fastapi_image" {
  description = "FastAPI Docker image (will be built and pushed to GCR)"
  type        = string
  default     = "gcr.io/PROJECT_ID/vdb-api:latest"
}

variable "fastapi_replicas" {
  description = "Number of FastAPI replicas"
  type        = number
  default     = 2
}

variable "fastapi_domain" {
  description = "Domain for FastAPI backend (optional, for SSL/HTTPS)"
  type        = string
  default     = ""
}

# ==================== SSL Configuration (Optional) ====================
variable "ssl_email" {
  description = "Email for Let's Encrypt SSL certificates (optional)"
  type        = string
  default     = ""
}

# ==================== Labels ====================
variable "labels" {
  description = "Labels to apply to all resources"
  type        = map(string)
  default = {
    project     = "vectordb"
    environment = "production"
    managed_by  = "terraform"
  }
}

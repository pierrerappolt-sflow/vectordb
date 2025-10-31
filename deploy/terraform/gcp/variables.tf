variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "cluster_name" {
  description = "GKE cluster name"
  type        = string
  default     = "vdb-cluster"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "production"
}

variable "network" {
  description = "VPC network name"
  type        = string
  default     = "default"
}

variable "subnetwork" {
  description = "VPC subnetwork name"
  type        = string
  default     = "default"
}

variable "cluster_ipv4_cidr" {
  description = "IP range for cluster pods"
  type        = string
  default     = ""  # GKE will auto-assign
}

variable "services_ipv4_cidr" {
  description = "IP range for cluster services"
  type        = string
  default     = ""  # GKE will auto-assign
}

variable "release_channel" {
  description = "GKE release channel (RAPID, REGULAR, STABLE)"
  type        = string
  default     = "REGULAR"
}

# Node pool configuration
variable "machine_type" {
  description = "Machine type for primary node pool"
  type        = string
  default     = "e2-standard-4"  # 4 vCPUs, 16GB RAM
}

variable "disk_size_gb" {
  description = "Disk size for nodes in GB"
  type        = number
  default     = 100
}

variable "node_count" {
  description = "Initial node count per zone"
  type        = number
  default     = 1
}

variable "min_node_count" {
  description = "Minimum node count per zone"
  type        = number
  default     = 1
}

variable "max_node_count" {
  description = "Maximum node count per zone"
  type        = number
  default     = 10
}

# Preemptible node pool
variable "preemptible_machine_type" {
  description = "Machine type for preemptible node pool"
  type        = string
  default     = "e2-standard-2"  # 2 vCPUs, 8GB RAM
}

variable "preemptible_node_count" {
  description = "Initial preemptible node count"
  type        = number
  default     = 0
}

variable "preemptible_min_count" {
  description = "Minimum preemptible node count"
  type        = number
  default     = 0
}

variable "preemptible_max_count" {
  description = "Maximum preemptible node count"
  type        = number
  default     = 5
}

# Domain configuration
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

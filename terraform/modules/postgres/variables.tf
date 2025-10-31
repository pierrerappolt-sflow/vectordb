/**
 * PostgreSQL Module Variables
 */

variable "temporal_db_size_gb" {
  description = "Storage size for Temporal PostgreSQL (GB)"
  type        = number
  default     = 10
}

variable "app_db_size_gb" {
  description = "Storage size for Application PostgreSQL (GB)"
  type        = number
  default     = 10
}

variable "storage_class" {
  description = "Kubernetes storage class for persistent volumes"
  type        = string
  default     = "standard-rwo"
}

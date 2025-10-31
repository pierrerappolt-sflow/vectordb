/**
 * Temporal Module Variables
 */

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

variable "postgres_host" {
  description = "PostgreSQL host for Temporal"
  type        = string
}

variable "postgres_database" {
  description = "PostgreSQL database name"
  type        = string
  default     = "temporal"
}

variable "postgres_user" {
  description = "PostgreSQL user"
  type        = string
  default     = "temporal"
}

variable "postgres_password" {
  description = "PostgreSQL password"
  type        = string
  sensitive   = true
}

variable "expose_ui_publicly" {
  description = "Expose Temporal UI via public LoadBalancer"
  type        = bool
  default     = true
}

variable "ui_domain" {
  description = "Domain for Temporal UI (optional, for DNS/SSL)"
  type        = string
  default     = ""
}

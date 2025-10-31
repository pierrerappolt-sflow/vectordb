/**
 * Main Terraform configuration for VectorDB GKE deployment
 * Cost-optimized setup: ~$90/month
 *
 * Architecture:
 * - GKE zonal cluster in us-west1-a
 * - CloudNativePG operator for managed Postgres
 * - Temporal workflow engine with public UI
 * - FastAPI backend with public LoadBalancer
 */

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
  }

  # Uncomment for remote state
  # backend "gcs" {
  #   bucket = "your-terraform-state-bucket"
  #   prefix = "terraform/state"
  # }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
  zone    = var.gcp_zone
}

provider "kubernetes" {
  host                   = "https://${module.gke.endpoint}"
  token                  = data.google_client_config.default.access_token
  cluster_ca_certificate = base64decode(module.gke.ca_certificate)
}

provider "helm" {
  kubernetes {
    host                   = "https://${module.gke.endpoint}"
    token                  = data.google_client_config.default.access_token
    cluster_ca_certificate = base64decode(module.gke.ca_certificate)
  }
}

data "google_client_config" "default" {}

# ==================== GKE Cluster ====================
module "gke" {
  source = "./modules/gke"

  project_id    = var.gcp_project_id
  region        = var.gcp_region
  zone          = var.gcp_zone
  cluster_name  = var.cluster_name

  # Cost optimization: e2-medium nodes
  machine_type  = var.machine_type
  min_nodes     = var.min_nodes
  max_nodes     = var.max_nodes
  disk_size_gb  = var.disk_size_gb

  # Enable preemptible nodes for additional cost savings
  preemptible   = var.use_preemptible_nodes
}

# ==================== PostgreSQL Databases ====================
module "postgres" {
  source = "./modules/postgres"

  depends_on = [module.gke]

  # Single-instance clusters for cost optimization
  temporal_db_size_gb = var.postgres_storage_size_gb
  app_db_size_gb      = var.postgres_storage_size_gb

  # Storage class for persistent volumes
  storage_class       = "standard-rwo"
}

# ==================== Temporal Workflow Engine ====================
module "temporal" {
  source = "./modules/temporal"

  depends_on = [module.postgres]

  # Temporal configuration
  temporal_version    = var.temporal_version
  temporal_ui_version = var.temporal_ui_version

  # Database connection (from postgres module)
  postgres_host     = module.postgres.temporal_db_host
  postgres_database = "temporal"
  postgres_user     = "temporal"
  postgres_password = module.postgres.temporal_db_password

  # Public access configuration
  expose_ui_publicly = true
  ui_domain          = var.temporal_ui_domain  # Optional: for SSL/HTTPS
}

# ==================== FastAPI Application ====================
module "application" {
  source = "./modules/application"

  depends_on = [module.postgres, module.temporal]

  # Application configuration
  app_image           = var.fastapi_image
  app_replicas        = var.fastapi_replicas

  # Database connections
  app_db_host         = module.postgres.app_db_host
  app_db_name         = "vectordb"
  app_db_user         = "vdbuser"
  app_db_password     = module.postgres.app_db_password

  # Temporal connection
  temporal_host       = module.temporal.temporal_grpc_host
  temporal_port       = 7233
  temporal_namespace  = "default"

  # Public access configuration
  expose_api_publicly = true
  api_domain          = var.fastapi_domain  # Optional: for SSL/HTTPS

  # Worker configuration
  worker_task_queue   = "vdb-tasks"
}

# ==================== Optional: SSL/HTTPS Setup ====================
# Uncomment if you have a domain and want automatic SSL certificates
# module "ssl" {
#   source = "./modules/ssl"
#
#   depends_on = [module.temporal, module.application]
#
#   temporal_ui_domain = var.temporal_ui_domain
#   fastapi_domain     = var.fastapi_domain
#   email              = var.ssl_email
# }

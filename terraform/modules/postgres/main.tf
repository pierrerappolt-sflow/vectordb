/**
 * PostgreSQL Module using CloudNativePG Operator
 * Creates two single-instance database clusters:
 * 1. temporal-postgres - For Temporal workflow engine
 * 2. app-postgres - For application data with pgvector
 */

# Install CloudNativePG operator via Helm
resource "helm_release" "cloudnative_pg" {
  name       = "cloudnative-pg"
  repository = "https://cloudnative-pg.github.io/charts"
  chart      = "cloudnative-pg"
  version    = "0.20.0"  # Latest stable version

  namespace        = "cnpg-system"
  create_namespace = true

  set {
    name  = "monitoring.podMonitorEnabled"
    value = "false"  # Disable Prometheus monitoring to save costs
  }

  wait = true
}

# Temporal PostgreSQL Cluster (single instance for cost savings)
resource "kubernetes_manifest" "temporal_postgres" {
  depends_on = [helm_release.cloudnative_pg]

  manifest = {
    apiVersion = "postgresql.cnpg.io/v1"
    kind       = "Cluster"
    metadata = {
      name      = "temporal-postgres"
      namespace = "default"
    }
    spec = {
      instances = 1  # Single instance (no replicas) for cost optimization

      storage = {
        size         = "${var.temporal_db_size_gb}Gi"
        storageClass = var.storage_class
      }

      # PostgreSQL configuration
      postgresql = {
        parameters = {
          max_connections           = "100"
          shared_buffers            = "256MB"
          effective_cache_size      = "1GB"
          maintenance_work_mem      = "64MB"
          checkpoint_completion_target = "0.9"
          wal_buffers               = "16MB"
          default_statistics_target = "100"
          random_page_cost          = "1.1"
          effective_io_concurrency  = "200"
        }
      }

      # Bootstrap configuration
      bootstrap = {
        initdb = {
          database = "temporal"
          owner    = "temporal"
          secret = {
            name = kubernetes_secret.temporal_postgres_creds.metadata[0].name
          }
        }
      }

      # Resources
      resources = {
        requests = {
          memory = "512Mi"
          cpu    = "250m"
        }
        limits = {
          memory = "1Gi"
          cpu    = "500m"
        }
      }

      # Backup configuration (optional, disabled for cost savings)
      # backup = {
      #   barmanObjectStore = {
      #     destinationPath = "gs://your-backup-bucket/temporal-postgres"
      #     gcs = {
      #       bucket = "your-backup-bucket"
      #     }
      #   }
      # }
    }
  }
}

# Temporal PostgreSQL credentials
resource "kubernetes_secret" "temporal_postgres_creds" {
  metadata {
    name      = "temporal-postgres-creds"
    namespace = "default"
  }

  data = {
    username = "temporal"
    password = random_password.temporal_postgres_password.result
  }
}

resource "random_password" "temporal_postgres_password" {
  length  = 24
  special = true
}

# Application PostgreSQL Cluster with pgvector (single instance)
resource "kubernetes_manifest" "app_postgres" {
  depends_on = [helm_release.cloudnative_pg]

  manifest = {
    apiVersion = "postgresql.cnpg.io/v1"
    kind       = "Cluster"
    metadata = {
      name      = "app-postgres"
      namespace = "default"
    }
    spec = {
      instances = 1  # Single instance (no replicas) for cost optimization

      # Use pgvector image
      imageName = "pgvector/pgvector:pg16"

      storage = {
        size         = "${var.app_db_size_gb}Gi"
        storageClass = var.storage_class
      }

      # PostgreSQL configuration
      postgresql = {
        parameters = {
          max_connections           = "100"
          shared_buffers            = "256MB"
          effective_cache_size      = "1GB"
          maintenance_work_mem      = "64MB"
          checkpoint_completion_target = "0.9"
          wal_buffers               = "16MB"
          default_statistics_target = "100"
          random_page_cost          = "1.1"
          effective_io_concurrency  = "200"
        }
      }

      # Bootstrap configuration
      bootstrap = {
        initdb = {
          database = "vectordb"
          owner    = "vdbuser"
          secret = {
            name = kubernetes_secret.app_postgres_creds.metadata[0].name
          }
          # Enable pgvector extension
          postInitSQL = [
            "CREATE EXTENSION IF NOT EXISTS vector;"
          ]
        }
      }

      # Resources
      resources = {
        requests = {
          memory = "512Mi"
          cpu    = "250m"
        }
        limits = {
          memory = "1Gi"
          cpu    = "500m"
        }
      }
    }
  }
}

# Application PostgreSQL credentials
resource "kubernetes_secret" "app_postgres_creds" {
  metadata {
    name      = "app-postgres-creds"
    namespace = "default"
  }

  data = {
    username = "vdbuser"
    password = random_password.app_postgres_password.result
  }
}

resource "random_password" "app_postgres_password" {
  length  = 24
  special = true
}

# Outputs
output "temporal_db_host" {
  description = "Temporal PostgreSQL host (internal service name)"
  value       = "temporal-postgres-rw.default.svc.cluster.local"
}

output "temporal_db_password" {
  description = "Temporal PostgreSQL password"
  value       = random_password.temporal_postgres_password.result
  sensitive   = true
}

output "app_db_host" {
  description = "Application PostgreSQL host (internal service name)"
  value       = "app-postgres-rw.default.svc.cluster.local"
}

output "app_db_password" {
  description = "Application PostgreSQL password"
  value       = random_password.app_postgres_password.result
  sensitive   = true
}

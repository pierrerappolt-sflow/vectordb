/**
 * Application Module
 * Deploys FastAPI backend and Temporal worker
 */

# ConfigMap for application environment variables
resource "kubernetes_config_map" "app_config" {
  metadata {
    name      = "vdb-app-config"
    namespace = "default"
  }

  data = {
    DATABASE_URL      = "postgresql://${var.app_db_user}:${var.app_db_password}@${var.app_db_host}:5432/${var.app_db_name}"
    TEMPORAL_HOST     = var.temporal_host
    TEMPORAL_PORT     = tostring(var.temporal_port)
    TEMPORAL_NAMESPACE = var.temporal_namespace
    WORKER_TASK_QUEUE = var.worker_task_queue
  }
}

# FastAPI Backend Deployment
resource "kubernetes_deployment" "fastapi" {
  metadata {
    name      = "vdb-api"
    namespace = "default"
    labels = {
      app = "vdb-api"
    }
  }

  spec {
    replicas = var.app_replicas

    selector {
      match_labels = {
        app = "vdb-api"
      }
    }

    template {
      metadata {
        labels = {
          app = "vdb-api"
        }
      }

      spec {
        # Init container to wait for PostgreSQL
        init_container {
          name  = "wait-for-postgres"
          image = "busybox:1.36"
          command = [
            "sh",
            "-c",
            "until nc -z ${var.app_db_host} 5432; do echo waiting for postgres; sleep 2; done"
          ]
        }

        # Init container to wait for Temporal
        init_container {
          name  = "wait-for-temporal"
          image = "busybox:1.36"
          command = [
            "sh",
            "-c",
            "until nc -z ${var.temporal_host} ${var.temporal_port}; do echo waiting for temporal; sleep 2; done"
          ]
        }

        container {
          name  = "fastapi"
          image = var.app_image

          env_from {
            config_map_ref {
              name = kubernetes_config_map.app_config.metadata[0].name
            }
          }

          port {
            name           = "http"
            container_port = 8000
            protocol       = "TCP"
          }

          resources {
            requests = {
              memory = "256Mi"
              cpu    = "200m"
            }
            limits = {
              memory = "512Mi"
              cpu    = "500m"
            }
          }

          liveness_probe {
            http_get {
              path = "/health"
              port = 8000
            }
            initial_delay_seconds = 30
            period_seconds        = 10
            timeout_seconds       = 5
            failure_threshold     = 3
          }

          readiness_probe {
            http_get {
              path = "/health"
              port = 8000
            }
            initial_delay_seconds = 10
            period_seconds        = 5
          }
        }
      }
    }
  }
}

# FastAPI Service (public LoadBalancer)
resource "kubernetes_service" "fastapi" {
  metadata {
    name      = "vdb-api"
    namespace = "default"
    annotations = var.api_domain != "" ? {
      "external-dns.alpha.kubernetes.io/hostname" = var.api_domain
    } : {}
  }

  spec {
    type = var.expose_api_publicly ? "LoadBalancer" : "ClusterIP"

    selector = {
      app = "vdb-api"
    }

    port {
      name        = "http"
      port        = 80
      target_port = 8000
      protocol    = "TCP"
    }
  }
}

# Temporal Worker Deployment
resource "kubernetes_deployment" "temporal_worker" {
  metadata {
    name      = "vdb-temporal-worker"
    namespace = "default"
    labels = {
      app = "vdb-temporal-worker"
    }
  }

  spec {
    replicas = 1  # Single worker instance for cost savings

    selector {
      match_labels = {
        app = "vdb-temporal-worker"
      }
    }

    template {
      metadata {
        labels = {
          app = "vdb-temporal-worker"
        }
      }

      spec {
        # Init container to wait for PostgreSQL
        init_container {
          name  = "wait-for-postgres"
          image = "busybox:1.36"
          command = [
            "sh",
            "-c",
            "until nc -z ${var.app_db_host} 5432; do echo waiting for postgres; sleep 2; done"
          ]
        }

        # Init container to wait for Temporal
        init_container {
          name  = "wait-for-temporal"
          image = "busybox:1.36"
          command = [
            "sh",
            "-c",
            "until nc -z ${var.temporal_host} ${var.temporal_port}; do echo waiting for temporal; sleep 2; done"
          ]
        }

        container {
          name  = "worker"
          image = var.app_image

          # Override command to run worker instead of API
          command = ["uv", "run", "--directory", "/workspace", "python", "-m", "vdb_api.worker"]

          env_from {
            config_map_ref {
              name = kubernetes_config_map.app_config.metadata[0].name
            }
          }

          resources {
            requests = {
              memory = "256Mi"
              cpu    = "200m"
            }
            limits = {
              memory = "512Mi"
              cpu    = "500m"
            }
          }

          # No liveness probe for worker (long-running workflows)
        }
      }
    }
  }
}

# Outputs
output "fastapi_url" {
  description = "FastAPI backend URL"
  value       = var.expose_api_publicly ? "http://${kubernetes_service.fastapi.status[0].load_balancer[0].ingress[0].ip}" : "http://vdb-api.default.svc.cluster.local"
}

output "fastapi_ip" {
  description = "FastAPI LoadBalancer IP"
  value       = var.expose_api_publicly ? kubernetes_service.fastapi.status[0].load_balancer[0].ingress[0].ip : null
}

output "worker_deployment_name" {
  description = "Temporal worker deployment name"
  value       = kubernetes_deployment.temporal_worker.metadata[0].name
}

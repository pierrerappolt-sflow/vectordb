/**
 * Temporal Module
 * Deploys Temporal server and UI with public access to UI
 */

# Namespace for Temporal components
resource "kubernetes_namespace" "temporal" {
  metadata {
    name = "temporal"
  }
}

# ConfigMap for Temporal dynamic configuration
resource "kubernetes_config_map" "temporal_config" {
  metadata {
    name      = "temporal-config"
    namespace = kubernetes_namespace.temporal.metadata[0].name
  }

  data = {
    "development-sql.yaml" = <<-EOT
      ---
      # Temporal dynamic configuration for SQL backend
      system.forceSearchAttributesCacheRefreshOnRead:
        - value: true
          constraints: {}
      EOT
  }
}

# Temporal Server Deployment
resource "kubernetes_deployment" "temporal" {
  metadata {
    name      = "temporal"
    namespace = kubernetes_namespace.temporal.metadata[0].name
    labels = {
      app = "temporal"
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "temporal"
      }
    }

    template {
      metadata {
        labels = {
          app = "temporal"
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
            "until nc -z ${var.postgres_host} 5432; do echo waiting for postgres; sleep 2; done"
          ]
        }

        container {
          name  = "temporal"
          image = "temporalio/auto-setup:${var.temporal_version}"

          env {
            name  = "DB"
            value = "postgresql"
          }
          env {
            name  = "DB_PORT"
            value = "5432"
          }
          env {
            name  = "POSTGRES_USER"
            value = var.postgres_user
          }
          env {
            name  = "POSTGRES_PWD"
            value = var.postgres_password
          }
          env {
            name  = "POSTGRES_SEEDS"
            value = var.postgres_host
          }
          env {
            name  = "DYNAMIC_CONFIG_FILE_PATH"
            value = "/etc/temporal/config/dynamicconfig/development-sql.yaml"
          }

          port {
            name           = "grpc"
            container_port = 7233
            protocol       = "TCP"
          }

          volume_mount {
            name       = "config"
            mount_path = "/etc/temporal/config/dynamicconfig"
          }

          resources {
            requests = {
              memory = "512Mi"
              cpu    = "250m"
            }
            limits = {
              memory = "1Gi"
              cpu    = "500m"
            }
          }

          liveness_probe {
            exec {
              command = ["tctl", "--address", "temporal:7233", "cluster", "health"]
            }
            initial_delay_seconds = 30
            period_seconds        = 10
            timeout_seconds       = 5
            failure_threshold     = 3
          }
        }

        volume {
          name = "config"
          config_map {
            name = kubernetes_config_map.temporal_config.metadata[0].name
          }
        }
      }
    }
  }
}

# Temporal Server Service (internal gRPC)
resource "kubernetes_service" "temporal" {
  metadata {
    name      = "temporal"
    namespace = kubernetes_namespace.temporal.metadata[0].name
  }

  spec {
    type = "ClusterIP"

    selector = {
      app = "temporal"
    }

    port {
      name        = "grpc"
      port        = 7233
      target_port = 7233
      protocol    = "TCP"
    }
  }
}

# Temporal UI Deployment
resource "kubernetes_deployment" "temporal_ui" {
  metadata {
    name      = "temporal-ui"
    namespace = kubernetes_namespace.temporal.metadata[0].name
    labels = {
      app = "temporal-ui"
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "temporal-ui"
      }
    }

    template {
      metadata {
        labels = {
          app = "temporal-ui"
        }
      }

      spec {
        container {
          name  = "temporal-ui"
          image = "temporalio/ui:${var.temporal_ui_version}"

          env {
            name  = "TEMPORAL_ADDRESS"
            value = "temporal.${kubernetes_namespace.temporal.metadata[0].name}.svc.cluster.local:7233"
          }
          env {
            name  = "TEMPORAL_CORS_ORIGINS"
            value = "*"  # Allow all origins for now, restrict in production
          }

          port {
            name           = "http"
            container_port = 8080
            protocol       = "TCP"
          }

          resources {
            requests = {
              memory = "256Mi"
              cpu    = "100m"
            }
            limits = {
              memory = "512Mi"
              cpu    = "250m"
            }
          }

          liveness_probe {
            http_get {
              path = "/"
              port = 8080
            }
            initial_delay_seconds = 10
            period_seconds        = 10
          }
        }
      }
    }
  }
}

# Temporal UI Service (public LoadBalancer)
resource "kubernetes_service" "temporal_ui" {
  metadata {
    name      = "temporal-ui"
    namespace = kubernetes_namespace.temporal.metadata[0].name
    annotations = var.ui_domain != "" ? {
      "external-dns.alpha.kubernetes.io/hostname" = var.ui_domain
    } : {}
  }

  spec {
    type = var.expose_ui_publicly ? "LoadBalancer" : "ClusterIP"

    selector = {
      app = "temporal-ui"
    }

    port {
      name        = "http"
      port        = 80
      target_port = 8080
      protocol    = "TCP"
    }
  }
}

# Outputs
output "temporal_grpc_host" {
  description = "Temporal gRPC service host (internal)"
  value       = "temporal.${kubernetes_namespace.temporal.metadata[0].name}.svc.cluster.local"
}

output "temporal_ui_url" {
  description = "Temporal UI URL"
  value       = var.expose_ui_publicly ? "http://${kubernetes_service.temporal_ui.status[0].load_balancer[0].ingress[0].ip}" : "http://temporal-ui.${kubernetes_namespace.temporal.metadata[0].name}.svc.cluster.local"
}

output "temporal_ui_ip" {
  description = "Temporal UI LoadBalancer IP"
  value       = var.expose_ui_publicly ? kubernetes_service.temporal_ui.status[0].load_balancer[0].ingress[0].ip : null
}

output "temporal_namespace" {
  description = "Kubernetes namespace for Temporal"
  value       = kubernetes_namespace.temporal.metadata[0].name
}

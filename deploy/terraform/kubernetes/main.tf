terraform {
  required_version = ">= 1.0"

  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
}

# Note: kubectl connection should be configured before running this
# Run: gcloud container clusters get-credentials <cluster-name> --region <region>

provider "kubernetes" {
  # Uses ~/.kube/config by default
  # Or configure explicitly:
  # config_path = "~/.kube/config"
}

# Generate secure random passwords
resource "random_password" "postgres_password" {
  length  = 32
  special = true
}

resource "random_password" "temporal_postgres_password" {
  length  = 32
  special = true
}

resource "random_password" "rabbitmq_password" {
  length  = 32
  special = true
}

# Namespace
resource "kubernetes_namespace" "vdb" {
  metadata {
    name = "vdb"
    labels = {
      app         = "vectordb"
      environment = var.environment
    }
  }
}

# ConfigMap
resource "kubernetes_config_map" "vdb_config" {
  metadata {
    name      = "vdb-config"
    namespace = kubernetes_namespace.vdb.metadata[0].name
  }

  data = {
    # Database Configuration
    POSTGRES_DB               = "vectordb"
    POSTGRES_USER             = "vdbuser"
    TEMPORAL_POSTGRES_DB      = "temporal"
    TEMPORAL_POSTGRES_USER    = "temporal"

    # Temporal Configuration
    TEMPORAL_HOST      = "temporal"
    TEMPORAL_PORT      = "7233"
    TEMPORAL_NAMESPACE = "default"
    WORKER_TASK_QUEUE  = "vdb-tasks"

    # RabbitMQ Configuration
    RABBITMQ_HOST         = "rabbitmq"
    RABBITMQ_PORT         = "5672"
    RABBITMQ_DEFAULT_USER = "guest"

    # Database URLs (non-sensitive parts)
    DATABASE_HOST          = "app-postgres"
    DATABASE_PORT          = "5432"
    TEMPORAL_DATABASE_HOST = "temporal-postgres"
    TEMPORAL_DATABASE_PORT = "5432"

    # Search Service
    SEARCH_SERVICE_URL = "http://search:8001"

    # Application Settings
    API_HOST                = "0.0.0.0"
    API_PORT                = "8001"
    NODE_ENV                = var.environment
    NEXT_TELEMETRY_DISABLED = "1"
  }
}

# Secrets
resource "kubernetes_secret" "vdb_secrets" {
  metadata {
    name      = "vdb-secrets"
    namespace = kubernetes_namespace.vdb.metadata[0].name
  }

  data = {
    POSTGRES_PASSWORD          = random_password.postgres_password.result
    TEMPORAL_POSTGRES_PASSWORD = random_password.temporal_postgres_password.result
    RABBITMQ_DEFAULT_PASS      = random_password.rabbitmq_password.result
    COHERE_API_KEY             = var.cohere_api_key

    DATABASE_URL = "postgresql://vdbuser:${random_password.postgres_password.result}@app-postgres:5432/vectordb"
    TEMPORAL_DATABASE_URL = "postgresql://temporal:${random_password.temporal_postgres_password.result}@temporal-postgres:5432/temporal"
  }
}

# Apply Kubernetes manifests
resource "kubernetes_manifest" "kubernetes_resources" {
  for_each = fileset("${path.module}/../../kubernetes", "*.yaml")

  manifest = yamldecode(templatefile(
    "${path.module}/../../kubernetes/${each.value}",
    {
      namespace           = kubernetes_namespace.vdb.metadata[0].name
      ingress_ip_name     = var.ingress_ip_name
      domain              = var.domain
      api_subdomain       = var.api_subdomain
      app_subdomain       = var.app_subdomain
      temporal_subdomain  = var.temporal_subdomain
      container_registry  = var.container_registry
    }
  ))

  depends_on = [
    kubernetes_namespace.vdb,
    kubernetes_config_map.vdb_config,
    kubernetes_secret.vdb_secrets
  ]
}

output "namespace" {
  description = "Kubernetes namespace"
  value       = kubernetes_namespace.vdb.metadata[0].name
}

output "postgres_password" {
  description = "Generated PostgreSQL password"
  value       = random_password.postgres_password.result
  sensitive   = true
}

output "temporal_postgres_password" {
  description = "Generated Temporal PostgreSQL password"
  value       = random_password.temporal_postgres_password.result
  sensitive   = true
}

output "rabbitmq_password" {
  description = "Generated RabbitMQ password"
  value       = random_password.rabbitmq_password.result
  sensitive   = true
}

output "database_url" {
  description = "Application database URL"
  value       = "postgresql://vdbuser:${random_password.postgres_password.result}@app-postgres:5432/vectordb"
  sensitive   = true
}

/**
 * Terraform outputs for VectorDB GKE deployment
 */

# ==================== GKE Cluster Outputs ====================
output "gke_cluster_name" {
  description = "GKE cluster name"
  value       = module.gke.cluster_name
}

output "gke_cluster_endpoint" {
  description = "GKE cluster endpoint"
  value       = module.gke.endpoint
  sensitive   = true
}

output "gke_cluster_region" {
  description = "GKE cluster region"
  value       = var.gcp_region
}

output "kubectl_config_command" {
  description = "Command to configure kubectl"
  value       = "gcloud container clusters get-credentials ${module.gke.cluster_name} --zone ${var.gcp_zone} --project ${var.gcp_project_id}"
}

# ==================== PostgreSQL Outputs ====================
output "temporal_db_host" {
  description = "Temporal PostgreSQL host (internal)"
  value       = module.postgres.temporal_db_host
}

output "app_db_host" {
  description = "Application PostgreSQL host (internal)"
  value       = module.postgres.app_db_host
}

# ==================== Temporal Outputs ====================
output "temporal_ui_url" {
  description = "Temporal UI public URL"
  value       = module.temporal.temporal_ui_url
}

output "temporal_grpc_endpoint" {
  description = "Temporal gRPC endpoint (internal)"
  value       = "${module.temporal.temporal_grpc_host}:7233"
}

# ==================== FastAPI Outputs ====================
output "fastapi_url" {
  description = "FastAPI backend public URL"
  value       = module.application.fastapi_url
}

# ==================== Cost Estimation ====================
output "estimated_monthly_cost" {
  description = "Estimated monthly cost breakdown (USD)"
  value = {
    gke_cluster     = "$${var.use_preemptible_nodes ? 29 : 73}"
    postgres_storage = "$4"
    load_balancers  = "$36"
    total           = "$${var.use_preemptible_nodes ? 69 : 113}"
    note            = "Actual costs may vary. Use GCP pricing calculator for precise estimates."
  }
}

# ==================== Next Steps ====================
output "next_steps" {
  description = "Post-deployment instructions"
  value       = <<-EOT

  ====================================
  🚀 Deployment Complete!
  ====================================

  1. Configure kubectl:
     ${self.kubectl_config_command}

  2. Access Temporal UI:
     ${module.temporal.temporal_ui_url}

  3. Access FastAPI:
     ${module.application.fastapi_url}

  4. Check pod status:
     kubectl get pods -A

  5. View logs:
     kubectl logs -n default deployment/vdb-api
     kubectl logs -n temporal deployment/temporal

  6. (Optional) Set up DNS:
     - Point ${var.temporal_ui_domain} to ${module.temporal.temporal_ui_ip}
     - Point ${var.fastapi_domain} to ${module.application.fastapi_ip}

  7. (Optional) Enable SSL/HTTPS:
     - Uncomment ssl module in main.tf
     - Set temporal_ui_domain and fastapi_domain variables
     - Run: terraform apply

  ====================================
  EOT
}

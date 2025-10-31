output "cluster_name" {
  description = "GKE cluster name"
  value       = google_container_cluster.primary.name
}

output "cluster_endpoint" {
  description = "GKE cluster endpoint"
  value       = google_container_cluster.primary.endpoint
  sensitive   = true
}

output "cluster_ca_certificate" {
  description = "GKE cluster CA certificate"
  value       = google_container_cluster.primary.master_auth[0].cluster_ca_certificate
  sensitive   = true
}

output "region" {
  description = "GCP region"
  value       = var.region
}

output "project_id" {
  description = "GCP project ID"
  value       = var.project_id
}

output "ingress_ip" {
  description = "Static IP address for ingress"
  value       = google_compute_global_address.ingress_ip.address
}

output "ingress_ip_name" {
  description = "Name of the static IP resource"
  value       = google_compute_global_address.ingress_ip.name
}

output "backup_bucket" {
  description = "GCS bucket for backups"
  value       = google_storage_bucket.backups.name
}

output "artifact_registry_url" {
  description = "Artifact Registry repository URL"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.vdb_images.repository_id}"
}

output "workload_identity_service_account" {
  description = "Service account email for workload identity"
  value       = google_service_account.vdb_sa.email
}

output "kubectl_connection_command" {
  description = "Command to configure kubectl"
  value       = "gcloud container clusters get-credentials ${google_container_cluster.primary.name} --region ${var.region} --project ${var.project_id}"
}

output "dns_records" {
  description = "DNS A records to configure"
  value = {
    api      = "${var.api_subdomain}.${var.domain} -> ${google_compute_global_address.ingress_ip.address}"
    app      = "${var.app_subdomain}.${var.domain} -> ${google_compute_global_address.ingress_ip.address}"
    temporal = "${var.temporal_subdomain}.${var.domain} -> ${google_compute_global_address.ingress_ip.address}"
  }
}

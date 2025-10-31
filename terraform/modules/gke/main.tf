/**
 * GKE Cluster Module - Cost Optimized
 * Zonal cluster with e2-medium nodes and autoscaling
 */

resource "google_container_cluster" "primary" {
  name     = var.cluster_name
  location = var.zone  # Zonal cluster (cheaper than regional)

  # We can't create a cluster with no node pool defined, but we want to only use
  # separately managed node pools. So we create the smallest possible default
  # node pool and immediately delete it.
  remove_default_node_pool = true
  initial_node_count       = 1

  # Network configuration
  network    = "default"
  subnetwork = "default"

  # Cluster configuration
  enable_autopilot = false  # Standard cluster for more control

  # Release channel for auto-updates
  release_channel {
    channel = "REGULAR"
  }

  # Workload Identity for secure service account access
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  # Maintenance window
  maintenance_policy {
    daily_maintenance_window {
      start_time = "03:00"  # 3 AM PST
    }
  }

  # Resource labels
  resource_labels = var.labels

  # Addons
  addons_config {
    http_load_balancing {
      disabled = false
    }
    horizontal_pod_autoscaling {
      disabled = false
    }
  }

  # Disable client certificate for security
  master_auth {
    client_certificate_config {
      issue_client_certificate = false
    }
  }

  # Enable binary authorization (optional, for added security)
  # binary_authorization {
  #   evaluation_mode = "PROJECT_SINGLETON_POLICY_ENFORCE"
  # }
}

resource "google_container_node_pool" "primary_nodes" {
  name       = "${var.cluster_name}-node-pool"
  location   = var.zone
  cluster    = google_container_cluster.primary.name

  # Autoscaling configuration
  autoscaling {
    min_node_count = var.min_nodes
    max_node_count = var.max_nodes
  }

  # Node configuration
  node_config {
    machine_type = var.machine_type  # e2-medium: 2 vCPU, 4GB RAM

    # Preemptible nodes for cost savings (optional)
    preemptible  = var.preemptible
    spot         = false  # Set to true for even cheaper spot instances

    disk_size_gb = var.disk_size_gb
    disk_type    = "pd-standard"  # Standard persistent disk (cheaper than SSD)

    # Scopes for GCP service access
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform",
    ]

    # Workload Identity
    workload_metadata_config {
      mode = "GKE_METADATA"
    }

    # Resource labels
    labels = var.labels

    # Metadata
    metadata = {
      disable-legacy-endpoints = "true"
    }

    # Security: Enable shielded nodes
    shielded_instance_config {
      enable_secure_boot          = true
      enable_integrity_monitoring = true
    }
  }

  # Upgrade settings
  management {
    auto_repair  = true
    auto_upgrade = true
  }

  # Node pool lifecycle
  lifecycle {
    ignore_changes = [
      initial_node_count,
    ]
  }
}

# Outputs
output "cluster_name" {
  description = "GKE cluster name"
  value       = google_container_cluster.primary.name
}

output "endpoint" {
  description = "GKE cluster endpoint"
  value       = google_container_cluster.primary.endpoint
}

output "ca_certificate" {
  description = "GKE cluster CA certificate"
  value       = google_container_cluster.primary.master_auth[0].cluster_ca_certificate
  sensitive   = true
}

output "cluster_id" {
  description = "GKE cluster ID"
  value       = google_container_cluster.primary.id
}

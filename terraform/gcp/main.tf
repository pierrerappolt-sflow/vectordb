terraform {
  required_version = ">= 1.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  # Uncomment for remote state
  # backend "gcs" {
  #   bucket = "your-tf-state-bucket"
  #   prefix = "vdb/gke"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# GKE Cluster
resource "google_container_cluster" "primary" {
  name     = var.cluster_name
  location = var.region

  # Remove default node pool
  remove_default_node_pool = true
  initial_node_count       = 1

  # Network configuration
  network    = var.network
  subnetwork = var.subnetwork

  # Cluster networking
  ip_allocation_policy {
    cluster_ipv4_cidr_block  = var.cluster_ipv4_cidr
    services_ipv4_cidr_block = var.services_ipv4_cidr
  }

  # Cluster features
  addons_config {
    http_load_balancing {
      disabled = false
    }
    gce_persistent_disk_csi_driver_config {
      enabled = true
    }
  }

  # Workload Identity
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  # Maintenance window
  maintenance_policy {
    daily_maintenance_window {
      start_time = "03:00"
    }
  }

  # Release channel for automatic upgrades
  release_channel {
    channel = var.release_channel
  }

  # Network policy
  network_policy {
    enabled = true
  }

  # Logging and monitoring
  logging_config {
    enable_components = ["SYSTEM_COMPONENTS", "WORKLOADS"]
  }

  monitoring_config {
    enable_components = ["SYSTEM_COMPONENTS"]
    managed_prometheus {
      enabled = true
    }
  }
}

# Primary node pool
resource "google_container_node_pool" "primary_nodes" {
  name       = "${var.cluster_name}-node-pool"
  location   = var.region
  cluster    = google_container_cluster.primary.name
  node_count = var.node_count

  autoscaling {
    min_node_count = var.min_node_count
    max_node_count = var.max_node_count
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }

  node_config {
    machine_type = var.machine_type
    disk_size_gb = var.disk_size_gb
    disk_type    = "pd-standard"

    # OAuth scopes
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    # Metadata
    metadata = {
      disable-legacy-endpoints = "true"
    }

    # Workload Identity
    workload_metadata_config {
      mode = "GKE_METADATA"
    }

    # Labels
    labels = {
      environment = var.environment
      managed_by  = "terraform"
    }

    # Tags
    tags = ["gke-node", "${var.cluster_name}-node"]
  }
}

# Preemptible node pool for non-critical workloads
resource "google_container_node_pool" "preemptible_nodes" {
  name       = "${var.cluster_name}-preemptible-pool"
  location   = var.region
  cluster    = google_container_cluster.primary.name
  node_count = var.preemptible_node_count

  autoscaling {
    min_node_count = var.preemptible_min_count
    max_node_count = var.preemptible_max_count
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }

  node_config {
    preemptible  = true
    machine_type = var.preemptible_machine_type
    disk_size_gb = 100
    disk_type    = "pd-standard"

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    metadata = {
      disable-legacy-endpoints = "true"
    }

    workload_metadata_config {
      mode = "GKE_METADATA"
    }

    labels = {
      environment = var.environment
      managed_by  = "terraform"
      preemptible = "true"
    }

    # Taint for preemptible nodes
    taint {
      key    = "preemptible"
      value  = "true"
      effect = "NO_SCHEDULE"
    }

    tags = ["gke-node", "${var.cluster_name}-preemptible"]
  }
}

# Static IP for Ingress
resource "google_compute_global_address" "ingress_ip" {
  name = "${var.cluster_name}-ingress-ip"
}

# GCS bucket for backups
resource "google_storage_bucket" "backups" {
  name          = "${var.project_id}-vdb-backups"
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }
}

# Service account for workload identity
resource "google_service_account" "vdb_sa" {
  account_id   = "vdb-workload-identity"
  display_name = "VDB Workload Identity Service Account"
}

# IAM binding for GCS bucket access
resource "google_storage_bucket_iam_member" "backup_writer" {
  bucket = google_storage_bucket.backups.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.vdb_sa.email}"
}

# Artifact Registry for Docker images
resource "google_artifact_registry_repository" "vdb_images" {
  location      = var.region
  repository_id = "vdb-images"
  description   = "VectorDB Docker images"
  format        = "DOCKER"
}

# GCP Project Configuration
project_id = "ci-dev-376017"
region     = "us-central1"

# Cluster Configuration
cluster_name = "vdb-cluster"
environment  = "development"

# Network (use "default" or your custom VPC)
network    = "default"
subnetwork = "default"

# Node Pool Configuration
machine_type   = "e2-standard-4"  # 4 vCPUs, 16GB RAM
disk_size_gb   = 100
node_count     = 1
min_node_count = 1
max_node_count = 5

# Preemptible Nodes (optional, for cost savings)
preemptible_machine_type = "e2-standard-2"  # 2 vCPUs, 8GB RAM
preemptible_node_count   = 0
preemptible_min_count    = 0
preemptible_max_count    = 3

# Domain Configuration
domain             = "pierrestack.com"
api_subdomain      = "api"
app_subdomain      = "app"
temporal_subdomain = "temporal"

# Release Channel
release_channel = "REGULAR"  # RAPID, REGULAR, or STABLE

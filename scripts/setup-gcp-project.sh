#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "GCP Project Setup for VectorDB"
echo "=========================================="
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI not found${NC}"
    echo "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Get project ID
read -p "Enter GCP Project ID (e.g., pierre-dev): " PROJECT_ID
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}Error: Project ID cannot be empty${NC}"
    exit 1
fi

# Check if project exists
if gcloud projects describe $PROJECT_ID &>/dev/null; then
    echo -e "${YELLOW}Project $PROJECT_ID already exists${NC}"
    read -p "Use existing project? (y/n): " use_existing
    if [ "$use_existing" != "y" ]; then
        exit 0
    fi
else
    echo -e "${GREEN}Creating project $PROJECT_ID...${NC}"
    gcloud projects create $PROJECT_ID --name="$PROJECT_ID"

    echo ""
    echo "Listing billing accounts..."
    gcloud billing accounts list
    echo ""

    read -p "Enter billing account ID: " BILLING_ACCOUNT_ID
    if [ -z "$BILLING_ACCOUNT_ID" ]; then
        echo -e "${RED}Error: Billing account ID cannot be empty${NC}"
        exit 1
    fi

    echo "Linking billing account..."
    gcloud billing projects link $PROJECT_ID --billing-account=$BILLING_ACCOUNT_ID
fi

# Set as default project
echo "Setting project as default..."
gcloud config set project $PROJECT_ID

echo ""
echo -e "${GREEN}✓ Project configured${NC}"
echo ""

# Enable APIs
echo "Enabling required APIs (this may take a few minutes)..."
gcloud services enable \
  container.googleapis.com \
  compute.googleapis.com \
  artifactregistry.googleapis.com \
  cloudresourcemanager.googleapis.com \
  iam.googleapis.com \
  servicenetworking.googleapis.com \
  storage.googleapis.com \
  --quiet

echo ""
echo -e "${GREEN}✓ APIs enabled${NC}"
echo ""

# Set up IAM permissions for current user
echo "Configuring IAM permissions..."
USER_EMAIL=$(gcloud config get-value account)

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="user:$USER_EMAIL" \
  --role="roles/container.admin" \
  --quiet

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="user:$USER_EMAIL" \
  --role="roles/compute.admin" \
  --quiet

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="user:$USER_EMAIL" \
  --role="roles/iam.serviceAccountAdmin" \
  --quiet

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="user:$USER_EMAIL" \
  --role="roles/storage.admin" \
  --quiet

echo ""
echo -e "${GREEN}✓ IAM permissions configured${NC}"
echo ""

# Create Terraform state bucket
BUCKET_NAME="${PROJECT_ID}-terraform-state"
echo "Creating Terraform state bucket: $BUCKET_NAME..."

if gsutil ls gs://$BUCKET_NAME &>/dev/null; then
    echo -e "${YELLOW}Bucket already exists${NC}"
else
    gsutil mb -p $PROJECT_ID -l us-central1 gs://$BUCKET_NAME
    gsutil versioning set on gs://$BUCKET_NAME
    echo -e "${GREEN}✓ Terraform state bucket created${NC}"
fi

echo ""

# Get domain
read -p "Enter your domain name (e.g., example.com): " DOMAIN
if [ -z "$DOMAIN" ]; then
    echo -e "${YELLOW}Warning: Domain not set, you can set it later${NC}"
    DOMAIN="your-domain.com"
fi

# Get Cohere API key
read -p "Enter Cohere API key (or press Enter to skip): " COHERE_API_KEY
if [ -z "$COHERE_API_KEY" ]; then
    echo -e "${YELLOW}Warning: Cohere API key not set, you'll need to set it before deployment${NC}"
    COHERE_API_KEY="your-cohere-api-key"
fi

# Create terraform.tfvars
echo ""
echo "Creating terraform.tfvars..."

cd "$(dirname "$0")/../terraform/gcp"

cat > terraform.tfvars <<EOF
# GCP Project Configuration
project_id = "$PROJECT_ID"
region     = "us-central1"

# Cluster Configuration
cluster_name = "vdb-cluster"
environment  = "development"

# Network
network    = "default"
subnetwork = "default"

# Node Pool Configuration
machine_type   = "e2-standard-4"  # 4 vCPUs, 16GB RAM
disk_size_gb   = 100
node_count     = 1
min_node_count = 1
max_node_count = 5

# Preemptible Nodes (optional, for cost savings)
preemptible_machine_type = "e2-standard-2"
preemptible_node_count   = 0
preemptible_min_count    = 0
preemptible_max_count    = 3

# Domain Configuration
domain             = "$DOMAIN"
api_subdomain      = "api"
app_subdomain      = "app"
temporal_subdomain = "temporal"

# Release Channel
release_channel = "REGULAR"
EOF

echo -e "${GREEN}✓ terraform.tfvars created${NC}"
echo ""

# Create environment variables file
echo "Creating .env file for deployment..."

cd "$(dirname "$0")/.."

cat > .env.deploy <<EOF
# VectorDB GCP Deployment Environment Variables
export PROJECT_ID=$PROJECT_ID
export DOMAIN=$DOMAIN
export COHERE_API_KEY=$COHERE_API_KEY
export REGION=us-central1
export CLUSTER_NAME=vdb-cluster
EOF

echo -e "${GREEN}✓ .env.deploy created${NC}"
echo ""

# Update backend.tf if using remote state
echo "Configuring Terraform remote state..."

cd "$(dirname "$0")/../terraform/gcp"

cat > backend.tf <<EOF
terraform {
  backend "gcs" {
    bucket = "$BUCKET_NAME"
    prefix = "vdb/gke"
  }
}
EOF

echo -e "${GREEN}✓ Terraform backend configured${NC}"
echo ""

# Summary
echo "=========================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Project ID:           $PROJECT_ID"
echo "Domain:               $DOMAIN"
echo "Region:               us-central1"
echo "Terraform State:      gs://$BUCKET_NAME"
echo ""
echo "Next steps:"
echo ""
echo "  1. Load environment variables:"
echo "     ${YELLOW}source .env.deploy${NC}"
echo ""
echo "  2. Initialize Terraform:"
echo "     ${YELLOW}make gke-init${NC}"
echo ""
echo "  3. Preview deployment:"
echo "     ${YELLOW}make gke-plan${NC}"
echo ""
echo "  4. Deploy to GKE:"
echo "     ${YELLOW}make gke-full${NC}"
echo ""
echo "  Or see detailed guide:"
echo "     ${YELLOW}cat terraform/SETUP.md${NC}"
echo ""
echo "=========================================="

#!/bin/bash
set -e

# End-to-end deployment script for VectorDB on GKE
# This script will:
# 1. Validate prerequisites
# 2. Build and push Docker image
# 3. Deploy infrastructure with Terraform
# 4. Configure kubectl
# 5. Wait for services to be ready

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}VectorDB GKE Deployment Script${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Check if PROJECT_ID is provided
PROJECT_ID=${1:-$(gcloud config get-value project 2>/dev/null)}

if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}Error: GCP project ID not set${NC}"
    echo "Usage: $0 PROJECT_ID"
    echo "Or set default: gcloud config set project PROJECT_ID"
    exit 1
fi

# Navigate to project root
cd "$(dirname "$0")/.."

# Step 1: Validate prerequisites
echo -e "${YELLOW}[1/6] Validating prerequisites...${NC}"

command -v gcloud >/dev/null 2>&1 || { echo -e "${RED}Error: gcloud not found${NC}"; exit 1; }
command -v terraform >/dev/null 2>&1 || { echo -e "${RED}Error: terraform not found${NC}"; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo -e "${RED}Error: kubectl not found${NC}"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo -e "${RED}Error: docker not found${NC}"; exit 1; }

echo -e "${GREEN}✓ All prerequisites met${NC}"
echo ""

# Step 2: Enable GCP APIs
echo -e "${YELLOW}[2/6] Enabling required GCP APIs...${NC}"

gcloud services enable container.googleapis.com --project=$PROJECT_ID
gcloud services enable compute.googleapis.com --project=$PROJECT_ID
gcloud services enable servicenetworking.googleapis.com --project=$PROJECT_ID

echo -e "${GREEN}✓ APIs enabled${NC}"
echo ""

# Step 3: Build and push Docker image
echo -e "${YELLOW}[3/6] Building and pushing Docker image...${NC}"

./scripts/build-and-push.sh "$PROJECT_ID" latest

echo ""

# Step 4: Check terraform.tfvars
echo -e "${YELLOW}[4/6] Checking Terraform configuration...${NC}"

if [ ! -f "terraform/terraform.tfvars" ]; then
    echo -e "${YELLOW}terraform.tfvars not found. Creating from example...${NC}"
    cp terraform/terraform.tfvars.example terraform/terraform.tfvars

    # Update project ID in tfvars
    sed -i.bak "s/your-gcp-project-id/$PROJECT_ID/g" terraform/terraform.tfvars
    sed -i.bak "s|gcr.io/PROJECT_ID|gcr.io/$PROJECT_ID|g" terraform/terraform.tfvars
    rm terraform/terraform.tfvars.bak

    echo -e "${GREEN}✓ Created terraform.tfvars${NC}"
    echo -e "${YELLOW}Please review terraform/terraform.tfvars before continuing${NC}"
    echo ""
    echo "Press Enter to continue or Ctrl+C to abort..."
    read -r
fi

echo -e "${GREEN}✓ Terraform configuration ready${NC}"
echo ""

# Step 5: Deploy with Terraform
echo -e "${YELLOW}[5/6] Deploying infrastructure with Terraform...${NC}"

cd terraform

# Initialize Terraform
terraform init

# Plan
echo -e "${BLUE}Terraform plan:${NC}"
terraform plan

echo ""
echo -e "${YELLOW}Review the plan above. Continue with deployment?${NC}"
echo "Type 'yes' to continue: "
read -r CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo -e "${RED}Deployment aborted${NC}"
    exit 1
fi

# Apply
terraform apply -auto-approve

echo -e "${GREEN}✓ Infrastructure deployed${NC}"
echo ""

# Step 6: Configure kubectl
echo -e "${YELLOW}[6/6] Configuring kubectl...${NC}"

CLUSTER_NAME=$(terraform output -raw gke_cluster_name)
CLUSTER_ZONE="us-west1-a"

gcloud container clusters get-credentials "$CLUSTER_NAME" \
    --zone "$CLUSTER_ZONE" \
    --project "$PROJECT_ID"

echo -e "${GREEN}✓ kubectl configured${NC}"
echo ""

# Wait for services
echo -e "${YELLOW}Waiting for services to be ready...${NC}"
echo "This may take 5-10 minutes..."
echo ""

# Wait for CloudNativePG operator
kubectl wait --for=condition=available deployment/cloudnative-pg \
    -n cnpg-system \
    --timeout=300s || echo -e "${YELLOW}CloudNativePG operator not ready yet${NC}"

# Wait for Temporal
kubectl wait --for=condition=available deployment/temporal \
    -n temporal \
    --timeout=300s || echo -e "${YELLOW}Temporal not ready yet${NC}"

# Wait for FastAPI
kubectl wait --for=condition=available deployment/vdb-api \
    -n default \
    --timeout=300s || echo -e "${YELLOW}FastAPI not ready yet${NC}"

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Deployment Complete! 🎉${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

# Show URLs
TEMPORAL_UI_URL=$(terraform output -raw temporal_ui_url)
FASTAPI_URL=$(terraform output -raw fastapi_url)

echo -e "${BLUE}Service URLs:${NC}"
echo "Temporal UI: $TEMPORAL_UI_URL"
echo "FastAPI: $FASTAPI_URL"
echo ""

echo -e "${BLUE}Useful commands:${NC}"
echo "View all pods: kubectl get pods -A"
echo "View logs: kubectl logs -n default deployment/vdb-api -f"
echo "Port-forward: kubectl port-forward -n temporal svc/temporal-ui 8080:80"
echo ""

echo -e "${BLUE}Next steps:${NC}"
echo "1. Access Temporal UI: $TEMPORAL_UI_URL"
echo "2. Access FastAPI docs: $FASTAPI_URL/docs"
echo "3. (Optional) Set up DNS for custom domains"
echo "4. (Optional) Enable SSL/HTTPS"
echo ""

cd ..

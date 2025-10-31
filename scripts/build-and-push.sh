#!/bin/bash
set -e

# Build and push Docker image to Google Container Registry
# Usage: ./scripts/build-and-push.sh [PROJECT_ID] [TAG]

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get project ID from gcloud or argument
PROJECT_ID=${1:-$(gcloud config get-value project 2>/dev/null)}
TAG=${2:-latest}

if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}Error: GCP project ID not set${NC}"
    echo "Usage: $0 [PROJECT_ID] [TAG]"
    echo "Or set default project: gcloud config set project PROJECT_ID"
    exit 1
fi

IMAGE_NAME="gcr.io/${PROJECT_ID}/vdb-api"
IMAGE_TAG="${IMAGE_NAME}:${TAG}"

echo -e "${GREEN}Building and pushing Docker image${NC}"
echo "Project ID: $PROJECT_ID"
echo "Image: $IMAGE_TAG"
echo ""

# Navigate to project root
cd "$(dirname "$0")/.."

# Build the image
echo -e "${YELLOW}Building Docker image...${NC}"
docker build -t "$IMAGE_TAG" -f apps/api/Dockerfile .

# Configure Docker for GCR
echo -e "${YELLOW}Configuring Docker for GCR...${NC}"
gcloud auth configure-docker --quiet

# Push to GCR
echo -e "${YELLOW}Pushing to Google Container Registry...${NC}"
docker push "$IMAGE_TAG"

echo -e "${GREEN}✓ Image pushed successfully!${NC}"
echo "Image: $IMAGE_TAG"
echo ""
echo "Next steps:"
echo "1. Update terraform.tfvars:"
echo "   fastapi_image = \"$IMAGE_TAG\""
echo ""
echo "2. Deploy with Terraform:"
echo "   cd terraform && terraform apply"

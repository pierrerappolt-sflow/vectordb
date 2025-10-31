#!/bin/bash
set -e

# Build and deploy UI using Cloud Build
# Usage: ./scripts/deploy-ui.sh

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get project ID from gcloud
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)

if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}Error: GCP project ID not set${NC}"
    echo "Set default project: gcloud config set project PROJECT_ID"
    exit 1
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Building and Deploying UI with Cloud Build${NC}"
echo -e "${BLUE}========================================${NC}"
echo "Project ID: $PROJECT_ID"
echo "Cluster: vdb-cluster (us-central1)"
echo ""

# Navigate to project root
cd "$(dirname "$0")/.."

# Trigger Cloud Build
echo -e "${YELLOW}Triggering Cloud Build...${NC}"
gcloud builds submit \
  --config=cloudbuild-ui.yaml \
  --project="$PROJECT_ID" \
  .

echo ""
echo -e "${GREEN}✓ UI deployment complete!${NC}"
echo ""
echo "Check status:"
echo "  kubectl get pods -n vdb -l app=ui"
echo "  kubectl logs -n vdb -l app=ui --tail=50"
echo ""
echo "Access UI:"
echo "  kubectl port-forward -n vdb svc/ui 3000:3000"
echo "  Open: http://localhost:3000"

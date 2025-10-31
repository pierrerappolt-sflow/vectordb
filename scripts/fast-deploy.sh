#!/bin/bash
set -e

IMAGE="us-central1-docker.pkg.dev/ci-dev-376017/vdb-images/vdb-api:latest"

echo "🔨 Building with BuildKit cache..."
docker buildx build \
  --platform linux/amd64 \
  --target production \
  --cache-from type=registry,ref=${IMAGE}-cache \
  --cache-to type=registry,ref=${IMAGE}-cache,mode=max \
  -t ${IMAGE} \
  -f apps/api/Dockerfile \
  --push \
  .

echo "♻️  Restarting deployment..."
kubectl rollout restart deployment api -n vdb

echo "⏳ Waiting for rollout..."
kubectl rollout status deployment api -n vdb --timeout=3m

echo "✅ Deployment complete!"

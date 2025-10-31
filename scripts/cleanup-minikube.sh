#!/bin/bash
set -e

echo "🧹 Cleaning up VectorDB from Minikube"
echo "======================================"

# Delete all resources in the vdb namespace
echo ""
echo "Deleting all resources in vdb namespace..."
kubectl delete namespace vdb --ignore-not-found=true

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "To completely remove minikube cluster, run: minikube delete"

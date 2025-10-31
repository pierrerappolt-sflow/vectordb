#!/bin/bash
set -e

echo "🚀 Deploying VectorDB to Minikube"
echo "=================================="

# Step 1: Configure Docker to use minikube's daemon
echo ""
echo "Step 1: Configuring Docker to use minikube's daemon..."
eval $(minikube -p minikube docker-env)

# Step 2: Build Docker images
echo ""
echo "Step 2: Building Docker images..."
echo "  - Building API image..."
docker build -t vdb-api:latest -f ./apps/api/Dockerfile --target production .

echo "  - Building Worker image..."
docker build -t vdb-worker:latest -f ./apps/worker/Dockerfile .

echo "  - Building Search Service image..."
docker build -t vdb-search:latest -f ./apps/search-service/Dockerfile --target development ./apps/search-service

echo "  - Building UI image..."
docker build -t vdb-ui:latest -f ./apps/ui/Dockerfile --target runner .

# Step 3: Create namespace
echo ""
echo "Step 3: Creating namespace..."
kubectl apply -f deploy/kubernetes/00-namespace.yaml

# Step 4: Apply ConfigMap and Secrets
echo ""
echo "Step 4: Applying ConfigMap and Secrets..."
kubectl apply -f deploy/kubernetes/01-configmap.yaml
kubectl apply -f deploy/kubernetes/02-secrets-minikube.yaml
kubectl apply -f deploy/kubernetes/03-config-file.yaml

# Step 5: Apply Storage (PVCs)
echo ""
echo "Step 5: Creating persistent volumes..."
kubectl apply -f deploy/kubernetes/10-storage-temporal-postgres.yaml
kubectl apply -f deploy/kubernetes/11-storage-app-postgres.yaml
kubectl apply -f deploy/kubernetes/12-storage-rabbitmq.yaml

# Step 6: Deploy Databases and Message Queue
echo ""
echo "Step 6: Deploying databases and message queue..."
kubectl apply -f deploy/kubernetes/20-temporal-postgres.yaml
kubectl apply -f deploy/kubernetes/21-app-postgres.yaml
kubectl apply -f deploy/kubernetes/22-rabbitmq.yaml

echo "  Waiting for databases to be ready..."
kubectl wait --for=condition=ready pod -l app=temporal-postgres -n vdb --timeout=300s
kubectl wait --for=condition=ready pod -l app=app-postgres -n vdb --timeout=300s
kubectl wait --for=condition=ready pod -l app=rabbitmq -n vdb --timeout=300s

# Step 7: Deploy Temporal
echo ""
echo "Step 7: Deploying Temporal..."
kubectl apply -f deploy/kubernetes/30-temporal.yaml
kubectl apply -f deploy/kubernetes/31-temporal-ui.yaml

echo "  Waiting for Temporal to be ready..."
kubectl wait --for=condition=ready pod -l app=temporal -n vdb --timeout=300s

# Step 8: Deploy Application Services
echo ""
echo "Step 8: Deploying application services..."
kubectl apply -f deploy/kubernetes/40-api.yaml
kubectl apply -f deploy/kubernetes/41-worker.yaml
kubectl apply -f deploy/kubernetes/42-event-dispatcher.yaml
kubectl apply -f deploy/kubernetes/43-event-log-consumer.yaml
kubectl apply -f deploy/kubernetes/44-search.yaml
kubectl apply -f deploy/kubernetes/45-search-worker.yaml

# Step 9: Deploy UI
echo ""
echo "Step 9: Deploying UI..."
kubectl apply -f deploy/kubernetes/50-ui.yaml

# Step 10: Deploy Database UI (pgweb)
echo ""
echo "Step 10: Deploying pgweb..."
kubectl apply -f deploy/kubernetes/60-pgweb.yaml

# Step 11: Wait for all pods to be ready
echo ""
echo "Step 11: Waiting for all pods to be ready..."
kubectl wait --for=condition=ready pod --all -n vdb --timeout=600s || true

# Step 12: Show status
echo ""
echo "=================================="
echo "✅ Deployment Complete!"
echo "=================================="
echo ""
kubectl get pods -n vdb
echo ""
echo "Access URLs (via NodePort):"
echo "  - UI:         http://localhost:30300"
echo "  - API:        http://localhost:30000"
echo "  - Temporal UI: http://localhost:30080"
echo "  - PGWeb:      http://localhost:30081"
echo ""
echo "To access services, run: minikube service <service-name> -n vdb"
echo "To view logs: kubectl logs -f <pod-name> -n vdb"
echo ""

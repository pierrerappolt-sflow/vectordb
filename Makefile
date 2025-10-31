.PHONY: help format lint test clean dev format-py lint-py test-py format-ui lint-ui test-ui migrate \
	minikube-start minikube-build minikube-load minikube-deploy minikube-status minikube-logs \
	minikube-clean minikube-tunnel minikube-full minikube-port-forward \
	gke-init gke-plan gke-apply gke-destroy gke-output gke-build gke-push gke-deploy-k8s \
	gke-full gke-status gke-logs gke-connect

help:
	@echo "Available commands:"
	@echo ""
	@echo "Development:"
	@echo "  make dev        - Start frontend and API in development mode"
	@echo ""
	@echo "Code Quality:"
	@echo "  make format     - Format all code (Python + UI)"
	@echo "  make format-py  - Format Python code only"
	@echo "  make format-ui  - Format UI code only"
	@echo "  make lint       - Run all linting checks (Python + UI)"
	@echo "  make lint-py    - Run Python linting only"
	@echo "  make lint-ui    - Run UI linting only"
	@echo "  make test       - Run all tests (Python + UI)"
	@echo "  make test-py    - Run Python tests only"
	@echo "  make test-ui    - Run UI tests only"
	@echo ""
	@echo "Database:"
	@echo "  make migrate    - Apply database migrations"
	@echo ""
	@echo "Minikube Deployment (Local):"
	@echo "  make minikube-full        - Complete deployment (start + build + deploy)"
	@echo "  make minikube-start       - Start minikube cluster"
	@echo "  make minikube-build       - Build Docker images"
	@echo "  make minikube-load        - Load images into minikube"
	@echo "  make minikube-deploy      - Deploy to minikube"
	@echo "  make minikube-status      - Check deployment status"
	@echo "  make minikube-port-forward - Forward ports for local access"
	@echo "  make minikube-logs        - View application logs"
	@echo "  make minikube-clean       - Clean up minikube deployment"
	@echo ""
	@echo "GKE Deployment (Production):"
	@echo "  make gke-full             - Complete GKE deployment (init + apply + deploy)"
	@echo "  make gke-init             - Initialize Terraform"
	@echo "  make gke-plan             - Preview Terraform changes"
	@echo "  make gke-apply            - Create GKE cluster & infrastructure"
	@echo "  make gke-output           - Show Terraform outputs (IPs, URLs, etc.)"
	@echo "  make gke-connect          - Configure kubectl for GKE cluster"
	@echo "  make gke-build            - Build Docker images for GKE"
	@echo "  make gke-push             - Push images to Artifact Registry"
	@echo "  make gke-deploy-k8s       - Deploy Kubernetes resources to GKE"
	@echo "  make gke-status           - Check GKE deployment status"
	@echo "  make gke-logs             - View GKE application logs"
	@echo "  make gke-destroy          - Destroy GKE cluster & infrastructure"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean      - Remove cache files"

# Python commands
format-py:
	uv run ruff format .
	uv run ruff check --fix .

lint-py:
	uv run ruff check .
	uv run mypy .

test-py:
	uv run pytest -v

# UI commands
format-ui:
	cd apps/ui && npm run lint:fix

lint-ui:
	cd apps/ui && npm run lint

test-ui:
	cd apps/ui && npm run test

# Combined commands
format: format-py format-ui

lint: lint-py lint-ui

test: test-py test-ui

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

dev:
	@trap 'kill 0' EXIT; \
	cd apps/api && uv run uvicorn vdb_api.main:app --reload --port 8000 & \
	cd apps/ui && npm install && npm run dev

migrate:
	@echo "Applying database migrations..."
	@./scripts/apply-migrations.sh

# ==================== Minikube Deployment ====================

# Start minikube cluster
minikube-start:
	@echo "Starting minikube cluster..."
	@minikube status >/dev/null 2>&1 || minikube start \
		--cpus=4 \
		--memory=8192 \
		--disk-size=50g \
		--driver=docker
	@minikube addons enable ingress
	@minikube addons enable metrics-server
	@echo "Minikube cluster started!"
	@echo "Kubernetes version: $$(kubectl version --short 2>/dev/null | grep Server || echo 'unknown')"

# Build Docker images
minikube-build:
	@echo "Building Docker images..."
	@eval $$(minikube docker-env) && \
		docker build -f apps/api/Dockerfile -t vdb-api:latest . && \
		docker build -f apps/worker/Dockerfile -t vdb-worker:latest . && \
		docker build -f apps/ui/Dockerfile -t vdb-ui:latest .
	@echo "Images built successfully!"

# Load images into minikube (alternative to building inside)
minikube-load:
	@echo "Loading Docker images into minikube..."
	@docker build -f apps/api/Dockerfile -t vdb-api:latest .
	@docker build -f apps/worker/Dockerfile -t vdb-worker:latest .
	@docker build -f apps/ui/Dockerfile -t vdb-ui:latest .
	@minikube image load vdb-api:latest
	@minikube image load vdb-worker:latest
	@minikube image load vdb-ui:latest
	@echo "Images loaded into minikube!"

# Deploy to minikube
minikube-deploy:
	@echo "Deploying to minikube..."
	@echo "Creating namespace and secrets..."
	@kubectl create namespace vdb --dry-run=client -o yaml | kubectl apply -f -
	@kubectl create secret generic vdb-secrets \
		--from-literal=POSTGRES_PASSWORD="dev-password" \
		--from-literal=TEMPORAL_POSTGRES_PASSWORD="dev-password" \
		--from-literal=RABBITMQ_DEFAULT_PASS="dev-password" \
		--from-literal=COHERE_API_KEY="$${COHERE_API_KEY:-your-cohere-key}" \
		--from-literal=DATABASE_URL="postgresql://vdbuser:dev-password@app-postgres:5432/vectordb" \
		--from-literal=TEMPORAL_DATABASE_URL="postgresql://temporal:dev-password@temporal-postgres:5432/temporal" \
		-n vdb --dry-run=client -o yaml | kubectl apply -f -
	@echo "Applying Kubernetes manifests..."
	@kubectl apply -f deploy/kubernetes/00-namespace.yaml
	@kubectl apply -f deploy/kubernetes/01-configmap.yaml
	@kubectl apply -f deploy/kubernetes/10-storage-temporal-postgres.yaml
	@kubectl apply -f deploy/kubernetes/11-storage-app-postgres.yaml
	@kubectl apply -f deploy/kubernetes/12-storage-rabbitmq.yaml
	@kubectl apply -f deploy/kubernetes/20-temporal-postgres.yaml
	@kubectl apply -f deploy/kubernetes/21-app-postgres.yaml
	@kubectl apply -f deploy/kubernetes/22-rabbitmq.yaml
	@echo "Waiting for databases to be ready..."
	@kubectl wait --for=condition=ready pod -l app=temporal-postgres -n vdb --timeout=300s || true
	@kubectl wait --for=condition=ready pod -l app=app-postgres -n vdb --timeout=300s || true
	@kubectl wait --for=condition=ready pod -l app=rabbitmq -n vdb --timeout=300s || true
	@kubectl apply -f deploy/kubernetes/30-temporal.yaml
	@kubectl apply -f deploy/kubernetes/31-temporal-ui.yaml
	@echo "Waiting for Temporal to be ready..."
	@kubectl wait --for=condition=ready pod -l app=temporal -n vdb --timeout=300s || true
	@kubectl apply -f deploy/kubernetes/40-api.yaml
	@kubectl apply -f deploy/kubernetes/41-worker.yaml
	@kubectl apply -f deploy/kubernetes/42-event-dispatcher.yaml
	@kubectl apply -f deploy/kubernetes/43-event-log-consumer.yaml
	@kubectl apply -f deploy/kubernetes/44-search.yaml
	@kubectl apply -f deploy/kubernetes/50-ui.yaml
	@kubectl apply -f deploy/kubernetes/60-adminer.yaml
	@echo ""
	@echo "Deployment complete!"
	@echo ""
	@echo "Run 'make minikube-status' to check deployment status"
	@echo "Run 'make minikube-port-forward' to access services"

# Check deployment status
minikube-status:
	@echo "Deployment Status:"
	@echo ""
	@kubectl get pods -n vdb
	@echo ""
	@kubectl get svc -n vdb
	@echo ""
	@kubectl get pvc -n vdb

# Port forward services for local access
minikube-port-forward:
	@echo "Setting up port forwarding..."
	@echo ""
	@echo "Access your services at:"
	@echo "  UI:         http://localhost:3000"
	@echo "  API:        http://localhost:8000"
	@echo "  Temporal:   http://localhost:8080"
	@echo "  Adminer:    http://localhost:8081"
	@echo "  RabbitMQ:   http://localhost:15672"
	@echo ""
	@echo "Press Ctrl+C to stop port forwarding"
	@echo ""
	@trap 'kill 0' EXIT; \
	kubectl port-forward -n vdb svc/ui 3000:3000 & \
	kubectl port-forward -n vdb svc/api 8000:8000 & \
	kubectl port-forward -n vdb svc/temporal-ui 8080:8080 & \
	kubectl port-forward -n vdb svc/adminer 8081:8080 & \
	kubectl port-forward -n vdb svc/rabbitmq-management 15672:15672 & \
	wait

# View logs
minikube-logs:
	@echo "Recent logs from all services:"
	@echo ""
	@echo "=== API Logs ==="
	@kubectl logs -n vdb -l app=api --tail=20
	@echo ""
	@echo "=== UI Logs ==="
	@kubectl logs -n vdb -l app=ui --tail=20
	@echo ""
	@echo "=== Worker Logs ==="
	@kubectl logs -n vdb -l app=worker --tail=20
	@echo ""
	@echo "For live logs, run: kubectl logs -f -n vdb -l app=<service-name>"

# Clean up minikube deployment
minikube-clean:
	@echo "Cleaning up minikube deployment..."
	@kubectl delete namespace vdb --ignore-not-found=true
	@echo "Namespace deleted. Run 'minikube delete' to remove the cluster entirely."

# Full deployment from scratch
minikube-full: minikube-start minikube-build minikube-deploy
	@echo ""
	@echo "=========================================="
	@echo "Minikube deployment complete!"
	@echo "=========================================="
	@echo ""
	@echo "Next steps:"
	@echo "  1. Check status:        make minikube-status"
	@echo "  2. Access services:     make minikube-port-forward"
	@echo "  3. View logs:           make minikube-logs"
	@echo ""
	@echo "To clean up:              make minikube-clean"
	@echo ""

# ==================== GKE Deployment (Production) ====================

# Check required environment variables
check-gke-env:
	@if [ -z "$$PROJECT_ID" ]; then \
		echo "ERROR: PROJECT_ID environment variable not set"; \
		echo "Run: export PROJECT_ID=your-gcp-project-id"; \
		exit 1; \
	fi
	@if [ -z "$$DOMAIN" ]; then \
		echo "ERROR: DOMAIN environment variable not set"; \
		echo "Run: export DOMAIN=yourdomain.com"; \
		exit 1; \
	fi
	@echo "✓ PROJECT_ID: $$PROJECT_ID"
	@echo "✓ DOMAIN: $$DOMAIN"

# Initialize Terraform
gke-init: check-gke-env
	@echo "Initializing Terraform for GKE..."
	@cd deploy/terraform/gcp && terraform init
	@echo "Terraform initialized!"

# Plan infrastructure changes
gke-plan: check-gke-env
	@echo "Planning Terraform changes..."
	@cd deploy/terraform/gcp && terraform plan \
		-var="project_id=$$PROJECT_ID" \
		-var="domain=$$DOMAIN" \
		-var="region=$${REGION:-us-central1}" \
		-var="cluster_name=$${CLUSTER_NAME:-vdb-cluster}"

# Apply infrastructure (create GKE cluster)
gke-apply: check-gke-env
	@echo "Creating GKE cluster and infrastructure..."
	@echo "This will take 5-10 minutes..."
	@cd deploy/terraform/gcp && terraform apply \
		-var="project_id=$$PROJECT_ID" \
		-var="domain=$$DOMAIN" \
		-var="region=$${REGION:-us-central1}" \
		-var="cluster_name=$${CLUSTER_NAME:-vdb-cluster}" \
		-auto-approve
	@echo ""
	@echo "GKE cluster created!"
	@echo ""
	@cd deploy/terraform/gcp && terraform output

# Show Terraform outputs
gke-output:
	@cd deploy/terraform/gcp && terraform output

# Connect kubectl to GKE cluster
gke-connect: check-gke-env
	@echo "Configuring kubectl for GKE cluster..."
	@cd deploy/terraform/gcp && \
		CLUSTER_NAME=$$(terraform output -raw cluster_name) && \
		REGION=$$(terraform output -raw region) && \
		gcloud container clusters get-credentials $$CLUSTER_NAME --region $$REGION --project $$PROJECT_ID
	@echo ""
	@echo "kubectl configured! Testing connection..."
	@kubectl get nodes
	@echo ""
	@echo "✓ Connected to GKE cluster"

# Build Docker images for GKE
gke-build: check-gke-env
	@echo "Building Docker images for GKE..."
	@REGISTRY=$$(cd deploy/terraform/gcp && terraform output -raw artifact_registry_url 2>/dev/null || echo "$$REGION-docker.pkg.dev/$$PROJECT_ID/vdb-images") && \
		echo "Building images for registry: $$REGISTRY" && \
		docker build -f apps/api/Dockerfile -t $$REGISTRY/vdb-api:latest . && \
		docker build -f apps/worker/Dockerfile -t $$REGISTRY/vdb-worker:latest . && \
		docker build -f apps/ui/Dockerfile -t $$REGISTRY/vdb-ui:latest .
	@echo "Images built successfully!"

# Push images to Artifact Registry
gke-push: check-gke-env
	@echo "Configuring Docker for Artifact Registry..."
	@gcloud auth configure-docker $${REGION:-us-central1}-docker.pkg.dev
	@echo "Pushing images to Artifact Registry..."
	@REGISTRY=$$(cd deploy/terraform/gcp && terraform output -raw artifact_registry_url 2>/dev/null || echo "$${REGION:-us-central1}-docker.pkg.dev/$$PROJECT_ID/vdb-images") && \
		docker push $$REGISTRY/vdb-api:latest && \
		docker push $$REGISTRY/vdb-worker:latest && \
		docker push $$REGISTRY/vdb-ui:latest
	@echo "Images pushed successfully!"

# Deploy Kubernetes resources to GKE
gke-deploy-k8s: check-gke-env
	@echo "Deploying Kubernetes resources to GKE..."
	@REGISTRY=$$(cd deploy/terraform/gcp && terraform output -raw artifact_registry_url 2>/dev/null) && \
		INGRESS_IP=$$(cd deploy/terraform/gcp && terraform output -raw ingress_ip) && \
		INGRESS_IP_NAME=$$(cd deploy/terraform/gcp && terraform output -raw ingress_ip_name) && \
		echo "Using registry: $$REGISTRY" && \
		echo "Using ingress IP: $$INGRESS_IP" && \
		echo "" && \
		echo "Creating namespace and secrets..." && \
		kubectl create namespace vdb --dry-run=client -o yaml | kubectl apply -f - && \
		kubectl create secret generic vdb-secrets \
			--from-literal=POSTGRES_PASSWORD="$$(openssl rand -base64 32)" \
			--from-literal=TEMPORAL_POSTGRES_PASSWORD="$$(openssl rand -base64 32)" \
			--from-literal=RABBITMQ_DEFAULT_PASS="$$(openssl rand -base64 32)" \
			--from-literal=COHERE_API_KEY="$${COHERE_API_KEY:?COHERE_API_KEY not set}" \
			-n vdb --dry-run=client -o yaml | kubectl apply -f - && \
		echo "" && \
		echo "Updating manifests with registry and domain..." && \
		sed "s|image: vdb-api:latest|image: $$REGISTRY/vdb-api:latest|g" deploy/kubernetes/40-api-loadbalancer.yaml | kubectl apply -f - && \
		sed "s|image: vdb-worker:latest|image: $$REGISTRY/vdb-worker:latest|g" deploy/kubernetes/41-worker.yaml | kubectl apply -f - && \
		sed "s|image: vdb-worker:latest|image: $$REGISTRY/vdb-worker:latest|g" deploy/kubernetes/42-event-dispatcher.yaml | kubectl apply -f - && \
		sed "s|image: vdb-worker:latest|image: $$REGISTRY/vdb-worker:latest|g" deploy/kubernetes/43-event-log-consumer.yaml | kubectl apply -f - && \
		sed "s|image: vdb-worker:latest|image: $$REGISTRY/vdb-worker:latest|g" deploy/kubernetes/44-search.yaml | kubectl apply -f - && \
		sed "s|image: vdb-ui:latest|image: $$REGISTRY/vdb-ui:latest|g" deploy/kubernetes/50-ui-loadbalancer.yaml | \
		sed "s|yourdomain.com|$$DOMAIN|g" | kubectl apply -f - && \
		sed "s|yourdomain.com|$$DOMAIN|g" deploy/kubernetes/70-ingress-gke.yaml | \
		sed "s|vdb-ingress-ip|$$INGRESS_IP_NAME|g" | kubectl apply -f - && \
		kubectl apply -f deploy/kubernetes/00-namespace.yaml && \
		kubectl apply -f deploy/kubernetes/01-configmap.yaml && \
		kubectl apply -f deploy/kubernetes/10-storage-temporal-postgres.yaml && \
		kubectl apply -f deploy/kubernetes/11-storage-app-postgres.yaml && \
		kubectl apply -f deploy/kubernetes/12-storage-rabbitmq.yaml && \
		kubectl apply -f deploy/kubernetes/20-temporal-postgres.yaml && \
		kubectl apply -f deploy/kubernetes/21-app-postgres.yaml && \
		kubectl apply -f deploy/kubernetes/22-rabbitmq.yaml && \
		echo "" && \
		echo "Waiting for databases..." && \
		kubectl wait --for=condition=ready pod -l app=temporal-postgres -n vdb --timeout=300s || true && \
		kubectl wait --for=condition=ready pod -l app=app-postgres -n vdb --timeout=300s || true && \
		kubectl wait --for=condition=ready pod -l app=rabbitmq -n vdb --timeout=300s || true && \
		kubectl apply -f deploy/kubernetes/30-temporal.yaml && \
		kubectl apply -f deploy/kubernetes/31-temporal-ui.yaml && \
		kubectl apply -f deploy/kubernetes/60-adminer.yaml
	@echo ""
	@echo "=========================================="
	@echo "GKE deployment complete!"
	@echo "=========================================="
	@echo ""
	@INGRESS_IP=$$(cd deploy/terraform/gcp && terraform output -raw ingress_ip) && \
		echo "Configure DNS A records:" && \
		echo "  api.$$DOMAIN     -> $$INGRESS_IP" && \
		echo "  app.$$DOMAIN     -> $$INGRESS_IP" && \
		echo "  temporal.$$DOMAIN -> $$INGRESS_IP" && \
		echo "" && \
		echo "Then access at:" && \
		echo "  UI:         https://app.$$DOMAIN" && \
		echo "  API:        https://api.$$DOMAIN" && \
		echo "  Temporal:   https://temporal.$$DOMAIN" && \
		echo "" && \
		echo "Certificate provisioning takes 10-15 minutes after DNS is configured"

# Check GKE deployment status
gke-status:
	@echo "GKE Deployment Status:"
	@echo ""
	@kubectl get nodes
	@echo ""
	@kubectl get pods -n vdb
	@echo ""
	@kubectl get svc -n vdb
	@echo ""
	@echo "Ingress status:"
	@kubectl get ingress -n vdb
	@echo ""
	@echo "Certificate status:"
	@kubectl get managedcertificate -n vdb

# View GKE logs
gke-logs:
	@echo "Recent logs from GKE services:"
	@echo ""
	@echo "=== API Logs ==="
	@kubectl logs -n vdb -l app=api --tail=20
	@echo ""
	@echo "=== UI Logs ==="
	@kubectl logs -n vdb -l app=ui --tail=20
	@echo ""
	@echo "=== Worker Logs ==="
	@kubectl logs -n vdb -l app=worker --tail=20
	@echo ""
	@echo "For live logs: kubectl logs -f -n vdb -l app=<service-name>"

# Destroy GKE infrastructure
gke-destroy: check-gke-env
	@echo "WARNING: This will destroy the GKE cluster and all resources!"
	@echo "Press Ctrl+C to cancel, or wait 10 seconds to continue..."
	@sleep 10
	@echo "Deleting Kubernetes resources..."
	@kubectl delete namespace vdb --ignore-not-found=true || true
	@echo "Destroying Terraform infrastructure..."
	@cd deploy/terraform/gcp && terraform destroy \
		-var="project_id=$$PROJECT_ID" \
		-var="domain=$$DOMAIN" \
		-var="region=$${REGION:-us-central1}" \
		-var="cluster_name=$${CLUSTER_NAME:-vdb-cluster}" \
		-auto-approve
	@echo "GKE infrastructure destroyed"

# Full GKE deployment
gke-full: check-gke-env gke-init gke-apply gke-connect gke-build gke-push gke-deploy-k8s
	@echo ""
	@echo "=========================================="
	@echo "Complete GKE deployment finished!"
	@echo "=========================================="
	@echo ""
	@echo "Next steps:"
	@echo "  1. Configure DNS (see output above)"
	@echo "  2. Check status:     make gke-status"
	@echo "  3. View logs:        make gke-logs"
	@echo ""

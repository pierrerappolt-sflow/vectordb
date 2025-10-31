# Dockerfile for VectorDB Worker
# Unified worker for processing document ingestion and search tasks via Temporal
#
# Build context must be the project root (where pyproject.toml is)
# Example: docker build -f apps/worker/Dockerfile .

FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast Python package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory to project root
WORKDIR /workspace

# Copy workspace configuration
COPY pyproject.toml uv.lock ./

# Copy all workspace packages (needed for dependency resolution)
COPY packages/ ./packages/
COPY apps/ ./apps/

# Install dependencies using uv
RUN uv sync --frozen --no-dev

# Set working directory to worker
WORKDIR /workspace/apps/worker

# Run the worker
CMD ["uv", "run", "--directory", "/workspace", "python", "-m", "vdb_worker.worker"]

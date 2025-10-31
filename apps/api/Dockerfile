# Multi-stage Dockerfile for VectorDB API
# Used for both API server and Temporal worker
#
# Build context must be the project root (where pyproject.toml is)
# Example: docker build -f apps/api/Dockerfile .

FROM python:3.12-slim as base

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

# Copy only dependency files first (better cache invalidation)
COPY pyproject.toml uv.lock ./
COPY packages/core/pyproject.toml ./packages/core/
COPY apps/api/pyproject.toml ./apps/api/
COPY apps/worker/pyproject.toml ./apps/worker/
COPY apps/search-service/pyproject.toml ./apps/search-service/

# Copy source code so editable workspace packages have their files (e.g., README.md)
COPY packages/ ./packages/
COPY apps/ ./apps/

# Install dependencies using uv with cache mount (after sources are present)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# ==================== Development Stage ====================
FROM base as development

# Install development dependencies with cache mount
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --all-extras

# Expose API port
EXPOSE 8000

# Set working directory to api app for runtime (volumes will mount here)
WORKDIR /app

# Default command (will use mounted volumes from docker-compose)
CMD ["uv", "run", "--directory", "/workspace", "uvicorn", "vdb_api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ==================== Production Stage ====================
FROM base as production

# Set working directory
WORKDIR /workspace/apps/api

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /workspace

USER appuser

# Expose API port
EXPOSE 8000

# Production command (no reload, no mounted volumes)
CMD ["uv", "run", "--directory", "/workspace", "uvicorn", "vdb_api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

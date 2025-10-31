# Dockerfile for VectorDB Search Service
# Vector search service with in-memory NumPy indices
#
# Build context must be the project root (where pyproject.toml is)
# Example: docker build -f apps/search-service/Dockerfile .

FROM python:3.12-slim as base

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

# ==================== Development Stage ====================
FROM base as development

# Expose search service port
EXPOSE 8001

# Run the search service using the installed virtual environment
CMD ["/workspace/.venv/bin/python", "-m", "search_service.main"]

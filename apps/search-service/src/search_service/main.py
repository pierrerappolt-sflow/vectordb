"""Main entry point for vector search service."""

from __future__ import annotations

import asyncio
import logging
import os

import uvicorn

from search_service.api import create_search_app
from search_service.vector_index import VectorIndexManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


async def run_search_service() -> None:
    """Run the vector search service.

    This is the main entry point for the search service container.
    It:
    1. Bootstraps indices from postgres on startup
    2. Starts FastAPI server for search queries

    The service only supports:
    - FLAT indexing (brute force exact search)
    - COSINE similarity metric
    """
    # Get configuration from environment
    database_url = os.getenv("DATABASE_URL", "postgresql://vdbuser:vdbpass@localhost:5432/vectordb")
    api_host = os.getenv("API_HOST", "0.0.0.0")
    api_port = int(os.getenv("API_PORT", "8001"))

    logger.info("=" * 80)
    logger.info("VDB Vector Search Service")
    logger.info("=" * 80)
    logger.info("Database: %s", database_url)
    logger.info("API: %s:%s", api_host, api_port)
    logger.info("Strategy: FLAT indexing with COSINE similarity")
    logger.info("=" * 80)

    # Initialize index manager
    index_manager = VectorIndexManager()

    # Bootstrap indices from postgres
    logger.info("Bootstrapping indices from postgres...")
    total_indexed = await index_manager.bootstrap_from_postgres(database_url)
    logger.info("✅ Bootstrap complete: %s embeddings indexed", total_indexed)

    # Create FastAPI app
    app = create_search_app(index_manager, database_url)

    # Start API server
    logger.info("Starting API server on %s:%s...", api_host, api_port)
    config = uvicorn.Config(
        app,
        host=api_host,
        port=api_port,
        log_level="info",
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(run_search_service())

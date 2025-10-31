"""FastAPI endpoints for vector search service."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING
from collections.abc import AsyncGenerator, Generator
import asyncpg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from vdb_core.domain.value_objects import VectorSimilarityMetric

if TYPE_CHECKING:
    from search_service.vector_index import VectorIndexManager

logger = logging.getLogger(__name__)


class EmbeddingItem(BaseModel):
    """Single embedding to index."""

    embedding_id: str
    vector: list[float]


class BatchIndexRequest(BaseModel):
    """Request to index multiple vectors (batch operation)."""

    library_id: str
    config_id: str
    embeddings: list[EmbeddingItem]


class BatchIndexResponse(BaseModel):
    """Response from batch index endpoint."""

    indexed_count: int
    failed_count: int = 0


class BatchDeleteRequest(BaseModel):
    """Request to delete multiple embeddings from index."""

    library_id: str
    config_id: str
    embedding_ids: list[str]


class BatchDeleteResponse(BaseModel):
    """Response from batch delete endpoint."""

    deleted_count: int


class SearchRequest(BaseModel):
    """Request to search for similar vectors."""

    library_id: str
    config_id: str
    query_vector: list[float]
    k: int = Field(default=10, ge=1, le=100, description="Number of results to return")


class SearchResult(BaseModel):
    """Single search result."""

    embedding_id: str
    chunk_id: str
    distance: float
    content: str | None = None


class SearchResponse(BaseModel):
    """Response from search endpoint."""

    results: list[SearchResult]
    total: int


class IndexStats(BaseModel):
    """Statistics for a single index."""

    library_id: str
    config_id: str
    dimensions: int
    strategy: str
    count: int


class StatsResponse(BaseModel):
    """Response from stats endpoint."""

    indices: list[IndexStats]
    total_embeddings: int


def create_search_app(index_manager: VectorIndexManager, database_url: str) -> FastAPI:
    """Create FastAPI application for search service.

    Args:
        index_manager: Vector index manager singleton
        database_url: PostgreSQL connection string

    Returns:
        FastAPI application

    """
    pool: asyncpg.Pool | None = None

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        """Manage application lifespan."""
        nonlocal pool
        logger.info("Starting search service API...")
        pool = await asyncpg.create_pool(database_url, min_size=2, max_size=10)
        logger.info("Database pool ready")
        yield
        if pool:
            await pool.close()
            logger.info("Database pool closed")

    app = FastAPI(title="VDB Search Service", version="0.1.0", lifespan=lifespan)

    @app.post("/index", response_model=BatchIndexResponse)
    async def batch_index_vectors(request: BatchIndexRequest) -> BatchIndexResponse:
        """Index multiple vectors in the in-memory index (batch operation)."""
        if not pool:
            msg = "Database pool not initialized"
            raise HTTPException(status_code=503, detail=msg)

        try:
            # Lookup VectorizationConfig to get strategy and metric
            config_row = await pool.fetchrow(
                """
                SELECT vector_indexing_strategy, vector_similarity_metric
                FROM vectorization_configs
                WHERE id = $1
                """,
                request.config_id,
            )

            if not config_row:
                msg = f"VectorizationConfig not found: {request.config_id}"
                raise HTTPException(status_code=404, detail=msg)

            strategy = config_row["vector_indexing_strategy"]
            metric = VectorSimilarityMetric(config_row["vector_similarity_metric"])

            # Get dimensions from first embedding vector
            if not request.embeddings:
                msg = "No embeddings provided"
                raise HTTPException(status_code=400, detail=msg)

            dimensions = len(request.embeddings[0].vector)

            # Batch add vectors to index manager
            for item in request.embeddings:
                index_manager.add_vector(
                    embedding_id=item.embedding_id,
                    library_id=request.library_id,
                    config_id=request.config_id,
                    vector=item.vector,
                    dimensions=dimensions,
                    strategy=strategy,
                    metric=metric,
                )

            indexed_count = len(request.embeddings)
            logger.info(
                "Batch indexed %s embeddings for library=%s, config=%s",
                indexed_count,
                request.library_id,
                request.config_id,
            )

            return BatchIndexResponse(indexed_count=indexed_count, failed_count=0)

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Batch indexing failed: %s", str(e))
            raise HTTPException(status_code=500, detail=f"Batch indexing failed: {e!s}") from e

    @app.delete("/index", response_model=BatchDeleteResponse)
    async def batch_delete_vectors(request: BatchDeleteRequest) -> BatchDeleteResponse:
        """Delete multiple vectors from the in-memory index (batch operation)."""
        try:
            removed_count, _ = index_manager.remove_vectors(
                library_id=request.library_id,
                config_id=request.config_id,
                embedding_ids=request.embedding_ids,
            )

            logger.info(
                "Batch deleted %s embeddings for library=%s, config=%s",
                removed_count,
                request.library_id,
                request.config_id,
            )

            return BatchDeleteResponse(deleted_count=removed_count)

        except Exception as e:
            logger.error("Batch deletion failed: %s", str(e))
            raise HTTPException(status_code=500, detail=f"Batch deletion failed: {e!s}") from e

    @app.post("/search", response_model=SearchResponse)
    async def search(request: SearchRequest) -> SearchResponse:
        """Vector similarity search endpoint."""
        if not pool:
            msg = "Database pool not initialized"
            raise HTTPException(status_code=503, detail=msg)

        try:
            # Perform vector search
            embedding_ids, distances = index_manager.search(
                library_id=request.library_id,
                config_id=request.config_id,
                query_vector=request.query_vector,
                k=request.k,
            )

            if not embedding_ids:
                return SearchResponse(results=[], total=0)

            # Enrich with chunk content from database
            rows = await pool.fetch(
                """
                SELECT e.id as embedding_id, e.chunk_id, c.content
                FROM embeddings e
                JOIN chunks c ON e.chunk_id = c.id
                WHERE e.id::text = ANY($1::text[])
                """,
                embedding_ids,
            )

            # Build result mapping
            content_map = {str(row["embedding_id"]): (str(row["chunk_id"]), row["content"]) for row in rows}

            # Construct results maintaining order from search
            results = []
            for embedding_id, distance in zip(embedding_ids, distances, strict=False):
                chunk_id, content = content_map.get(embedding_id, ("", None))
                results.append(
                    SearchResult(
                        embedding_id=embedding_id,
                        chunk_id=chunk_id,
                        distance=distance,
                        content=content,
                    )
                )

            return SearchResponse(results=results, total=len(results))

        except Exception as e:
            logger.error("Search failed: %s", str(e))
            raise HTTPException(status_code=500, detail=f"Search failed: {e!s}") from e

    @app.get("/stats", response_model=StatsResponse)
    async def stats() -> StatsResponse:
        """Index statistics endpoint."""
        try:
            stats_data = index_manager.get_stats()
            # Convert dict to IndexStats objects
            indices = [
                IndexStats(
                    library_id=stat["library_id"],  # type: ignore[arg-type]
                    config_id=stat["config_id"],  # type: ignore[arg-type]
                    dimensions=stat["dimensions"],  # type: ignore[arg-type]
                    strategy=stat["strategy"],  # type: ignore[arg-type]
                    count=stat["count"],  # type: ignore[arg-type]
                )
                for stat in stats_data
            ]
            total = sum(stat.count for stat in indices)
            return StatsResponse(indices=indices, total_embeddings=total)
        except Exception as e:
            logger.error("Stats failed: %s", str(e))
            raise HTTPException(status_code=500, detail=f"Stats failed: {e!s}") from e

    @app.get("/health")
    async def health():
        """Health check endpoint."""
        return {"status": "healthy", "service": "search"}

    return app

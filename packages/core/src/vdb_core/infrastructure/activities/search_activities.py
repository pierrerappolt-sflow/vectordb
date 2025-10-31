"""Temporal activities for vector search operations.

Activities are the units of work that execute domain logic within Temporal workflows.
They call domain services and repositories to perform actual business operations.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

# Rebuild Chunk dataclass to resolve forward references (fixes Pydantic error)
# This is needed because Chunk has a LibraryId field with a forward reference
from pydantic.dataclasses import rebuild_dataclass
from temporalio import activity

from uuid import UUID

from vdb_core.domain.value_objects import ChunkId
from vdb_core.domain.value_objects.chunk import Chunk


# Import the DI container getter from ingestion activities
from vdb_core.infrastructure.activities.ingestion_activities import get_di_container

rebuild_dataclass(Chunk)  # type: ignore[arg-type]


@activity.defn(name="generate_query_embedding")
async def generate_query_embedding_activity(
    query_text: str,
    library_id: str,
    config_id: str,
) -> list[float]:
    """Generate embedding vector for search query.

    Args:
        query_text: The text query to embed
        library_id: UUID of the library being searched
        config_id: VectorizationConfig ID to use for embedding strategy

    Returns:
        Embedding vector as list of floats

    """
    activity.logger.info(f"Generating embedding for query: {query_text[:50]}...")

    # Get dependencies from DI container
    container = get_di_container()
    uow = container.get_unit_of_work()
    strategy_resolver: Any = container.get_strategy_resolver()  # type: ignore[no-untyped-call]

    # Load the VectorizationConfig to get the correct embedding strategy entity
    from vdb_core.domain.value_objects import VectorizationConfigId

    async with uow:
        config = await uow.vectorization_configs.get(VectorizationConfigId(UUID(config_id)))

        # Get embedding strategy from the config
        embedding_strategy_entity = config.embedding_strategy

        activity.logger.info(
            f"Using embedding strategy: {embedding_strategy_entity.name} "
            f"({embedding_strategy_entity.dimensions}D)"
        )

    # Resolve the strategy entity to its implementation
    embedding_strategy_impl = strategy_resolver.get_embedder(embedding_strategy_entity)

    # Generate embedding using the strategy implementation with SEARCH input type
    vectors = await embedding_strategy_impl.embed(
        content=[query_text],
        input_type="search_query",
    )
    vector = vectors[0]  # Extract single vector from batch result

    activity.logger.info(f"Generated {len(vector)}-dimensional embedding")

    return list(vector)


@activity.defn(name="search_vectors")
async def search_vectors_activity(
    library_id: str,
    config_id: str,
    query_vector: list[float],
    top_k: int,
) -> list[dict[str, str | float]]:
    """Search for similar vectors in the vector index.

    Args:
        library_id: UUID of the library to search in
        config_id: UUID of the VectorizationConfig to search with
        query_vector: Query embedding vector
        top_k: Maximum number of results to return

    Returns:
        List of search results with embedding IDs, chunk IDs, and similarity scores

    """
    activity.logger.info(f"Searching library {library_id} config {config_id} for top {top_k} results")

    # Get search service URL from environment
    search_service_url = os.getenv("SEARCH_SERVICE_URL", "http://localhost:8001")

    # Make request to search service
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{search_service_url}/search",
            json={
                "library_id": library_id,
                "config_id": config_id,
                "query_vector": query_vector,
                "k": top_k,
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()

        results = data.get("results", [])
        activity.logger.info(f"Found {len(results)} results from search service")

        # Convert to expected format
        return [
            {
                "embedding_id": result["embedding_id"],
                "chunk_id": result["chunk_id"],
                "score": result["distance"],
            }
            for result in results
        ]


@activity.defn(name="enrich_search_results")
async def enrich_search_results_activity(
    raw_results: list[dict[str, str | float]],
) -> list[dict[str, str | float]]:
    """Enrich search results with chunk and document details.

    Args:
        raw_results: Raw search results with embedding IDs and scores

    Returns:
        Enriched results with chunk content, document names, etc.

    """
    activity.logger.info(f"Enriching {len(raw_results)} search results")

    # Get dependencies from DI container
    container = get_di_container()
    chunk_repository = container.get_chunk_read_repository()
    # No document repository needed for now (title omitted)

    enriched = []

    # Cache for document titles to avoid repeated fetches
    document_titles: dict[str, str] = {}

    for result in raw_results:
        chunk_id_str = result["chunk_id"]
        assert isinstance(chunk_id_str, str), f"chunk_id must be str, got {type(chunk_id_str)}"
        chunk_id_vo = ChunkId(chunk_id_str)

        # Fetch chunk from repository
        chunk = await chunk_repository.get_by_id(chunk_id_vo)

        if chunk is None:
            activity.logger.warning(f"Chunk not found: {result['chunk_id']}")
            continue

        # Fetch document title if not cached
        document_id_str = str(chunk.document_id)
        if document_id_str not in document_titles:
            document_titles[document_id_str] = f"Document {document_id_str[:8]}"

        # Build enriched result
        enriched.append(
            {
                "chunk_id": str(chunk.id),
                "embedding_id": result["embedding_id"],
                "document_id": document_id_str,
                "document_title": document_titles[document_id_str],
                "score": result["score"],
                "text": chunk.text,  # Include chunk text for display
                "status": chunk.status,
            }
        )

    activity.logger.info(f"Enriched {len(enriched)} results")

    return enriched


@activity.defn(name="update_query_status")
async def update_query_status_activity(
    query_id: str,
    status: str,
    results: list[dict[str, Any]] | None = None,
    error_message: str | None = None,
) -> None:
    """Update query status and results in database.

    Args:
        query_id: UUID of the query to update
        status: New status (PROCESSING, COMPLETED, FAILED)
        results: List of result dicts with chunk_id and score (for COMPLETED status)
                Format: [{"chunk_id": "...", "score": 0.95}, ...]
        error_message: Error message (for FAILED status)

    """
    import json
    from datetime import UTC, datetime
    from sqlalchemy import text

    activity.logger.info(f"Updating query {query_id} to status {status}")

    # Get dependencies from DI container
    container = get_di_container()
    uow = container.get_unit_of_work()

    async with uow:
        if status == "COMPLETED":
            # Update with results as JSONB
            await uow.session.execute(  # type: ignore[attr-defined]
                text("""
                    UPDATE queries
                    SET status = :status,
                        results = CAST(:results AS jsonb),
                        result_count = :result_count,
                        completed_at = :completed_at
                    WHERE id = :query_id
                """),
                {
                    "status": status,
                    "results": json.dumps(results or []),
                    "result_count": len(results) if results else 0,
                    "completed_at": datetime.now(UTC),
                    "query_id": query_id,
                }
            )
        elif status == "FAILED":
            # Update with error
            await uow.session.execute(  # type: ignore[attr-defined]
                text("""
                    UPDATE queries
                    SET status = :status,
                        error_message = :error_message,
                        completed_at = :completed_at
                    WHERE id = :query_id
                """),
                {
                    "status": status,
                    "error_message": error_message,
                    "completed_at": datetime.now(UTC),
                    "query_id": query_id,
                }
            )
        else:
            # Just update status (PROCESSING)
            await uow.session.execute(  # type: ignore[attr-defined]
                text("""
                    UPDATE queries
                    SET status = :status
                    WHERE id = :query_id
                """),
                {
                    "status": status,
                    "query_id": query_id,
                }
            )

        await uow.commit()

    activity.logger.info(f"Query {query_id} updated to {status}")

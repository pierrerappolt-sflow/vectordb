"""Temporal activities for VectorizationConfig processing workflow.

Each activity handles a single I/O operation for proper retry control.
"""

import logging
from typing import Any
from uuid import UUID

from temporalio import activity

from vdb_core.application.read_models import ChunkReadModel
from vdb_core.domain.entities.extracted_content import ExtractedContent
from vdb_core.domain.value_objects import (
    Chunk,
    ChunkId,
    ContentHash,
    Embedding,
    EmbeddingId,
    ModalityType,
    ModalityType,
    VectorizationConfigId,
)
from vdb_core.domain.value_objects.document.extracted_content_status import ExtractedContentStatus
from vdb_core.infrastructure.activities.ingestion_activities import get_di_container

logger = logging.getLogger(__name__)


@activity.defn(name="load_extracted_content")
async def load_extracted_content_activity(
    library_id: str,
    extracted_content_ids: list[str],
) -> list[dict[str, Any]]:
    """Load ExtractedContent objects from database.

    Args:
        library_id: ID of the library
        extracted_content_ids: IDs of ExtractedContent to load

    Returns:
        List of ExtractedContent objects serialized as dicts

    """
    activity.logger.info(f"Loading {len(extracted_content_ids)} ExtractedContent objects")

    container = get_di_container()
    uow = container.get_unit_of_work()

    async with uow:
        from sqlalchemy import text

        from vdb_core.infrastructure.persistence.postgres_unit_of_work import PostgresUnitOfWork

        # Cast to concrete type to access session
        # TODO: Consider adding session to IUnitOfWork interface or using a read repository
        if not isinstance(uow, PostgresUnitOfWork):
            msg = "This activity requires PostgresUnitOfWork"
            raise TypeError(msg)

        # Query ExtractedContent from database directly by IDs
        query = text("""
            SELECT id, document_id, document_fragment_id, content, modality_type,
                   modality_sequence_number, is_last_of_modality, metadata,
                   status, created_at, updated_at
            FROM extracted_contents
            WHERE id = ANY(:ids)
            ORDER BY modality_sequence_number
        """)

        if uow.session is None:
            msg = "PostgresUnitOfWork session is not initialized"
            raise RuntimeError(msg)
        result = await uow.session.execute(query, {"ids": extracted_content_ids})
        rows = result.mappings().all()

        extracted_contents = []
        for row in rows:
            ec_dict = {
                "id": str(row["id"]),
                "document_id": str(row["document_id"]),
                "document_fragment_id": str(row["document_fragment_id"]),
                "content": row["content"],
                "modality": row["modality_type"],
                "modality_sequence_number": row["modality_sequence_number"],
                "is_last_of_modality": row["is_last_of_modality"],
                "metadata": row["metadata"] or {},
            }
            extracted_contents.append(ec_dict)

        activity.logger.info(f"Loaded {len(extracted_contents)} ExtractedContent objects")
        return extracted_contents


@activity.defn(name="chunk_content")
async def chunk_content_activity(
    library_id: str,
    config_id: str,
    document_id: str,
    extracted_contents: list[dict[str, Any]],
) -> list[str]:
    """Chunk content using VectorizationConfig's chunking strategy.

    Args:
        library_id: ID of the library
        config_id: ID of the VectorizationConfig
        document_id: ID of the document
        extracted_contents: List of ExtractedContent objects as dicts

    Returns:
        List of created Chunk IDs

    """
    activity.logger.info(f"Chunking {len(extracted_contents)} ExtractedContent objects with config {config_id}")

    container = get_di_container()
    uow = container.get_unit_of_work()
    strategy_resolver = container.get_strategy_resolver()

    async with uow:
        # Load library and config
        library = await uow.libraries.get(UUID(library_id))

        # Load VectorizationConfig from repository
        config_uuid = VectorizationConfigId(UUID(config_id))
        vectorization_config = await uow.vectorization_configs.get(config_uuid)  # type: ignore[attr-defined]

        if not vectorization_config:
            msg = f"VectorizationConfig {config_id} not found"
            raise ValueError(msg)

        document = await library.get_document(UUID(document_id))

        chunk_ids = []
        document_chunk_index = 0

        # Process each ExtractedContent
        for ec_dict in extracted_contents:
            extracted = _deserialize_extracted_content(ec_dict)

            activity.logger.info(f"Chunking {extracted.modality.value.upper()} content ({len(extracted.content)} bytes)")

            # Get ChunkingStrategy for this modality from config
            from vdb_core.domain.value_objects import ModalityType

            modality_enum = ModalityType[extracted.modality.value.upper()]

            # Find chunking strategy for this modality
            chunking_strategy = next(
                (s for s in vectorization_config.chunking_strategies if s.modality.value == modality_enum),
                None,
            )

            if not chunking_strategy:
                activity.logger.warning(f"No chunking strategy for {extracted.modality.value}, skipping")
                continue

            # Resolve to implementation
            chunker_impl = strategy_resolver.get_chunker(chunking_strategy)

            # Chunk the content
            raw_chunks = chunker_impl.chunk(extracted.content)

            activity.logger.info(f"Created {len(raw_chunks)} chunks using {chunking_strategy.model_key}")

            # Create Chunk value objects
            for chunk_content in raw_chunks:
                # Create Chunk value object (immutable, deduplicated)
                chunk = Chunk(
                    library_id=library.id,
                    document_id=document.id,
                    modality=extracted.modality,
                    content=chunk_content,
                    chunking_strategy_id=chunking_strategy.id,
                    content_hash=ContentHash.from_content(chunk_content),
                    metadata=extracted.metadata or {},
                )

                # Add chunk to library (deduplication happens here)
                stored_chunk = library.add_chunk(chunk)

                # Persist chunk to database directly (we have the context here)
                from sqlalchemy import text

                # Convert content to string if bytes
                chunk_content_str = chunk_content
                if isinstance(chunk_content_str, bytes):
                    chunk_content_str = chunk_content_str.decode("utf-8")

                # ChunkId.value is already a UUID string
                chunk_ids.append(stored_chunk.chunk_id.value)

                await uow.session.execute(
                    text("""
                        INSERT INTO chunks (
                            id, document_id, chunking_strategy_id, extracted_content_id,
                            sequence_number, content, content_hash, modality_type
                        ) VALUES (
                            :id, :document_id, :chunking_strategy_id, :extracted_content_id,
                            :sequence_number, :content, :content_hash, :modality_type
                        )
                        ON CONFLICT (id) DO NOTHING
                    """),
                    {
                        "id": stored_chunk.chunk_id.value,
                        "document_id": str(document.id),
                        "chunking_strategy_id": str(chunking_strategy.id),
                        "extracted_content_id": str(extracted.id),
                        "sequence_number": document_chunk_index,
                        "content": chunk_content_str,
                        "content_hash": stored_chunk.content_hash.value,
                        "modality_type": extracted.modality.value,
                    },
                )

                document_chunk_index += 1

        await uow.commit()

        activity.logger.info(f"✅ Created {len(chunk_ids)} chunks total")
        return chunk_ids


@activity.defn(name="generate_embeddings")
async def generate_embeddings_activity(
    library_id: str,
    config_id: str,
    chunk_ids: list[str],
) -> dict[str, Any]:
    """Generate embeddings using VectorizationConfig's embedding strategy.

    Args:
        library_id: ID of the library
        config_id: ID of the VectorizationConfig
        chunk_ids: List of Chunk IDs to embed

    Returns:
        Dict with embedding_ids, num_embeddings, and avg_dimension

    """
    activity.logger.info(f"Generating embeddings for {len(chunk_ids)} chunks with config {config_id}")

    container = get_di_container()
    uow = container.get_unit_of_work()
    strategy_resolver = container.get_strategy_resolver()
    chunk_read_repo = container.get_chunk_read_repository()

    async with uow:
        # Load library and config
        library = await uow.libraries.get(UUID(library_id))

        # Load VectorizationConfig from repository
        config_uuid = VectorizationConfigId(UUID(config_id))
        vectorization_config = await uow.vectorization_configs.get(config_uuid)  # type: ignore[attr-defined]

        if not vectorization_config:
            msg = f"VectorizationConfig {config_id} not found"
            raise ValueError(msg)

        # Load chunks from database using chunk read repository
        chunks = []
        for chunk_id_str in chunk_ids:
            try:
                # ChunkId expects a string (the UUID as string)
                chunk = await chunk_read_repo.get_by_id(ChunkId(chunk_id_str))
                if chunk:
                    chunks.append(chunk)
            except Exception as e:
                activity.logger.warning(f"Failed to load chunk {chunk_id_str}: {e}")

        if not chunks:
            msg = f"No valid chunks found to embed out of {len(chunk_ids)} chunk IDs"
            raise ValueError(msg)

        # Group chunks by modality (different strategies per modality)
        chunks_by_modality: dict[str, list[ChunkReadModel]] = {}
        for chunk in chunks:
            # ChunkReadModel stores modality_type in metadata dict
            modality_key = chunk.metadata.get("modality_type")
            if not modality_key or not isinstance(modality_key, str):
                activity.logger.warning(f"Chunk {chunk.id} missing modality_type in metadata, skipping")
                continue
            if modality_key not in chunks_by_modality:
                chunks_by_modality[modality_key] = []
            chunks_by_modality[modality_key].append(chunk)

        embedding_ids = []
        total_dim = 0

        # Process each modality with its specific strategy
        for modality_key, modality_chunks in chunks_by_modality.items():
            activity.logger.info(f"Embedding {len(modality_chunks)} {modality_key} chunks")

            # Get EmbeddingStrategy entity for this modality
            from vdb_core.domain.value_objects import ModalityType

            modality_enum = ModalityType[modality_key.upper()]

            # VectorizationConfig has exactly ONE embedding strategy (can be multimodal)
            # Use the first (and only) embedding strategy
            embedding_strategy = vectorization_config.embedding_strategy

            if not embedding_strategy:
                activity.logger.warning(f"No embedding strategy for {modality_key}, skipping")
                continue

            # Resolve to implementation
            embedder_impl = strategy_resolver.get_embedder(embedding_strategy)

            # Check database for existing embeddings before calling API
            from sqlalchemy import text
            import json

            # Build map of chunk_id -> expected embedding_id
            chunk_to_embedding_id = {}
            for chunk in modality_chunks:
                chunk_id = ChunkId(chunk.id)
                embedding_id = EmbeddingId.from_chunk_and_strategy(chunk_id, embedding_strategy.id)
                chunk_to_embedding_id[chunk.id] = embedding_id.value

            # Query database for existing embeddings
            existing_query = text("""
                SELECT chunk_id, vector
                FROM embeddings
                WHERE chunk_id = ANY(:chunk_ids)
                  AND embedding_strategy_id = :strategy_id
            """)

            result = await uow.session.execute(
                existing_query,
                {
                    "chunk_ids": [chunk.id for chunk in modality_chunks],
                    "strategy_id": str(embedding_strategy.id),
                }
            )
            existing_rows = result.mappings().all()

            # Map chunk_id -> vector for existing embeddings
            existing_embeddings = {}
            for row in existing_rows:
                vector_data = row["vector"]
                if isinstance(vector_data, str):
                    vector = json.loads(vector_data)
                else:
                    vector = vector_data
                existing_embeddings[row["chunk_id"]] = vector

            activity.logger.info(
                f"Found {len(existing_embeddings)}/{len(modality_chunks)} existing embeddings in database"
            )

            # Separate chunks into existing (skip API) and new (call API)
            chunks_needing_embedding = []
            chunk_contents_needing_embedding = []

            for chunk in modality_chunks:
                if chunk.id not in existing_embeddings:
                    chunks_needing_embedding.append(chunk)
                    chunk_contents_needing_embedding.append(chunk.text)

            # Only call API for chunks without existing embeddings
            new_vectors = []
            if chunk_contents_needing_embedding:
                activity.logger.info(
                    f"Calling embedding API for {len(chunk_contents_needing_embedding)} new chunks"
                )
                # Use "search_document" for document indexing (not search queries)
                new_vectors = await embedder_impl.embed(
                    chunk_contents_needing_embedding,
                    input_type="search_document"
                )

            # Merge existing and new vectors in original order
            vectors = []
            new_vector_idx = 0
            for chunk in modality_chunks:
                if chunk.id in existing_embeddings:
                    vectors.append(existing_embeddings[chunk.id])
                else:
                    vectors.append(new_vectors[new_vector_idx])
                    new_vector_idx += 1

            # Create Embedding value objects and persist to database (only for new embeddings)
            for chunk, vector in zip(modality_chunks, vectors, strict=False):
                # ChunkReadModel has 'id' field (UUID string)
                # Create ChunkId from the chunk's UUID
                chunk_id = ChunkId(chunk.id)

                # Calculate embedding ID
                embedding_id = EmbeddingId.from_chunk_and_strategy(chunk_id, embedding_strategy.id)
                embedding_ids.append(embedding_id.value)
                total_dim += len(vector)

                # Skip persisting if this embedding already exists in database
                if chunk.id in existing_embeddings:
                    activity.logger.debug(f"Skipping persistence for existing embedding {embedding_id.value}")
                    continue

                embedding = Embedding(
                    chunk_id=chunk_id,
                    embedding_strategy_id=embedding_strategy.id,
                    vector=tuple(vector) if not isinstance(vector, tuple) else vector,
                    library_id=library.id,
                    vectorization_config_id=vectorization_config.id,
                )

                # Add embedding to library (deduplication happens here)
                stored_embedding = library.add_embedding(
                    embedding,
                    vector_indexing_strategy=vectorization_config.vector_indexing_strategy.value
                )

                # Persist new embedding to database
                await uow.session.execute(
                    text("""
                        INSERT INTO embeddings (
                            id, chunk_id, embedding_strategy_id, vectorization_config_id,
                            library_id, vector, dimensions
                        ) VALUES (
                            :id, :chunk_id, :embedding_strategy_id, :vectorization_config_id,
                            :library_id, :vector, :dimensions
                        )
                        ON CONFLICT (id) DO NOTHING
                    """),
                    {
                        "id": stored_embedding.embedding_id.value,
                        "chunk_id": chunk.id,  # Use chunk UUID directly
                        "embedding_strategy_id": str(embedding_strategy.id),
                        "vectorization_config_id": str(vectorization_config.id),
                        "library_id": str(library.id),
                        "vector": json.dumps(list(vector)),
                        "dimensions": len(vector),
                    },
                )

            num_reused = len(existing_embeddings)
            num_new = len(vectors) - num_reused
            activity.logger.info(
                f"Embeddings: {num_new} new (API call), {num_reused} reused (from DB) "
                f"using {embedding_strategy.model_key}"
            )

        await uow.commit()

        return {
            "embedding_ids": embedding_ids,
            "num_embeddings": len(embedding_ids),
            "avg_dimension": total_dim // len(embedding_ids) if embedding_ids else 0,
        }


@activity.defn(name="index_vectors")
async def index_vectors_activity(
    library_id: str,
    config_id: str,
    embedding_ids: list[str],
) -> int:
    """Index embeddings in search service via API call.

    This activity sends vectors to the search service for indexing in its in-memory index.

    Args:
        library_id: ID of the library
        config_id: ID of the VectorizationConfig
        embedding_ids: List of Embedding IDs to index

    Returns:
        Number of vectors indexed

    """
    import json
    import os

    from sqlalchemy import text

    from vdb_core.infrastructure.persistence.postgres_unit_of_work import PostgresUnitOfWork
    from vdb_core.infrastructure.search_client import SearchServiceClient

    activity.logger.info(f"Indexing {len(embedding_ids)} embeddings via search service API")

    container = get_di_container()
    uow = container.get_unit_of_work()

    async with uow:
        # Load VectorizationConfig from repository
        config_uuid = VectorizationConfigId(UUID(config_id))
        vectorization_config = await uow.vectorization_configs.get(config_uuid)  # type: ignore[attr-defined]

        if not vectorization_config:
            msg = f"VectorizationConfig {config_id} not found"
            raise ValueError(msg)

        # Load embeddings from database
        if not isinstance(uow, PostgresUnitOfWork):
            msg = "This activity requires PostgresUnitOfWork"
            raise TypeError(msg)

        query = text("""
            SELECT id, vector
            FROM embeddings
            WHERE id = ANY(:ids)
        """)

        if uow.session is None:
            msg = "PostgresUnitOfWork session is not initialized"
            raise RuntimeError(msg)

        result = await uow.session.execute(query, {"ids": embedding_ids})
        rows = result.mappings().all()

        if not rows:
            msg = f"No embeddings found in database for {len(embedding_ids)} embedding IDs"
            raise ValueError(msg)

        activity.logger.info(f"Loaded {len(rows)} embeddings from database for indexing")

        # Parse embeddings from database rows
        embeddings = []
        for row in rows:
            vector_data = row["vector"]
            # Parse JSON vector array
            if isinstance(vector_data, str):
                vector = json.loads(vector_data)
            else:
                vector = vector_data

            embeddings.append({
                "embedding_id": str(row["id"]),  # Convert UUID to string for JSON serialization
                "vector": vector,
            })

        if not embeddings:
            msg = "No valid embeddings found to index"
            raise ValueError(msg)

        # Call search service API to index vectors
        search_url = os.getenv("SEARCH_SERVICE_URL", "http://search:8001")

        async with SearchServiceClient(base_url=search_url, timeout=60.0) as search_client:
            result = await search_client.batch_index(
                library_id=library_id,
                config_id=config_id,
                embeddings=embeddings,
            )

        indexed_count = result.get("indexed_count", 0)
        failed_count = result.get("failed_count", 0)

        activity.logger.info(
            f"✅ Indexed {indexed_count} embeddings via search service (failed={failed_count})"
        )
        return indexed_count


def _deserialize_extracted_content(data: dict[str, Any]) -> ExtractedContent:
    """Deserialize ExtractedContent entity from dict (from database query).

    Note: We bypass the auto-generated id by creating entity directly.
    """
    from vdb_core.utils.dt_utils import utc_now

    # Create entity bypassing __init__
    ec = object.__new__(ExtractedContent)

    # Set all required fields directly
    object.__setattr__(ec, "id", UUID(data["id"]))
    object.__setattr__(ec, "document_id", UUID(data["document_id"]))
    object.__setattr__(ec, "document_fragment_id", UUID(data["document_fragment_id"]))
    object.__setattr__(ec, "content", data["content"])
    object.__setattr__(ec, "modality", ModalityType[data["modality"].upper()])
    object.__setattr__(ec, "modality_sequence_number", data["modality_sequence_number"])
    object.__setattr__(ec, "is_last_of_modality", data["is_last_of_modality"])
    object.__setattr__(ec, "metadata", data.get("metadata"))

    # Set default fields from IEntity
    object.__setattr__(ec, "status", ExtractedContentStatus.PENDING)
    object.__setattr__(ec, "created_at", utc_now())
    object.__setattr__(ec, "updated_at", utc_now())
    object.__setattr__(ec, "events", [])
    object.__setattr__(ec, "_allow_setattr", False)

    return ec


@activity.defn(name="mark_config_processing_completed")
async def mark_config_processing_completed_activity(
    document_id: str,
    config_id: str,
    status: str,
    error_message: str | None = None,
) -> None:
    """Mark document vectorization status as completed or failed for this config.

    Args:
        document_id: ID of the document
        config_id: ID of the VectorizationConfig
        status: Processing status ("completed" or "failed")
        error_message: Optional error message if status is "failed"

    """
    activity.logger.info(f"Marking config {config_id} processing as {status} for document {document_id}")

    container = get_di_container()
    status_repo = container.get_document_vectorization_status_repository()

    from vdb_core.domain.value_objects import DocumentId, VectorizationConfigId

    await status_repo.upsert(
        document_id=DocumentId(document_id),
        config_id=VectorizationConfigId(config_id),
        status=status,
        error_message=error_message,
    )

    activity.logger.info(f"✅ Marked config {config_id} as {status} for document {document_id}")


def _load_chunks_from_library(library: Any, chunk_ids: list[str]) -> list[Chunk]:
    """Load chunks from library cache OR database, filtering out missing ones.

    Note: Library may not have chunks in cache after database reconstitution.
    This is expected - chunks are lazy-loaded or accessed via read repositories.
    For now, we return empty list and log a message.
    """
    chunks = []
    for chunk_id_str in chunk_ids:
        chunk = library.get_chunk(ChunkId(chunk_id_str))
        if chunk:
            chunks.append(chunk)
        else:
            # Chunk not in library cache (library was reconstituted from DB)
            # This is expected - chunks need to be loaded separately
            logger.debug("Chunk %s not in library cache (library reconstituted from DB)", chunk_id_str)

    if not chunks and chunk_ids:
        logger.warning(
            "No chunks found in library cache for %d chunk IDs. "
            "This happens when library is loaded from DB without chunks. "
            "Chunks should be loaded via chunk read repository instead.",
            len(chunk_ids)
        )

    return chunks

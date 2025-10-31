"""Temporal activities for document ingestion pipeline.

Activities are the units of work that execute domain logic within Temporal workflows.
They call domain services and repositories to perform actual business operations.

These activities coordinate the document ingestion process:
- Detect modality
- Chunk documents
- Generate embeddings
- Index vectors
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from temporalio import activity

if TYPE_CHECKING:
    from vdb_core.infrastructure.di.containers import DIContainer

# Global DI container - will be set by worker on startup
_di_container: DIContainer | None = None


def set_di_container(container: DIContainer) -> None:
    """Set the global DI container for activities.

    This should be called by the worker when it starts up.

    Args:
        container: DI container instance

    """
    global _di_container
    _di_container = container


def get_di_container() -> DIContainer:
    """Get the global DI container.

    Returns:
        DI container instance

    Raises:
        RuntimeError: If container not initialized

    """
    if _di_container is None:
        msg = "DI container not initialized. Call set_di_container() first."
        raise RuntimeError(msg)
    return _di_container


@activity.defn(name="chunk_document")
async def chunk_document_activity(
    document_id: str,
    pipeline_id: str,
    modality: str,
) -> list[dict[str, str]]:
    """Chunk a document into smaller segments based on pipeline strategy.

    Args:
        document_id: ID of the document to chunk
        pipeline_id: ID of the pipeline (contains chunking strategy)
        modality: Modality type detected

    Returns:
        List of chunk dictionaries with IDs and metadata

    """
    activity.logger.info(f"Chunking document {document_id} with modality {modality}")

    # Get dependencies from DI container
    container = get_di_container()
    container.get_chunk_repository()

    # TODO(pierre): Implement actual chunking logic
    # For now, return empty list as placeholder
    # In production, this would:
    # 1. Load pipeline to get chunking strategy
    # 2. Load document content
    # 3. Apply chunking strategy based on modality
    # 4. Create Chunk entities
    # 5. Persist via chunk_repository

    activity.logger.warning("Chunking logic not yet implemented - returning empty chunks")

    return []


@activity.defn(name="generate_chunk_embeddings")
async def generate_chunk_embeddings_activity(
    chunks: list[dict[str, str]],
    pipeline_id: str,
) -> list[dict[str, str | list[float]]]:
    """Generate embeddings for all chunks.

    Args:
        chunks: List of chunk dictionaries
        pipeline_id: ID of the pipeline (contains embedding strategy)

    Returns:
        List of embedding dictionaries with vectors

    """
    activity.logger.info(f"Generating embeddings for {len(chunks)} chunks")

    # Get dependencies from DI container
    get_di_container()

    # TODO(pierre): Implement actual embedding generation
    # For now, return empty list as placeholder
    # In production, this would:
    # 1. Load pipeline to get embedding strategy
    # 2. For each chunk:
    #    a. Extract text content
    #    b. Generate embedding via embedding_service
    #    c. Create Embedding entity
    # 3. Can batch/parallelize for performance

    activity.logger.warning("Embedding generation not yet implemented - returning empty embeddings")

    return []


@activity.defn(name="index_embeddings")
async def index_embeddings_activity(
    embeddings: list[dict[str, str | list[float]]],
    library_id: str,
) -> int:
    """Index embeddings into vector database.

    Args:
        embeddings: List of embedding dictionaries with vectors
        library_id: ID of the library to index into

    Returns:
        Number of embeddings indexed

    """
    activity.logger.info(f"Indexing {len(embeddings)} embeddings for library {library_id}")

    # Get dependencies from DI container
    container = get_di_container()
    container.get_vector_repository()

    # TODO(pierre): Implement actual vector indexing
    # For now, return 0 as placeholder
    # In production, this would:
    # 1. Convert embedding dicts to Embedding entities
    # 2. Batch index via vector_repository.add_embeddings()
    # 3. Return count of indexed embeddings

    activity.logger.warning("Vector indexing not yet implemented - returning 0")

    return 0


@activity.defn(name="parse_all_fragments")
async def parse_all_fragments_activity(
    library_id: str,
    document_id: str,
) -> dict[str, list[str]]:
    """Parse all fragments into ExtractedContent.

    Args:
        library_id: UUID of the library
        document_id: UUID of the document

    Returns:
        Dict with:
            - extracted_content_ids: List of created ExtractedContent IDs

    """
    activity.logger.info(f"Parsing all fragments for document {document_id}")

    # Get dependencies from DI container
    container = get_di_container()

    # Create and execute ParseAllFragmentsCommand
    from vdb_core.application.commands.ingestion_commands import ParseAllFragmentsCommand
    from vdb_core.application.commands.inputs import ParseAllFragmentsInput

    command = ParseAllFragmentsCommand(
        uow_factory=container.get_unit_of_work,
        message_bus=container.get_message_bus(),
        parser=container.get_parser(),
    )

    result = await command.execute(
        ParseAllFragmentsInput(
            library_id=library_id,
            document_id=document_id,
        )
    )

    activity.logger.info(f"Parsed {len(result.extracted_content_ids)} ExtractedContent objects")

    return {
        "extracted_content_ids": result.extracted_content_ids,
    }


@activity.defn(name="get_library_configs")
async def get_library_configs_activity(
    library_id: str,
) -> list[dict[str, str]]:
    """Get all VectorizationConfigs associated with a library.

    Args:
        library_id: UUID of the library

    Returns:
        List of dicts with config_id

    """
    activity.logger.info(f"Loading configs for library {library_id}")

    # Get dependencies from DI container
    container = get_di_container()
    uow = container.get_unit_of_work()

    # Get library aggregate using LibraryId value object
    from vdb_core.domain.value_objects import LibraryId

    async with uow:
        library = await uow.libraries.get(LibraryId(library_id))

        # Get associated config entities and extract IDs
        configs = library.configs
        config_ids = [config.id for config in configs]

        activity.logger.info(f"Found {len(config_ids)} configs for library {library_id}")

        return [{"config_id": str(config_id)} for config_id in config_ids]


@activity.defn(name="mark_document_completed")
async def mark_document_completed_activity(
    library_id: str,
    document_id: str,
    error_message: str | None = None,
) -> None:
    """Mark document as COMPLETED or FAILED.

    Simple domain operation - no command needed.

    Args:
        library_id: UUID of the library
        document_id: UUID of the document
        error_message: Optional error message if marking as FAILED

    """
    from vdb_core.domain.value_objects import DocumentId, DocumentStatus, LibraryId

    status = DocumentStatus.FAILED if error_message else DocumentStatus.COMPLETED
    activity.logger.info(f"Marking document {document_id} as {status}")

    # Get dependencies from DI container
    container = get_di_container()
    uow = container.get_unit_of_work()

    # Simple domain operation: load entity, update status, commit
    async with uow:
        library = await uow.libraries.get(LibraryId(library_id))
        document = await library.get_document(DocumentId(document_id))
        document.update(status=status)
        await uow.commit()

    activity.logger.info(f"Document {document_id} marked as {status}")

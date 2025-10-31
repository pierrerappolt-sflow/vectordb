"""PostgreSQL implementation of Library repository using SQLAlchemy."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import text

from vdb_core.domain.entities import Library
from vdb_core.domain.entities.library import DocumentFragment
from vdb_core.domain.repositories import AbstractRepository
from vdb_core.domain.value_objects import (
    DocumentFragmentId,
    DocumentId,
    DocumentName,
    LibraryId,
    LibraryName,
)

from .postgres_mapper import to_datetime, to_uuid

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable

    from sqlalchemy.ext.asyncio import AsyncSession

    from vdb_core.domain.entities import Document
    from vdb_core.domain.events import DomainEvent


class PostgresLibraryRepository(AbstractRepository[Library, LibraryId]):
    """PostgreSQL implementation of Library repository using SQLAlchemy.

    Uses raw SQL queries with SQLAlchemy AsyncSession for database operations.

    Following patterns:
    - Extends AbstractRepository for automatic `self.seen` tracking
    - Implements private methods (_add, _get, _update) for storage operations
    - Uses SQLAlchemy AsyncSession for connection pooling
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with SQLAlchemy async session.

        Args:
            session: SQLAlchemy async session for database operations

        """
        super().__init__()
        self.session = session

    def _create_document_loader(
        self, library_id: LibraryId
    ) -> Callable[[DocumentId | None], AsyncIterator[Document]]:
        """Create a document loader function for lazy loading documents.

        Args:
            library_id: Library ID to load documents for

        Returns:
            Async generator function that yields documents

        """

        async def document_loader(document_id: DocumentId | None = None) -> AsyncIterator[Document]:
            """Load documents from database."""
            from vdb_core.domain.entities.library import Document

            if document_id:
                # Load specific document
                result = await self.session.execute(
                    text("""
                        SELECT id, library_id, name, status, upload_complete, created_at, updated_at
                        FROM documents
                        WHERE library_id = :library_id AND id = :document_id
                    """),
                    {"library_id": str(library_id), "document_id": str(document_id)},
                )
                row = result.mappings().one_or_none()
                if row:
                    # Create document and set all fields including internal ones
                    document = object.__new__(Document)
                    document_id_uuid = to_uuid(row["id"])
                    object.__setattr__(document, "id", document_id_uuid)
                    object.__setattr__(document, "library_id", to_uuid(row["library_id"]))
                    object.__setattr__(document, "name", row["name"])
                    object.__setattr__(document, "status", row["status"])
                    object.__setattr__(document, "upload_complete", row["upload_complete"])
                    object.__setattr__(document, "created_at", to_datetime(row["created_at"]))
                    object.__setattr__(document, "updated_at", to_datetime(row["updated_at"]))

                    # Initialize LazyCollection for fragments
                    from vdb_core.domain.base import LazyCollection

                    fragments_collection: LazyCollection[DocumentFragment, DocumentFragmentId] = LazyCollection()
                    fragments_collection.set_loader(
                        loader=self._create_fragment_loader(document_id_uuid),
                        get_id=lambda f: f.id,
                    )
                    object.__setattr__(document, "_fragments", fragments_collection)

                    object.__setattr__(document, "_extracted_contents", {})
                    object.__setattr__(document, "_chunks", {})
                    object.__setattr__(document, "_chunk_loader", None)
                    object.__setattr__(document, "events", [])
                    yield document
            else:
                # Load all documents for library
                result = await self.session.execute(
                    text("""
                        SELECT id, library_id, name, status, upload_complete, created_at, updated_at
                        FROM documents
                        WHERE library_id = :library_id
                        ORDER BY created_at
                    """),
                    {"library_id": str(library_id)},
                )
                rows = result.mappings().all()
                for row in rows:
                    # Create document and set all fields including internal ones
                    from vdb_core.domain.base import LazyCollection

                    document = object.__new__(Document)
                    document_id_uuid = to_uuid(row["id"])
                    object.__setattr__(document, "id", document_id_uuid)
                    object.__setattr__(document, "library_id", to_uuid(row["library_id"]))
                    object.__setattr__(document, "name", row["name"])
                    object.__setattr__(document, "status", row["status"])
                    object.__setattr__(document, "upload_complete", row["upload_complete"])
                    object.__setattr__(document, "created_at", to_datetime(row["created_at"]))
                    object.__setattr__(document, "updated_at", to_datetime(row["updated_at"]))

                    # Initialize LazyCollection for fragments
                    fragments_collection = LazyCollection()
                    fragments_collection.set_loader(
                        loader=self._create_fragment_loader(document_id_uuid),
                        get_id=lambda f: f.id,
                    )
                    object.__setattr__(document, "_fragments", fragments_collection)

                    object.__setattr__(document, "_extracted_contents", {})
                    object.__setattr__(document, "_chunks", {})
                    object.__setattr__(document, "_chunk_loader", None)
                    object.__setattr__(document, "events", [])
                    yield document

        return document_loader

    def _create_fragment_loader(self, document_id: DocumentId) -> Callable[[DocumentFragmentId | None], AsyncIterator[DocumentFragment]]:
        """Create a fragment loader function for lazy loading document fragments.

        Args:
            document_id: Document ID to load fragments for

        Returns:
            Async generator function that yields document fragments

        """

        async def fragment_loader(fragment_id: DocumentFragmentId | None = None) -> AsyncIterator[DocumentFragment]:
            """Load fragments from database for this document.

            Args:
                fragment_id: Optional fragment ID to load a specific fragment. If None, loads all fragments.

            """
            from vdb_core.domain.value_objects import ContentHash

            # Build query based on whether we're loading a specific fragment or all
            if fragment_id is not None:
                query = text("""
                    SELECT id, document_id, sequence_number, content, content_hash, is_final, created_at
                    FROM document_fragments
                    WHERE document_id = :document_id AND id = :fragment_id
                """)
                params = {"document_id": str(document_id), "fragment_id": str(fragment_id)}
            else:
                query = text("""
                    SELECT id, document_id, sequence_number, content, content_hash, is_final, created_at
                    FROM document_fragments
                    WHERE document_id = :document_id
                    ORDER BY sequence_number
                """)
                params = {"document_id": str(document_id)}

            fragments_result = await self.session.execute(query, params)

            fragment_rows = fragments_result.mappings().all()

            for frag_row in fragment_rows:
                fragment = object.__new__(DocumentFragment)
                object.__setattr__(fragment, "id", to_uuid(frag_row["id"]))
                object.__setattr__(fragment, "document_id", to_uuid(frag_row["document_id"]))
                object.__setattr__(fragment, "sequence_number", frag_row["sequence_number"])
                object.__setattr__(fragment, "content", frag_row["content"])
                object.__setattr__(fragment, "content_hash", ContentHash(value=frag_row["content_hash"]))
                object.__setattr__(fragment, "is_last_fragment", frag_row["is_final"])
                object.__setattr__(fragment, "created_at", to_datetime(frag_row["created_at"]))
                object.__setattr__(fragment, "events", [])  # Initialize events list
                yield fragment

        return fragment_loader

    async def _add(self, entity: Library) -> None:
        """Persist library to database.

        Args:
            entity: The library to add

        """
        await self.session.execute(
            text("""
                INSERT INTO libraries (id, name, status, created_at, updated_at)
                VALUES (:id, :name, :status, :created_at, :updated_at)
            """),
            {
                "id": str(entity.id),
                "name": entity.name.value,
                "status": entity.status,
                "created_at": entity.created_at,
                "updated_at": entity.updated_at,
            },
        )

        # Handle domain events (config associations during creation)
        await self._handle_events(entity)

        # Persist documents (Library is aggregate root, responsible for child entities)
        for document in entity._documents.values():
            await self.session.execute(
                text("""
                    INSERT INTO documents (id, library_id, name, status, upload_complete, created_at, updated_at)
                    VALUES (:id, :library_id, :name, :status, :upload_complete, :created_at, :updated_at)
                """),
                {
                    "id": str(document.id),
                    "library_id": str(entity.id),
                    "name": document.name,
                    "status": document.status,
                    "upload_complete": document.upload_complete,
                    "created_at": document.created_at,
                    "updated_at": document.updated_at,
                },
            )

            # Persist document fragments (only cached items, not lazy-loaded)
            for fragment in document._fragments.cached_items:
                await self.session.execute(
                    text("""
                        INSERT INTO document_fragments (id, document_id, sequence_number, content, content_hash, is_final, created_at)
                        VALUES (:id, :document_id, :sequence_number, :content, :content_hash, :is_final, :created_at)
                    """),
                    {
                        "id": str(fragment.id),
                        "document_id": str(document.id),
                        "sequence_number": fragment.sequence_number,
                        "content": fragment.content,
                        "content_hash": str(fragment.content_hash.value),
                        "is_final": fragment.is_last_fragment,
                        "created_at": fragment.created_at,
                    },
                )

    async def _get(self, id: LibraryId) -> Library:
        """Retrieve library from database.

        Args:
            id: The library ID

        Returns:
            The library entity

        Raises:
            LibraryNotFoundError: If library does not exist

        """
        from vdb_core.domain.exceptions import LibraryNotFoundError
        from vdb_core.domain.value_objects import VectorizationConfigId

        result = await self.session.execute(
            text("""
                SELECT id, name, status, created_at, updated_at
                FROM libraries
                WHERE id = :id
            """),
            {"id": str(id)},
        )
        row = result.mappings().one_or_none()

        if not row:
            raise LibraryNotFoundError(str(id))

        # Load associated config IDs and full configs from junction table + vectorization_configs
        config_result = await self.session.execute(
            text("""
                SELECT
                    vc.id,
                    vc.version,
                    vc.status,
                    vc.previous_version_id,
                    vc.description,
                    vc.chunking_strategy_ids,
                    vc.embedding_strategy_ids,
                    vc.vector_indexing_strategy,
                    vc.vector_similarity_metric,
                    vc.created_at,
                    vc.updated_at
                FROM library_vectorization_configs lvc
                JOIN vectorization_configs vc ON lvc.vectorization_config_id = vc.id
                WHERE lvc.library_id = :library_id
            """),
            {"library_id": str(id)},
        )
        config_rows = config_result.mappings().all()

        # Build config entities
        from vdb_core.domain.entities import VectorizationConfig
        from vdb_core.domain.value_objects import (
            ChunkingStrategyId,
            EmbeddingStrategyId,
        )

        configs = []
        for config_row in config_rows:
            config_id = VectorizationConfigId(to_uuid(config_row["id"]))

            # Create VectorizationConfig entity
            config = object.__new__(VectorizationConfig)
            object.__setattr__(config, "id", config_id)
            object.__setattr__(config, "version", config_row["version"])
            object.__setattr__(config, "status", config_row["status"])
            object.__setattr__(
                config,
                "previous_version_id",
                VectorizationConfigId(to_uuid(config_row["previous_version_id"]))
                if config_row["previous_version_id"]
                else None,
            )
            object.__setattr__(config, "description", config_row["description"])
            object.__setattr__(
                config,
                "chunking_strategy_ids",
                [ChunkingStrategyId(to_uuid(cid)) for cid in config_row["chunking_strategy_ids"]],
            )
            object.__setattr__(
                config,
                "embedding_strategy_ids",
                [EmbeddingStrategyId(to_uuid(eid)) for eid in config_row["embedding_strategy_ids"]],
            )
            object.__setattr__(
                config,
                "vector_indexing_strategy",
                config_row["vector_indexing_strategy"],
            )
            object.__setattr__(
                config,
                "vector_similarity_metric",
                config_row["vector_similarity_metric"],
            )
            object.__setattr__(config, "created_at", to_datetime(config_row["created_at"]))
            object.__setattr__(config, "updated_at", to_datetime(config_row["updated_at"]))
            object.__setattr__(config, "events", [])
            configs.append(config)

        # Map database row to domain entity
        library = Library.reconstitute(
            id=to_uuid(row["id"]),
            name=LibraryName(value=row["name"]),
            status=row["status"],
            created_at=to_datetime(row["created_at"]),
            updated_at=to_datetime(row["updated_at"]),
            configs=tuple(configs),
        )

        # Set up document loader for lazy loading
        object.__setattr__(library, "_document_loader", self._create_document_loader(library.id))

        return library

    async def _handle_events(self, entity: Library) -> None:
        """Handle domain events from library entity.

        Processes LibraryConfigAdded, LibraryConfigRemoved, DocumentDeleted, and ExtractedContentCreated events.

        Args:
            entity: The library entity with events to process

        """
        from vdb_core.domain.events.document_events import DocumentDeleted
        from vdb_core.domain.events.extracted_content_events import ExtractedContentCreated
        from vdb_core.domain.events.library_events import LibraryConfigAdded, LibraryConfigRemoved

        for event in entity.events:
            if isinstance(event, DocumentDeleted):
                # Delete document from database (CASCADE deletes fragments, chunks, embeddings)
                await self.session.execute(
                    text("""
                        DELETE FROM documents
                        WHERE id = :document_id
                    """),
                    {
                        "document_id": str(event.document_id),
                    },
                )
            elif isinstance(event, ExtractedContentCreated):
                # Persist extracted content to database
                # Load document to access extracted content
                document = await entity.get_document(event.document_id)
                extracted_content = document._extracted_contents.get(event.extracted_content_id)

                if extracted_content:
                    import json

                    from vdb_core.domain.value_objects import ContentHash

                    # Convert content to string if it's bytes
                    content_value = extracted_content.content
                    content_str: str
                    if isinstance(content_value, bytes):
                        content_str = content_value.decode("utf-8")
                    else:
                        content_str = content_value

                    # Compute content hash (like chunks do)
                    content_hash = ContentHash.from_content(content_str)

                    await self.session.execute(
                        text("""
                            INSERT INTO extracted_contents (
                                id, document_id, document_fragment_id, content, content_hash, modality_type,
                                modality_sequence_number, is_last_of_modality, status, metadata, created_at
                            ) VALUES (
                                :id, :document_id, :document_fragment_id, :content, :content_hash, :modality_type,
                                :modality_sequence_number, :is_last_of_modality, :status, CAST(:metadata AS jsonb), :created_at
                            )
                            ON CONFLICT (id) DO NOTHING
                        """),
                        {
                            "id": str(extracted_content.id),
                            "document_id": str(extracted_content.document_id),
                            "document_fragment_id": str(extracted_content.document_fragment_id),
                            "content": content_str,  # Use decoded string, not raw bytes
                            "content_hash": content_hash.value,
                            "modality_type": extracted_content.modality.value.upper(),
                            "modality_sequence_number": extracted_content.modality_sequence_number,
                            "is_last_of_modality": extracted_content.is_last_of_modality,
                            "status": extracted_content.status.value,
                            "metadata": json.dumps(extracted_content.metadata or {}),
                            "created_at": extracted_content.created_at,
                        },
                    )
            elif isinstance(event, LibraryConfigAdded):
                # Insert association into junction table (idempotent)
                await self.session.execute(
                    text(
                        """
                        INSERT INTO library_vectorization_configs (
                            library_id, vectorization_config_id, created_at, updated_at
                        ) VALUES (
                            :library_id, :config_id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                        )
                        ON CONFLICT (library_id, vectorization_config_id) DO NOTHING
                        """
                    ),
                    {
                        "library_id": str(event.library_id),
                        "config_id": str(event.config_id),
                    },
                )
            elif isinstance(event, LibraryConfigRemoved):
                # Remove association from junction table (if exists)
                await self.session.execute(
                    text(
                        """
                        DELETE FROM library_vectorization_configs
                        WHERE library_id = :library_id AND vectorization_config_id = :config_id
                        """
                    ),
                    {
                        "library_id": str(event.library_id),
                        "config_id": str(event.config_id),
                    },
                )

    async def _update(self, entity: Library) -> None:
        """Update library in database.

        Args:
            entity: The library to update

        Raises:
            ValueError: If library doesn't exist

        """
        result = await self.session.execute(
            text("""
                UPDATE libraries
                SET name = :name, status = :status, updated_at = :updated_at
                WHERE id = :id
            """),
            {
                "id": str(entity.id),
                "name": entity.name.value,
                "status": entity.status,
                "updated_at": entity.updated_at,
            },
        )

        # Check if any rows were updated
        if result.rowcount == 0:  # type: ignore[attr-defined]
            msg = f"Library {entity.id} not found"
            raise ValueError(msg)

        # Handle domain events (config associations, document deletions)
        await self._handle_events(entity)

        # Persist documents (Library is aggregate root, responsible for child entities)
        # Access private _documents dict directly since it's internal to the aggregate
        for document in entity._documents.values():
            # Upsert document (insert or update if exists)
            await self.session.execute(
                text("""
                    INSERT INTO documents (id, library_id, name, status, upload_complete, created_at, updated_at)
                    VALUES (:id, :library_id, :name, :status, :upload_complete, :created_at, :updated_at)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        status = EXCLUDED.status,
                        upload_complete = EXCLUDED.upload_complete,
                        updated_at = EXCLUDED.updated_at
                """),
                {
                    "id": str(document.id),
                    "library_id": str(entity.id),
                    "name": document.name,
                    "status": document.status,
                    "upload_complete": document.upload_complete,
                    "created_at": document.created_at,
                    "updated_at": document.updated_at,
                },
            )

            # Persist document fragments (only cached items, not lazy-loaded)
            for fragment in document._fragments.cached_items:
                await self.session.execute(
                    text("""
                        INSERT INTO document_fragments (id, document_id, sequence_number, content, content_hash, is_final, created_at)
                        VALUES (:id, :document_id, :sequence_number, :content, :content_hash, :is_final, :created_at)
                        ON CONFLICT (id) DO NOTHING
                    """),
                    {
                        "id": str(fragment.id),
                        "document_id": str(document.id),
                        "sequence_number": fragment.sequence_number,
                        "content": fragment.content,
                        "content_hash": str(fragment.content_hash.value),
                        "is_final": fragment.is_last_fragment,
                        "created_at": fragment.created_at,
                    },
                )

    async def _delete(self, id: LibraryId) -> None:
        """Hard delete a library by ID (removes from database).

        Args:
            id: The library ID

        Raises:
            ValueError: If library doesn't exist

        """
        result = await self.session.execute(
            text("""
                DELETE FROM libraries
                WHERE id = :id
            """),
            {"id": str(id)},
        )

        if result.rowcount == 0:  # type: ignore[attr-defined]
            msg = f"Library {id} not found"
            raise ValueError(msg)

    async def _soft_delete(self, entity: Library) -> None:
        """Soft delete a library (marks as DELETED).

        Args:
            entity: The library to soft delete

        Raises:
            ValueError: If library doesn't exist

        """
        # Update in database
        result = await self.session.execute(
            text("""
                UPDATE libraries
                SET status = :status, updated_at = :updated_at
                WHERE id = :id
            """),
            {
                "id": str(entity.id),
                "status": entity.status,
                "updated_at": entity.updated_at,
            },
        )

        if result.rowcount == 0:  # type: ignore[attr-defined]
            msg = f"Library {entity.id} not found"
            raise ValueError(msg)

    async def stream(
        self,
        skip: int = 0,
        limit: int | None = None,
    ) -> AsyncIterator[Library]:
        """Stream libraries for memory-efficient iteration.

        Args:
            skip: Number of entities to skip
            limit: Maximum number to yield

        Yields:
            Libraries one at a time

        """
        query = """
            SELECT id, name, status, created_at, updated_at
            FROM libraries
            ORDER BY created_at DESC
            OFFSET :skip
        """
        params = {"skip": skip}

        if limit is not None:
            query += " LIMIT :limit"
            params["limit"] = limit

        result = await self.session.execute(text(query), params)
        rows = result.mappings().all()

        for row in rows:
            # Load associated config IDs and full configs
            from vdb_core.domain.entities import VectorizationConfig
            from vdb_core.domain.value_objects import (
                ChunkingStrategyId,
                EmbeddingStrategyId,
                VectorizationConfigId,
            )

            config_result = await self.session.execute(
                text("""
                    SELECT
                        vc.id,
                        vc.version,
                        vc.status,
                        vc.previous_version_id,
                        vc.description,
                        vc.chunking_strategy_ids,
                        vc.embedding_strategy_ids,
                        vc.vector_indexing_strategy,
                        vc.vector_similarity_metric,
                        vc.created_at,
                        vc.updated_at
                    FROM library_vectorization_configs lvc
                    JOIN vectorization_configs vc ON lvc.vectorization_config_id = vc.id
                    WHERE lvc.library_id = :library_id
                """),
                {"library_id": str(row["id"])},
            )
            config_rows = config_result.mappings().all()

            configs = []
            for config_row in config_rows:
                config_id = VectorizationConfigId(to_uuid(config_row["id"]))

                # Create VectorizationConfig entity
                config = object.__new__(VectorizationConfig)
                object.__setattr__(config, "id", config_id)
                object.__setattr__(config, "version", config_row["version"])
                object.__setattr__(config, "status", config_row["status"])
                object.__setattr__(
                    config,
                    "previous_version_id",
                    VectorizationConfigId(to_uuid(config_row["previous_version_id"]))
                    if config_row["previous_version_id"]
                    else None,
                )
                object.__setattr__(config, "description", config_row["description"])
                object.__setattr__(
                    config,
                    "chunking_strategy_ids",
                    [ChunkingStrategyId(to_uuid(cid)) for cid in config_row["chunking_strategy_ids"]],
                )
                object.__setattr__(
                    config,
                    "embedding_strategy_ids",
                    [EmbeddingStrategyId(to_uuid(eid)) for eid in config_row["embedding_strategy_ids"]],
                )
                object.__setattr__(
                    config,
                    "vector_indexing_strategy",
                    config_row["vector_indexing_strategy"],
                )
                object.__setattr__(
                    config,
                    "vector_similarity_metric",
                    config_row["vector_similarity_metric"],
                )
                object.__setattr__(config, "created_at", config_row["created_at"])
                object.__setattr__(config, "updated_at", config_row["updated_at"])
                object.__setattr__(config, "events", [])
                configs.append(config)

            library = Library.reconstitute(
                id=to_uuid(row["id"]),
                name=LibraryName(value=row["name"]),
                status=row["status"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                configs=tuple(configs),
            )
            # Set up document loader for lazy loading
            object.__setattr__(library, "_document_loader", self._create_document_loader(library.id))
            yield library

    async def get_by_document_id(self, document_id: UUID) -> Library:
        """Get library that contains the specified document.

        Args:
            document_id: Document ID to search for

        Returns:
            Library containing the document

        Raises:
            ValueError: If no library contains this document

        """
        # Query to find library_id for a document
        query = """
            SELECT library_id
            FROM documents
            WHERE id = :document_id
        """

        result = await self.session.execute(text(query), {"document_id": str(document_id)})
        row = result.mappings().one_or_none()

        if not row:
            msg = f"No library found containing document {document_id}"
            raise ValueError(msg)

        library_id = LibraryId(str(row["library_id"]))
        return await self.get(library_id)

    def collect_events(self) -> list[DomainEvent]:
        """Collect domain events from all tracked entities.

        Returns:
            List of domain events from seen entities

        """
        events: list[DomainEvent] = []

        for entity in self.seen:
            if isinstance(entity, Library):
                events.extend(entity.events)
                entity.events.clear()

        return events

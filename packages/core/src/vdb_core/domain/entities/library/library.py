"""Library - an aggregate root collection of Documents and Pipelines."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, override
from uuid import uuid4

from vdb_core.domain.base import IEntity
from vdb_core.domain.events.document_events import DocumentCreated, DocumentDeleted, DocumentUpdated, DocumentFragmentReceived
from vdb_core.domain.events.library_events import LibraryCreated
from vdb_core.domain.events.extracted_content_events import ExtractedContentCreated
from vdb_core.domain.events.embedding_events import EmbeddingCreated
from vdb_core.domain.exceptions import DocumentNotFoundError
from vdb_core.domain.value_objects import (
    Chunk,
    ChunkId,
    ContentHash,
    DocumentId,
    DocumentName,
    Embedding,
    EmbeddingId,
    LibraryId,
    LibraryName,
    LibraryStatus,
    VectorizationConfigId,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable
    from datetime import datetime

    from vdb_core.domain.entities.extracted_content import ExtractedContent
    from vdb_core.domain.entities.vectorization_config import VectorizationConfig
    from vdb_core.domain.base import DomainEvent

    from .document import Document
    from .document_fragment import DocumentFragment


@dataclass(kw_only=True, eq=False)
class Library(IEntity):
    """Library aggregate root."""

    id: LibraryId = field(default_factory=uuid4, init=False)
    name: LibraryName
    status: LibraryStatus = field(default=LibraryStatus.ACTIVE, init=False)
    _configs: tuple[VectorizationConfig, ...] = field(default_factory=tuple, init=False, repr=False)
    _documents: dict[DocumentId, Document] = field(default_factory=dict, init=False, repr=False)
    _document_loader: Callable[[DocumentId | None], AsyncIterator[Document]] | None = field(
        default=None, init=False, repr=False
    )

    # Chunk and Embedding storage (deduplicated value objects)
    _chunks: dict[ChunkId, Chunk] = field(default_factory=dict, init=False, repr=False)
    _embeddings: dict[EmbeddingId, Embedding] = field(default_factory=dict, init=False, repr=False)

    # Track pending config associations/disassociations within the aggregate lifecycle
    _added_configs: set[VectorizationConfigId] = field(default_factory=set, init=False, repr=False)
    _removed_configs: set[VectorizationConfigId] = field(default_factory=set, init=False, repr=False)

    # Define which fields can be updated via update() method
    _mutable_fields: frozenset[str] = frozenset({"name", "status"})

    @override
    def __post_init__(self) -> None:
        self.events.append(LibraryCreated(library_id=self.id, name=self.name))
        IEntity.__post_init__(self)

    @classmethod
    def reconstitute(
        cls,
        *,
        id: LibraryId,
        name: LibraryName,
        status: LibraryStatus,
        created_at: datetime,
        updated_at: datetime,
        configs: tuple[VectorizationConfig, ...] | None = None,
    ) -> Library:
        library = object.__new__(cls)
        object.__setattr__(library, "id", id)
        object.__setattr__(library, "name", name)
        object.__setattr__(library, "status", status)
        object.__setattr__(library, "created_at", created_at)
        object.__setattr__(library, "updated_at", updated_at)
        object.__setattr__(library, "_configs", configs or tuple())
        object.__setattr__(library, "_documents", {})
        object.__setattr__(library, "_document_loader", None)
        object.__setattr__(library, "_chunks", {})
        object.__setattr__(library, "_embeddings", {})
        object.__setattr__(library, "_added_configs", set())
        object.__setattr__(library, "_removed_configs", set())
        object.__setattr__(library, "events", [])
        object.__setattr__(library, "_allow_setattr", False)
        return library

    @property
    def configs(self) -> tuple[VectorizationConfig, ...]:
        return self._configs

    @property
    def config_ids(self) -> tuple[str, ...]:
        return tuple(str(config.id) for config in self._configs)

    # Document management methods (Library is aggregate root for Documents)

    def add_document(self, name: DocumentName) -> Document:
        from .document import Document

        document = Document(library_id=self.id, name=name)
        self._documents[document.id] = document
        self.events.append(DocumentCreated(document_id=document.id, library_id=self.id, name=name))
        return document

    async def update_document(self, document_id: DocumentId, name: DocumentName) -> Document:
        document = await self.get_document(document_id)
        document.update(name=name)
        self.events.append(DocumentUpdated(document_id=document_id, library_id=self.id, name=name))
        return document

    async def remove_document(self, document_id: DocumentId) -> None:
        await self.get_document(document_id)
        del self._documents[document_id]
        self.events.append(DocumentDeleted(document_id=document_id, library_id=self.id))

    async def add_document_fragment(
        self,
        document_id: DocumentId,
        sequence_number: int,
        content: bytes,
        content_hash: ContentHash,
        is_final: bool = False,  # noqa: FBT002
    ) -> DocumentFragment:
        # using imported DocumentFragmentReceived
        from vdb_core.utils.dt_utils import utc_now

        from .document_fragment import DocumentFragment

        document = await self.get_document(document_id)
        fragment = DocumentFragment(
            document_id=document_id,
            sequence_number=sequence_number,
            content=content,
            content_hash=content_hash,
            is_last_fragment=is_final,
        )
        document._fragments.add_to_cache(fragment)

        if is_final:
            object.__setattr__(document, "upload_complete", True)
            from vdb_core.domain.value_objects.document.document_status import DocumentStatus
            object.__setattr__(document, "status", DocumentStatus.PROCESSING)

        object.__setattr__(document, "updated_at", utc_now())

        self.events.append(
            DocumentFragmentReceived(
                library_id=self.id,
                document_id=document_id,
                fragment_id=fragment.id,
                sequence_number=sequence_number,
                is_final=is_final,
            )
        )
        return fragment

    async def add_document_extracted_content(
        self,
        document_id: DocumentId,
        extracted_content: ExtractedContent,
    ) -> None:
        # using imported ExtractedContentCreated
        from vdb_core.utils.dt_utils import utc_now

        document = await self.get_document(document_id)
        document._extracted_contents[extracted_content.id] = extracted_content
        object.__setattr__(document, "updated_at", utc_now())

        self.events.append(
            ExtractedContentCreated(
                library_id=self.id,
                document_id=document_id,
                document_fragment_id=extracted_content.document_fragment_id,
                extracted_content_id=extracted_content.id,
                modality=extracted_content.modality,
                modality_sequence_number=extracted_content.modality_sequence_number,
                is_last_of_modality=extracted_content.is_last_of_modality,
            )
        )

    async def get_document(self, document_id: DocumentId) -> Document:
        if document_id in self._documents:
            return self._documents[document_id]
        if not self._document_loader:
            msg = "No document loader configured for this library"
            raise RuntimeError(msg)
        async for document in self._document_loader(document_id):
            self._documents[document.id] = document
            if document.id == document_id:
                return document
        raise DocumentNotFoundError(str(document_id))

    async def get_documents(self) -> AsyncIterator[Document]:
        for document in self._documents.values():
            yield document
        if not self._document_loader:
            msg = "No document loader configured for this library"
            raise RuntimeError(msg)
        async for document in self._document_loader(None):
            if document.id not in self._documents:
                self._documents[document.id] = document
                yield document

    def collect_all_events(self) -> list[DomainEvent]:
        from vdb_core.utils.dt_utils import utc_now

        all_events: list[DomainEvent] = []
        has_child_events = False
        all_events.extend(self.events)
        self.events.clear()
        for document in self._documents.values():
            if document.events:
                has_child_events = True
                all_events.extend(document.events)
                document.events.clear()
            for fragment in document.fragments:
                if fragment.events:
                    has_child_events = True
                    all_events.extend(fragment.events)
                    fragment.events.clear()
        if has_child_events:
            object.__setattr__(self, "updated_at", utc_now())
        return all_events

    # Vectorization config association management

    def add_config(self, config_id: VectorizationConfigId) -> None:
        """Associate a vectorization config with this library.

        Emits LibraryConfigAdded event and tracks pending association.
        """
        # Avoid duplicate if already associated
        if any(str(cfg.id) == str(config_id) for cfg in self._configs):
            return
        if config_id in self._added_configs:
            return
        from vdb_core.domain.events.library_events import LibraryConfigAdded

        self._added_configs.add(config_id)
        self.events.append(LibraryConfigAdded(library_id=self.id, config_id=config_id))

    def remove_config(self, config_id: VectorizationConfigId) -> None:
        """Disassociate a vectorization config from this library.

        Emits LibraryConfigRemoved event and tracks pending removal.
        """
        if config_id in self._removed_configs:
            return
        from vdb_core.domain.events.library_events import LibraryConfigRemoved

        self._removed_configs.add(config_id)
        self.events.append(LibraryConfigRemoved(library_id=self.id, config_id=config_id))

    # Chunk and Embedding management (deduplicated value objects)

    def add_chunk(self, chunk: Chunk) -> Chunk:

        chunk_id = chunk.chunk_id
        if chunk_id in self._chunks:
            return self._chunks[chunk_id]
        self._chunks[chunk_id] = chunk
        return chunk

    def get_chunk(self, chunk_id: ChunkId) -> Chunk | None:
        return self._chunks.get(chunk_id)

    def add_embedding(self, embedding: Embedding, vector_indexing_strategy: str) -> Embedding:
        # using imported EmbeddingCreated

        embedding_id = embedding.embedding_id
        if embedding_id in self._embeddings:
            return self._embeddings[embedding_id]
        self._embeddings[embedding_id] = embedding
        self.events.append(
            EmbeddingCreated(
                embedding_id=embedding_id,
                chunk_id=embedding.chunk_id,
                library_id=embedding.library_id,
                embedding_strategy_id=embedding.embedding_strategy_id,
                vector=embedding.vector,
                dimensions=embedding.dimensions,
                vector_indexing_strategy=vector_indexing_strategy,
            )
        )
        return embedding

    def get_embedding(self, embedding_id: EmbeddingId) -> Embedding | None:
        return self._embeddings.get(embedding_id)

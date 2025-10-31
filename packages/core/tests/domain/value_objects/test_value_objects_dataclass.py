from __future__ import annotations

from uuid import uuid4

import pytest

from vdb_core.domain.exceptions import ValidationException
from vdb_core.domain.value_objects import (
    Chunk,
    ChunkId,
    ContentHash,
    Embedding,
    EmbeddingId,
    ModalityType,
    ModalityType,
)
from vdb_core.domain.value_objects.strategy import EmbeddingStrategyId
from vdb_core.domain.value_objects.library import LibraryId
from vdb_core.domain.value_objects.document import DocumentFragmentId


def test_chunk_text_validation_and_id():
    library_id: LibraryId = uuid4()

    chunk = Chunk(
        library_id=library_id,
        modality=ModalityType.TEXT,
        content="Hello world",
        chunking_strategy_id=None,  # type: ignore[arg-type]
        content_hash=ContentHash.from_content("Hello world"),
    )

    assert isinstance(chunk.chunk_id, ChunkId)
    same = Chunk(
        library_id=library_id,
        modality=ModalityType.TEXT,
        content="Hello world",
        chunking_strategy_id=None,  # type: ignore[arg-type]
        content_hash=ContentHash.from_content("Hello world"),
    )
    assert chunk == same
    assert chunk.chunk_id == same.chunk_id


def test_chunk_binary_validation():
    library_id: LibraryId = uuid4()

    with pytest.raises(TypeError):
        Chunk(
            library_id=library_id,
            modality=ModalityType(ModalityType.IMAGE),
            content="not-bytes",  # type: ignore[arg-type]
            chunking_strategy_id=None,  # type: ignore[arg-type]
            content_hash=ContentHash.from_content("x"),
        )

    img = Chunk(
        library_id=library_id,
        modality=ModalityType(ModalityType.IMAGE),
        content=b"\xff\xd8\xff\xdb",
        chunking_strategy_id=None,  # type: ignore[arg-type]
        content_hash=ContentHash.from_bytes(b"\xff\xd8\xff\xdb"),
    )
    assert isinstance(img.binary_content, bytes)


def test_embedding_validation_properties():
    library_id: LibraryId = uuid4()
    strategy_id: EmbeddingStrategyId = EmbeddingStrategyId(uuid4())

    chunk = Chunk(
        library_id=library_id,
        modality=ModalityType.TEXT,
        content="abc",
        chunking_strategy_id=None,  # type: ignore[arg-type]
        content_hash=ContentHash.from_content("abc"),
    )

    with pytest.raises(ValidationException):
        Embedding(
            chunk_id=chunk.chunk_id,
            embedding_strategy_id=strategy_id,
            vector=tuple(),
            library_id=library_id,
            vectorization_config_id=None,  # type: ignore[arg-type]
        )

    emb = Embedding(
        chunk_id=chunk.chunk_id,
        embedding_strategy_id=strategy_id,
        vector=(0.1, 0.2, 0.3),
        library_id=library_id,
        vectorization_config_id=None,  # type: ignore[arg-type]
    )
    assert emb.dimensions == 3
    assert isinstance(emb.embedding_id, EmbeddingId)


def test_extracted_content_validation():
    frag_id: DocumentFragmentId = uuid4()

    from vdb_core.domain.value_objects.document import ExtractedContent

    with pytest.raises(TypeError):
        ExtractedContent(  # type: ignore[call-arg]
            content="not-bytes",
            modality=ModalityType.TEXT,
            source_fragments=[(frag_id, 0, 10)],
            document_offset_start=0,
            document_offset_end=10,
        )



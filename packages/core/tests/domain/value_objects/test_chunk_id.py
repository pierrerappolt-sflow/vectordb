from __future__ import annotations

from uuid import uuid4

from vdb_core.domain.value_objects.chunk import ChunkId


def test_chunk_id_same_library_same_content_same_id():
    lib = uuid4()
    a = ChunkId.from_content(library_id=lib, content="hello")
    b = ChunkId.from_content(library_id=lib, content="hello")
    assert a.value == b.value


def test_chunk_id_different_libraries_different_id():
    lib_a = uuid4()
    lib_b = uuid4()
    a = ChunkId.from_content(library_id=lib_a, content="hello")
    b = ChunkId.from_content(library_id=lib_b, content="hello")
    assert a.value != b.value


def test_chunk_id_bytes_and_str_equivalence():
    lib = uuid4()
    a = ChunkId.from_content(library_id=lib, content="héllö")
    b = ChunkId.from_content(library_id=lib, content="héllö".encode("utf-8"))
    assert a.value == b.value

"""Tests for ChunkId value object."""

from uuid import UUID, uuid4

from vdb_core.domain.value_objects import ChunkId
from vdb_core.domain.value_objects.library import LibraryId
from vdb_core.domain.value_objects.strategy import ChunkingStrategyId


class TestChunkId:
    """Tests for ChunkId value object."""

    def test_chunk_id_creation(self) -> None:
        """Test creating a ChunkId from content."""
        library_id: LibraryId = uuid4()
        document_id: UUID = uuid4()
        strategy_id = ChunkingStrategyId(uuid4())
        chunk_id = ChunkId.from_content(
            library_id=library_id,
            document_id=document_id,
            chunking_strategy_id=strategy_id,
            content="Sample chunk text",
        )

        assert isinstance(chunk_id, ChunkId)
        assert isinstance(chunk_id.value, str)
        assert len(chunk_id.value) == 36  # UUID string length (includes hyphens)

    def test_chunk_id_deterministic(self) -> None:
        """Test that ChunkId generation is deterministic."""
        library_id: LibraryId = uuid4()
        document_id: UUID = uuid4()
        strategy_id = ChunkingStrategyId(uuid4())
        content = "Sample chunk text"

        chunk_id1 = ChunkId.from_content(
            library_id=library_id,
            document_id=document_id,
            chunking_strategy_id=strategy_id,
            content=content,
        )
        chunk_id2 = ChunkId.from_content(
            library_id=library_id,
            document_id=document_id,
            chunking_strategy_id=strategy_id,
            content=content,
        )

        assert chunk_id1 == chunk_id2
        assert chunk_id1.value == chunk_id2.value

    def test_chunk_id_different_content(self) -> None:
        """Test that different content produces different chunk IDs."""
        library_id: LibraryId = uuid4()
        document_id: UUID = uuid4()
        strategy_id = ChunkingStrategyId(uuid4())

        chunk_id1 = ChunkId.from_content(
            library_id=library_id,
            document_id=document_id,
            chunking_strategy_id=strategy_id,
            content="Content A",
        )
        chunk_id2 = ChunkId.from_content(
            library_id=library_id,
            document_id=document_id,
            chunking_strategy_id=strategy_id,
            content="Content B",
        )

        assert chunk_id1 != chunk_id2
        assert chunk_id1.value != chunk_id2.value

    def test_chunk_id_different_library(self) -> None:
        """Test that same content in different libraries produces different chunk IDs."""
        library_id1: LibraryId = uuid4()
        library_id2: LibraryId = uuid4()
        document_id: UUID = uuid4()
        strategy_id = ChunkingStrategyId(uuid4())
        content = "Same content"

        chunk_id1 = ChunkId.from_content(
            library_id=library_id1,
            document_id=document_id,
            chunking_strategy_id=strategy_id,
            content=content,
        )
        chunk_id2 = ChunkId.from_content(
            library_id=library_id2,
            document_id=document_id,
            chunking_strategy_id=strategy_id,
            content=content,
        )

        assert chunk_id1 != chunk_id2
        assert chunk_id1.value != chunk_id2.value

    def test_chunk_id_different_document(self) -> None:
        """Test that same content in different documents produces different chunk IDs."""
        library_id: LibraryId = uuid4()
        document_id1: UUID = uuid4()
        document_id2: UUID = uuid4()
        strategy_id = ChunkingStrategyId(uuid4())
        content = "Same content"

        chunk_id1 = ChunkId.from_content(
            library_id=library_id,
            document_id=document_id1,
            chunking_strategy_id=strategy_id,
            content=content,
        )
        chunk_id2 = ChunkId.from_content(
            library_id=library_id,
            document_id=document_id2,
            chunking_strategy_id=strategy_id,
            content=content,
        )

        assert chunk_id1 != chunk_id2
        assert chunk_id1.value != chunk_id2.value

    def test_chunk_id_different_strategy(self) -> None:
        """Test that same content with different strategies produces different chunk IDs."""
        library_id: LibraryId = uuid4()
        document_id: UUID = uuid4()
        strategy_id1 = ChunkingStrategyId(uuid4())
        strategy_id2 = ChunkingStrategyId(uuid4())
        content = "Same content"

        chunk_id1 = ChunkId.from_content(
            library_id=library_id,
            document_id=document_id,
            chunking_strategy_id=strategy_id1,
            content=content,
        )
        chunk_id2 = ChunkId.from_content(
            library_id=library_id,
            document_id=document_id,
            chunking_strategy_id=strategy_id2,
            content=content,
        )

        assert chunk_id1 != chunk_id2
        assert chunk_id1.value != chunk_id2.value

    def test_chunk_id_bytes_content(self) -> None:
        """Test that ChunkId works with bytes content."""
        library_id: LibraryId = uuid4()
        document_id: UUID = uuid4()
        strategy_id = ChunkingStrategyId(uuid4())
        content_bytes = b"Sample chunk bytes"

        chunk_id1 = ChunkId.from_content(
            library_id=library_id,
            document_id=document_id,
            chunking_strategy_id=strategy_id,
            content=content_bytes,
        )
        chunk_id2 = ChunkId.from_content(
            library_id=library_id,
            document_id=document_id,
            chunking_strategy_id=strategy_id,
            content="Sample chunk bytes",
        )

        # Same content as string or bytes should produce same ID
        assert chunk_id1 == chunk_id2
        assert chunk_id1.value == chunk_id2.value

    def test_chunk_id_equality(self) -> None:
        """Test ChunkId equality comparison."""
        library_id: LibraryId = uuid4()
        document_id: UUID = uuid4()
        strategy_id = ChunkingStrategyId(uuid4())
        content = "Test content"

        chunk_id1 = ChunkId.from_content(
            library_id=library_id,
            document_id=document_id,
            chunking_strategy_id=strategy_id,
            content=content,
        )
        chunk_id2 = ChunkId.from_content(
            library_id=library_id,
            document_id=document_id,
            chunking_strategy_id=strategy_id,
            content=content,
        )

        assert chunk_id1 == chunk_id2
        assert hash(chunk_id1) == hash(chunk_id2)

    def test_chunk_id_immutability(self) -> None:
        """Test that ChunkId is immutable (frozen dataclass)."""
        library_id: LibraryId = uuid4()
        document_id: UUID = uuid4()
        strategy_id = ChunkingStrategyId(uuid4())
        chunk_id = ChunkId.from_content(
            library_id=library_id,
            document_id=document_id,
            chunking_strategy_id=strategy_id,
            content="Test",
        )

        # Should raise error when trying to modify frozen dataclass
        try:
            chunk_id.value = "new_value"  # type: ignore[misc]
            assert False, "Should have raised FrozenInstanceError"
        except Exception:
            pass  # Expected

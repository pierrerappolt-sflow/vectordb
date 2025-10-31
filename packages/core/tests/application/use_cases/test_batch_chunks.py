"""Standalone tests for UploadDocumentCommand._batch_chunks method."""

from collections.abc import AsyncIterator

import pytest
from vdb_core.application.commands import UploadDocumentCommand
from vdb_core.domain.value_objects import MAX_FRAGMENT_SIZE_BYTES


async def async_chunk_generator(chunks: list[bytes]) -> AsyncIterator[bytes]:
    """Helper to create async chunk iterator."""
    for chunk in chunks:
        yield chunk


@pytest.mark.asyncio
class TestBatchChunks:
    """Standalone tests for the _batch_chunks method without infrastructure dependencies."""

    async def test_batch_chunks_combines_small_chunks(self) -> None:
        """Test that small chunks are combined into larger batches."""
        # Create a minimal command instance (we only need _batch_chunks method)
        command = object.__new__(UploadDocumentCommand)

        # Input: two chunks that fit within 1 MB when combined
        chunks = [b"a" * 500_000, b"b" * 400_000]

        # Act
        batches = []
        async for batch in command._batch_chunks(async_chunk_generator(chunks)):
            batches.append(batch)

        # Assert: should be combined into one batch
        assert len(batches) == 1
        assert len(batches[0]) == 900_000
        assert batches[0] == b"a" * 500_000 + b"b" * 400_000

    async def test_batch_chunks_splits_oversized_chunks(self) -> None:
        """Test that oversized chunks are split at MAX_FRAGMENT_SIZE_BYTES boundaries."""
        command = object.__new__(UploadDocumentCommand)

        # Input: two chunks that exceed MAX_FRAGMENT_SIZE_BYTES when combined
        # 60MB + 60MB = 120MB total (exceeds 100MB limit)
        chunk_size = 60 * 1024 * 1024  # 60 MB
        chunks = [b"x" * chunk_size, b"y" * chunk_size]

        # Act
        batches = []
        async for batch in command._batch_chunks(async_chunk_generator(chunks)):
            batches.append(batch)

        # Assert: should be split into two batches
        assert len(batches) == 2

        # First batch: exactly MAX_FRAGMENT_SIZE_BYTES (all of first chunk + part of second)
        assert len(batches[0]) == MAX_FRAGMENT_SIZE_BYTES
        assert batches[0][:chunk_size] == b"x" * chunk_size

        # Second batch: remaining bytes
        remaining = (chunk_size * 2) - MAX_FRAGMENT_SIZE_BYTES
        assert len(batches[1]) == remaining

    async def test_batch_chunks_handles_exact_boundary(self) -> None:
        """Test that exactly 1 MB chunk is yielded as-is."""
        command = object.__new__(UploadDocumentCommand)

        chunks = [b"z" * MAX_FRAGMENT_SIZE_BYTES]

        # Act
        batches = []
        async for batch in command._batch_chunks(async_chunk_generator(chunks)):
            batches.append(batch)

        # Assert: single batch of exactly 1 MB
        assert len(batches) == 1
        assert len(batches[0]) == MAX_FRAGMENT_SIZE_BYTES

    async def test_batch_chunks_handles_just_over_boundary(self) -> None:
        """Test that 1 MB + 1 byte is split into two batches."""
        command = object.__new__(UploadDocumentCommand)

        chunks = [b"m" * (MAX_FRAGMENT_SIZE_BYTES + 1)]

        # Act
        batches = []
        async for batch in command._batch_chunks(async_chunk_generator(chunks)):
            batches.append(batch)

        # Assert: two batches (1 MB + 1 byte)
        assert len(batches) == 2
        assert len(batches[0]) == MAX_FRAGMENT_SIZE_BYTES
        assert len(batches[1]) == 1

    async def test_batch_chunks_handles_multiple_max_size_chunks(self) -> None:
        """Test that multiple 1 MB chunks are yielded separately."""
        command = object.__new__(UploadDocumentCommand)

        chunks = [
            b"a" * MAX_FRAGMENT_SIZE_BYTES,
            b"b" * MAX_FRAGMENT_SIZE_BYTES,
            b"c" * MAX_FRAGMENT_SIZE_BYTES,
        ]

        # Act
        batches = []
        async for batch in command._batch_chunks(async_chunk_generator(chunks)):
            batches.append(batch)

        # Assert: three separate batches
        assert len(batches) == 3
        assert all(len(batch) == MAX_FRAGMENT_SIZE_BYTES for batch in batches)

    async def test_batch_chunks_handles_empty_stream(self) -> None:
        """Test that empty stream yields no batches."""
        command = object.__new__(UploadDocumentCommand)

        chunks: list[bytes] = []

        # Act
        batches = []
        async for batch in command._batch_chunks(async_chunk_generator(chunks)):
            batches.append(batch)

        # Assert: no batches
        assert len(batches) == 0

    async def test_batch_chunks_handles_many_small_chunks(self) -> None:
        """Test batching many small chunks together."""
        command = object.__new__(UploadDocumentCommand)

        # 100 chunks of 10KB each = 1MB total
        chunks = [b"x" * 10_000 for _ in range(100)]

        # Act
        batches = []
        async for batch in command._batch_chunks(async_chunk_generator(chunks)):
            batches.append(batch)

        # Assert: combined into one batch
        assert len(batches) == 1
        assert len(batches[0]) == 1_000_000

    async def test_batch_chunks_preserves_content_order(self) -> None:
        """Test that content is preserved in correct order across batches."""
        command = object.__new__(UploadDocumentCommand)

        # Create distinct chunks that will be split
        chunks = [
            b"A" * 700_000,
            b"B" * 700_000,
        ]

        # Act
        batches = []
        async for batch in command._batch_chunks(async_chunk_generator(chunks)):
            batches.append(batch)

        # Reconstruct full content
        full_content = b"".join(batches)

        # Assert: content matches original order
        expected = b"A" * 700_000 + b"B" * 700_000
        assert full_content == expected

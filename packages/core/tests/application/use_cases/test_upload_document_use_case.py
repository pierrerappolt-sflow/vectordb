"""Tests for UploadDocumentCommand."""

from collections.abc import AsyncIterator

import pytest
from vdb_core.application.commands import (
    CreateDocumentCommand,
    CreateDocumentFragmentCommand,
    UploadDocumentCommand,
    UploadDocumentInput,
)
from vdb_core.domain.entities import Library
from vdb_core.domain.events import DocumentCreated, DocumentFragmentReceived
from vdb_core.domain.exceptions import LibraryNotFoundError
from vdb_core.domain.value_objects import MAX_FRAGMENT_SIZE_BYTES, LibraryName
from vdb_core.infrastructure.message_bus import InMemoryMessageBus
from vdb_core.infrastructure.persistence import InMemoryUnitOfWork


async def async_chunk_generator(chunks: list[bytes]) -> AsyncIterator[bytes]:
    """Helper to create async chunk iterator."""
    for chunk in chunks:
        yield chunk


@pytest.mark.asyncio
class TestUploadDocumentCommand:
    """Tests for UploadDocumentCommand."""

    async def test_upload_document_creates_document_and_fragments(self) -> None:
        """Test uploading a document creates document and fragments."""
        # Arrange
        uow = InMemoryUnitOfWork()
        message_bus = InMemoryMessageBus()

        # Create the sub-commands
        create_doc_cmd = CreateDocumentCommand(uow_factory=lambda: uow, message_bus=message_bus)
        create_frag_cmd = CreateDocumentFragmentCommand(
            uow_factory=lambda: uow, message_bus=message_bus
        )
        command = UploadDocumentCommand(
            create_document_command=create_doc_cmd,
            create_fragment_command=create_frag_cmd,
        )

        # Create library first
        library = Library(name=LibraryName(value="Test Library"))
        async with uow:
            await uow.libraries.add(library)
            await uow.commit()

        # Use small chunks that will be batched together (well under 100MB limit)
        chunks = [b"chunk1", b"chunk2", b"chunk3"]

        # Act
        input_data = UploadDocumentInput(
            library_id=str(library.id),
            filename="test.txt",
        )
        document_id = await command.execute(
            input_data=input_data,
            chunks=async_chunk_generator(chunks),
        )

        # Assert
        assert document_id is not None

        # Verify document was created
        async with uow:
            lib = await uow.libraries.get(library.id)
            document = await lib.get_document(document_id)
            assert document is not None
            assert document.name.value == "test.txt"
            assert document.upload_complete is True  # Final fragment marks upload complete

        # Verify events were published
        event_types = [type(event) for event in message_bus.handled_events]
        assert DocumentCreated in event_types

        # Small chunks get batched into 1 fragment
        fragment_events = [
            e for e in message_bus.handled_events if isinstance(e, DocumentFragmentReceived)
        ]
        assert len(fragment_events) == 1
        assert fragment_events[0].is_final is True

    async def test_upload_document_with_library_not_found(self) -> None:
        """Test uploading document to non-existent library raises error."""
        # Arrange
        uow = InMemoryUnitOfWork()
        message_bus = InMemoryMessageBus()

        create_doc_cmd = CreateDocumentCommand(uow_factory=lambda: uow, message_bus=message_bus)
        create_frag_cmd = CreateDocumentFragmentCommand(
            uow_factory=lambda: uow, message_bus=message_bus
        )
        command = UploadDocumentCommand(
            create_document_command=create_doc_cmd,
            create_fragment_command=create_frag_cmd,
        )

        chunks = [b"chunk1"]

        # Act & Assert
        input_data = UploadDocumentInput(
            library_id="00000000-0000-0000-0000-000000000000",
            filename="test.txt",
        )

        with pytest.raises(LibraryNotFoundError):
            await command.execute(
                input_data=input_data,
                chunks=async_chunk_generator(chunks),
            )

    async def test_batch_chunks_combines_small_chunks_into_fragments(self) -> None:
        """Test that small chunks are batched together into <= 1 MB fragments."""
        # Arrange
        uow = InMemoryUnitOfWork()
        message_bus = InMemoryMessageBus()

        create_doc_cmd = CreateDocumentCommand(uow_factory=lambda: uow, message_bus=message_bus)
        create_frag_cmd = CreateDocumentFragmentCommand(
            uow_factory=lambda: uow, message_bus=message_bus
        )
        command = UploadDocumentCommand(
            create_document_command=create_doc_cmd,
            create_fragment_command=create_frag_cmd,
        )

        library = Library(name=LibraryName(value="Test Library"))
        async with uow:
            await uow.libraries.add(library)
            await uow.commit()

        # Create chunks that should be batched: 500KB + 400KB = 900KB (fits in one fragment)
        chunks = [
            b"x" * 500_000,  # 500 KB
            b"y" * 400_000,  # 400 KB
        ]

        # Act
        input_data = UploadDocumentInput(
            library_id=str(library.id),
            filename="test.txt",
        )
        document_id = await command.execute(
            input_data=input_data,
            chunks=async_chunk_generator(chunks),
        )

        # Assert
        async with uow:
            lib = await uow.libraries.get(library.id)
            document = await lib.get_document(document_id)
            fragments = document.fragments

            # Should have 1 fragment containing both chunks batched together
            assert len(fragments) == 1

            # Fragment should contain both chunks batched together and be marked as final
            assert fragments[0].size_bytes == 900_000
            assert fragments[0].content == b"x" * 500_000 + b"y" * 400_000
            assert fragments[0].is_last_fragment is True

    async def test_batch_chunks_splits_large_stream_into_multiple_fragments(self) -> None:
        """Test that large stream is split into multiple <= 1 MB fragments."""
        # Arrange
        uow = InMemoryUnitOfWork()
        message_bus = InMemoryMessageBus()

        create_doc_cmd = CreateDocumentCommand(uow_factory=lambda: uow, message_bus=message_bus)
        create_frag_cmd = CreateDocumentFragmentCommand(
            uow_factory=lambda: uow, message_bus=message_bus
        )
        command = UploadDocumentCommand(
            create_document_command=create_doc_cmd,
            create_fragment_command=create_frag_cmd,
        )

        library = Library(name=LibraryName(value="Test Library"))
        async with uow:
            await uow.libraries.add(library)
            await uow.commit()

        # Create chunks that exceed MAX_FRAGMENT_SIZE_BYTES (100MB) when combined
        # 60MB + 60MB = 120MB total
        chunk_size = 60 * 1024 * 1024  # 60 MB
        chunks = [
            b"a" * chunk_size,
            b"b" * chunk_size,
        ]

        # Act
        input_data = UploadDocumentInput(
            library_id=str(library.id),
            filename="test.txt",
        )
        document_id = await command.execute(
            input_data=input_data,
            chunks=async_chunk_generator(chunks),
        )

        # Assert
        async with uow:
            lib = await uow.libraries.get(library.id)
            document = await lib.get_document(document_id)
            fragments = document.fragments

            # Should have 2 fragments (last one marked as final)
            assert len(fragments) == 2

            # First fragment should be exactly MAX_FRAGMENT_SIZE_BYTES
            assert fragments[0].size_bytes == MAX_FRAGMENT_SIZE_BYTES
            assert fragments[0].is_last_fragment is False

            # Second fragment should contain remaining bytes and be marked as final
            remaining = (chunk_size * 2) - MAX_FRAGMENT_SIZE_BYTES
            assert fragments[1].size_bytes == remaining
            assert fragments[1].is_last_fragment is True

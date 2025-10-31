"""Integration test for UploadDocumentCommand with real PDF file."""

from collections.abc import AsyncIterator
from pathlib import Path

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
from vdb_core.domain.value_objects import LibraryName
from vdb_core.infrastructure.message_bus import InMemoryMessageBus
from vdb_core.infrastructure.persistence import InMemoryUnitOfWork


async def async_file_reader(file_path: Path, chunk_size: int = 8192) -> AsyncIterator[bytes]:
    """Async generator to read file in chunks."""
    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            yield chunk


@pytest.mark.asyncio
class TestUploadDocumentCommandIntegration:
    """Integration tests for UploadDocumentCommand with real PDF file."""

    async def test_upload_pdf_file_creates_document_and_fragments(self) -> None:
        """Test uploading a real PDF file creates document and fragments correctly."""
        # Arrange
        uow = InMemoryUnitOfWork()
        message_bus = InMemoryMessageBus()

        # Create commands
        create_doc_command = CreateDocumentCommand(
            uow_factory=lambda: uow,
            message_bus=message_bus,
        )
        create_fragment_command = CreateDocumentFragmentCommand(
            uow_factory=lambda: uow,
            message_bus=message_bus,
        )
        upload_command = UploadDocumentCommand(
            create_document_command=create_doc_command,
            create_fragment_command=create_fragment_command,
        )

        # Create library first
        library = Library(name=LibraryName(value="Test Library"))
        async with uow:
            await uow.libraries.add(library)
            await uow.commit()

        # Get test PDF file
        test_pdf = Path(__file__).parent.parent.parent / "fixtures" / "test.pdf"
        assert test_pdf.exists(), f"Test PDF not found at {test_pdf}"

        # Act - Upload the PDF
        input_data = UploadDocumentInput(
            library_id=str(library.id),
            filename="test.pdf",
        )
        document_id = await upload_command.execute(
            input_data=input_data,
            chunks=async_file_reader(test_pdf, chunk_size=200),  # Small chunks to test batching
        )

        # Assert
        assert document_id is not None

        # Verify document was created
        async with uow:
            lib = await uow.libraries.get(library.id)
            document = await lib.get_document(document_id)
            assert document is not None
            assert document.name.value == "test.pdf"
            assert document.upload_complete is True

        # Verify events were published
        event_types = [type(event) for event in message_bus.handled_events]
        assert DocumentCreated in event_types

        # Should have fragment events (data fragments + EOF)
        fragment_events = [e for e in message_bus.handled_events if isinstance(e, DocumentFragmentReceived)]
        assert len(fragment_events) > 0

        # Verify last event is EOF marker
        eof_event = fragment_events[-1]
        assert eof_event.is_final is True

        # Verify fragments can be reconstructed into original PDF
        async with uow:
            lib = await uow.libraries.get(library.id)
            document = await lib.get_document(document_id)
            fragments = document.fragments

            # All fragments contain data (last one is marked as final)
            # Reconstruct PDF from all fragments
            reconstructed = b"".join(frag.content for frag in fragments)

            # Read original PDF
            with open(test_pdf, "rb") as f:
                original = f.read()

            # Verify reconstruction matches original
            assert reconstructed == original, "Reconstructed PDF doesn't match original"
            assert len(reconstructed) == len(original)

    async def test_upload_pdf_with_nonexistent_library_fails(self) -> None:
        """Test uploading PDF to non-existent library raises error."""
        # Arrange
        uow = InMemoryUnitOfWork()
        message_bus = InMemoryMessageBus()

        create_doc_command = CreateDocumentCommand(
            uow_factory=lambda: uow,
            message_bus=message_bus,
        )
        create_fragment_command = CreateDocumentFragmentCommand(
            uow_factory=lambda: uow,
            message_bus=message_bus,
        )
        upload_command = UploadDocumentCommand(
            create_document_command=create_doc_command,
            create_fragment_command=create_fragment_command,
        )

        # Get test PDF
        test_pdf = Path(__file__).parent.parent.parent / "fixtures" / "test.pdf"

        # Act & Assert
        input_data = UploadDocumentInput(
            library_id="00000000-0000-0000-0000-000000000000",
            filename="test.pdf",
        )

        with pytest.raises(LibraryNotFoundError):
            await upload_command.execute(
                input_data=input_data,
                chunks=async_file_reader(test_pdf),
            )

    async def test_upload_pdf_fragments_have_correct_sequence_numbers(self) -> None:
        """Test that fragments are numbered sequentially starting from 0."""
        # Arrange
        uow = InMemoryUnitOfWork()
        message_bus = InMemoryMessageBus()

        create_doc_command = CreateDocumentCommand(
            uow_factory=lambda: uow,
            message_bus=message_bus,
        )
        create_fragment_command = CreateDocumentFragmentCommand(
            uow_factory=lambda: uow,
            message_bus=message_bus,
        )
        upload_command = UploadDocumentCommand(
            create_document_command=create_doc_command,
            create_fragment_command=create_fragment_command,
        )

        # Create library
        library = Library(name=LibraryName(value="Test Library"))
        async with uow:
            await uow.libraries.add(library)
            await uow.commit()

        # Get test PDF
        test_pdf = Path(__file__).parent.parent.parent / "fixtures" / "test.pdf"

        # Act
        input_data = UploadDocumentInput(
            library_id=str(library.id),
            filename="test.pdf",
        )
        document_id = await upload_command.execute(
            input_data=input_data,
            chunks=async_file_reader(test_pdf, chunk_size=100),  # Very small chunks
        )

        # Assert
        async with uow:
            lib = await uow.libraries.get(library.id)
            document = await lib.get_document(document_id)
            fragments = document.fragments

            # Verify sequence numbers are consecutive starting from 0
            for i, fragment in enumerate(fragments):
                expected_sequence = i
                assert fragment.sequence_number == expected_sequence, (
                    f"Fragment {i} has sequence_number {fragment.sequence_number}, expected {expected_sequence}"
                )

            # Verify last fragment is marked as final
            assert fragments[-1].is_last_fragment is True

    async def test_upload_pdf_events_published_incrementally(self) -> None:
        """Test that fragment events are published as fragments are created."""
        # Arrange
        uow = InMemoryUnitOfWork()
        message_bus = InMemoryMessageBus()

        create_doc_command = CreateDocumentCommand(
            uow_factory=lambda: uow,
            message_bus=message_bus,
        )
        create_fragment_command = CreateDocumentFragmentCommand(
            uow_factory=lambda: uow,
            message_bus=message_bus,
        )
        upload_command = UploadDocumentCommand(
            create_document_command=create_doc_command,
            create_fragment_command=create_fragment_command,
        )

        # Create library
        library = Library(name=LibraryName(value="Test Library"))
        async with uow:
            await uow.libraries.add(library)
            await uow.commit()

        # Get test PDF
        test_pdf = Path(__file__).parent.parent.parent / "fixtures" / "test.pdf"

        # Act
        input_data = UploadDocumentInput(
            library_id=str(library.id),
            filename="test.pdf",
        )
        await upload_command.execute(
            input_data=input_data,
            chunks=async_file_reader(test_pdf),
        )

        # Assert
        fragment_events = [e for e in message_bus.handled_events if isinstance(e, DocumentFragmentReceived)]

        # Should have at least one fragment
        assert len(fragment_events) > 0

        # First fragment should have sequence_number=0
        assert fragment_events[0].sequence_number == 0

        if len(fragment_events) == 1:
            # Single fragment is marked as final
            assert fragment_events[0].is_final is True
        else:
            # Multiple fragments: first is not final
            assert fragment_events[0].is_final is False

            # Middle fragments should not be final
            for event in fragment_events[1:-1]:
                assert event.is_final is False

            # Last fragment should have is_final=True
            assert fragment_events[-1].is_final is True

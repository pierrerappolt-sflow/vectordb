"""Test that updated_at timestamps propagate from child entities to aggregate root."""

import asyncio
from typing import TYPE_CHECKING

import pytest
from vdb_core.domain.entities import Library
from vdb_core.domain.value_objects import ContentHash, DocumentName, LibraryName

if TYPE_CHECKING:
    from datetime import datetime


@pytest.mark.asyncio
async def test_fragment_addition_updates_document_and_library_timestamps() -> None:
    """When a DocumentFragment is added, both Document and Library updated_at should be updated."""
    # Create library
    library = Library(name=LibraryName(value="Test Library"))
    library_initial_updated_at = library.updated_at

    # Small delay to ensure timestamps are different
    await asyncio.sleep(0.01)

    # Add document to library
    document = library.add_document(name=DocumentName("Test Doc"))
    document_initial_updated_at = document.updated_at

    # Small delay to ensure timestamps are different
    await asyncio.sleep(0.01)

    # Add fragment to document
    fragment = document.add_fragment(
        sequence_number=0,
        content=b"test bytes",
        content_hash=ContentHash.from_bytes(b"test bytes"),
        is_final=False,
    )

    # Document's updated_at should be updated immediately
    assert document.updated_at > document_initial_updated_at, (
        "Document.updated_at should be updated when fragment is added"
    )

    # Collect events (this is when Library's updated_at gets updated)
    events = library.collect_all_events()

    # Library's updated_at should be updated after collecting events
    assert library.updated_at > library_initial_updated_at, (
        "Library.updated_at should be updated when child entities have events"
    )

    # Verify events were collected
    assert len(events) > 0, "Should have collected events from document fragment"

    # Verify fragment event is in collected events
    from vdb_core.domain.events import DocumentFragmentReceived

    fragment_events = [e for e in events if isinstance(e, DocumentFragmentReceived)]
    assert len(fragment_events) == 1, "Should have one DocumentFragmentReceived event"
    assert fragment_events[0].fragment_id == fragment.id


@pytest.mark.asyncio
async def test_library_timestamp_not_updated_when_no_child_events() -> None:
    """Library.updated_at should NOT be updated when there are no child events."""
    library = Library(name=LibraryName(value="Test Library"))
    initial_updated_at = library.updated_at

    # Clear library's own events (LibraryCreated)
    library.events.clear()

    # Small delay
    await asyncio.sleep(0.01)

    # Collect events when there are none
    events = library.collect_all_events()

    # Library's updated_at should NOT change
    assert library.updated_at == initial_updated_at, "Library.updated_at should not change when there are no events"

    assert len(events) == 0, "Should have no events"


@pytest.mark.asyncio
async def test_multiple_fragments_update_timestamps() -> None:
    """Multiple fragment additions should continually update timestamps."""
    library = Library(name=LibraryName(value="Test Library"))
    document = library.add_document(name=DocumentName("Test Doc"))

    timestamps_doc: list[datetime] = []
    timestamps_lib: list[datetime] = []

    for i in range(3):
        await asyncio.sleep(0.01)

        # Create content
        content = b"0123456789"  # 10 bytes

        # Add fragment
        document.add_fragment(
            sequence_number=i,
            content=content,
            content_hash=ContentHash.from_bytes(content),
            is_final=(i == 2),
        )

        timestamps_doc.append(document.updated_at)

        # Collect events to trigger library timestamp update
        library.collect_all_events()
        timestamps_lib.append(library.updated_at)

    # Each timestamp should be strictly increasing
    for i in range(1, len(timestamps_doc)):
        assert timestamps_doc[i] > timestamps_doc[i - 1], f"Document timestamp {i} should be > timestamp {i - 1}"

    for i in range(1, len(timestamps_lib)):
        assert timestamps_lib[i] > timestamps_lib[i - 1], f"Library timestamp {i} should be > timestamp {i - 1}"

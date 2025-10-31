"""Tests for Document domain events."""

from datetime import UTC, datetime
from uuid import uuid4

from vdb_core.domain.events import DocumentCreated, DocumentDeleted, DocumentUpdated
from vdb_core.domain.value_objects import DocumentName


def test_document_created_event() -> None:
    """Test DocumentCreated event creation."""
    document_id = uuid4()
    library_id = uuid4()
    name = "Test Document"

    event = DocumentCreated(
        document_id=document_id,
        library_id=library_id,
        name=name,
    )

    assert event.document_id == document_id
    assert event.library_id == library_id
    assert event.name == name
    assert isinstance(event.event_id, str)
    assert isinstance(event.occurred_at, datetime)
    assert event.occurred_at.tzinfo == UTC


def test_document_updated_event() -> None:
    """Test DocumentUpdated event creation."""
    document_id = uuid4()
    library_id = uuid4()
    name = DocumentName("Updated Document")

    event = DocumentUpdated(
        document_id=document_id,
        library_id=library_id,
        name=name,
    )

    assert event.document_id == document_id
    assert event.library_id == library_id
    assert event.name == name
    assert isinstance(event.event_id, str)
    assert isinstance(event.occurred_at, datetime)


def test_document_deleted_event() -> None:
    """Test DocumentDeleted event creation."""
    document_id = uuid4()
    library_id = uuid4()

    event = DocumentDeleted(
        document_id=document_id,
        library_id=library_id,
    )

    assert event.document_id == document_id
    assert event.library_id == library_id
    assert isinstance(event.event_id, str)
    assert isinstance(event.occurred_at, datetime)


def test_document_events_are_immutable() -> None:
    """Test that domain events are immutable."""
    from dataclasses import FrozenInstanceError

    import pytest

    document_id = uuid4()
    library_id = uuid4()
    name = DocumentName("Test")

    event = DocumentCreated(
        document_id=document_id,
        library_id=library_id,
        name=name,
    )

    with pytest.raises(FrozenInstanceError):
        event.document_id = uuid4()  # type: ignore[misc]


def test_document_events_have_unique_ids() -> None:
    """Test that each event gets a unique ID."""
    document_id = uuid4()
    library_id = uuid4()
    name = DocumentName("Test")

    event1 = DocumentCreated(
        document_id=document_id,
        library_id=library_id,
        name=name,
    )

    event2 = DocumentCreated(
        document_id=document_id,
        library_id=library_id,
        name=name,
    )

    assert event1.event_id != event2.event_id

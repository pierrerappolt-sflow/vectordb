"""Tests for entity event collection."""

from uuid import uuid4

from vdb_core.domain.entities import Document, Library
from vdb_core.domain.events import DocumentCreated, LibraryCreated
from vdb_core.domain.value_objects import DocumentName, LibraryName


def test_entity_can_raise_events() -> None:
    """Test that entities raise domain events as side effects.

    Following Cosmic Python pattern:
    - Events are added to entity.events as side effects during __post_init__
    - No manual raise_event() calls
    """
    library = Library(name=LibraryName(value="Test Library"))

    # __post_init__ adds LibraryCreated event as side effect
    assert len(library.events) == 1
    assert isinstance(library.events[0], LibraryCreated)


def test_entity_can_collect_multiple_events() -> None:
    """Test that entities can collect multiple domain events.

    Following Cosmic Python pattern:
    - Events are appended directly to entity.events
    - No raise_event() method calls
    """
    library_id = uuid4()
    document = Document(
        library_id=library_id,
        name=DocumentName("Test Doc"),
    )

    # Add multiple events directly to events list
    event1 = DocumentCreated(
        document_id=document.id,
        library_id=library_id,
        name=document.name,
    )
    event2 = DocumentCreated(
        document_id=document.id,
        library_id=library_id,
        name=document.name,
    )

    document.events.append(event1)
    document.events.append(event2)

    # Check both events were collected
    assert len(document.events) == 2
    assert event1 in document.events
    assert event2 in document.events


def test_entity_can_clear_events() -> None:
    """Test that events can be collected and cleared.

    Following Cosmic Python pattern:
    - UoW collects events from entity.events
    - After collection, events list is cleared
    """
    library = Library(name=LibraryName(value="Test Library"))

    # __post_init__ already added 1 event, add one more
    event = LibraryCreated(library_id=library.id, name=library.name)
    library.events.append(event)

    # Simulate UoW collecting events (what collect_events() does)
    collected_events = list(library.events)
    library.events.clear()

    # Check events were collected and collection is now empty
    assert len(collected_events) == 2
    assert event in collected_events
    assert len(library.events) == 0


def test_events_list_is_directly_mutable() -> None:
    """Test that events list is directly mutable (Cosmic Python pattern).

    In Cosmic Python, events is a public list that can be appended to directly.
    This is intentional - events are added as side effects by appending.
    """
    library = Library(name=LibraryName(value="Test Library"))

    # __post_init__ already added 1 event
    assert len(library.events) == 1

    # Append directly to events list (this is the Cosmic Python way)
    library.events.append(LibraryCreated(library_id=library.id, name=library.name))

    # Events list should now have 2 events
    assert len(library.events) == 2

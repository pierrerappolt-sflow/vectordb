"""Tests for IEntity base class."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from vdb_core.domain.entities import IEntity
from vdb_core.domain.value_objects import DocumentId, LibraryId


@dataclass(slots=True, kw_only=True, eq=False)
class SampleEntity(IEntity):
    """Sample entity for testing IEntity behavior."""

    id: LibraryId = field(default_factory=uuid4, init=False)
    name: str


def test_entity_id_auto_generated() -> None:
    """Test that entity ID is automatically generated."""
    entity = SampleEntity(name="test")

    assert isinstance(entity.id, UUID)
    assert entity.id is not None


def test_entity_created_at_auto_generated() -> None:
    """Test that created_at timestamp is automatically generated."""
    entity = SampleEntity(name="test")

    assert isinstance(entity.created_at, datetime)
    assert entity.created_at.tzinfo == UTC


def test_entity_updated_at_auto_generated() -> None:
    """Test that updated_at timestamp is automatically generated."""
    entity = SampleEntity(name="test")

    assert isinstance(entity.updated_at, datetime)
    assert entity.updated_at.tzinfo == UTC


def test_entity_created_at_equals_updated_at_initially() -> None:
    """Test that created_at and updated_at are equal when entity is created."""
    entity = SampleEntity(name="test")

    # They should be very close (within microseconds)
    assert abs((entity.updated_at - entity.created_at).total_seconds()) < 0.001


def test_entity_equality_based_on_id() -> None:
    """Test that entities are equal if they have the same ID."""
    entity1 = SampleEntity(name="test1")
    entity2 = SampleEntity(name="test2")

    # Different entities with different IDs
    assert entity1 != entity2

    # Same ID (by manually setting)
    entity3 = SampleEntity(name="test3")
    entity4 = SampleEntity(name="test4")

    # Force same ID
    object.__setattr__(entity4, "id", entity3.id)

    assert entity3 == entity4


def test_entity_hash_based_on_id() -> None:
    """Test that entity hash is based on ID."""
    entity = SampleEntity(name="test")

    assert hash(entity) == hash(entity.id)


def test_entity_can_be_added_to_set() -> None:
    """Test that entities can be added to sets (hashable)."""
    entity1 = SampleEntity(name="test1")
    entity2 = SampleEntity(name="test2")
    entity3 = SampleEntity(name="test3")

    entity_set = {entity1, entity2, entity3}

    assert len(entity_set) == 3
    assert entity1 in entity_set


def test_entity_different_types_not_equal() -> None:
    """Test that entities of different types are not equal even with same ID."""

    @dataclass(slots=True, kw_only=True, eq=False)
    class AnotherEntity(IEntity):
        id: DocumentId = field(default_factory=uuid4, init=False)
        value: int

    entity1 = SampleEntity(name="test")
    entity2 = AnotherEntity(value=42)

    # Force same ID
    object.__setattr__(entity2, "id", entity1.id)

    assert entity1 != entity2


def test_entity_not_equal_to_non_entity() -> None:
    """Test that entity is not equal to non-entity objects."""
    entity = SampleEntity(name="test")

    assert entity != "test"
    assert entity != 42
    assert entity != None  # noqa: E711
    assert entity != {"id": entity.id}


def test_multiple_entities_have_unique_ids() -> None:
    """Test that multiple entities get unique IDs."""
    entities = [SampleEntity(name=f"test{i}") for i in range(100)]
    ids = [e.id for e in entities]

    assert len(set(ids)) == 100  # All IDs are unique

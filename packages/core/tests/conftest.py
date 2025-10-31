"""Shared test fixtures and base classes for domain tests."""

import os
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, ClassVar
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import asyncpg
import pytest
import pytest_asyncio
from pydantic import ValidationError

# ==================== Use Case Test Fixtures ====================


@pytest.fixture
def mock_uow() -> MagicMock:
    """Create a mock Unit of Work with common setup.

    The UoW is pre-configured to work as an async context manager
    and has a commit method that returns an empty event list.

    Usage:
        async def test_something(mock_uow):
            mock_uow.libraries = AsyncMock()
            mock_uow.commit = AsyncMock(return_value=[mock_event])
            # ... use in test
    """
    uow = MagicMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)
    uow.commit = AsyncMock(return_value=[])
    return uow


@pytest.fixture
def mock_event_bus() -> AsyncMock:
    """Create a mock event bus for use cases.

    Returns:
        AsyncMock event bus with handle_events method

    """
    return AsyncMock()


# ==================== Domain Test Mixins ====================


class EntityTestMixin(ABC):
    """Base test mixin for IEntity subclasses.

    Provides common tests for entity behavior:
    - Timestamp generation (created_at, updated_at)
    - Equality based on ID
    - Hashability
    - Set membership

    Subclasses must define:
        entity_class: The entity class to test
        create_entity(**kwargs): Factory method to create an instance
    """

    entity_class: ClassVar[type]

    @abstractmethod
    def create_entity(self, **kwargs: Any) -> Any:
        """Factory method to create an entity instance.

        Override this in subclasses to provide entity-specific construction.
        """
        ...

    def test_entity_has_timestamps(self) -> None:
        """Test that entity has created_at and updated_at timestamps."""
        entity = self.create_entity()

        assert isinstance(entity.created_at, datetime)
        assert isinstance(entity.updated_at, datetime)
        assert entity.created_at.tzinfo == UTC
        assert entity.updated_at.tzinfo == UTC

    def test_entity_created_at_equals_updated_at_initially(self) -> None:
        """Test that created_at and updated_at are equal when entity is created."""
        entity = self.create_entity()

        # They should be very close (within microseconds)
        assert abs((entity.updated_at - entity.created_at).total_seconds()) < 0.001

    def test_entity_equality_based_on_id(self) -> None:
        """Test that entities are equal if they have the same ID."""
        entity1 = self.create_entity()
        entity2 = self.create_entity()

        # Different entities with different IDs
        assert entity1 != entity2

        # Same ID (by manually setting)
        entity3 = self.create_entity()
        object.__setattr__(entity3, "id", entity1.id)

        assert entity1 == entity3

    def test_entity_hash_based_on_id(self) -> None:
        """Test that entity hash is based on ID."""
        entity = self.create_entity()

        assert hash(entity) == hash(entity.id)

    def test_entity_can_be_added_to_set(self) -> None:
        """Test that entities can be added to sets (hashable)."""
        entity1 = self.create_entity()
        entity2 = self.create_entity()
        entity3 = self.create_entity()

        entity_set = {entity1, entity2, entity3}

        assert len(entity_set) == 3
        assert entity1 in entity_set

    def test_entity_not_equal_to_non_entity(self) -> None:
        """Test that entity is not equal to non-entity objects."""
        entity = self.create_entity()

        assert entity != "test"
        assert entity != 42
        assert entity != None  # noqa: E711
        assert entity != {"id": entity.id}


class UuidValueObjectTestMixin(ABC):
    """Base test mixin for UUID-based value objects.

    Provides common tests for UUID-based value object behavior:
    - Creation with UUID
    - generate() factory method
    - Immutability
    - Equality/inequality
    - Hashability

    Subclasses must define:
        value_object_class: The value object class to test
    """

    value_object_class: ClassVar[type]

    def test_vo_creation(self) -> None:
        """Test creating a value object with a UUID."""
        test_uuid = uuid4()
        # ID classes are now UUID aliases, pass string to constructor
        vo = self.value_object_class(str(test_uuid))

        assert vo == test_uuid
        assert isinstance(vo, UUID)

    def test_vo_generate(self) -> None:
        """Test generating a new value object."""
        # UUID aliases use uuid4() to generate
        vo = uuid4()

        assert isinstance(vo, UUID)
        assert vo is not None

    def test_vo_immutable(self) -> None:
        """Test that value object fields are immutable."""
        # UUIDs are immutable by design
        vo = uuid4()

        # UUIDs raise TypeError when trying to set attributes
        with pytest.raises(TypeError, match="UUID objects are immutable"):
            vo.int = 12345  # type: ignore[misc]

    def test_vo_equality(self) -> None:
        """Test that value objects with same UUID are equal."""
        test_uuid = uuid4()
        vo1 = self.value_object_class(str(test_uuid))
        vo2 = self.value_object_class(str(test_uuid))

        assert vo1 == vo2
        assert vo1 == test_uuid

    def test_vo_inequality(self) -> None:
        """Test that value objects with different UUIDs are not equal."""
        vo1 = uuid4()
        vo2 = uuid4()

        assert vo1 != vo2

    def test_vo_hashable(self) -> None:
        """Test that value objects can be used in sets and dicts."""
        vo1 = uuid4()
        vo2 = uuid4()
        vo3 = uuid4()

        vo_set = {vo1, vo2, vo3}

        assert len(vo_set) == 3
        assert vo1 in vo_set

        # Same UUID should hash the same
        test_uuid = uuid4()
        vo4 = self.value_object_class(str(test_uuid))
        vo5 = self.value_object_class(str(test_uuid))
        assert hash(vo4) == hash(vo5)


class NameValueObjectTestMixin(ABC):
    """Base test mixin for name-based string value objects.

    Provides common tests for text/name value object behavior:
    - Creation with string value
    - Immutability
    - Equality/inequality
    - Hashability
    - Empty string validation
    - Max length validation

    Subclasses must define:
        value_object_class: The value object class to test
        max_length: Maximum allowed length (from constants)
    """

    value_object_class: ClassVar[type]
    max_length: ClassVar[int]

    def test_name_creation(self) -> None:
        """Test creating a name value object with a valid string."""
        name = self.value_object_class(value="Test Name")

        assert name.value == "Test Name"
        assert isinstance(name.value, str)

    def test_name_immutable(self) -> None:
        """Test that name value object fields are immutable."""
        name = self.value_object_class(value="Test Name")

        with pytest.raises(FrozenInstanceError):
            name.value = "New Name"

    def test_name_equality(self) -> None:
        """Test that names with same value are equal."""
        name1 = self.value_object_class(value="Same Name")
        name2 = self.value_object_class(value="Same Name")

        assert name1 == name2

    def test_name_inequality(self) -> None:
        """Test that names with different values are not equal."""
        name1 = self.value_object_class(value="Name 1")
        name2 = self.value_object_class(value="Name 2")

        assert name1 != name2

    def test_name_hashable(self) -> None:
        """Test that names can be used in sets and dicts."""
        name1 = self.value_object_class(value="Name 1")
        name2 = self.value_object_class(value="Name 2")
        name3 = self.value_object_class(value="Name 3")

        name_set = {name1, name2, name3}

        assert len(name_set) == 3
        assert name1 in name_set

    def test_name_empty_string_fails(self) -> None:
        """Test that empty string is rejected."""
        with pytest.raises(ValidationError, match="at least 1 character"):
            self.value_object_class(value="")

    def test_name_too_long_fails(self) -> None:
        """Test that names longer than max_length are rejected."""
        long_name = "a" * (self.max_length + 1)

        with pytest.raises(ValidationError, match="at most"):
            self.value_object_class(value=long_name)

    def test_name_max_length_succeeds(self) -> None:
        """Test that names exactly max_length long are accepted."""
        max_name = "a" * self.max_length
        name = self.value_object_class(value=max_name)

        assert len(name.value) == self.max_length


class HashValueObjectTestMixin(ABC):
    """Base test mixin for hash-based value objects.

    Provides common tests for hash-based value object behavior:
    - Immutability
    - Equality/inequality
    - Hashability

    Subclasses must define:
        value_object_class: The value object class to test
        create_value_object(**kwargs): Factory method to create an instance
    """

    value_object_class: ClassVar[type]

    @abstractmethod
    def create_value_object(self, **kwargs: Any) -> Any:
        """Factory method to create a value object instance.

        Override this in subclasses to provide value-object-specific construction.
        """
        ...

    def test_hash_vo_immutable(self) -> None:
        """Test that value object fields are immutable."""
        vo = self.create_value_object()

        with pytest.raises(FrozenInstanceError):
            vo.value = "new-value"

    def test_hash_vo_equality(self) -> None:
        """Test that value objects with same inputs are equal."""
        vo1 = self.create_value_object()
        vo2 = self.create_value_object()

        assert vo1 == vo2

    def test_hash_vo_hashable(self) -> None:
        """Test that value objects can be used in sets and dicts."""
        vo1 = self.create_value_object()
        vo2 = self.create_value_object()
        vo3 = self.create_value_object()

        vo_set = {vo1, vo2, vo3}

        # All should be equal, so set should have 1 item
        assert len(vo_set) == 1
        assert vo1 in vo_set


class StrEnumTestMixin(ABC):
    """Base test mixin for StrEnum-based value objects.

    Provides common tests for StrEnum behavior:
    - String value correctness
    - Equality/inequality
    - Singleton behavior
    - Dictionary key usage
    - String representation

    Subclasses must define:
        enum_class: The StrEnum class to test
        test_cases: List of (member_name, expected_value) tuples
    """

    enum_class: ClassVar[type]
    test_cases: ClassVar[list[tuple[str, str]]]

    def test_enum_values(self) -> None:
        """Test that enum members have correct string values."""
        for member_name, expected_value in self.test_cases:
            member = getattr(self.enum_class, member_name)
            assert member.value == expected_value
            assert isinstance(member, str)

    def test_enum_equality(self) -> None:
        """Test that same enum members are equal."""
        if not self.test_cases:
            return
        member_name, _ = self.test_cases[0]
        member1 = getattr(self.enum_class, member_name)
        member2 = getattr(self.enum_class, member_name)

        assert member1 == member2
        assert member1 is member2  # StrEnum members are singletons

    def test_enum_inequality(self) -> None:
        """Test that different enum members are not equal."""
        if len(self.test_cases) < 2:
            return
        member1_name, _ = self.test_cases[0]
        member2_name, _ = self.test_cases[1]

        member1 = getattr(self.enum_class, member1_name)
        member2 = getattr(self.enum_class, member2_name)

        assert member1 != member2

    def test_enum_as_dict_key(self) -> None:
        """Test that enum members can be used as dictionary keys."""
        if not self.test_cases:
            return
        member_name, _ = self.test_cases[0]
        member = getattr(self.enum_class, member_name)

        test_dict = {member: "test_value"}
        assert test_dict[member] == "test_value"

    def test_enum_str_representation(self) -> None:
        """Test that string representation is the enum value."""
        for member_name, expected_value in self.test_cases:
            member = getattr(self.enum_class, member_name)
            assert str(member) == expected_value


# ==================== PostgreSQL Database Fixtures ====================


def get_test_db_url() -> str:
    """Get PostgreSQL database URL from environment or default to docker-compose setup.

    Returns:
        PostgreSQL connection URL for testing

    """
    return os.getenv(
        "TEST_DATABASE_URL",
        "postgresql://vdbuser:vdbpass@localhost:5432/vectordb_test",
    )


@pytest_asyncio.fixture(scope="session")
async def db_pool() -> AsyncGenerator[asyncpg.Pool]:
    """Create a PostgreSQL connection pool for testing.

    This fixture creates a test database, runs the schema, and provides
    a connection pool for tests. The database is dropped after all tests complete.

    Requires PostgreSQL with pgvector extension (e.g., from docker-compose).

    Yields:
        asyncpg connection pool

    """
    # Get base connection URL (to postgres database)
    base_url = os.getenv(
        "TEST_DATABASE_BASE_URL",
        "postgresql://vdbuser:vdbpass@localhost:5432/postgres",
    )

    # Connect to postgres database to create test database
    conn = await asyncpg.connect(base_url)

    try:
        # Drop test database if it exists
        await conn.execute("DROP DATABASE IF EXISTS vectordb_test")

        # Create test database
        await conn.execute("CREATE DATABASE vectordb_test")
    finally:
        await conn.close()

    # Connect to test database
    test_db_url = get_test_db_url()
    pool = await asyncpg.create_pool(test_db_url, min_size=2, max_size=10)

    if pool is None:
        msg = "Failed to create database pool"
        raise RuntimeError(msg)

    try:
        # Run schema setup
        await _create_test_schema(pool)

        yield pool
    finally:
        # Clean up
        await pool.close()

        # Drop test database
        conn = await asyncpg.connect(base_url)
        try:
            await conn.execute("DROP DATABASE IF EXISTS vectordb_test")
        finally:
            await conn.close()


async def _create_test_schema(pool: asyncpg.Pool) -> None:
    """Create test database schema in PostgreSQL with pgvector.

    Runs the schema.sql file to set up all tables, indexes, and pgvector extension.

    Args:
        pool: asyncpg connection pool

    """
    # Find schema.sql file (in scripts/ directory at project root)
    schema_path = Path(__file__).parent.parent.parent.parent / "scripts" / "schema.sql"

    if not schema_path.exists():
        msg = f"Schema file not found: {schema_path}"
        raise FileNotFoundError(msg)

    # Read schema file
    schema_sql = schema_path.read_text()

    # Execute schema
    async with pool.acquire() as conn:
        await conn.execute(schema_sql)


@pytest_asyncio.fixture
async def db(db_pool: asyncpg.Pool) -> AsyncGenerator[asyncpg.Pool]:
    """Provide a clean database for each test.

    This fixture truncates all tables before each test to ensure isolation.

    Args:
        db_pool: Session-scoped database pool

    Yields:
        Database pool with clean tables

    """
    async with db_pool.acquire() as conn:
        # Truncate all tables (CASCADE to handle foreign keys)
        await conn.execute(
            """
            TRUNCATE TABLE
                search_queries,
                message_queue,
                library_document_pipelines,
                embeddings,
                chunks,
                document_fragments,
                documents,
                libraries
            CASCADE
            """
        )

    yield db_pool

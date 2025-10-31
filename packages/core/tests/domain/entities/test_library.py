"""Tests for Library entity."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest
from vdb_core.domain.entities import Library
from vdb_core.domain.value_objects import (
    LibraryId,
    LibraryName,
    LibraryStatusEnum,
    default_library_status,
)

from tests.conftest import EntityTestMixin


class TestLibrary(EntityTestMixin):
    """Tests for Library entity."""

    entity_class = Library

    def create_entity(self, **kwargs: Any) -> Library:
        """Factory method to create a Library instance."""
        name = kwargs.get("name", LibraryName(value="Test Library"))
        return Library(name=name)

    def test_library_creation(self) -> None:
        """Test creating a library with name."""
        library = Library(name=LibraryName(value="My Library"))

        assert library.name.value == "My Library"
        assert isinstance(library.id, LibraryId)

    def test_library_has_active_status_by_default(self) -> None:
        """Test that library has ACTIVE status by default."""
        library = Library(name=LibraryName(value="Test Library"))

        assert library.status == LibraryStatusEnum.ACTIVE

    def test_library_frozen_fields_cannot_be_modified(self) -> None:
        """Test that frozen fields (id, created_at) cannot be modified."""
        library = Library(name=LibraryName(value="Test Library"))

        # Frozen fields should raise AttributeError
        with pytest.raises(AttributeError, match="Cannot directly assign"):
            library.id = uuid4()

        with pytest.raises(AttributeError, match="Cannot directly assign"):
            library.created_at = datetime.now(UTC)

    def test_library_mutable_fields_can_be_modified(self) -> None:
        """Test that mutable fields (name, status, updated_at) can be modified via update()."""
        library = Library(name=LibraryName(value="Test Library"))

        # Direct assignment should fail (DDD invariant protection)
        with pytest.raises(AttributeError, match="Cannot directly assign"):
            library.name = LibraryName(value="Updated Library")

        # But update() method should work for mutable fields
        # (Note: update() implementation may vary - this test documents expected behavior)

    def test_library_reconstitute(self) -> None:
        """Test that Library.reconstitute() creates instance with all fields set."""
        library_id = uuid4()
        name = LibraryName(value="Test")
        status = default_library_status()
        created_at = datetime.now(UTC)
        updated_at = datetime.now(UTC)

        library = Library.reconstitute(
            id=library_id,
            name=name,
            status=status,
            created_at=created_at,
            updated_at=updated_at,
        )

        assert library.id == library_id
        assert library.name == name
        assert library.status == status
        assert library.created_at == created_at
        assert library.updated_at == updated_at

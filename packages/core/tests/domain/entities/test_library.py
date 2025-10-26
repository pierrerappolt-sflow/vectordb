"""Tests for Library entity."""

from datetime import UTC, datetime
from uuid import UUID

from vdb_core.domain.entities import Library


def test_library_creation() -> None:
    """Test creating a library with name."""
    library = Library(name="My Library")

    assert library.name == "My Library"
    assert isinstance(library.id, UUID)


def test_library_has_timestamps() -> None:
    """Test that library has created_at and updated_at timestamps."""
    library = Library(name="Test Library")

    assert isinstance(library.created_at, datetime)
    assert isinstance(library.updated_at, datetime)
    assert library.created_at.tzinfo == UTC
    assert library.updated_at.tzinfo == UTC


def test_library_equality() -> None:
    """Test library equality based on ID."""
    lib1 = Library(name="Library 1")
    lib2 = Library(name="Library 2")

    assert lib1 != lib2  # Different IDs

    # Same ID
    lib3 = Library(name="Library 3")
    object.__setattr__(lib3, "id", lib1.id)

    assert lib1 == lib3  # Same ID, equal


def test_library_hashable() -> None:
    """Test that libraries can be added to sets."""
    lib1 = Library(name="Library 1")
    lib2 = Library(name="Library 2")
    lib3 = Library(name="Library 3")

    library_set = {lib1, lib2, lib3}

    assert len(library_set) == 3
    assert lib1 in library_set

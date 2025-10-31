"""Tests for UUID-based ID value objects."""

from vdb_core.domain.value_objects import DocumentFragmentId, DocumentId, LibraryId

from tests.conftest import UuidValueObjectTestMixin


class TestLibraryId(UuidValueObjectTestMixin):
    """Tests for LibraryId value object."""

    value_object_class = LibraryId


class TestDocumentId(UuidValueObjectTestMixin):
    """Tests for DocumentId value object."""

    value_object_class = DocumentId


class TestDocumentFragmentId(UuidValueObjectTestMixin):
    """Tests for DocumentFragmentId value object."""

    value_object_class = DocumentFragmentId

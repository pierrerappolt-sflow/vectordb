"""Tests for Name-based value objects."""

from vdb_core.domain.value_objects import DocumentName, LibraryName
from vdb_core.domain.value_objects.document.constants import MAX_NAME_LENGTH

from tests.conftest import NameValueObjectTestMixin


class TestLibraryName(NameValueObjectTestMixin):
    """Tests for LibraryName value object."""

    value_object_class = LibraryName
    max_length = MAX_NAME_LENGTH


class TestDocumentName(NameValueObjectTestMixin):
    """Tests for DocumentName value object."""

    value_object_class = DocumentName
    max_length = MAX_NAME_LENGTH

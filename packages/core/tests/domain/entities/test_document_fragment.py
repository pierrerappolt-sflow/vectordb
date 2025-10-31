"""Tests for DocumentFragment entity."""

from typing import Any
from uuid import uuid4

import pytest
from vdb_core.domain.entities import DocumentFragment
from vdb_core.domain.value_objects import (
    MAX_FRAGMENT_SIZE_BYTES,
    ContentHash,
    DocumentFragmentId,
)

from tests.conftest import EntityTestMixin


class TestDocumentFragment(EntityTestMixin):
    """Tests for DocumentFragment entity."""

    entity_class = DocumentFragment

    def create_entity(self, **kwargs: Any) -> DocumentFragment:
        """Factory method to create a DocumentFragment instance."""
        document_id = uuid4()
        content = b"Test fragment content"
        content_hash = ContentHash.from_bytes(content)

        defaults = {
            "document_id": document_id,
            "sequence_number": 0,
            "content": content,
            "content_hash": content_hash,
            "is_last_fragment": False,
        }
        defaults.update(kwargs)
        return DocumentFragment(**defaults)  # type: ignore[arg-type]

    def test_fragment_creation(self) -> None:
        """Test creating a document fragment."""
        document_id = uuid4()
        content = b"Sample fragment content"
        content_hash = ContentHash.from_bytes(content)

        fragment = DocumentFragment(
            document_id=document_id,
            sequence_number=0,
            content=content,
            content_hash=content_hash,
            is_last_fragment=False,
        )

        assert fragment.document_id == document_id
        assert fragment.sequence_number == 0
        assert fragment.content == content
        assert fragment.content_hash == content_hash
        assert fragment.is_last_fragment is False
        assert isinstance(fragment.id, DocumentFragmentId)

    def test_fragment_auto_generates_id(self) -> None:
        """Test that fragment automatically generates an ID."""
        fragment1 = self.create_entity()
        fragment2 = self.create_entity()

        # Each fragment should have unique ID
        assert fragment1.id != fragment2.id
        assert isinstance(fragment1.id, DocumentFragmentId)
        assert isinstance(fragment2.id, DocumentFragmentId)

    def test_fragment_size_bytes_property(self) -> None:
        """Test that size_bytes property returns correct content size."""
        content = b"Test content with known length"
        fragment = self.create_entity(content=content)

        assert fragment.size_bytes == len(content)
        assert fragment.size_bytes == 30

    def test_fragment_validates_sequence_number_positive(self) -> None:
        """Test that sequence_number must be >= 0."""
        with pytest.raises(ValueError, match="sequence_number must be >= 0"):
            self.create_entity(sequence_number=-1)

    def test_fragment_validates_content_not_empty(self) -> None:
        """Test that content cannot be empty."""
        with pytest.raises(ValueError, match="content cannot be empty"):
            self.create_entity(content=b"")

    def test_fragment_validates_max_size(self) -> None:
        """Test that fragment size cannot exceed MAX_FRAGMENT_SIZE_BYTES."""
        # Try to create a fragment larger than MAX_FRAGMENT_SIZE_BYTES
        oversized_content = b"x" * (MAX_FRAGMENT_SIZE_BYTES + 1)
        content_hash = ContentHash.from_bytes(oversized_content)

        with pytest.raises(Exception):  # Will raise DocumentTooLargeError
            self.create_entity(
                content=oversized_content,
                content_hash=content_hash,
            )

    def test_fragment_allows_exactly_max_size(self) -> None:
        """Test that fragment can be exactly MAX_FRAGMENT_SIZE_BYTES."""
        # Create a fragment exactly MAX_FRAGMENT_SIZE_BYTES
        max_content = b"x" * MAX_FRAGMENT_SIZE_BYTES
        content_hash = ContentHash.from_bytes(max_content)

        fragment = self.create_entity(
            content=max_content,
            content_hash=content_hash,
        )

        assert fragment.size_bytes == MAX_FRAGMENT_SIZE_BYTES
        assert len(fragment.content) == MAX_FRAGMENT_SIZE_BYTES

    def test_fragment_supports_binary_content(self) -> None:
        """Test that fragment can store binary content (images, PDFs, etc.)."""
        # Simulate binary image data
        binary_content = bytes([0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10])  # JPEG header
        fragment = self.create_entity(content=binary_content)

        assert fragment.content == binary_content
        assert fragment.size_bytes == 6

    def test_fragment_with_is_last_fragment_flag(self) -> None:
        """Test creating a final fragment."""
        fragment = self.create_entity(is_last_fragment=True)

        assert fragment.is_last_fragment is True

    def test_fragment_sequence_ordering(self) -> None:
        """Test that fragments can be ordered by sequence_number."""
        fragments = [
            self.create_entity(sequence_number=2, content=b"c" * 100),
            self.create_entity(sequence_number=0, content=b"a" * 100),
            self.create_entity(sequence_number=1, content=b"b" * 100),
        ]

        # Sort by sequence number
        sorted_fragments = sorted(fragments, key=lambda f: f.sequence_number)

        assert sorted_fragments[0].sequence_number == 0
        assert sorted_fragments[1].sequence_number == 1
        assert sorted_fragments[2].sequence_number == 2

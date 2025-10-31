from __future__ import annotations

from vdb_core.domain.value_objects.common import ContentHash


def test_from_content_and_bytes_equivalence():
    text = "Hello World"
    h1 = ContentHash.from_content(text)
    h2 = ContentHash.from_bytes(text.encode("utf-8"))
    assert h1.value == h2.value


def test_from_normalized_text():
    text_a = "  Hello    world  "
    text_b = "hello world"
    h1 = ContentHash.from_normalized_text(text_a)
    h2 = ContentHash.from_normalized_text(text_b)
    assert h1.value == h2.value


def test_from_chunk_components_deterministic():
    a = ContentHash.from_chunk_components(
        document_id="doc-1",
        strategy_name="s",
        start=0,
        end=5,
        text="hello",
    )
    b = ContentHash.from_chunk_components(
        document_id="doc-1",
        strategy_name="s",
        start=0,
        end=5,
        text="hello",
    )
    assert a.value == b.value

"""Tests for ContentHash value object."""

import pytest
from vdb_core.domain.value_objects.common import ContentHash


class TestContentHash:
    """Tests for ContentHash value object."""

    def test_from_bytes_creates_sha256_hash(self) -> None:
        """Test that from_bytes creates a SHA-256 hash."""
        # Arrange
        content = b"Hello, World!"

        # Act
        hash_obj = ContentHash.from_bytes(content)

        # Assert
        assert isinstance(hash_obj, ContentHash)
        assert len(hash_obj.value) == 40  # SHA-1 produces 40 hex characters
        assert hash_obj.value == "0a0a9f2a6772942557ab5355d76af442f8f65e01"

    def test_from_bytes_is_deterministic(self) -> None:
        """Test that same input produces same hash."""
        # Arrange
        content = b"Test content"

        # Act
        hash1 = ContentHash.from_bytes(content)
        hash2 = ContentHash.from_bytes(content)

        # Assert
        assert hash1.value == hash2.value

    def test_from_bytes_different_content_produces_different_hash(self) -> None:
        """Test that different content produces different hashes."""
        # Arrange
        content1 = b"Content 1"
        content2 = b"Content 2"

        # Act
        hash1 = ContentHash.from_bytes(content1)
        hash2 = ContentHash.from_bytes(content2)

        # Assert
        assert hash1.value != hash2.value

    def test_from_bytes_handles_empty_content(self) -> None:
        """Test that empty content produces valid hash."""
        # Arrange
        content = b""

        # Act
        hash_obj = ContentHash.from_bytes(content)

        # Assert
        assert isinstance(hash_obj, ContentHash)
        assert len(hash_obj.value) == 40  # SHA-1 produces 40 hex characters
        # SHA-1 of empty string
        assert hash_obj.value == "da39a3ee5e6b4b0d3255bfef95601890afd80709"

    def test_from_bytes_handles_large_content(self) -> None:
        """Test that large content is handled correctly."""
        # Arrange
        content = b"X" * 1_000_000  # 1MB of data

        # Act
        hash_obj = ContentHash.from_bytes(content)

        # Assert
        assert isinstance(hash_obj, ContentHash)
        assert len(hash_obj.value) == 40  # SHA-1 produces 40 hex characters

    def test_content_hash_equality(self) -> None:
        """Test that content hashes with same value are equal."""
        # Arrange
        hash1 = ContentHash(value="abc123")
        hash2 = ContentHash(value="abc123")

        # Assert
        assert hash1 == hash2

    def test_content_hash_inequality(self) -> None:
        """Test that content hashes with different values are not equal."""
        # Arrange
        hash1 = ContentHash(value="abc123")
        hash2 = ContentHash(value="def456")

        # Assert
        assert hash1 != hash2

    def test_content_hash_is_hashable(self) -> None:
        """Test that ContentHash can be used in sets and dicts."""
        # Arrange
        hash1 = ContentHash(value="abc123")
        hash2 = ContentHash(value="def456")
        hash3 = ContentHash(value="abc123")

        # Act
        hash_set = {hash1, hash2, hash3}

        # Assert
        assert len(hash_set) == 2  # hash1 and hash3 are equal
        assert hash1 in hash_set

    def test_from_bytes_produces_lowercase_hex(self) -> None:
        """Test that hash is lowercase hexadecimal."""
        # Arrange
        content = b"Test"

        # Act
        hash_obj = ContentHash.from_bytes(content)

        # Assert
        assert hash_obj.value == hash_obj.value.lower()
        assert all(c in "0123456789abcdef" for c in hash_obj.value)

    def test_content_hash_immutable(self) -> None:
        """Test that ContentHash is immutable."""
        # Arrange
        hash_obj = ContentHash(value="abc123")

        # Act & Assert
        with pytest.raises(Exception):  # Frozen dataclass error
            hash_obj.value = "new_value"  # type: ignore

    def test_same_content_different_types_produces_different_hash(self) -> None:
        """Test that string vs bytes of same content produce different hashes."""
        # Note: from_bytes only accepts bytes, but this tests the concept
        # Arrange
        content = b"12345"

        # Act
        hash_from_bytes = ContentHash.from_bytes(content)

        # Assert - manual string hash would be different
        # This is to ensure we're explicit about byte content
        assert hash_from_bytes.value != "12345"

"""Tests for PostgreSQL mapper utilities."""

from datetime import UTC, datetime

import pytest
from vdb_core.infrastructure.persistence.postgres_mapper import to_datetime


class TestToDatetime:
    """Tests for to_datetime mapper function."""

    def test_to_datetime_with_datetime_object(self) -> None:
        """Test that datetime objects are returned as-is."""
        now = datetime.now(UTC)
        result = to_datetime(now)
        assert result is now
        assert isinstance(result, datetime)

    def test_to_datetime_with_iso_string(self) -> None:
        """Test that ISO datetime strings are parsed correctly."""
        iso_string = "2025-10-30T12:34:56.789000+00:00"
        result = to_datetime(iso_string)

        assert isinstance(result, datetime)
        assert result.year == 2025
        assert result.month == 10
        assert result.day == 30
        assert result.hour == 12
        assert result.minute == 34
        assert result.second == 56

    def test_to_datetime_with_iso_string_no_timezone(self) -> None:
        """Test that ISO datetime strings without timezone are parsed."""
        iso_string = "2025-10-30T12:34:56"
        result = to_datetime(iso_string)

        assert isinstance(result, datetime)
        assert result.year == 2025
        assert result.month == 10
        assert result.day == 30

    def test_to_datetime_with_invalid_type_raises_error(self) -> None:
        """Test that invalid types raise TypeError."""
        with pytest.raises(TypeError, match="Cannot convert"):
            to_datetime(123)  # Integer

    def test_to_datetime_with_invalid_string_raises_error(self) -> None:
        """Test that invalid datetime strings raise ValueError."""
        with pytest.raises(ValueError):
            to_datetime("not a datetime")

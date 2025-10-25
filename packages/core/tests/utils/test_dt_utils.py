"""Tests for datetime utilities."""

from datetime import UTC, datetime

from vdb_core.utils import utc_now


def test_utc_now_returns_datetime() -> None:
    """Test that utc_now returns a datetime object."""
    result = utc_now()
    assert isinstance(result, datetime)


def test_utc_now_has_utc_timezone() -> None:
    """Test that utc_now returns datetime with UTC timezone."""
    result = utc_now()
    assert result.tzinfo == UTC


def test_utc_now_is_recent() -> None:
    """Test that utc_now returns current time (within 1 second)."""
    before = datetime.now(UTC)
    result = utc_now()
    after = datetime.now(UTC)

    assert before <= result <= after
    assert (after - result).total_seconds() < 1


def test_utc_now_multiple_calls_increment() -> None:
    """Test that multiple calls to utc_now return increasing timestamps."""
    first = utc_now()
    second = utc_now()

    assert second >= first

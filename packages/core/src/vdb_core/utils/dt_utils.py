"""Datetime utilities."""

from datetime import UTC, datetime


def utc_now() -> datetime:
    """Get current UTC datetime with timezone info."""
    return datetime.now(UTC)

"""Mapper utilities for converting between PostgreSQL and domain types.

This module provides utilities for handling type conversions between asyncpg
database types and domain value objects.
"""

from datetime import datetime
from enum import StrEnum
from typing import TypeVar
from uuid import UUID

StatusEnumT = TypeVar("StatusEnumT", bound=StrEnum)


def to_uuid(value: object) -> UUID:
    """Convert asyncpg UUID to Python UUID.

    asyncpg returns asyncpg.pgproto.pgproto.UUID which is not compatible
    with Python's uuid.UUID. This function handles the conversion.

    Args:
        value: UUID from asyncpg (or already a Python UUID or string)

    Returns:
        Python UUID object

    Example:
        >>> row = await conn.fetchrow("SELECT id FROM libraries WHERE ...")
        >>> library_id = to_uuid(row["id"])

    """
    if isinstance(value, UUID):
        return value
    # Convert asyncpg UUID or string to Python UUID
    return UUID(str(value))


def to_uuid_str(value: object) -> str:
    """Convert asyncpg UUID to string.

    Args:
        value: UUID from asyncpg (or already a Python UUID or string)

    Returns:
        String representation of UUID

    Example:
        >>> row = await conn.fetchrow("SELECT id FROM strategies WHERE ...")
        >>> strategy_id = ChunkingStrategyId(to_uuid_str(row["id"]))

    """
    if isinstance(value, str):
        return value
    return str(value)

def to_datetime(value: object) -> datetime:
    """Convert database datetime value to Python datetime.

    Some database drivers (especially with text-based protocols) may return
    datetime values as ISO-formatted strings. This function handles conversion
    from both datetime objects and ISO datetime strings.

    Args:
        value: Datetime from database (datetime object or ISO string)

    Returns:
        Python datetime object

    Raises:
        ValueError: If string value is not a valid ISO datetime

    Example:
        >>> row = await conn.fetchrow("SELECT created_at FROM documents WHERE ...")
        >>> created_at = to_datetime(row["created_at"])

    """
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        # Parse ISO format datetime string
        return datetime.fromisoformat(value)
    msg = f"Cannot convert {type(value)} to datetime"
    raise TypeError(msg)

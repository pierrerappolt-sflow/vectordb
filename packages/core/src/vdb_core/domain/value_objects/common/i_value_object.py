"""Marker protocol for domain value objects.

This project standardizes on Pydantic v2 dataclasses for Value Objects to avoid
mixing `dataclasses.dataclass` with Pydantic `BaseModel`.

All Value Objects should use `from pydantic.dataclasses import dataclass` with
frozen=True (and slots/kw_only as needed), and SHOULD NOT inherit from a base
class. This protocol remains for typing purposes where a common VO marker is
useful.
"""

from typing import Protocol


class IValueObject(Protocol):
    """Marker protocol for all Value Objects in the domain."""


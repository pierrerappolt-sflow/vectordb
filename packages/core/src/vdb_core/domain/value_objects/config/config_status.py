"""ConfigStatus value object for vectorization config lifecycle."""

from __future__ import annotations

from enum import StrEnum, auto
from typing import final




@final
class ConfigStatusEnum(StrEnum):
    """Enum for vectorization config status values.

    Lifecycle:
    - DRAFT: Config created but not yet active (reserved for future use)
    - ACTIVE: Config is in use, can be attached to libraries
    - DEPRECATED: Config has been superseded by a new version, but still in use
    - ARCHIVED: Config is no longer in use, kept for historical reference

    Note: Currently configs are created directly as ACTIVE since users
    choose from pre-created defaults. DRAFT is reserved for future admin UI.
    """

    DRAFT = auto()
    ACTIVE = auto()
    DEPRECATED = auto()
    ARCHIVED = auto()


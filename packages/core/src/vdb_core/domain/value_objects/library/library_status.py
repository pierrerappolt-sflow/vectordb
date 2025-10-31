"""LibraryStatus value object - status of a Library entity."""

from enum import StrEnum, auto
from typing import final


@final
class LibraryStatus(StrEnum):
    """Enum for library status values."""

    ACTIVE = auto()  # Library is active and accepting documents
    ARCHIVED = auto()  # Library is archived, read-only
    DELETED = auto()  # Library marked for deletion

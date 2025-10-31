"""LibraryName value object - name for Library entities."""

from typing import final

from pydantic import Field
from pydantic.dataclasses import dataclass


@final
@dataclass(frozen=True, slots=True, config={"validate_assignment": True, "arbitrary_types_allowed": True})
class LibraryName:
    """Value object representing a Library's name.

    Constraints enforced by Pydantic Field:
    - Minimum length: 1 character
    - Maximum length: 50 characters
    """

    value: str = Field(min_length=1, max_length=50)

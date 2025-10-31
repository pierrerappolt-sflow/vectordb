"""EventLogId value object."""

from typing import final
from uuid import UUID

from pydantic.dataclasses import dataclass


@final
@dataclass(frozen=True, slots=True)
class EventLogId:
    """Value object for EventLog entity identifier."""

    value: str

    def __post_init__(self) -> None:
        """Validate that value is a valid UUID."""
        # Validate UUID format
        try:
            UUID(self.value)
        except ValueError as e:
            msg = f"Invalid UUID format: {self.value}"
            raise ValueError(msg) from e

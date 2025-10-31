"""Transaction exceptions (HTTP 500)."""

from typing import final, override

from vdb_core.domain.base import DomainException


@final
class TransactionError(DomainException):
    """Transaction commit or rollback failed (HTTP 500).

    Raised when database transactions fail due to:
    - Constraint violations
    - Deadlocks
    - Connection issues
    - Infrastructure failures

    Maps to HTTP 500 Internal Server Error.
    """

    @override
    def __init__(self, message: str) -> None:
        """Initialize transaction error.

        Args:
            message: Description of the transaction failure

        """
        super().__init__(message)

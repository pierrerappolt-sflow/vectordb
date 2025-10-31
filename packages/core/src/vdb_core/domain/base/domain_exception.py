"""Base domain exception."""


class DomainException(Exception):
    """Base exception for all domain-level errors.

    Domain exceptions represent violations of business rules and invariants
    in the domain layer. They should be caught at the application layer
    and mapped to appropriate responses at the presentation layer.

    Attributes:
        message: Human-readable error message

    """

    def __init__(self, message: str) -> None:
        """Initialize domain exception with message.

        Args:
            message: Error message describing the domain violation

        """
        self.message = message
        super().__init__(message)

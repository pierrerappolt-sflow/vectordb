"""Base application exception."""


class ApplicationException(Exception):
    """Base exception for application layer (use case) failures.

    Application exceptions represent failures in business processes and workflows
    orchestrated by use cases. They differ from domain exceptions in that they
    represent use case failures rather than domain rule violations.

    These exceptions should be caught at the presentation layer and mapped to
    appropriate HTTP status codes.

    Attributes:
        message: Human-readable error message
        details: Optional dictionary containing additional error context

    """

    def __init__(self, message: str, details: dict[str, object] | None = None) -> None:
        """Initialize application exception.

        Args:
            message: Error message describing the failure
            details: Optional dictionary with additional error context

        """
        self.message = message
        self.details = details or {}
        super().__init__(message)

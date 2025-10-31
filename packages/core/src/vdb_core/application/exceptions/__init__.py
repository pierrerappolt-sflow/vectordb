"""Application layer exceptions.

These exceptions represent failures in use cases and business workflows.
They are distinct from domain exceptions which represent business rule violations.

Exception hierarchy:
    ApplicationException (base)
    └── Used for general application failures that don't fit other categories

Domain exceptions (LibraryNotFoundError, etc.) should be re-raised or wrapped
by use cases when appropriate, but typically domain exceptions flow through
the application layer unchanged.
"""

from .base import ApplicationException

__all__ = [
    "ApplicationException",
]

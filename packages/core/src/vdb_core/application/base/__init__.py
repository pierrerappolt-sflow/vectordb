"""Base classes for application layer CQRS pattern."""

from .command import Command
from .query import Query

__all__ = ["Command", "Query"]

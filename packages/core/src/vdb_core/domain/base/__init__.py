"""Base interfaces and abstract classes for domain layer."""

from .abstract_repository import AbstractRepository
from .domain_event import DomainEvent
from .domain_exception import DomainException
from .i_entity import IEntity
from .lazy_collection import LazyCollection

__all__ = ["AbstractRepository", "DomainEvent", "DomainException", "IEntity", "LazyCollection"]

"""Library - an aggregate root collection of Documents."""

from dataclasses import dataclass

from .i_entity import IEntity


@dataclass(slots=True, kw_only=True, eq=False)
class Library(IEntity):
    """Library aggregate root."""

    name: str

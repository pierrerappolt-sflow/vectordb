"""Strategy-related repository interfaces for aggregate roots.

Defines write-side repository interfaces for strategy aggregates.
Currently includes the VectorizationConfig aggregate root.
"""

from __future__ import annotations

from abc import ABC

from vdb_core.domain.base import AbstractRepository
from vdb_core.domain.entities import VectorizationConfig
from vdb_core.domain.value_objects import VectorizationConfigId


class IVectorizationConfigRepository(
    AbstractRepository[VectorizationConfig, VectorizationConfigId], ABC
):
    """Repository interface for the VectorizationConfig aggregate root.

    Inherits standard CRUD operations, soft delete, and streaming from
    AbstractRepository. Implementations should persist associated strategy
    entities referenced by the aggregate as needed.
    """

    pass



"""VectorizationConfigId value object - unique identifier for vectorization configs."""

from typing import NewType
from uuid import UUID

VectorizationConfigId = NewType("VectorizationConfigId", UUID)

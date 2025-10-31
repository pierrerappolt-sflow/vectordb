"""ChunkingStrategyId value object - unique identifier for chunking strategies."""

from typing import NewType
from uuid import UUID

ChunkingStrategyId = NewType("ChunkingStrategyId", UUID)

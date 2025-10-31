"""EmbeddingStrategyId value object - unique identifier for embedding strategies."""

from typing import NewType
from uuid import UUID

EmbeddingStrategyId = NewType("EmbeddingStrategyId", UUID)

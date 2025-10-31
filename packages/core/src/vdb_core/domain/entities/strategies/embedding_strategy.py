"""EmbeddingStrategy entity."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from vdb_core.domain.base import IEntity
from vdb_core.domain.value_objects import EmbeddingStrategyId, ModalityType
from vdb_core.domain.value_objects.strategy import EmbeddingStrategyStatus


@dataclass(slots=True, kw_only=True, eq=False)
class EmbeddingStrategy(IEntity):
    """Defines an embedding strategy configuration (single modality)."""

    id: EmbeddingStrategyId = field(init=False)
    name: str
    model_key: str
    modality: ModalityType
    dimensions: int
    status: EmbeddingStrategyStatus
    model_name: str
    max_tokens: int | None = None
    max_image_size_bytes: int | None = None
    config: dict[str, object] = field(default_factory=dict)

    def can_embed_modality(self, modality: ModalityType) -> bool:
        # MULTIMODAL can embed all modalities
        if self.modality == ModalityType.MULTIMODAL:
            return True
        return modality.value == self.modality.value

    def __post_init__(self) -> None:
        # Validate required limits by modality
        mod = self.modality.value
        if mod == "TEXT":
            if self.max_tokens is None or self.max_tokens <= 0:
                msg = "TEXT modality requires positive max_tokens"
                raise ValueError(msg)
        if mod == "IMAGE":
            if self.max_image_size_bytes is None or self.max_image_size_bytes <= 0:
                msg = "IMAGE modality requires positive max_image_size_bytes"
                raise ValueError(msg)

        # Assign deterministic UUID v5 based on content (model_key)
        namespace = uuid.UUID("00000000-0000-0000-0000-000000000000")
        deterministic_id = uuid.uuid5(namespace, f"embedding:{self.model_key}")
        object.__setattr__(self, "id", EmbeddingStrategyId(deterministic_id))

        # Call parent __post_init__ to finalize entity initialization
        IEntity.__post_init__(self)
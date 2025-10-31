"""IEmbeddingStrategy - domain interface for embedding implementations."""

from __future__ import annotations

from typing import Protocol

from vdb_core.domain.value_objects import ModalityType


class IEmbeddingStrategy(Protocol):
    identifier: str

    @property
    def name(self) -> str:  # noqa: D401
        """Human-readable name."""

    @property
    def model_name(self) -> str:  # noqa: D401
        """Provider/model name used by implementation."""

    @property
    def modality(self) -> ModalityType:  # noqa: D401
        """Modality supported by this strategy."""

    @property
    def dimensions(self) -> int:  # noqa: D401
        """Embedding dimensionality."""

    @property
    def max_tokens(self) -> int:  # noqa: D401
        """Maximum input tokens supported."""

    def can_embed_modality(self, modality: ModalityType) -> bool:
        """Return True if this strategy can embed the given modality."""

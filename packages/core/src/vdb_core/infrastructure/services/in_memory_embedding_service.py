"""In-memory embedding service for testing and development."""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

from vdb_core.domain.value_objects import EmbedInputTypeEnum, ModalityTypeEnum

if TYPE_CHECKING:
    from vdb_core.domain.entities import EmbeddingStrategy
    from vdb_core.domain.value_objects.chunk import Chunk


class InMemoryEmbeddingService:
    """In-memory embedding service that generates deterministic fake embeddings."""

    async def generate_embedding(
        self,
        chunk: Chunk,
        strategy: EmbeddingStrategy,
        input_type: EmbedInputTypeEnum,
    ) -> tuple[float, ...]:
        if not strategy.can_embed_modality(chunk.modality):
            msg = (
                f"Strategy {strategy.name} (modality={strategy.modality.value}) "
                f"cannot embed chunk with modality={chunk.modality.value}"
            )
            raise ValueError(msg)

        dimensions = strategy.dimensions

        if chunk.modality.value == ModalityTypeEnum.TEXT:
            content_bytes = chunk.text_content.encode("utf-8")
        else:
            content_bytes = chunk.binary_content

        text_hash = hashlib.sha256(content_bytes).digest()

        vector = []
        hash_index = 0

        for _i in range(dimensions):
            if hash_index >= len(text_hash):
                text_hash = hashlib.sha256(text_hash).digest()
                hash_index = 0

            byte_value = text_hash[hash_index]
            normalized_value = (byte_value / 127.5) - 1.0
            vector.append(normalized_value)
            hash_index += 1

        magnitude = sum(x * x for x in vector) ** 0.5
        if magnitude > 0:
            vector = [x / magnitude for x in vector]

        return tuple(vector)

"""Cohere embedding service implementation."""

import base64
import logging
from typing import TYPE_CHECKING

import cohere

from vdb_core.domain.services import IEmbeddingService
from vdb_core.domain.value_objects import EmbedInputTypeEnum, ModalityTypeEnum

if TYPE_CHECKING:
    from vdb_core.domain.entities import EmbeddingStrategy
    from vdb_core.domain.value_objects.chunk import Chunk

logger = logging.getLogger(__name__)


class CohereEmbeddingService(IEmbeddingService):
    """Cohere embedding service using Cohere API."""

    def __init__(self, api_key: str | None) -> None:
        self.client = cohere.Client(api_key=api_key or None)

    async def generate_embedding(
        self,
        chunk: "Chunk",
        strategy: "EmbeddingStrategy",
        input_type: EmbedInputTypeEnum,
    ) -> tuple[float, ...]:
        # Validate that strategy can embed this chunk's modality
        if not strategy.can_embed_modality(chunk.modality):
            msg = (
                f"Strategy {strategy.name} (modality={strategy.modality.value}) "
                f"cannot embed chunk with modality={chunk.modality.value}"
            )
            raise ValueError(msg)

        # Map EmbedInputTypeEnum to Cohere's input_type parameter
        if input_type == EmbedInputTypeEnum.SEARCH:
            cohere_input_type = "search_query"
        elif input_type == EmbedInputTypeEnum.DOCUMENT:
            cohere_input_type = "search_document"
        else:
            msg = f"Unsupported input type: {input_type}"
            raise ValueError(msg)

        chunk_modality = chunk.modality.value

        if chunk_modality == ModalityTypeEnum.TEXT:
            text_content = chunk.text_content
            response = self.client.embed(
                texts=[text_content],
                model=strategy.model_name,
                input_type=cohere_input_type,
                embedding_types=["float"],
            )
            if hasattr(response.embeddings, "float_"):
                embedding = response.embeddings.float_[0]  # type: ignore[index]
            else:
                embedding = response.embeddings[0]  # type: ignore[index]

        elif chunk_modality == ModalityTypeEnum.IMAGE:
            binary_content = chunk.binary_content
            base64_image = base64.b64encode(binary_content).decode("utf-8")
            response = self.client.embed(
                images=[base64_image],
                model=strategy.model_name,
                input_type=cohere_input_type,
                embedding_types=["float"],
            )
            if hasattr(response.embeddings, "float_"):
                embedding = response.embeddings.float_[0]  # type: ignore[index]
            else:
                embedding = response.embeddings[0]  # type: ignore[index]
        else:
            msg = f"Unsupported chunk modality: {chunk_modality}"
            raise ValueError(msg)

        vector = tuple(float(x) for x in embedding)

        if len(vector) != strategy.dimensions:
            msg = f"Expected embedding dimension {strategy.dimensions}, got {len(vector)}"
            raise ValueError(msg)

        logger.debug(
            "Generated %s embedding for %s chunk using %s",
            input_type.value,
            chunk_modality.value,
            strategy.name,
        )

        return vector

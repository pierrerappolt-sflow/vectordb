"""Tests for EmbeddingStrategy entity with MULTIMODAL support."""

import pytest
from vdb_core.domain.entities.strategies import EmbeddingStrategy
from vdb_core.domain.value_objects import ModalityType, ModalityType


class TestEmbeddingStrategyMultimodal:
    """Test MULTIMODAL embedding strategy validation."""

    def test_multimodal_strategy_creation_succeeds(self) -> None:
        """MULTIMODAL embedding strategy can be created without modality-specific limits."""
        strategy = EmbeddingStrategy(
            name="Cohere Multimodal v4",
            model_key="cohere/embed-multimodal-v4.0",
            modality=ModalityType(ModalityType.MULTIMODAL),
            dimensions=1024,
            model_name="embed-multimodal-v4.0",
        )

        assert strategy.modality.value == ModalityType.MULTIMODAL
        assert strategy.max_tokens is None
        assert strategy.max_image_size_bytes is None

    def test_multimodal_strategy_can_embed_any_modality(self) -> None:
        """MULTIMODAL strategy returns True for can_embed_modality on any modality."""
        strategy = EmbeddingStrategy(
            name="Cohere Multimodal v4",
            model_key="cohere/embed-multimodal-v4.0",
            modality=ModalityType(ModalityType.MULTIMODAL),
            dimensions=1024,
            model_name="embed-multimodal-v4.0",
        )

        # MULTIMODAL can handle all modalities
        assert strategy.can_embed_modality(ModalityType.TEXT) is True
        assert strategy.can_embed_modality(ModalityType(ModalityType.IMAGE)) is True

    def test_text_strategy_only_embeds_text(self) -> None:
        """Single-modality TEXT strategy only accepts TEXT chunks."""
        strategy = EmbeddingStrategy(
            name="Cohere English v3",
            model_key="cohere/embed-english-v3.0",
            modality=ModalityType.TEXT,
            dimensions=1024,
            max_tokens=512,
            model_name="embed-english-v3.0",
        )

        # TEXT strategy only handles TEXT
        assert strategy.can_embed_modality(ModalityType.TEXT) is True
        assert strategy.can_embed_modality(ModalityType(ModalityType.IMAGE)) is False

    def test_image_strategy_only_embeds_image(self) -> None:
        """Single-modality IMAGE strategy only accepts IMAGE chunks."""
        strategy = EmbeddingStrategy(
            name="Image Embedder",
            model_key="cohere/embed-multimodal-v4.0",
            modality=ModalityType(ModalityType.IMAGE),
            dimensions=1024,
            max_image_size_bytes=10 * 1024 * 1024,
            model_name="embed-multimodal-v4.0",
        )

        # IMAGE strategy only handles IMAGE
        assert strategy.can_embed_modality(ModalityType.TEXT) is False
        assert strategy.can_embed_modality(ModalityType(ModalityType.IMAGE)) is True

    def test_text_strategy_requires_max_tokens(self) -> None:
        """TEXT modality requires max_tokens to be set."""
        with pytest.raises(ValueError, match="TEXT modality requires positive max_tokens"):
            EmbeddingStrategy(
                name="Cohere English v3",
                model_key="cohere/embed-english-v3.0",
                modality=ModalityType.TEXT,
                dimensions=1024,
                # Missing max_tokens
                model_name="embed-english-v3.0",
            )

    def test_image_strategy_requires_max_image_size_bytes(self) -> None:
        """IMAGE modality requires max_image_size_bytes to be set."""
        with pytest.raises(ValueError, match="IMAGE modality requires positive max_image_size_bytes"):
            EmbeddingStrategy(
                name="Image Embedder",
                model_key="cohere/embed-multimodal-v4.0",
                modality=ModalityType(ModalityType.IMAGE),
                dimensions=1024,
                # Missing max_image_size_bytes
                model_name="embed-multimodal-v4.0",
            )

    def test_multimodal_with_optional_limits_succeeds(self) -> None:
        """MULTIMODAL can optionally have limit fields for documentation/guidance."""
        strategy = EmbeddingStrategy(
            name="Cohere Multimodal v4",
            model_key="cohere/embed-multimodal-v4.0",
            modality=ModalityType(ModalityType.MULTIMODAL),
            dimensions=1024,
            model_name="embed-multimodal-v4.0",
            # Optional limits for documentation
            max_tokens=512,
            max_image_size_bytes=10 * 1024 * 1024,
        )

        assert strategy.modality.value == ModalityType.MULTIMODAL
        assert strategy.max_tokens == 512
        assert strategy.max_image_size_bytes == 10 * 1024 * 1024

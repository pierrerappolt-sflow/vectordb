"""Strategy resolver for mapping model keys to implementations."""

from vdb_core.domain.entities import ChunkingStrategy, EmbeddingStrategy
from vdb_core.domain.services import IChunkingStrategy, IEmbeddingStrategy
from vdb_core.domain.value_objects.strategy.model_key import (
    ChunkingModelKey,
    EmbedModelKey,
)


class StrategyResolver:
    """Resolve strategy entities to their implementation classes.

    Maps model_key from persisted entities to actual Python classes
    that implement IChunkingStrategy or IEmbeddingStrategy protocols.

    Example:
        resolver = StrategyResolver()

        # Chunking
        strategy_entity = ChunkingStrategy(model_key="recursive-text-splitter")
        impl = resolver.get_chunker(strategy_entity)  # → RecursiveTextSplitter instance

        # Embedding
        strategy_entity = EmbeddingStrategy(model_key="openai/text-embedding-3-small")
        impl = resolver.get_embedder(strategy_entity)  # → OpenAIEmbedding instance

    """

    def __init__(self) -> None:
        """Initialize resolver with empty registries."""
        self._chunking_strategies: dict[str, type[IChunkingStrategy]] = {}
        self._embedding_strategies: dict[str, type[IEmbeddingStrategy]] = {}

    def register_chunking_strategy(self, model_key: str, implementation: type[IChunkingStrategy]) -> None:
        """Register a chunking strategy implementation.

        Args:
            model_key: Unique identifier (e.g., "recursive-text-splitter")
            implementation: Class implementing IChunkingStrategy

        """
        self._chunking_strategies[model_key] = implementation

    def register_embedding_strategy(self, model_key: str, implementation: type[IEmbeddingStrategy]) -> None:
        """Register an embedding strategy implementation.

        Args:
            model_key: Unique identifier (e.g., "openai/text-embedding-3-small")
            implementation: Class implementing IEmbeddingStrategy

        """
        self._embedding_strategies[model_key] = implementation

    def get_chunker(self, strategy: ChunkingStrategy) -> IChunkingStrategy:
        """Resolve ChunkingStrategy entity to implementation instance.

        Args:
            strategy: ChunkingStrategy entity from database

        Returns:
            Instance of IChunkingStrategy implementation

        Raises:
            ValueError: If model_key not registered

        """
        impl_class = self._chunking_strategies.get(strategy.model_key)
        if not impl_class:
            msg = f"No chunking strategy registered for model_key: {strategy.model_key}"
            raise ValueError(msg)

        # Build config from strategy entity fields
        config = {
            "chunk_size_tokens": strategy.chunk_size_tokens,
            "chunk_overlap_tokens": strategy.chunk_overlap_tokens,
            "min_chunk_size_tokens": strategy.min_chunk_size_tokens,
            "max_chunk_size_tokens": strategy.max_chunk_size_tokens,
            **strategy.config,  # Merge any custom config
        }

        # Instantiate with strategy configuration
        return impl_class(config=config)  # type: ignore[call-arg]

    def get_embedder(self, strategy: EmbeddingStrategy) -> IEmbeddingStrategy:
        """Resolve EmbeddingStrategy entity to implementation instance.

        Args:
            strategy: EmbeddingStrategy entity from database

        Returns:
            Instance of IEmbeddingStrategy implementation

        Raises:
            ValueError: If model_key not registered

        """
        impl_class = self._embedding_strategies.get(strategy.model_key)
        if not impl_class:
            msg = f"No embedding strategy registered for model_key: {strategy.model_key}"
            raise ValueError(msg)

        # Pass the strategy's config dict to implementation
        return impl_class(config=strategy.config)  # type: ignore[call-arg]


# Global resolver instance (singleton pattern)
_resolver: StrategyResolver | None = None


def get_strategy_resolver() -> StrategyResolver:
    """Get the global strategy resolver instance.

    Returns:
        Singleton StrategyResolver instance

    """
    global _resolver
    if _resolver is None:
        _resolver = StrategyResolver()

        # Register available strategy implementations
        from vdb_core.infrastructure.strategies.chunking import CohereTokenChunker
        from vdb_core.infrastructure.strategies.embedding import (
            CohereEnglishLightV3Strategy,
            CohereEnglishV3Strategy,
            CohereMultilingualLightV3Strategy,
            CohereMultilingualV3Strategy,
            CohereMultimodalV4Strategy,
        )

        # Register chunking strategies (same implementation, different config)
        _resolver.register_chunking_strategy(ChunkingModelKey.COHERE_TOKEN_256.value, CohereTokenChunker)
        _resolver.register_chunking_strategy(ChunkingModelKey.COHERE_TOKEN_1024.value, CohereTokenChunker)

        # Register Cohere v3 embedding strategies
        _resolver.register_embedding_strategy(EmbedModelKey.EMBED_ENGLISH_V3.value, CohereEnglishV3Strategy)
        _resolver.register_embedding_strategy(EmbedModelKey.EMBED_MULTILINGUAL_V3.value, CohereMultilingualV3Strategy)
        _resolver.register_embedding_strategy(EmbedModelKey.EMBED_ENGLISH_LIGHT_V3.value, CohereEnglishLightV3Strategy)
        _resolver.register_embedding_strategy(EmbedModelKey.EMBED_MULTILINGUAL_LIGHT_V3.value, CohereMultilingualLightV3Strategy)

        # Register Cohere v4 embedding strategies
        _resolver.register_embedding_strategy(EmbedModelKey.EMBED_MULTIMODAL_V4.value, CohereMultimodalV4Strategy)

    return _resolver

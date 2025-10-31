"""StrategyResolver - resolves strategy identifiers to implementations.

The resolver acts as a registry that maps string identifiers to concrete
strategy implementations. It's configured at application startup and used
throughout the application layer to resolve strategies.

Architecture:
    Domain Layer: Stores string IDs (e.g., "openai/text-embedding-3-small")
    Infrastructure Layer: Concrete implementations (OpenAITextEmbedding3Small)
    StrategyResolver: Bridges them (resolves string ID → implementation)

Example:
    # Setup (at application startup)
    resolver = StrategyResolver()
    resolver.register_embedding_strategy(
        OpenAITextEmbedding3Small(api_key=config.openai_api_key)
    )
    resolver.register_chunking_strategy(
        SentenceSplitChunker(max_chunk_size=512)
    )

    # Usage (in application services)
    config = VectorizationConfig(
        embedding_strategy_id="openai/text-embedding-3-small",
        chunking_strategies={ModalityType.TEXT: "sentence-split"}
    )

    embedding_impl = resolver.get_embedding_strategy(config.embedding_strategy_id)
    vector = await embedding_impl.embed([chunk.content], input_type="search_document")

"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

if TYPE_CHECKING:
    from vdb_core.domain.services import IChunkingStrategy, IEmbeddingStrategy


@final
class StrategyResolver:
    """Resolves strategy identifiers to concrete implementations.

    This class maintains registries of strategy implementations and provides
    lookup methods to resolve string identifiers to actual implementations.

    Each strategy implementation defines its own identifier via the `identifier`
    property, which is used as the key in the registry.

    Thread-safety: This class is not thread-safe. It should be configured
    at application startup before being used concurrently.
    """

    def __init__(self) -> None:
        """Initialize empty strategy registries."""
        self._embedding_strategies: dict[str, IEmbeddingStrategy] = {}
        self._chunking_strategies: dict[str, IChunkingStrategy] = {}

    def register_embedding_strategy(self, strategy: IEmbeddingStrategy) -> None:
        """Register an embedding strategy by its identifier.

        Args:
            strategy: The embedding strategy implementation to register

        Raises:
            ValueError: If a strategy with the same identifier is already registered

        Example:
            openai_small = OpenAITextEmbedding3Small(api_key="...")
            resolver.register_embedding_strategy(openai_small)
            # Now available via: resolver.get_embedding_strategy("openai/text-embedding-3-small")

        """
        identifier = strategy.identifier
        if identifier in self._embedding_strategies:
            msg = f"Embedding strategy '{identifier}' is already registered"
            raise ValueError(msg)

        self._embedding_strategies[identifier] = strategy

    def register_chunking_strategy(self, strategy: IChunkingStrategy) -> None:
        """Register a chunking strategy by its identifier.

        Args:
            strategy: The chunking strategy implementation to register

        Raises:
            ValueError: If a strategy with the same identifier is already registered

        Example:
            sentence_split = SentenceSplitChunker(max_chunk_size=512)
            resolver.register_chunking_strategy(sentence_split)
            # Now available via: resolver.get_chunking_strategy("sentence-split")

        """
        identifier = strategy.identifier
        if identifier in self._chunking_strategies:
            msg = f"Chunking strategy '{identifier}' is already registered"
            raise ValueError(msg)

        self._chunking_strategies[identifier] = strategy

    def get_embedding_strategy(self, identifier: str) -> IEmbeddingStrategy:
        """Resolve embedding strategy from identifier.

        Args:
            identifier: The strategy identifier string (e.g., "openai/text-embedding-3-small")

        Returns:
            The registered embedding strategy implementation

        Raises:
            ValueError: If no strategy is registered with this identifier

        Example:
            config = VectorizationConfig(embedding_strategy_id="openai/text-embedding-3-small")
            strategy = resolver.get_embedding_strategy(config.embedding_strategy_id)
            vector = await strategy.embed(["hello world"], input_type="search_document")

        """
        if identifier not in self._embedding_strategies:
            available = ", ".join(self._embedding_strategies.keys())
            msg = f"Unknown embedding strategy: '{identifier}'. Available strategies: {available or 'none'}"
            raise ValueError(msg)

        return self._embedding_strategies[identifier]

    def get_chunking_strategy(self, identifier: str) -> IChunkingStrategy:
        """Resolve chunking strategy from identifier.

        Args:
            identifier: The strategy identifier string (e.g., "sentence-split")

        Returns:
            The registered chunking strategy implementation

        Raises:
            ValueError: If no strategy is registered with this identifier

        Example:
            config = VectorizationConfig(
                chunking_strategies={ModalityType.TEXT: "sentence-split"}
            )
            strategy_id = config.get_chunker_for_modality(ModalityType.TEXT)
            strategy = resolver.get_chunking_strategy(strategy_id)
            chunks = strategy.chunk("hello world")

        """
        if identifier not in self._chunking_strategies:
            available = ", ".join(self._chunking_strategies.keys())
            msg = f"Unknown chunking strategy: '{identifier}'. Available strategies: {available or 'none'}"
            raise ValueError(msg)

        return self._chunking_strategies[identifier]

    def list_embedding_strategies(self) -> list[str]:
        """List all registered embedding strategy identifiers.

        Returns:
            List of registered embedding strategy identifiers

        Example:
            identifiers = resolver.list_embedding_strategies()
            # ["openai/text-embedding-3-small", "openai/text-embedding-3-large", "cohere/embed-v3"]

        """
        return list(self._embedding_strategies.keys())

    def list_chunking_strategies(self) -> list[str]:
        """List all registered chunking strategy identifiers.

        Returns:
            List of registered chunking strategy identifiers

        Example:
            identifiers = resolver.list_chunking_strategies()
            # ["sentence-split", "semantic-v2", "recursive", "fixed"]

        """
        return list(self._chunking_strategies.keys())

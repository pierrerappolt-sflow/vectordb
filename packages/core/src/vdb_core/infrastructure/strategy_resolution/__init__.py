"""Strategy resolution for mapping entity configurations to implementations.

The StrategyResolver maps strategy entities (from the database) to their
concrete implementations that actually perform chunking and embedding.

Usage:
    from vdb_core.infrastructure.strategy_resolution import get_strategy_resolver

    # Get the global resolver (auto-registers all strategies)
    resolver = get_strategy_resolver()

    # Resolve a ChunkingStrategy entity to its implementation
    chunker = resolver.get_chunker(chunking_strategy_entity)
    chunks = chunker.chunk("Hello world...")

    # Resolve an EmbeddingStrategy entity to its implementation
    embedder = resolver.get_embedder(embedding_strategy_entity)
    vector = await embedder.embed(["Hello world"], input_type="search_document")
"""

from .strategy_resolver import StrategyResolver, get_strategy_resolver

__all__ = [
    "StrategyResolver",
    "get_strategy_resolver",
]

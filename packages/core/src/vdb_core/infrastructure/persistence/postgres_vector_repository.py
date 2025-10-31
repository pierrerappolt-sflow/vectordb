"""PostgreSQL vector repository with pgvector support."""

from __future__ import annotations

from typing import TYPE_CHECKING

from vdb_core.domain.repositories import IEmbeddingReadRepository

if TYPE_CHECKING:
    import asyncpg

    from vdb_core.domain.value_objects import Embedding, EmbeddingId, LibraryId, VectorIndexingStrategy


class PostgresVectorRepository(IEmbeddingReadRepository):
    """PostgreSQL repository for vector storage using pgvector extension.

    Uses pgvector's native vector operations and indexing:
    - HNSW index for fast approximate nearest neighbor search
    - Cosine distance operator: <=>
    - Inner product operator: <#>
    - L2 distance operator: <->

    Database schema:
        CREATE TABLE embeddings (
            id TEXT PRIMARY KEY,
            chunk_id TEXT NOT NULL,
            library_id UUID NOT NULL,
            strategy TEXT NOT NULL,
            vector VECTOR(1536) NOT NULL,  -- dimension varies by strategy
            created_at TIMESTAMP DEFAULT NOW()
        );

        CREATE INDEX ON embeddings USING hnsw (vector vector_cosine_ops);
    """

    def __init__(self, pool: asyncpg.Pool) -> None:
        """Initialize repository with database connection pool.

        Args:
            pool: AsyncPG connection pool

        """
        self.pool = pool

    async def add_embeddings(
        self,
        embeddings: list[Embedding],
        library_id: LibraryId,
    ) -> None:
        """Add multiple embeddings to the vector index.

        Args:
            embeddings: List of embeddings to index
            library_id: Library these embeddings belong to

        """
        if not embeddings:
            return

        # Prepare batch insert data
        records = [
            (
                str(emb.embedding_id),
                str(emb.chunk_id),
                str(library_id),
                str(emb.embedding_strategy_id),
                list(emb.vector),  # Convert tuple to list for pgvector
            )
            for emb in embeddings
        ]

        async with self.pool.acquire() as conn:
            # Use COPY for bulk insert (fastest)
            await conn.executemany(
                """
                INSERT INTO embeddings (id, chunk_id, library_id, strategy, vector)
                VALUES ($1, $2, $3, $4, $5::vector)
                ON CONFLICT (id) DO UPDATE SET
                    chunk_id = EXCLUDED.chunk_id,
                    library_id = EXCLUDED.library_id,
                    strategy = EXCLUDED.strategy,
                    vector = EXCLUDED.vector
                """,
                records,
            )

    async def remove_embeddings(
        self,
        embedding_ids: list[EmbeddingId],
        library_id: LibraryId,
    ) -> None:
        """Remove multiple embeddings from the vector index.

        Args:
            embedding_ids: IDs of embeddings to remove
            library_id: Library to remove embeddings from

        """
        if not embedding_ids:
            return

        ids = [str(emb_id) for emb_id in embedding_ids]

        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                DELETE FROM embeddings
                WHERE id = ANY($1::text[])
                AND library_id = $2
                """,
                ids,
                str(library_id),
            )

    async def search_similar(
        self,
        query_vector: tuple[float, ...],
        library_id: LibraryId,
        top_k: int,
        strategy: VectorIndexingStrategy,
    ) -> list[tuple[Embedding, float]]:
        """Search for similar embeddings using pgvector.

        Uses pgvector's cosine distance operator (<=>).
        Results are ordered by similarity (lower distance = higher similarity).

        Args:
            query_vector: The vector to find similar embeddings for
            library_id: Library to search within
            top_k: Maximum number of results to return
            strategy: Vector indexing strategy (uses pgvector's cosine distance regardless)

        Returns:
            List of (embedding, similarity_score) tuples

        """
        from vdb_core.domain.value_objects import ChunkId, Embedding

        # Convert query vector to list for pgvector
        query_vector_list = list(query_vector)

        async with self.pool.acquire() as conn:
            # Use pgvector's cosine distance operator
            # Lower distance = more similar
            # We convert to similarity score: 1 - distance
            rows = await conn.fetch(
                """
                SELECT
                    id,
                    chunk_id,
                    strategy,
                    vector,
                    (1 - (vector <=> $1::vector)) AS similarity
                FROM embeddings
                WHERE library_id = $2
                ORDER BY vector <=> $1::vector
                LIMIT $3
                """,
                query_vector_list,
                str(library_id),
                top_k,
            )

        # Convert rows to Embedding entities
        results = []
        for row in rows:
            # Parse strategy enum
            strategy_enum = EmbeddingStrategyEnum(row["strategy"])  # type: ignore[name-defined]
            embedding_strategy = EmbeddingStrategy(value=strategy_enum)  # type: ignore[name-defined]

            # Create embedding entity
            embedding = Embedding(  # type: ignore[call-arg]
                id=EmbeddingId(row["id"]),
                chunk_id=ChunkId(row["chunk_id"]),
                strategy=embedding_strategy,
                vector=tuple(row["vector"]),
            )

            similarity_score = float(row["similarity"])
            results.append((embedding, similarity_score))

        return results

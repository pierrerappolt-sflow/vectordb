-- Schema for embeddings stored as JSONB arrays
-- No pgvector required - simple storage with JSONB

-- ==================================================================
-- 1. EMBEDDING METADATA + VECTORS
-- ==================================================================

CREATE TABLE IF NOT EXISTS embeddings (
    id UUID PRIMARY KEY,
    chunk_id UUID NOT NULL,
    library_id UUID NOT NULL,
    embedding_strategy_id UUID NOT NULL,
    vectorization_config_id UUID NOT NULL,
    dimensions INT NOT NULL,

    -- Embedding vector stored as JSONB array of floats
    vector JSONB NOT NULL,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_embeddings_library
    ON embeddings(library_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_strategy
    ON embeddings(embedding_strategy_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_chunk
    ON embeddings(chunk_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_dimensions
    ON embeddings(dimensions);

-- GIN index on vector JSONB for fast lookups (optional)
CREATE INDEX IF NOT EXISTS idx_embeddings_vector
    ON embeddings USING GIN(vector);

-- ==================================================================
-- USAGE EXAMPLE
-- ==================================================================

-- Insert embedding
-- INSERT INTO embeddings (id, chunk_id, library_id, embedding_strategy_id, vectorization_config_id, dimensions, vector)
-- VALUES (
--     'uuid',
--     'chunk-uuid',
--     'lib-uuid',
--     'strategy-uuid',
--     'config-uuid',
--     1536,
--     '[0.1, 0.2, 0.3, ..., 0.5]'::jsonb
-- );

-- Retrieve embedding
-- SELECT id, chunk_id, vector
-- FROM embeddings
-- WHERE library_id = 'lib-uuid'
--   AND dimensions = 1536;

-- ==================================================================
-- NOTES
-- ==================================================================

-- 1. Vector similarity search must be done in application layer
--    - Fetch candidate embeddings from database
--    - Calculate cosine similarity / L2 distance in Python
--    - Sort and return top-k results

-- 2. For large datasets, consider:
--    - Approximate nearest neighbors (ANN) libraries like FAISS, Annoy
--    - Vector databases like Qdrant, Weaviate, Pinecone
--    - Elasticsearch with vector search plugin

-- 3. JSONB array format:
--    - Stored as: [0.123, -0.456, 0.789, ...]
--    - Retrieved as: Python list via json.loads()

-- 4. Performance considerations:
--    - JSONB is efficient for storage/retrieval
--    - No native vector distance operators
--    - Sequential scan required for similarity search
--    - Acceptable for small-to-medium datasets (<100k vectors)

-- Log success
DO $$
BEGIN
    RAISE NOTICE 'Step 2: Embeddings table initialized (JSONB storage, no pgvector)';
END $$;

-- Migration 008: Create embeddings table for vector storage
--
-- This migration creates the embeddings table that stores vector embeddings
-- for chunks, enabling vector similarity search

-- Enable pgvector extension if not already enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- Embeddings table (vector representations of chunks)
CREATE TABLE IF NOT EXISTS embeddings (
    id UUID PRIMARY KEY,
    chunk_id UUID NOT NULL,
    library_id UUID NOT NULL REFERENCES libraries(id) ON DELETE CASCADE,
    vectorization_config_id UUID NOT NULL REFERENCES vectorization_configs(id) ON DELETE CASCADE,
    vector vector(1536) NOT NULL,  -- Default dimension for many models, can be changed
    dimensions INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for efficient querying
CREATE INDEX idx_embeddings_chunk_id ON embeddings(chunk_id);
CREATE INDEX idx_embeddings_library_id ON embeddings(library_id);
CREATE INDEX idx_embeddings_vectorization_config_id ON embeddings(vectorization_config_id);

-- Index for vector similarity search (using HNSW algorithm)
CREATE INDEX idx_embeddings_vector_cosine ON embeddings USING hnsw (vector vector_cosine_ops);
CREATE INDEX idx_embeddings_vector_l2 ON embeddings USING hnsw (vector vector_l2_ops);
CREATE INDEX idx_embeddings_vector_ip ON embeddings USING hnsw (vector vector_ip_ops);

-- Comments for documentation
COMMENT ON TABLE embeddings IS 'Vector embeddings of chunks for similarity search';
COMMENT ON COLUMN embeddings.vector IS 'Vector representation of the chunk content';
COMMENT ON COLUMN embeddings.dimensions IS 'Number of dimensions in the vector';
COMMENT ON COLUMN embeddings.vectorization_config_id IS 'Configuration used to generate this embedding';

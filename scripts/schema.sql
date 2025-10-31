-- VectorDB PostgreSQL Schema
-- Requires pgvector extension

-- Enable pgvector extension (already done in init-db.sql)
CREATE EXTENSION IF NOT EXISTS vector;

-- ==================== Libraries ====================

CREATE TABLE IF NOT EXISTS libraries (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',
    modality_type VARCHAR(50) NOT NULL DEFAULT 'TEXT',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_libraries_status ON libraries(status);
CREATE INDEX idx_libraries_created_at ON libraries(created_at DESC);

-- ==================== Documents ====================

CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY,
    library_id UUID NOT NULL REFERENCES libraries(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    upload_complete BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_documents_library_id ON documents(library_id);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_created_at ON documents(created_at DESC);

-- ==================== Document Fragments ====================

CREATE TABLE IF NOT EXISTS document_fragments (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    sequence_number INTEGER NOT NULL,
    start_index BIGINT NOT NULL,
    end_index BIGINT NOT NULL,
    size_bytes BIGINT NOT NULL,
    storage_reference TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    is_final BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_fragments_document_id ON document_fragments(document_id);
CREATE INDEX idx_fragments_sequence ON document_fragments(document_id, sequence_number);
CREATE UNIQUE INDEX idx_fragments_unique_seq ON document_fragments(document_id, sequence_number);

-- ==================== Chunks ====================

CREATE TABLE IF NOT EXISTS chunks (
    id TEXT PRIMARY KEY,  -- Deterministic: sha1(document_id + strategy + start + end + text)
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunking_strategy VARCHAR(50) NOT NULL,  -- ChunkingStrategyEnum value
    start_index INTEGER NOT NULL,
    end_index INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_chunks_document_id ON chunks(document_id);
CREATE INDEX idx_chunks_strategy ON chunks(chunking_strategy);
CREATE INDEX idx_chunks_status ON chunks(status);
CREATE INDEX idx_chunks_document_strategy ON chunks(document_id, chunking_strategy);

-- ==================== Embeddings (Vector Storage) ====================

-- Table for storing embeddings with pgvector
-- Note: Vector dimensions vary by strategy (1536, 3072, 1024)
-- We use the maximum dimension (3072) and pad smaller vectors
CREATE TABLE IF NOT EXISTS embeddings (
    id TEXT PRIMARY KEY,
    chunk_id TEXT NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
    library_id UUID NOT NULL REFERENCES libraries(id) ON DELETE CASCADE,
    strategy TEXT NOT NULL,  -- EmbeddingStrategyEnum value
    dimensions INTEGER NOT NULL,  -- Actual dimensions used
    vector VECTOR(3072) NOT NULL,  -- Max dimension, smaller vectors are padded
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes for fast lookups
CREATE INDEX idx_embeddings_chunk_id ON embeddings(chunk_id);
CREATE INDEX idx_embeddings_library_id ON embeddings(library_id);
CREATE INDEX idx_embeddings_strategy ON embeddings(strategy);

-- HNSW index for fast approximate nearest neighbor search
-- Using cosine distance (best for normalized embeddings)
CREATE INDEX idx_embeddings_vector_hnsw ON embeddings
USING hnsw (vector vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Alternative: IVFFlat index (less memory, slightly slower)
-- CREATE INDEX idx_embeddings_vector_ivfflat ON embeddings
-- USING ivfflat (vector vector_cosine_ops)
-- WITH (lists = 100);

-- ==================== Pipelines ====================

CREATE TABLE IF NOT EXISTS library_document_pipelines (
    id UUID PRIMARY KEY,
    library_id UUID NOT NULL REFERENCES libraries(id) ON DELETE CASCADE,
    modality_type VARCHAR(50) NOT NULL,
    chunking_strategies JSONB NOT NULL,  -- Map of modality -> strategy
    embedding_strategy TEXT NOT NULL,
    vector_indexing_strategy TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_pipelines_library_id ON library_document_pipelines(library_id);

-- ==================== Message Queue (for MessageBus) ====================

CREATE TABLE IF NOT EXISTS message_queue (
    id BIGSERIAL PRIMARY KEY,
    event_type VARCHAR(255) NOT NULL,
    aggregate_id TEXT NOT NULL,
    payload JSONB NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',  -- PENDING, PROCESSING, COMPLETED, FAILED
    worker_id TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    max_retries INTEGER NOT NULL DEFAULT 3,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_message_queue_status ON message_queue(status);
CREATE INDEX idx_message_queue_event_type ON message_queue(event_type);
CREATE INDEX idx_message_queue_created_at ON message_queue(created_at);
CREATE INDEX idx_message_queue_processing ON message_queue(status, created_at) WHERE status = 'PENDING';

-- ==================== Search Query Tracking ====================

CREATE TABLE IF NOT EXISTS search_queries (
    id UUID PRIMARY KEY,
    library_id UUID NOT NULL REFERENCES libraries(id) ON DELETE CASCADE,
    query_text TEXT NOT NULL,
    workflow_id TEXT,  -- Temporal workflow ID
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',  -- PENDING, PROCESSING, COMPLETED, FAILED
    top_k INTEGER NOT NULL,
    result_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_search_queries_library_id ON search_queries(library_id);
CREATE INDEX idx_search_queries_workflow_id ON search_queries(workflow_id);
CREATE INDEX idx_search_queries_status ON search_queries(status);
CREATE INDEX idx_search_queries_created_at ON search_queries(created_at DESC);

-- ==================== Utility Functions ====================

-- Function to update updated_at timestamp automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for automatic updated_at
CREATE TRIGGER update_libraries_updated_at BEFORE UPDATE ON libraries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_chunks_updated_at BEFORE UPDATE ON chunks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_embeddings_updated_at BEFORE UPDATE ON embeddings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pipelines_updated_at BEFORE UPDATE ON library_document_pipelines
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==================== Vacuum and Analyze ====================

-- Optimize tables for pgvector
VACUUM ANALYZE embeddings;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO vdbuser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO vdbuser;

-- Migration 001: Create domain tables for Library aggregate
--
-- This migration creates the core domain entity tables that map to our domain model

-- Libraries table (aggregate root)
CREATE TABLE IF NOT EXISTS libraries (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_libraries_name ON libraries(name);
CREATE INDEX idx_libraries_status ON libraries(status);

-- Documents table (entity within library aggregate)
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY,
    library_id UUID NOT NULL REFERENCES libraries(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    upload_complete BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_documents_library_id ON documents(library_id);
CREATE INDEX idx_documents_name ON documents(name);
CREATE INDEX idx_documents_status ON documents(status);

-- Document fragments table (streaming upload chunks)
CREATE TABLE IF NOT EXISTS document_fragments (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    sequence_number INTEGER NOT NULL,
    content BYTEA NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    is_final BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_document_fragments_document_id ON document_fragments(document_id);
CREATE INDEX idx_document_fragments_content_hash ON document_fragments(content_hash);

-- Extracted contents table (parsed content from fragments)
CREATE TABLE IF NOT EXISTS extracted_contents (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    modality_type VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_extracted_contents_document_id ON extracted_contents(document_id);
CREATE INDEX idx_extracted_contents_modality_type ON extracted_contents(modality_type);
CREATE INDEX idx_extracted_contents_content_hash ON extracted_contents(content_hash);

-- Chunks table (chunked content ready for embedding)
CREATE TABLE IF NOT EXISTS chunks (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunking_strategy_id UUID NOT NULL,
    extracted_content_id UUID NOT NULL,
    sequence_number INTEGER NOT NULL,
    content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    modality_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_chunks_document_id ON chunks(document_id);
CREATE INDEX idx_chunks_chunking_strategy_id ON chunks(chunking_strategy_id);
CREATE INDEX idx_chunks_extracted_content_id ON chunks(extracted_content_id);
CREATE INDEX idx_chunks_content_hash ON chunks(content_hash);
CREATE INDEX idx_chunks_modality_type ON chunks(modality_type);

-- Vectorization configs table (library-scoped processing configs)
-- NOTE: This table is recreated in migration 002
CREATE TABLE IF NOT EXISTS vectorization_configs (
    id UUID PRIMARY KEY,
    library_id UUID NOT NULL REFERENCES libraries(id) ON DELETE CASCADE,
    chunking_strategy_id UUID NOT NULL,
    embedding_strategy_id UUID NOT NULL,
    modality_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_vectorization_configs_library_id ON vectorization_configs(library_id);
CREATE INDEX idx_vectorization_configs_chunking_strategy_id ON vectorization_configs(chunking_strategy_id);
CREATE INDEX idx_vectorization_configs_embedding_strategy_id ON vectorization_configs(embedding_strategy_id);
CREATE INDEX idx_vectorization_configs_modality_type ON vectorization_configs(modality_type);

-- Comments for documentation
COMMENT ON TABLE libraries IS 'Library aggregate root - collection of documents and processing configs';
COMMENT ON TABLE documents IS 'Document entity - part of library aggregate';
COMMENT ON TABLE document_fragments IS 'Document fragments - streamed upload chunks';
COMMENT ON TABLE extracted_contents IS 'Extracted content - parsed text/data from document fragments';
COMMENT ON TABLE chunks IS 'Chunks - split content ready for embedding';
COMMENT ON TABLE vectorization_configs IS 'Vectorization configs - library-scoped processing strategies';

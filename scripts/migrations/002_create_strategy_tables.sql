-- Migration 002: Create strategy tables for vectorization configuration
--
-- This migration creates the chunking_strategies and embedding_strategies tables,
-- and updates vectorization_configs to support multiple strategies per modality.

-- ==================== Chunking Strategies ====================

CREATE TABLE IF NOT EXISTS chunking_strategies (
    id UUID PRIMARY KEY,
    library_id UUID NOT NULL REFERENCES libraries(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    model_key VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'beta',
    modality VARCHAR(50) NOT NULL,
    behavior VARCHAR(50) NOT NULL,

    -- SPLIT behavior params (TEXT)
    chunk_size_tokens INTEGER,
    chunk_overlap_tokens INTEGER,
    min_chunk_size_tokens INTEGER,
    max_chunk_size_tokens INTEGER,

    -- PASSTHROUGH behavior params (IMAGE)
    max_content_size_bytes INTEGER,
    max_width_pixels INTEGER,
    max_height_pixels INTEGER,

    -- FRAME_EXTRACT behavior params (VIDEO)
    frame_sample_rate_fps REAL,
    max_frames INTEGER,
    max_video_duration_seconds INTEGER,

    -- TIME_SEGMENT behavior params (AUDIO)
    segment_duration_seconds REAL,
    segment_overlap_seconds REAL,
    max_audio_duration_seconds INTEGER,

    -- Implementation-specific config
    config JSONB NOT NULL DEFAULT '{}'::JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_chunking_strategies_library_id ON chunking_strategies(library_id);
CREATE INDEX idx_chunking_strategies_modality ON chunking_strategies(modality);
CREATE INDEX idx_chunking_strategies_status ON chunking_strategies(status);

COMMENT ON TABLE chunking_strategies IS 'Chunking strategies for document processing - scoped to library';
COMMENT ON COLUMN chunking_strategies.modality IS 'Single modality type: TEXT, IMAGE, VIDEO, AUDIO';
COMMENT ON COLUMN chunking_strategies.behavior IS 'Chunking behavior: SPLIT, PASSTHROUGH, FRAME_EXTRACT, TIME_SEGMENT';

-- ==================== Embedding Strategies ====================

CREATE TABLE IF NOT EXISTS embedding_strategies (
    id UUID PRIMARY KEY,
    library_id UUID NOT NULL REFERENCES libraries(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    model_key VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'beta',
    modality VARCHAR(50) NOT NULL,

    -- Common metadata
    dimensions INTEGER NOT NULL,
    provider VARCHAR(255) NOT NULL,
    model_name VARCHAR(255) NOT NULL,

    -- TEXT: token limit
    max_tokens INTEGER,

    -- IMAGE/VIDEO: size limits
    max_image_size_bytes INTEGER,
    max_width_pixels INTEGER,
    max_height_pixels INTEGER,

    -- AUDIO: duration limit
    max_audio_duration_seconds REAL,

    -- Implementation-specific config
    config JSONB NOT NULL DEFAULT '{}'::JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_embedding_strategies_library_id ON embedding_strategies(library_id);
CREATE INDEX idx_embedding_strategies_modality ON embedding_strategies(modality);
CREATE INDEX idx_embedding_strategies_status ON embedding_strategies(status);
CREATE INDEX idx_embedding_strategies_model_key ON embedding_strategies(model_key);

COMMENT ON TABLE embedding_strategies IS 'Embedding strategies for vector generation - scoped to library';
COMMENT ON COLUMN embedding_strategies.modality IS 'Single modality type: TEXT, IMAGE, VIDEO, AUDIO';

-- ==================== Update Vectorization Configs ====================

-- Drop the old vectorization_configs table
DROP TABLE IF EXISTS vectorization_configs CASCADE;

-- Recreate with support for multiple strategies
CREATE TABLE IF NOT EXISTS vectorization_configs (
    id UUID PRIMARY KEY,
    library_id UUID NOT NULL REFERENCES libraries(id) ON DELETE CASCADE,

    -- Arrays of strategy IDs (one per modality)
    chunking_strategy_ids UUID[] NOT NULL DEFAULT ARRAY[]::UUID[],
    embedding_strategy_ids UUID[] NOT NULL DEFAULT ARRAY[]::UUID[],

    -- Indexing configuration
    vector_indexing_strategy VARCHAR(50) NOT NULL DEFAULT 'HNSW',
    vector_similarity_metric VARCHAR(50) NOT NULL DEFAULT 'COSINE',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT check_at_least_one_chunking_strategy CHECK (array_length(chunking_strategy_ids, 1) > 0),
    CONSTRAINT check_at_least_one_embedding_strategy CHECK (array_length(embedding_strategy_ids, 1) > 0)
);

CREATE INDEX idx_vectorization_configs_library_id ON vectorization_configs(library_id);
CREATE INDEX idx_vectorization_configs_chunking_strategy_ids ON vectorization_configs USING GIN(chunking_strategy_ids);
CREATE INDEX idx_vectorization_configs_embedding_strategy_ids ON vectorization_configs USING GIN(embedding_strategy_ids);

COMMENT ON TABLE vectorization_configs IS 'Vectorization configuration - maps strategies to library processing pipeline';
COMMENT ON COLUMN vectorization_configs.chunking_strategy_ids IS 'Array of chunking strategy IDs - one per modality';
COMMENT ON COLUMN vectorization_configs.embedding_strategy_ids IS 'Array of embedding strategy IDs - one per modality';
COMMENT ON COLUMN vectorization_configs.vector_indexing_strategy IS 'Vector index type: HNSW, IVF, FLAT, PQ';
COMMENT ON COLUMN vectorization_configs.vector_similarity_metric IS 'Similarity metric: COSINE, L2, DOT_PRODUCT, L1';

-- Log success
DO $$
BEGIN
    RAISE NOTICE 'Migration 002: Created chunking_strategies, embedding_strategies, and updated vectorization_configs tables';
END $$;

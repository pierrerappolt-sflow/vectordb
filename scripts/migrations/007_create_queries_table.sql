-- Create queries table for tracking semantic search queries
-- Stores query metadata and results (as ordered chunk IDs)

CREATE TABLE IF NOT EXISTS queries (
    id UUID PRIMARY KEY,
    library_id UUID NOT NULL REFERENCES libraries(id) ON DELETE CASCADE,
    config_id UUID NOT NULL REFERENCES vectorization_configs(id) ON DELETE CASCADE,
    query_text TEXT NOT NULL,
    top_k INTEGER NOT NULL DEFAULT 10,
    status TEXT NOT NULL CHECK (status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')),

    -- Store results as JSONB array with chunk_id and score (populated when COMPLETED)
    -- Format: [{"chunk_id": "...", "score": 0.95}, ...]
    results JSONB DEFAULT NULL,
    result_count INTEGER DEFAULT 0,

    -- Error info if FAILED
    error_message TEXT DEFAULT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ DEFAULT NULL
);

-- Index for listing queries by library
CREATE INDEX idx_queries_library_id ON queries(library_id);

-- Index for filtering by status
CREATE INDEX idx_queries_status ON queries(status);

-- Index for time-based queries
CREATE INDEX idx_queries_created_at ON queries(created_at DESC);

-- Trigger to update updated_at
CREATE OR REPLACE FUNCTION update_queries_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_queries_updated_at
    BEFORE UPDATE ON queries
    FOR EACH ROW
    EXECUTE FUNCTION update_queries_updated_at();

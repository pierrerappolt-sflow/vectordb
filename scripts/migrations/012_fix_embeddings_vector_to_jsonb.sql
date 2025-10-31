-- Migration 012: Fix embeddings vector column to use JSONB instead of pgvector
--
-- Issue: Migration 008 used vector(1536) type, but code expects JSONB
-- This caused errors when inserting variable-dimension embeddings (384d, 1024d)
--
-- Changes:
-- 1. Drop pgvector HNSW indexes (incompatible with JSONB)
-- 2. Change vector column from vector(1536) to JSONB
-- 3. Add GIN index for JSONB (matches local dev setup)

BEGIN;

-- Drop pgvector indexes
DROP INDEX IF EXISTS idx_embeddings_vector_cosine CASCADE;
DROP INDEX IF EXISTS idx_embeddings_vector_l2 CASCADE;
DROP INDEX IF EXISTS idx_embeddings_vector_ip CASCADE;

-- Change vector column to JSONB to support variable dimensions
-- Note: Table is empty in production, so safe to convert
ALTER TABLE embeddings ALTER COLUMN vector TYPE JSONB USING '[]'::jsonb;

-- Add GIN index for JSONB (like local dev)
CREATE INDEX IF NOT EXISTS idx_embeddings_vector ON embeddings USING GIN(vector);

COMMIT;

-- Log success
DO $$
BEGIN
    RAISE NOTICE 'Migration 012: Fixed embeddings.vector column to JSONB';
    RAISE NOTICE '  - Dropped pgvector HNSW indexes';
    RAISE NOTICE '  - Changed vector(1536) -> JSONB';
    RAISE NOTICE '  - Added GIN index on vector JSONB column';
    RAISE NOTICE '  - Now supports variable dimensions (384d, 1024d, etc)';
END $$;

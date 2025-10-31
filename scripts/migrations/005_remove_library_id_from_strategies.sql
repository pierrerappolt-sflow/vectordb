-- Migration 005: Remove library_id from strategy tables
--
-- This migration makes chunking_strategies and embedding_strategies
-- reusable across libraries by removing the library_id foreign key.
-- Strategies are now global resources that can be referenced by any library's
-- vectorization config.

-- ==================== Remove library_id from chunking_strategies ====================

-- Drop the index first
DROP INDEX IF EXISTS idx_chunking_strategies_library_id;

-- Remove the library_id column and its foreign key constraint
ALTER TABLE chunking_strategies
DROP COLUMN IF EXISTS library_id;

-- ==================== Remove library_id from embedding_strategies ====================

-- Drop the index first
DROP INDEX IF EXISTS idx_embedding_strategies_library_id;

-- Remove the library_id column and its foreign key constraint
ALTER TABLE embedding_strategies
DROP COLUMN IF EXISTS library_id;

-- ==================== Update comments ====================

COMMENT ON TABLE chunking_strategies IS 'Chunking strategies for document processing - reusable across libraries';
COMMENT ON TABLE embedding_strategies IS 'Embedding strategies for vector generation - reusable across libraries';

-- Log success
DO $$
BEGIN
    RAISE NOTICE 'Migration 005: Removed library_id from chunking_strategies and embedding_strategies tables';
END $$;

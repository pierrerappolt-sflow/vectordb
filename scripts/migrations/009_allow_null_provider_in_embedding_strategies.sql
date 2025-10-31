-- Migration 009: Allow NULL for provider in embedding_strategies

-- Rationale:
-- Some bootstrap flows do not provide an embedding provider value. Make the
-- column nullable so inserts without an explicit provider succeed.

ALTER TABLE embedding_strategies
ALTER COLUMN provider DROP NOT NULL;

-- Log success
DO $$
BEGIN
    RAISE NOTICE 'Migration 009: Updated embedding_strategies.provider to allow NULL';
END $$;



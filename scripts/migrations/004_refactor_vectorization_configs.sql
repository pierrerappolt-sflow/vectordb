-- Migration 004: Refactor VectorizationConfig to be global with versioning
--
-- This migration transforms vectorization_configs from library-scoped to global entities
-- with immutable versioning, many-to-many library associations, and per-document processing status.
--
-- Changes:
-- 1. Add version, status, previous_version_id, description to vectorization_configs
-- 2. Create library_vectorization_configs junction table (many-to-many)
-- 3. Create document_vectorization_status table (processing status per document+config)
-- 4. Migrate existing configs to junction table
-- 5. Remove library_id from vectorization_configs
-- 6. Add indexes for performance

-- ==================== Step 1: Add new columns to vectorization_configs ====================

ALTER TABLE vectorization_configs
    ADD COLUMN version INTEGER NOT NULL DEFAULT 1,
    ADD COLUMN status VARCHAR(50) NOT NULL DEFAULT 'active',
    ADD COLUMN previous_version_id UUID REFERENCES vectorization_configs(id) ON DELETE SET NULL,
    ADD COLUMN description TEXT;

COMMENT ON COLUMN vectorization_configs.version IS 'Version number - increments with each edit (configs are immutable)';
COMMENT ON COLUMN vectorization_configs.status IS 'Config status: draft, active, deprecated, archived';
COMMENT ON COLUMN vectorization_configs.previous_version_id IS 'Link to previous version (for version chain)';
COMMENT ON COLUMN vectorization_configs.description IS 'User-provided description of this config/version';

-- Index for version chains
CREATE INDEX idx_vectorization_configs_previous_version_id ON vectorization_configs(previous_version_id);
CREATE INDEX idx_vectorization_configs_status ON vectorization_configs(status);

-- ==================== Step 2: Create library_vectorization_configs junction table ====================

CREATE TABLE IF NOT EXISTS library_vectorization_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    library_id UUID NOT NULL REFERENCES libraries(id) ON DELETE CASCADE,
    vectorization_config_id UUID NOT NULL REFERENCES vectorization_configs(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Prevent duplicate config associations per library
    UNIQUE(library_id, vectorization_config_id)
);

CREATE INDEX idx_library_vectorization_configs_library_id ON library_vectorization_configs(library_id);
CREATE INDEX idx_library_vectorization_configs_config_id ON library_vectorization_configs(vectorization_config_id);

COMMENT ON TABLE library_vectorization_configs IS 'Many-to-many: libraries can use multiple vectorization configs (UNIQUE constraint prevents duplicate configs per library)';

-- ==================== Step 3: Create document_vectorization_status table ====================

CREATE TABLE IF NOT EXISTS document_vectorization_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    vectorization_config_id UUID NOT NULL REFERENCES vectorization_configs(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- One status entry per document+config pair
    UNIQUE(document_id, vectorization_config_id)
);

CREATE INDEX idx_document_vectorization_status_document_id ON document_vectorization_status(document_id);
CREATE INDEX idx_document_vectorization_status_config_id ON document_vectorization_status(vectorization_config_id);
CREATE INDEX idx_document_vectorization_status_status ON document_vectorization_status(status);

COMMENT ON TABLE document_vectorization_status IS 'Tracks processing status for each document+config combination (UNIQUE constraint ensures one status per document+config pair)';
COMMENT ON COLUMN document_vectorization_status.status IS 'Processing status: pending, processing, completed, failed';
COMMENT ON COLUMN document_vectorization_status.error_message IS 'Error details if status is failed';

-- ==================== Step 4: Migrate existing data ====================

-- Copy existing library_id -> config associations to junction table
INSERT INTO library_vectorization_configs (library_id, vectorization_config_id, created_at, updated_at)
SELECT
    library_id,
    id as vectorization_config_id,
    created_at,
    updated_at
FROM vectorization_configs
WHERE library_id IS NOT NULL;

-- Create initial document_vectorization_status entries for all existing documents
-- with all configs from their library (defaults to 'pending')
INSERT INTO document_vectorization_status (document_id, vectorization_config_id, status, created_at, updated_at)
SELECT DISTINCT
    d.id as document_id,
    lvc.vectorization_config_id,
    'pending' as status,
    NOW() as created_at,
    NOW() as updated_at
FROM documents d
INNER JOIN library_vectorization_configs lvc ON d.library_id = lvc.library_id;

-- ==================== Step 5: Remove library_id from vectorization_configs ====================

-- Drop the old index
DROP INDEX IF EXISTS idx_vectorization_configs_library_id;

-- Remove the column
ALTER TABLE vectorization_configs
    DROP COLUMN library_id;

-- Update comment to reflect new global nature
COMMENT ON TABLE vectorization_configs IS 'Global vectorization configurations with immutable versioning - associated with libraries via junction table';

-- ==================== Step 6: Add validation constraints ====================

-- Ensure status is valid
ALTER TABLE vectorization_configs
    ADD CONSTRAINT check_config_status
    CHECK (status IN ('draft', 'active', 'deprecated', 'archived'));

ALTER TABLE document_vectorization_status
    ADD CONSTRAINT check_processing_status
    CHECK (status IN ('pending', 'processing', 'completed', 'failed'));

-- Log success
DO $$
BEGIN
    RAISE NOTICE 'Migration 004: Refactored vectorization_configs to be global with versioning';
    RAISE NOTICE '  - Added version, status, previous_version_id, description columns';
    RAISE NOTICE '  - Created library_vectorization_configs junction table';
    RAISE NOTICE '  - Created document_vectorization_status table';
    RAISE NOTICE '  - Migrated % existing config associations', (SELECT COUNT(*) FROM library_vectorization_configs);
    RAISE NOTICE '  - Created % document processing status entries', (SELECT COUNT(*) FROM document_vectorization_status);
    RAISE NOTICE '  - Removed library_id from vectorization_configs (now global)';
END $$;

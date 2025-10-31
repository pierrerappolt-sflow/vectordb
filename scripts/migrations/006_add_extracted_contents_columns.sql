-- Migration 006: Add missing columns to extracted_contents table
--
-- This migration adds columns that are required by the ExtractedContent entity
-- but were missing from the initial schema.

-- ==================== Add missing columns ====================

-- Add document_fragment_id column (FK to document_fragments)
ALTER TABLE extracted_contents
ADD COLUMN IF NOT EXISTS document_fragment_id UUID REFERENCES document_fragments(id) ON DELETE CASCADE;

-- Add modality sequencing columns
ALTER TABLE extracted_contents
ADD COLUMN IF NOT EXISTS modality_sequence_number INTEGER;

ALTER TABLE extracted_contents
ADD COLUMN IF NOT EXISTS is_last_of_modality BOOLEAN NOT NULL DEFAULT FALSE;

-- Add status column (PENDING, CHUNKED, FAILED)
ALTER TABLE extracted_contents
ADD COLUMN IF NOT EXISTS status VARCHAR(50) NOT NULL DEFAULT 'pending';

-- Add metadata column for parser metadata
ALTER TABLE extracted_contents
ADD COLUMN IF NOT EXISTS metadata JSONB;

-- ==================== Create indexes ====================

CREATE INDEX IF NOT EXISTS idx_extracted_contents_document_fragment_id
ON extracted_contents(document_fragment_id);

CREATE INDEX IF NOT EXISTS idx_extracted_contents_status
ON extracted_contents(status);

CREATE INDEX IF NOT EXISTS idx_extracted_contents_modality_sequence
ON extracted_contents(document_id, modality_type, modality_sequence_number);

-- ==================== Update comments ====================

COMMENT ON COLUMN extracted_contents.document_fragment_id IS 'Source fragment that this content was extracted from';
COMMENT ON COLUMN extracted_contents.modality_sequence_number IS 'Order within modality type (1st TEXT, 2nd TEXT, etc.)';
COMMENT ON COLUMN extracted_contents.is_last_of_modality IS 'True if this is the last content of this modality for the document';
COMMENT ON COLUMN extracted_contents.status IS 'Processing status: pending, chunked, or failed';
COMMENT ON COLUMN extracted_contents.metadata IS 'Optional metadata from parsing (encoding, page numbers, etc.)';

-- Log success
DO $$
BEGIN
    RAISE NOTICE 'Migration 006: Added missing columns to extracted_contents table';
END $$;

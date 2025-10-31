-- Migration 003: Create event_logs table for pipeline monitoring
-- 
-- This table captures all pipeline events for debugging, auditing, and monitoring.
-- Event logging is an infrastructure concern, not business logic.

CREATE TABLE IF NOT EXISTS event_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(100) NOT NULL,
    event_id VARCHAR(100),
    timestamp TIMESTAMPTZ NOT NULL,
    routing_key VARCHAR(200) NOT NULL,
    data JSONB NOT NULL,
    document_id VARCHAR(100),
    library_id VARCHAR(100),
    pipeline_stage VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Performance indexes for common query patterns
CREATE INDEX idx_event_logs_timestamp ON event_logs(timestamp DESC);
CREATE INDEX idx_event_logs_event_type ON event_logs(event_type);
CREATE INDEX idx_event_logs_routing_key ON event_logs(routing_key);

-- Conditional indexes (only index non-null values)
CREATE INDEX idx_event_logs_document_id ON event_logs(document_id) 
    WHERE document_id IS NOT NULL;
CREATE INDEX idx_event_logs_library_id ON event_logs(library_id) 
    WHERE library_id IS NOT NULL;
CREATE INDEX idx_event_logs_pipeline_stage ON event_logs(pipeline_stage) 
    WHERE pipeline_stage IS NOT NULL;

-- JSONB index for querying event data
CREATE INDEX idx_event_logs_data ON event_logs USING GIN(data);

-- Composite index for document timeline queries (most common use case)
CREATE INDEX idx_event_logs_doc_timeline ON event_logs(document_id, timestamp DESC) 
    WHERE document_id IS NOT NULL;

-- Add comment for documentation
COMMENT ON TABLE event_logs IS 'Captures all pipeline events for monitoring and debugging';
COMMENT ON COLUMN event_logs.event_type IS 'Event class name (e.g., FragmentDecoded)';
COMMENT ON COLUMN event_logs.routing_key IS 'RabbitMQ routing key that triggered this event';
COMMENT ON COLUMN event_logs.data IS 'Full event payload as JSONB';
COMMENT ON COLUMN event_logs.pipeline_stage IS 'Inferred stage: upload, decode, chunk, embed, index';

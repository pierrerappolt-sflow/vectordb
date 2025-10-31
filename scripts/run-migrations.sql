-- Run all migrations in order
-- This script is executed by docker-entrypoint-initdb.d after init-db.sql and init-vector-tables.sql

-- Track migration status
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(10) PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    description TEXT
);

-- Function to run migration if not already applied
CREATE OR REPLACE FUNCTION run_migration(migration_version VARCHAR, migration_file TEXT, migration_desc TEXT)
RETURNS VOID AS $$
DECLARE
    already_applied BOOLEAN;
BEGIN
    -- Check if migration already applied
    SELECT EXISTS(SELECT 1 FROM schema_migrations WHERE version = migration_version) INTO already_applied;

    IF NOT already_applied THEN
        RAISE NOTICE 'Running migration %: %', migration_version, migration_desc;

        -- Execute the migration file content
        -- Note: In docker-entrypoint-initdb.d context, we'll run migrations directly
        -- This function is for manual migration tracking

        -- Record migration
        INSERT INTO schema_migrations (version, description)
        VALUES (migration_version, migration_desc);

        RAISE NOTICE 'Migration % completed', migration_version;
    ELSE
        RAISE NOTICE 'Migration % already applied, skipping', migration_version;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Migration 001: Create domain tables
\i /docker-entrypoint-initdb.d/migrations/001_create_domain_tables.sql
INSERT INTO schema_migrations (version, description)
VALUES ('001', 'Create domain tables for Library aggregate')
ON CONFLICT (version) DO NOTHING;

-- Migration 002: Create strategy tables
\i /docker-entrypoint-initdb.d/migrations/002_create_strategy_tables.sql
INSERT INTO schema_migrations (version, description)
VALUES ('002', 'Create chunking_strategies and embedding_strategies tables')
ON CONFLICT (version) DO NOTHING;

-- Migration 003: Create event logs table
\i /docker-entrypoint-initdb.d/migrations/003_create_event_logs_table.sql
INSERT INTO schema_migrations (version, description)
VALUES ('003', 'Create event_logs table for pipeline monitoring')
ON CONFLICT (version) DO NOTHING;

-- Log completion
DO $$
BEGIN
    RAISE NOTICE 'All migrations completed successfully';
END $$;

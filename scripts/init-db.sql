-- Initialize database

-- Create schema for application tables (optional, can organize tables)
CREATE SCHEMA IF NOT EXISTS vdb;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE vectordb TO vdbuser;
GRANT ALL PRIVILEGES ON SCHEMA vdb TO vdbuser;
GRANT ALL PRIVILEGES ON SCHEMA public TO vdbuser;

-- Log success
DO $$
BEGIN
    RAISE NOTICE 'Step 1: Database initialized';
END $$;

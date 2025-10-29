-- Initialize PostgreSQL with TimescaleDB extension

-- Create TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Create UUID extension for generating UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create pg_trgm extension for text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Set timezone
SET timezone = 'UTC';

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE nqhub TO nqhub;

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'NQHUB database initialized with TimescaleDB';
END $$;

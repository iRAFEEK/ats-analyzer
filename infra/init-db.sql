-- Initialize ATS Analyzer database

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create database if it doesn't exist (handled by POSTGRES_DB env var)

-- Set timezone
SET timezone = 'UTC';

-- Create a basic health check function
CREATE OR REPLACE FUNCTION health_check()
RETURNS TABLE(status text, timestamp timestamptz)
LANGUAGE sql
AS $$
  SELECT 'healthy'::text, now();
$$;

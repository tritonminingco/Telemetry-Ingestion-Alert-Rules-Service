-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Enable PostGIS extension for spatial data
CREATE EXTENSION IF NOT EXISTS postgis;

-- Create database user if not exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'dsg_user') THEN
        CREATE USER dsg_user WITH PASSWORD 'dsg_password';
    END IF;
END
$$;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE dsg_telemetry TO dsg_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO dsg_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO dsg_user;

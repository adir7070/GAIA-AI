-- Postgres initialization script. Runs on first container startup.
-- Idempotent: safe to re-run.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Schemas are managed by Alembic; this file only ensures extensions exist.

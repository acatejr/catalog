#!/bin/bash
set -e

# Install pgvector extension
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS postgis;
    CREATE EXTENSION IF NOT EXISTS vector;
EOSQL

echo "PostGIS and pgvector extensions created successfully"

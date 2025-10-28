#!/bin/bash

set -e

# Perform all actions as $POSTGRES_USER
export PGUSER="$POSTGRES_USER"

# Create the 'template_postgis' template db
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<- 'EOSQL'
CREATE DATABASE template_postgis IS_TEMPLATE true;
EOSQL

# Load PostGIS into both template_database and $POSTGRES_DB
for DB in template_postgis "$POSTGRES_DB"; do
	echo "Loading PostGIS extensions into $DB"
	psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname="$DB" <<-'EOSQL'
		CREATE EXTENSION IF NOT EXISTS postgis;
		CREATE EXTENSION IF NOT EXISTS postgis_topology;
		-- Reconnect to update pg_setting.resetval
		-- See https://github.com/postgis/docker-postgis/issues/288
		\c
		CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
		CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder;
		CREATE EXTENSION IF NOT EXISTS vector;
        CREATE table if not exists documents (
            id SERIAL PRIMARY KEY,
            title TEXT,
            description TEXT,
            keywords TEXT[],
            authors TEXT[],
            chunk_text TEXT,
            chunk_index INTEGER,
            embedding vector(384), -- Adjust dimension based on your embedding model
            created_at TIMESTAMP DEFAULT NOW(),
            doc_id varchar(255),
            chunk_type varchar(255),
            data_source varchar(75),
            UNIQUE(doc_id, chunk_index)  -- Enables upsert functionality
        );
EOSQL
done
# Catalog

Proof-of-Concept Catalog App

## Dockerfile.cli

- Uses Python 3.14-slim base image
- Installs system dependencies (gcc, PostGIS libraries, GDAL) needed for data processing
- Installs Python dependencies from requirements.txt
- Copies the src/ directory structure
- Sets PYTHONPATH to include the src directory
- Defaults to showing CLI help (can be overridden when running the container)

You can use this to run CLI commands like:
docker build -f Dockerfile.cli -t catalog-cli .
docker run catalog-cli python -m cli download-all
docker run catalog-cli python -m cli embed-and-store

## Dockerfile.api

- Uses Python 3.14-slim base image
- Installs minimal system dependencies (gcc, g++, libpq-dev for database connectivity)
- References requirements-api.txt (you'll need to create this with FastAPI, uvicorn, langchain, etc.)
- Copies only the API and core code (excludes src/cli/)
- Exposes port 8000
- Defaults to running the FastAPI server with uvicorn

Note: You'll need to create requirements-api.txt with API-specific dependencies like:

- fastapi
- uvicorn
- langchain
- openai
- pydantic
- etc.

## Dockerfile.core

1. Dockerfile.core - Base image with core components

2. requirements-core.txt - Shared dependencies:

- psycopg2-binary (database access)
- pydantic (schemas)
- python-dotenv (environment variables)

3. build-core.sh - Build script

Note: This core image could be used as a base for both CLI and API Dockerfiles using multi-stage builds, which would:

- Reduce duplication
- Speed up builds (shared layers)
- Ensure consistency between CLI and API

## Compose.yml

Services:

1. db - PostgreSQL with pgvector extension

- Health check to ensure it's ready
- Persistent volume for data storage
- Port 5432 exposed

2. api - FastAPI application

- Builds from Dockerfile.api
- Exposes port 8000
- Waits for db to be healthy
- Includes all necessary environment variables

3. cli - CLI tool

- Builds from Dockerfile.cli
- Uses Docker profile (won't start automatically)
- Mounts ./data directory for storing downloaded metadata
- Waits for db to be healthy

Usage:

### Start db and api

docker compose up

### Run CLI commands

docker compose run cli python -m cli download-all
docker compose run cli python -m cli embed-and-store

### Or start everything including CLI

docker compose --profile cli up

The CLI uses a Docker profile so it doesn't auto-start (since CLI is typically run on-demand), but the API runs continuously.

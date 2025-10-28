# Docker Setup Guide

This guide explains how to use the unified Docker configuration for the Catalog project.

## Overview

The project now uses:
- **Single Dockerfile** with build arguments for dev/prod environments
- **Single docker-compose.yml** that adapts based on environment variables
- **Environment-aware configuration** that detects whether it's running on test server or locally

## Quick Start

### Local Development

1. Create a `.env` file (or copy from `.env.example`):
```bash
ENVIRONMENT=dev
POSTGRES_DB=catalog
POSTGRES_USER=catalog_user
POSTGRES_PASSWORD=catalog_password
X_API_KEY=your_local_api_key
OPENAI_API_KEY=your_openai_key
APP_PORT=8000
CODE_MOUNT=./src
MOUNT_MODE=rw
```

2. Start services:
```bash
docker compose up -d
```

3. View logs:
```bash
docker compose logs -f app
```

### Test Server Deployment

1. On the test server, create `.env` file using `.env.test.proposed` as template:
```bash
cd /root/apps/catalog
cp .env.test.proposed .env
```

2. Edit `.env` with production values:
```bash
vim .env
```

3. Deploy (automatically done via GitHub Actions on push to main):
```bash
git pull origin main
docker compose down
docker compose up -d --build
```

## How Environment Detection Works

The system uses the `ENVIRONMENT` variable in your `.env` file:

- **`ENVIRONMENT=dev`**:
  - Installs dev dependencies
  - Mounts code as read-write for hot reload
  - Suitable for local development

- **`ENVIRONMENT=prod`**:
  - Installs only production dependencies
  - Mounts code as read-only
  - Optimized for test/production servers

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `ENVIRONMENT` | Environment mode | `dev` or `prod` |
| `POSTGRES_DB` | Database name | `catalog` |
| `POSTGRES_USER` | Database user | `catalog_user` |
| `POSTGRES_PASSWORD` | Database password | `secure_password` |
| `X_API_KEY` | API authentication key | `your_api_key` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_PORT` | External port for API | `8000` |
| `POSTGRES_PORT` | External port for database | `5432` |
| `CODE_MOUNT` | Path to mount source code | `./src` |
| `MOUNT_MODE` | Mount mode (ro/rw) | `ro` |

## Common Commands

### Start services
```bash
docker compose up -d
```

### Stop services
```bash
docker compose down
```

### Rebuild and restart
```bash
docker compose up -d --build
```

### View logs
```bash
# All services
docker compose logs -f

# Just the app
docker compose logs -f app

# Just the database
docker compose logs -f db
```

### Check service health
```bash
docker compose ps
```

### Access application shell
```bash
docker compose exec app bash
```

### Access database
```bash
docker compose exec db psql -U catalog_user -d catalog
```

### Run CLI commands
```bash
# Download data
docker compose exec app sh -c "PYTHONPATH=/app/src python /app/src/cli.py download-all"

# Embed and store
docker compose exec app sh -c "PYTHONPATH=/app/src python /app/src/cli.py embed-and-store"
```

## File Structure

```
catalog/
├── Dockerfile                 # Unified Dockerfile for all environments
├── docker-compose.yml         # Unified compose configuration
├── .env                       # Local environment variables (gitignored)
├── .env.example              # Example environment variables
├── .env.test.proposed        # Template for test server
└── schema.sql                # Database schema (auto-loaded on first run)
```

## Deployment Workflow

The GitHub Actions workflow (`.github/workflows/deploy.yml`) automatically:

1. Connects to test server via SSH
2. Pulls latest code from main branch
3. Stops existing containers
4. Rebuilds and starts containers with new code
5. Verifies services are running

## Troubleshooting

### Services won't start
```bash
# Check logs
docker compose logs

# Check if ports are already in use
netstat -tulpn | grep -E '8000|5432'
```

### Database connection issues
```bash
# Verify database is healthy
docker compose exec db pg_isready -U catalog_user

# Check database logs
docker compose logs db
```

### Code changes not reflecting
- **Dev mode**: Code is mounted, restart app: `docker compose restart app`
- **Prod mode**: Rebuild image: `docker compose up -d --build app`

### Reset everything
```bash
# Stop and remove all containers and volumes
docker compose down -v

# Start fresh
docker compose up -d
```

## Migration from Old Setup

If you have existing Dockerfile.dev or separate compose files:

1. Back up your current `.env` file
2. Replace `Dockerfile` with `Dockerfile.proposed`
3. Replace `docker-compose.yml` with `docker-compose.yml.proposed`
4. Add `ENVIRONMENT=dev` (for local) or `ENVIRONMENT=prod` (for server) to `.env`
5. Remove old `Dockerfile.dev` and any other compose files
6. Rebuild: `docker compose up -d --build`

## Security Notes

- Never commit `.env` files to git
- Use strong passwords for `POSTGRES_PASSWORD`
- Rotate `X_API_KEY` regularly
- Keep `OPENAI_API_KEY` secure
- On production, ensure `MOUNT_MODE=ro` (read-only)

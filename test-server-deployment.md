# Test Server Deployment Guide

## Using the Docker Image from GHCR

Once your Docker image is published to ghcr.io, here's how to use it on a testing server.

## 1. Authenticate with GHCR (if image is private)

If your image is private, authenticate first:
```bash
echo $GITHUB_TOKEN | docker login ghcr.io -u acatejr --password-stdin
```

If you made the package public, you can skip authentication for pulling.

## 2. Pull the Image

```bash
docker pull ghcr.io/acatejr/catalog:latest
```

Or pull a specific version:
```bash
docker pull ghcr.io/acatejr/catalog:v1.0.0
```

## 3. Run the Container

### Option A: Run with docker run
```bash
docker run -d \
  --name catalog \
  -p 8000:8000 \
  -e OPENAI_API_KEY=your_key_here \
  -e DATABASE_URL=postgresql://user:pass@host:5432/catalog \
  ghcr.io/acatejr/catalog:latest
```

### Option B: Use Docker Compose (Recommended)

Use the provided `compose.tst.yml` file:

```bash
# Pull latest image
docker compose -f compose.tst.yml pull

# Start services
docker compose -f compose.tst.yml up -d

# View logs
docker compose -f compose.tst.yml logs -f

# Stop services
docker compose -f compose.tst.yml down
```

## 4. Update to Latest Version

When you push a new version:

```bash
docker compose -f compose.tst.yml pull
docker compose -f compose.tst.yml up -d
```

Or with plain Docker:
```bash
docker pull ghcr.io/acatejr/catalog:latest
docker stop catalog
docker rm catalog
docker run -d --name catalog ... ghcr.io/acatejr/catalog:latest
```

## Best Practices for Testing

**Use specific version tags for stability:**
```bash
docker pull ghcr.io/acatejr/catalog:v1.0.0
```

**Set up environment variables in a `.env` file:**
```bash
# .env on testing server
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://catalog_user:catalog_password@db:5432/catalog
```

**Check logs:**
```bash
docker logs catalog
# or
docker compose -f compose.tst.yml logs web
```

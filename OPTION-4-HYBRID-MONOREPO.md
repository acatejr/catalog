# Option 4: Hybrid Monorepo

Keep current structure but clarify boundaries with layered Docker architecture:

```
catalog/
├── src/
│   ├── __init__.py
│   ├── core/              # Shared (db, schema)
│   │   ├── __init__.py
│   │   ├── db.py
│   │   └── schema.py
│   ├── cli/               # CLI only
│   │   ├── __init__.py
│   │   └── cli.py
│   └── api/               # API only
│       ├── __init__.py
│       ├── api.py
│       └── llm.py
├── Dockerfile.core        # Base image with shared code
├── Dockerfile.cli         # CLI image (extends core)
├── Dockerfile.api         # API image (extends core)
├── requirements-core.txt  # Shared dependencies
├── requirements-cli.txt   # CLI-specific dependencies
├── requirements-api.txt   # API-specific dependencies
├── compose.yml            # DB + API services
├── compose.cli.yml        # CLI utility
├── build-core.sh          # Build core image
├── build-cli.sh           # Build CLI image
├── build-api.sh           # Build API image
└── build-all.sh           # Build all images
```

## Pros

- Minimal refactoring
- Clear separation between CLI, API, and shared code
- Keeps simplicity
- Can deploy CLI and API separately
- Layered Docker images reduce duplication
- Shared base image speeds up builds

## Cons

- Less structured than Option 1
- Requires building core image first

## Implementation Status

✅ **Step 1: Reorganize Current Structure** - COMPLETE

Directory structure created with proper separation:

```bash
src/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── db.py          # Database operations (PostgreSQL + pgvector)
│   └── schema.py      # Pydantic models
├── cli/
│   ├── __init__.py
│   └── cli.py         # Typer CLI commands (download, parse, embed)
└── api/
    ├── __init__.py
    ├── api.py         # FastAPI endpoints
    └── llm.py         # ChatBot and RAG implementation
```

✅ **Step 2: Create Layered Dockerfiles** - COMPLETE

Three-tier Docker architecture:

**Dockerfile.core** - Base image:
- Python 3.14-slim
- Core system dependencies (gcc, g++, libpq-dev)
- Shared Python packages (psycopg2-binary, pydantic, python-dotenv)
- Core source code (src/core/)

**Dockerfile.cli** - Extends core:
- Additional system deps (GDAL for geospatial data)
- CLI-specific packages (typer, beautifulsoup4, requests, rich)
- CLI source code only

**Dockerfile.api** - Extends core:
- No additional system deps needed
- API-specific packages (fastapi, uvicorn, openai, sentence-transformers)
- API source code only

✅ **Step 3: Create Compose Files** - COMPLETE

**compose.yml** - Main services:
- PostgreSQL with pgvector extension
- FastAPI application
- Proper networking and health checks

**compose.cli.yml** - CLI utilities:
- Connects to external network from compose.yml
- Runs one-off CLI commands
- Mounts ./data directory for metadata storage

✅ **Step 4: Add Build Scripts** - COMPLETE

- `build-core.sh` - Build base image
- `build-cli.sh` - Build core + CLI
- `build-api.sh` - Build core + API
- `build-all.sh` - Build everything in order

## Usage

### Building Images

```bash
# Build all images
./build-all.sh

# Or build individually
./build-core.sh
./build-cli.sh
./build-api.sh
```

### Running Services

```bash
# Start database and API
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down
```

### Running CLI Commands

```bash
# Run CLI commands (requires services to be running)
docker compose -f compose.cli.yml run --rm cli python -m cli download-all
docker compose -f compose.cli.yml run --rm cli python -m cli embed-and-store
docker compose -f compose.cli.yml run --rm cli python -m cli clear-docs-table
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│                  catalog-core                       │
│  (Python 3.14-slim + PostgreSQL deps + pydantic)    │
│               src/core/: db.py, schema.py           │
└──────────────────┬──────────────────────────────────┘
                   │
         ┌─────────┴─────────┐
         │                   │
┌────────▼────────┐  ┌──────▼────────┐
│  catalog-cli    │  │  catalog-api  │
│  + GDAL libs    │  │  + FastAPI    │
│  + typer        │  │  + OpenAI     │
│  + requests     │  │  + uvicorn    │
│  + bs4          │  │  + sentence-  │
│  src/cli/       │  │    transformers│
│                 │  │  src/api/      │
└─────────────────┘  └────────────────┘
```

## Component Responsibilities

### Core (`src/core/`)
- **db.py**: PostgreSQL + pgvector operations, vector search, bulk upsert
- **schema.py**: Pydantic models for USFS documents

### CLI (`src/cli/`)
- **cli.py**: Typer commands for:
  - Downloading metadata from USFS sources (fsgeodata, datahub, RDA)
  - Parsing XML/JSON metadata
  - Embedding documents with sentence-transformers
  - Bulk storing to vector database

### API (`src/api/`)
- **api.py**: FastAPI endpoints:
  - `/health` - Health check
  - `/query` - Query with RAG or keyword search
- **llm.py**: ChatBot class for LLM integration and vector search

## Migration Path

As your project matures:

1. **Phase 1 (Now)**: Implement Option 4 - Hybrid Monorepo
2. **Phase 2 (Growth)**: Move to Option 1 - Structured Monorepo with packages
3. **Phase 3 (Scale)**: Consider Option 2 - Separate repos if team grows significantly
4. **Phase 4 (Production)**: Evaluate Option 3 - Microservices if scale demands it

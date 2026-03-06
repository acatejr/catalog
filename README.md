# Catalog

Catalog is a Python CLI tool for discovering and exploring USFS (U.S. Forest Service) geospatial datasets. It harvests metadata from multiple federal data portals, builds a vector database, and enables semantic and AI-assisted search over the catalog.

## Features

- Downloads metadata (XML and JSON) from three USFS data sources
- Builds a unified catalog and indexes it with ChromaDB for semantic search
- Supports multiple search modes: vector search, hybrid (BM25 + semantic), and agentic search
- Integrates with Ollama and Verde LLM backends for natural language Q&A (RAG)

## Data Sources

| Source | Format | Description |
| ------ | ------ | ----------- |
| FSGeodata Clearinghouse | XML | Authoritative basemaps, boundaries, and operational layers |
| Geospatial Data Discovery (GDD) | DCAT JSON | Current operational GIS layers and services from ArcGIS Hub |
| Research Data Archive (RDA) | JSON | Research-grade datasets from the USFS research directory |

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager
- A running Ollama instance (for LLM-backed commands) or a Verde/LiteLLM proxy

## Installation

```bash
git clone https://github.com/acatejr/catalog.git
cd catalog
uv sync
```

## Configuration

Copy `.env.example` to `.env` and fill in the values:

```bash
cp .env.example .env
```

| Variable | Description |
| -------- | ----------- |
| `DATA_DIR` | Directory for downloaded metadata (default: `data/usfs`) |
| `CHROMADB_PATH` | Path for ChromaDB storage (default: `./chromadb`) |
| `OLLAMA_API_KEY` | API key for the Ollama server |
| `OLLAMA_API_URL` | URL of the Ollama server |
| `OLLAMA_MODEL` | Ollama model name to use |
| `VERDE_API_KEY` | API key for the Verde/LiteLLM proxy |
| `VERDE_URL` | URL of the Verde proxy |
| `VERDE_MODEL` | Verde model name to use |

## Usage

All commands are run via `uv run catalog <command>`.

### Check application health

```bash
uv run catalog health
```

### Download USFS metadata

Fetches XML and JSON metadata from FSGeodata, GDD, and RDA:

```bash
uv run catalog download-fs-metadata
```

### Build the catalog

Parses downloaded metadata into a unified JSON catalog:

```bash
uv run catalog build-fs-catalog
```

### Build the ChromaDB vector store

Indexes the catalog into ChromaDB for semantic search:

```bash
uv run catalog build-fs-chromadb
```

### Query the vector store

Returns semantically similar datasets for a query:

```bash
uv run catalog query-fs-chromadb --qstn "wildfire risk data"
uv run catalog query-fs-chromadb -q "watershed boundaries" -n 10
```

### LLM-assisted chat (Ollama)

Runs a vector search and uses Ollama to synthesize a natural language answer:

```bash
uv run catalog ollama-chat -q "What datasets exist for forest road conditions?"
```

### LLM-assisted chat (Verde)

Same as above using the Verde/LiteLLM backend:

```bash
uv run catalog ask-verde -q "Are there any datasets about timber harvesting?"
```

### Hybrid search

Combines BM25 keyword search with semantic vector search. Optionally routes results to an LLM:

```bash
# Hybrid search only
uv run catalog hybrid-search -q "fire perimeter data"

# With LLM synthesis
uv run catalog hybrid-search -q "fire perimeter data" --bot ollama

# With query expansion before searching
uv run catalog hybrid-search -q "burned areas" --expq --bot verde
```

### Agentic search

Runs an autonomous LLM-driven search loop. The model calls search tools iteratively until it can answer the question:

```bash
uv run catalog agent-search -q "What trail data is available for Region 5?"
```

## Development

```bash
# Run tests
uv run pytest -vs

# Lint and format
ruff check .
ruff format .

# Deploy documentation
make gh-deploy
```

## Project Structure

```text
catalog/
├── src/catalog/
│   ├── cli.py        # Click CLI commands
│   ├── usfs.py       # Data loaders (FSGeodata, GDD, RDA)
│   ├── core.py       # ChromaDB vector store
│   ├── schema.py     # Pydantic data models
│   ├── bots.py       # LLM clients (Ollama, Verde, AgentBot)
│   ├── search.py     # Hybrid search (BM25 + vector)
│   ├── tools.py      # Agent tool definitions
│   ├── lib.py        # Utility functions
│   └── config.py     # Settings from environment
├── data/usfs/        # Downloaded metadata
├── chromadb/         # Vector database storage
├── docs/             # MkDocs documentation
└── tests/            # pytest test suite
```

## Documentation

Full documentation is available in the `docs/` directory and can be served locally:

```bash
uv run mkdocs serve
```

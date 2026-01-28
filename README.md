# Catalog

A Python CLI tool for downloading, managing, and querying geospatial metadata from the USFS Geodata Clearinghouse. Features a RAG (Retrieval-Augmented Generation) system using ChromaDB for vector search and Ollama for LLM-powered question answering.

## Features

- **Multi-source metadata aggregation** from three federal data sources:
  - USFS Geodata Clearinghouse (FSGeodata)
  - Geospatial Data Discovery (GDD) via ArcGIS Hub
  - USFS Research Data Archive (RDA)
- **Vector search** using ChromaDB with embedded embeddings
- **LLM integration** via Ollama for natural language dataset discovery
- **Unified schema** normalizing heterogeneous metadata into a single format

## Installation

Requires Python 3.13+

```bash
# Clone the repository
git clone https://github.com/acatejr/catalog.git
cd catalog

# Install with uv
uv sync

# Or install with pip
pip install -e .
```

## Configuration

Create a `.env` file with your Ollama credentials:

```bash
OLLAMA_API_URL=https://your-ollama-instance.com
OLLAMA_API_KEY=your-api-key
OLLAMA_MODEL=llama3
```

## Usage

### Download Metadata

Download metadata from all three sources:

```bash
catalog download_fs_metadata
```

### Build Catalog

Parse downloaded metadata into a unified JSON catalog:

```bash
catalog build_fs_catalog
```

### Build ChromaDB Index

Load the catalog into ChromaDB for vector search:

```bash
catalog build_fs_chromadb
```

### Query the Catalog

Search for datasets using semantic similarity:

```bash
catalog query_fs_chromadb "forest fire data" -n 5
```

### Chat with LLM

Use natural language to discover datasets:

```bash
catalog ollama_chat "What datasets are available about wildfire management?"
```

### Health Check

```bash
catalog health
```

## Project Structure

```
src/catalog/
├── cli.py          # Click-based CLI entry point
├── usfs.py         # Data loaders & scrapers
├── core.py         # ChromaDB vector store logic
├── schema.py       # Pydantic data models
├── lib.py          # Utility functions
└── bots.py         # Ollama LLM integration
```

## Development

### Code Quality

```bash
# Format and lint with ruff
ruff check .
ruff format .
```

### Testing

```bash
# Run tests
uv run pytest tests/ -v
```

## Data Sources

| Source | URL | Format |
|--------|-----|--------|
| FSGeodata | https://data.fs.usda.gov/geodata/edw/datasets.php | XML metadata |
| GDD | https://data-usfs.hub.arcgis.com/api/feed/dcat-us/1.1.json | DCAT JSON |
| RDA | https://www.fs.usda.gov/rds/archive/webservice/datagov | JSON API |

## License

USDA / USFS / U of AZ

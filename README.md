# Catalog

A proof-of-concept metadata catalog that harvests publicly available data, stores it in a vector database, and enables LLM-enhanced search using Retrieval-Augmented Generation (RAG).

[![Documentation](https://img.shields.io/badge/docs-online-blue)](https://main.catalog-6fe.pages.dev/)
[![Streamlit Demo](https://img.shields.io/badge/demo-streamlit-red)](https://catalog-6zpfd6vrnnekbke3k8ga89.streamlit.app/)

## Features

- **Metadata Harvesting**: Automatically collect metadata from public sources
- **Vector Embeddings**: Store and index data using vector embeddings for semantic search
- **RAG-Enhanced Search**: Query data using LLMs with retrieval-augmented generation
- **REST API**: FastAPI-based endpoints for integration
- **CLI Interface**: Command-line tools for data management
- **Docker Support**: Containerized deployment with Docker Compose

## Tech Stack

- **Language**: Python 3.13+
- **Framework**: FastAPI, LangChain
- **Database**: PostgreSQL with vector extension
- **LLM**: OpenAI API
- **Embeddings**: Sentence Transformers
- **Testing**: pytest
- **Documentation**: MkDocs Material

## Prerequisites

- Python 3.13 or higher
- PostgreSQL (or use Docker Compose)
- OpenAI API key
- Docker & Docker Compose (optional, for containerized setup)

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/acatejr/catalog.git
cd catalog

# Create .env file with your OpenAI API key
echo "OPENAI_API_KEY=your_key_here" > .env

# Start services
docker compose up -d

# Access the API
curl http://localhost:8000
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY=your_key_here
export DATABASE_URL=postgresql://user:pass@localhost:5432/catalog

# Run CLI commands
PYTHONPATH=src python src/cli.py --help
PYTHONPATH=src python src/cli.py download-all
PYTHONPATH=src python src/cli.py embed-and-store
PYTHONPATH=src python src/cli.py run-api
```

## Usage

### CLI Commands

```bash
# Download metadata from sources
PYTHONPATH=src python src/cli.py download-all

# Process and store embeddings
PYTHONPATH=src python src/cli.py embed-and-store

# Start the API server
PYTHONPATH=src python src/cli.py run-api

# View all available commands
PYTHONPATH=src python src/cli.py --help
```

### API Endpoints

Once the API is running (default: `http://localhost:8000`):

- `GET /` - API status
- `GET /search?q=query` - Search metadata
- Full API documentation at `/docs` (Swagger UI)

## Project Structure

```
catalog/
├── src/                # Source code
│   ├── cli.py         # Command-line interface
│   ├── api.py         # FastAPI endpoints
│   ├── db.py          # Database operations
│   ├── llm.py         # LLM integration
│   └── schema.py      # Data schemas
├── docs/              # MkDocs documentation
├── tests/             # Test suite
├── data/              # Downloaded metadata
├── compose.yml        # Docker Compose for development
├── compose.tst.yml    # Docker Compose for testing/deployment
└── requirements.txt   # Python dependencies
```

## Development

### Running Tests

```bash
pytest
pytest --cov  # With coverage report
```

### Code Quality

```bash
# Lint with Ruff
ruff check .

# Format with Ruff
ruff format .
```

### Documentation

```bash
# Serve documentation locally
mkdocs serve

# Build documentation
mkdocs build
```

## Deployment

### Docker Image

Pre-built Docker images are available at:
```
ghcr.io/acatejr/catalog:latest
ghcr.io/acatejr/catalog:v1.0.0
```

### Test Server Deployment

See [Test Server Deployment Guide](docs/test-server-deployment.md) for detailed instructions.

Quick deployment:
```bash
docker compose -f compose.tst.yml pull
docker compose -f compose.tst.yml up -d
```

### Publishing Updates

See [Docker Publishing Guide](docs/docker-publishing.md) for information on:
- Triggering rebuilds
- Version tagging
- Manual workflow dispatch

## Documentation

- **Full Documentation**: [https://main.catalog-6fe.pages.dev/](https://main.catalog-6fe.pages.dev/)
- **Live Demo**: [Streamlit Prototype](https://catalog-6zpfd6vrnnekbke3k8ga89.streamlit.app/)
- **Deployment Guide**: [docs/test-server-deployment.md](docs/test-server-deployment.md)
- **Publishing Guide**: [docs/docker-publishing.md](docs/docker-publishing.md)

## Architecture

The catalog system consists of several key components:

1. **Data Harvester**: Scrapes and downloads metadata from public sources
2. **Embedding Engine**: Generates vector embeddings using sentence transformers
3. **Vector Database**: PostgreSQL with pgvector for similarity search
4. **LLM Layer**: Integrates with OpenAI for RAG-enhanced queries
5. **API Layer**: FastAPI REST endpoints for programmatic access
6. **CLI**: Typer-based command-line interface for operations

## Contributing

This is a proof-of-concept project. When contributing:

1. Run tests before committing: `pytest`
2. Follow code style: `ruff check . && ruff format .`
3. Update documentation for new features
4. Use conventional commits: `feat: description` or `fix: description`

## License

[Add your license here]

## Acknowledgments

Built with Python, FastAPI, LangChain, and OpenAI.

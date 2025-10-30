# Catalog - AI Assistant Context

## Project Overview
A proof-of-concept metadata catalog that harvests publicly available data, stores it in a vector database, and enables LLM-enhanced search using Retrieval-Augmented Generation (RAG).

## Tech Stack
- **Language**: Python 3.13+
- **Package Manager**: pip
  - `requirements.txt` - Production dependencies
  - `requirements-dev.txt` - Development dependencies (pytest, ruff, coverage tools)
- **Key Dependencies**: FastAPI, LangChain, OpenAI, PostgreSQL (psycopg2), Sentence Transformers
- **Testing**: pytest with coverage
- **Linting**: Ruff

## Project Structure
- `src/catalog/` - Main application code (modularized package)
  - `cli/` - Command-line interface
    - `cli.py` - CLI commands (Typer)
  - `api/` - API layer
    - `api.py` - FastAPI endpoints
    - `llm.py` - LLM integration logic
  - `core/` - Core functionality
    - `db.py` - Database operations
    - `schema.py` - Data schemas
- `sql/` - Database schema files
  - `schema.sql` - PostgreSQL schema with vector extension
- `services/` - Service configuration files
- `data/` - Downloaded metadata storage
- `tests/` - Test suite

## Development Setup

```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development tools

# Run CLI using helper script
./run-cli.sh --help

# Or run CLI directly (requires PYTHONPATH since code is in src/)
PYTHONPATH=src python -m catalog.cli.cli --help

# Run specific commands
./run-cli.sh download-all
./run-cli.sh embed-and-store

# Run API using helper script
./run-api.sh

# Or run API directly
PYTHONPATH=src python -m catalog.api.api

# Run tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html
```

## Deployment Scripts

- `run-cli.sh` - Wrapper script to run CLI commands with proper PYTHONPATH
- `run-api.sh` - Starts the FastAPI server locally
- `run-api-usfs.sh` - Starts the API with USFS-specific configuration
- `catalogapi.service` - systemd service file for production deployment

## Key Conventions
- Use Ruff for linting and formatting
- Environment variables stored in `.env`
- Docker Compose available for containerized setup

## Database

- PostgreSQL with vector extension support
- Schema defined in `sql/schema.sql`
- Vector embeddings for RAG functionality

## Important Notes

- This is a proof-of-concept project
- Web scraping components require `bs4` and `lxml`
- OpenAI API key required for LLM features

## When Making Changes

- Update tests for new functionality
- Run `pytest` before committing
- Follow existing patterns in `src/catalog/cli/cli.py` for new CLI commands
- All source code is in `src/catalog/` directory with modular structure (cli/, api/, core/)

## Git Commit Guidelines

- Use conventional commits format: `type(scope): message`
  - **Types**: feat, fix, docs, refactor, test, chore, style
  - **Example**: `feat(cli): add search command` or `fix(db): resolve connection timeout`
- Keep messages concise and descriptive (focus on "why" not "what")
- Always run tests before committing
- Stage only relevant files for each commit

### Using Claude for Commits

Simply ask Claude to commit your changes with commands like:

- "Commit these changes"
- "Create a commit for the CLI updates"
- "Commit with message 'feat: add vector search'"

Claude will automatically:

1. Check `git status` and `git diff` to review changes
2. Review recent commits for style consistency
3. Draft an appropriate commit message
4. Stage relevant files
5. Create the commit with attribution footer

**Safety Notes**:

- Claude follows Git Safety Protocol (no force pushes, no skipping hooks)
- Claude will not push to remote unless explicitly requested
- Pre-commit hooks will be respected

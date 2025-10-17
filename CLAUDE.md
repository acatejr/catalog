# Catalog - AI Assistant Context

## Project Overview
A proof-of-concept metadata catalog that harvests publicly available data, stores it in a vector database, and enables LLM-enhanced search using Retrieval-Augmented Generation (RAG).

## Tech Stack
- **Language**: Python 3.13+
- **Package Manager**: pip (requirements.txt)
- **Key Dependencies**: FastAPI, LangChain, OpenAI, PostgreSQL (psycopg2), Sentence Transformers
- **Testing**: pytest with coverage
- **Documentation**: MkDocs Material
- **Linting**: Ruff

## Project Structure
- `src/` - Main application code
  - `cli.py` - Command-line interface (Typer)
  - `api.py` - FastAPI endpoints
  - `db.py` - Database operations
  - `llm.py` - LLM integration logic
  - `schema.py` - Data schemas
- `docs/` - MkDocs documentation
- `tests/` - Test suite
- `data/` - Downloaded metadata storage

## Development Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run CLI (requires PYTHONPATH since code is in src/)
PYTHONPATH=src python src/cli.py --help

# Run specific commands
PYTHONPATH=src python src/cli.py download-all
PYTHONPATH=src python src/cli.py embed-and-store
PYTHONPATH=src python src/cli.py run-api

# Run tests
pytest

# Serve docs locally
mkdocs serve
```

## Key Conventions
- Use Ruff for linting and formatting
- Environment variables stored in `.env`
- Docker Compose available for containerized setup

## Database
- PostgreSQL with vector extension support
- Schema defined in `schema.sql`
- Vector embeddings for RAG functionality

## Important Notes
- This is a proof-of-concept project
- Web scraping components require `bs4` and `lxml`
- OpenAI API key required for LLM features
- Documentation hosted at: https://main.catalog-6fe.pages.dev/

## When Making Changes
- Update tests for new functionality
- Run `pytest` before committing
- Update documentation in `docs/` if adding features
- Follow existing patterns in `src/cli.py` for new commands
- All source code is in `src/` directory

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

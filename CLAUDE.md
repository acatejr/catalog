# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Catalog is a Python CLI tool for downloading and managing geospatial data from the USFS Geodata Clearinghouse. The project focuses on fetching metadata (XML) and web services information (JSON) from https://data.fs.usda.gov.

## Development Commands

### Environment Setup
```bash
# Install dependencies using uv (preferred)
uv sync

# Or use pip in development mode
pip install -e .
```

### Running the CLI
```bash
# The CLI is available via the 'timbercat' command after installation
timbercat --help

# Test basic health check
timbercat health

# Download FSGeodata files (downloads to data/fsgeodata/)
timbercat download-fsgeodata
```

### Code Quality
```bash
# Format and lint with ruff (configured as dev dependency)
ruff check .
ruff format .
```

## Architecture

### CLI Structure
The project uses Click for CLI implementation with a command group pattern:
- Entry point: `src/catalog/main.py` defines the CLI group via `@click.group()`
- Individual commands are registered with `@cli.command()`
- The `main()` function in `__init__.py` serves as the package entry point, mapped to the `timbercat` command in pyproject.toml

### Module Organization
```
src/catalog/
├── __init__.py          # Package entry point (exports main())
├── main.py              # CLI group and command definitions
└── fsgeodata.py         # FSGeodataDownloader class for data fetching
```

### FSGeodataDownloader Class
Located in `src/catalog/fsgeodata.py`, this class handles all data downloading:
- Scrapes the datasets page (https://data.fs.usda.gov/geodata/edw/datasets.php)
- Extracts metadata XML URLs and MapServer service URLs using BeautifulSoup
- Downloads files to structured directories:
  - `data/fsgeodata/metadata/*.xml` - Dataset metadata
  - `data/fsgeodata/services/*_service.json` - Web service definitions
- Uses requests.Session for HTTP requests with rate limiting (0.5s delay between downloads)
- Provides rich console output for progress tracking

### Key Design Patterns
- **Session Management**: Uses requests.Session with custom User-Agent headers for all HTTP operations
- **Path Management**: Utilizes pathlib.Path for cross-platform file operations
- **Error Handling**: Catches RequestException and continues downloading remaining datasets
- **Rate Limiting**: Built-in 0.5s sleep between requests to avoid overwhelming the server

## Environment Variables

The project expects a `.env` file (see `.env.example` for template):
- Database configuration (POSTGRES_*)
- LLM/AI API settings (LLM_API_KEY, LLM_BASE_URL, LLM_MODEL)
- API keys (X_API_KEY, GITHUB_TOKEN)
- CATALOG_API_BASE_URL for future API integration

Note: Currently the FSGeodata downloader doesn't use these environment variables, but they're reserved for future features.

## Python Version

Requires Python >=3.14 (specified in pyproject.toml). The project uses a .python-version file for version pinning.

## Data Directory Structure

The `data/` directory is created automatically and organized as:
```
data/fsgeodata/
├── metadata/     # XML metadata files for each dataset
└── services/     # JSON service definitions for MapServer endpoints
```

## Instructions

When running, IGNORE data/catalog.json.  I do NOT want to consume tokens or use up my Anthropic token limits.
If you don't know the answer to something, don't guess, just say you don't know.

## Current Work (January 2025)

### Open Issues
- `core.py:20` - logs directory not auto-created, causes FileNotFoundError (fix: add `Path("./logs").mkdir(exist_ok=True)`)

### In Progress
- `suggested_enhancements.md` created (excluded from git via `.git/info/exclude`)
  - Contains RAG enhancement recommendations, blog/LinkedIn content ideas
  - Ready to review for implementation priorities

### Next Steps
1. Consider implementing hybrid search (BM25 + vector) per enhancements doc


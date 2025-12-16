# Project Overview

The 'catalog' project is a Python-based command-line interface (CLI) application designed to aggregate and process geospatial and tabular metadata from various sources, including the USFS Geodata Clearinghouse, Research Data Archive (RDA), and Geospatial Data Discovery (GDD). Its primary function is to download metadata files, parse them, and consolidate the information into a unified catalog, typically saved as `data/catalog.json`.

**Main Technologies:**

*   **Python:** Core language.
*   **click:** For building the command-line interface.
*   **bs4, lxml, requests:** For web scraping and data retrieval.
*   **pydantic:** For data validation and serialization.
*   **rich:** For rich text and beautiful formatting in the terminal.
*   **uv:** For dependency management and package installation.
*   **MkDocs:** For project documentation (though current `mkdocs.yml` is minimal).

**Architecture:**

The project follows a modular structure with dedicated modules for different data sources (`fsgeodata.py`, `gdd.py`, `rda.py`) and a `lib.py` for common utilities. The `main.py` file serves as the CLI entry point, orchestrating the download and parsing processes. Data is likely modeled using Pydantic schemas defined in `schema.py`.

**Building and Running**

**Installation:**

Assuming `uv` is installed, install dependencies using:
```bash
uv sync
```

**Running the Application:**

The project uses a Click-based CLI with the entry point `timbercat`.

*   **Health Check:**
    ```bash
    uv run timbercat health
    ```
*   **Download FSGeodata:**
    ```bash
    uv run timbercat download_fsgeodata
    ```
*   **Download RDA Metadata:**
    ```bash
    uv run timbercat download_rda
    ```
*   **Download GDD Metadata:**
    ```bash
    uv run timbercat download_gdd
    ```
*   **Parse and Generate Catalog JSON:**
    ```bash
    uv run timbercat get_docs
    ```
    This command reads metadata from all sources and compiles them into `data/catalog.json`.

**Testing:**

Testing commands are not explicitly defined in the `pyproject.toml` or `README.md`. It's likely that `pytest` is used given the `.pytest_cache` directory.
To run tests:
```bash
# TODO: Confirm actual test command, e.g., pytest
```

**Development Conventions**

*   **Code Formatting:** The presence of `.ruff_cache` suggests `ruff` is used for linting and formatting. Developers should ensure code adheres to `ruff`'s standards.
*   **Documentation:** `mkdocs.yml` indicates that MkDocs is used for project documentation. Updates to documentation should follow MkDocs conventions.

**GEMINI Instructions**

- Ignore the scratch folder
- Do not guess at questions, just say you don't know.

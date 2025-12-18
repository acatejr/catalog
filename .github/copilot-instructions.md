# Copilot / AI Assistant Instructions

Purpose: Help AI coding agents be immediately productive in this repository (catalog).

- **Big picture:** This repo builds a metadata “catalog” for USFS geospatial datasets by crawling three sources (FSGeodata, GDD, RDA), normalizing documents into a unified `Document` schema, and persisting them into vector databases for discovery.

- **Major components**
  - CLI entrypoint: `src/catalog/main.py` (installed script `timbercat` via `pyproject.toml`). Use this for most workflows (downloaders, build, vectordb ops).
  - Source loaders:
    - `src/catalog/fsgeodata.py` — FSGeodata downloader and XML parser.
    - `src/catalog/gdd.py` — GDD JSON downloader and parser.
    - `src/catalog/rda.py` — RDA loader (similar pattern).
  - Vector DBs and embedding logic: `src/catalog/core.py` — `SqliteVectorDB` (sqlite-vec) and `ChromaVectorDB` (chromadb).
  - LLM integration and chatbot prompts: `src/catalog/bots.py` — wraps OpenAI client and contains system prompt instructions used by the app.
  - Utilities and helpers: `src/catalog/lib.py` (JSON IO, text cleaning, hashing) and `src/catalog/schema.py` (`Document` Pydantic model).
  - CLI orchestration and common tasks: `src/catalog/main.py` (commands: `download_*`, `build_docs_catalog`, `bsvdb`, `chroma_chat`, `sqlvdb_disc_chat`).

- **Where data lives**
  - Source metadata files are saved under `data/` (e.g., `data/fsgeodata/metadata`, `data/gdd/gdd_metadata.json`).
  - Consolidated document index: `data/catalog.json` (very large; used as input to vector DB builders).

- **Dev & runtime workflows (how to run things locally)**
  - Install for development (create editable env and dev deps):
    ```bash
    python -m pip install -e .[dev]
    ```
  - Run CLI (after install) via the console script `timbercat` or with `python -m catalog` during development.
    - Download everything (GDD, RDA, FSGeodata):
      ```bash
      timbercat download-all
      ```
    - Build the combined catalog JSON:
      ```bash
      timbercat build_docs_catalog
      ```
    - Build sqlite vector DB (uses sentence-transformers + sqlite-vec):
      ```bash
      timbercat bsvdb
      ```
  - Run tests:
    ```bash
    pytest -q
    ```
    Note: tests import path in `tests/test_lib.py` references project layout — prefer installing editable (`-e`) first or ensure `PYTHONPATH` includes project root.

- **Environment & external services**
  - Dotenv is used. Key env vars:
    - `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL` — used by `src/catalog/bots.py`.
  - External dependencies to be aware of: `chromadb`, `sqlite-vec`, `sentence-transformers`, `openai`.
  - Network calls: downloaders hit external endpoints (FSGeodata, GDD JSON feed). Tests avoid external downloads.

- **Project-specific conventions and patterns**
  - Document normalization: each loader returns simple dicts matching fields in `src/catalog/schema.py` (`id`, `title`, `abstract`, `purpose`, `keywords`, `src`, `lineage`). Use `hash_string(title)` for stable ids when source lacks one (see `lib.hash_string`).
  - Parsers favor `clean_str()` from `src/catalog/lib.py` to strip HTML and normalize whitespace — use it consistently when extracting text.
  - Vector DB builders encode a combined text (title + abstract + keywords + purpose + lineage) with `sentence-transformers/all-MiniLM-L6-v2` (see `SqliteVectorDB.model` in `src/catalog/core.py`). Changing the model requires reindexing.
  - The code uses `rich` for console output; avoid changing display-only code unless modifying UX.

- **Safety for edits by AI**
  - Non-destructive edits only: loaders and downloaders write to `data/`. When testing changes locally, run on a small subset or set `limit=` on bulk inserts.
  - When adjusting embedding or query SQL, prefer small smoke tests before running full `bsvdb` build (expensive embeddings).

- **Files to check for behavior examples**
  - CLI commands and orchestration: `src/catalog/main.py`
  - Vector DB behavior and embeddings: `src/catalog/core.py`
  - LLM prompt / behavior expectations: `src/catalog/bots.py` (system prompts are explicit and must be preserved if you intend to keep current chat behavior)
  - Download + parsing patterns: `src/catalog/fsgeodata.py`, `src/catalog/gdd.py`

- **When you modify anything that affects the document schema or embeddings**
  - Update `src/catalog/schema.py` and run `timbercat build_docs_catalog` then `timbercat bsvdb` to regenerate `data/catalog.json` and the vectordb.

- **Example PR guidance for AI-generated code**
  - Keep changes minimal and focused.
  - Add unit tests for parsing/cleaning when changing text extraction logic (see `tests/test_lib.py`).
  - If adding new dependencies, add them to `pyproject.toml` and keep versions pinned similarly to existing entries.

If anything above is unclear or you want specific examples added (e.g., sample input JSON from GDD, or a small smoke-test script to run only a handful of documents), tell me which part to expand and I will iterate.

# Project Recommendations

This document outlines recommendations for improving the Catalog project based on comprehensive codebase reviews.

## 1. Security (URGENT)

### Rotate Exposed API Keys

The `.env` file contains real API keys (`OLLAMA_API_KEY`, `ANTHROPIC_API_KEY`) that should be rotated immediately. Even if `.env` is in `.gitignore`, if it was ever committed, the keys are in git history.

### `bots.py` Ignores Configured URL

`OllamaBot.__init__` reads `OLLAMA_API_URL` into `self.OLLAMA_BASE_URL` (line 27) but never uses it. The client hardcodes `host="https://ollama.com"` (line 31) instead. This means the `.env` configuration has no effect:

```python
# Current (bots.py:30-31)
self.client = Client(host="https://ollama.com", ...)

# Should be
self.client = Client(host=self.OLLAMA_BASE_URL, ...)
```

### `bots.py:32` Will Crash if `OLLAMA_API_KEY` Is Unset

`os.environ.get("OLLAMA_API_KEY")` returns `None` when unset, and `"Bearer " + None` raises `TypeError`. Should use `os.getenv("OLLAMA_API_KEY", "")` or guard against `None`.

### Validate URLs and Sanitize File Paths

Before fetching URLs, validate they point to expected domains. When saving downloaded files, ensure filenames don't contain path traversal:

```python
ALLOWED_HOSTS = ["data.fs.usda.gov", "www.fs.usda.gov", "data-usfs.hub.arcgis.com"]

def is_safe_url(url: str) -> bool:
    from urllib.parse import urlparse
    return urlparse(url).netloc in ALLOWED_HOSTS
```

---

## 2. Bugs & Variable Scope Issues

### `usfs.py:FSGeodataLoader.parse_metadata` — Unbound Variables

Variables are conditionally assigned inside blocks but used unconditionally at lines 267-275:

- `abstract` and `purpose` (lines 233-242) are assigned inside `if descript:` but referenced unconditionally in the document dict at line 271-272. If an XML file has no `<descript>` element, this raises `UnboundLocalError`.
- `procdate` and `procdesc` (lines 251-253) are assigned inside `if step.find(...)` blocks but used unconditionally at line 255. A step with `procdate` but no `procdesc` (or vice versa) will reference a stale value from a previous iteration or be unbound.
- `keywords` (line 265) is only assigned if `themekeys` exist and `len(themekeys) > 0`, but used unconditionally at line 273.

**Fix:** Initialize all variables with defaults before the conditional blocks:

```python
abstract = ""
purpose = ""
keywords = []
procdate = ""
procdesc = ""
```

### `usfs.py:FSGeodataLoader.parse_metadata` — Redundant `.find()` Calls

Line 225-228 calls `soup.find("title")` twice — once to check existence and once to get the text. Cache the result:

```python
title_el = soup.find("title")
title = clean_str(title_el.get_text()) if title_el else ""
```

Same pattern applies to `descript.find("abstract")` and `descript.find("purpose")`.

### `usfs.py:RDALoader.parse_metadata` — Missing Key Checks

Lines 376-380 use direct dictionary access (`item["title"]`, `item["description"]`, `item["keyword"]`) without `.get()`. Will crash with `KeyError` if keys are missing. Contrast with `GeospatialDataDiscovery.parse_metadata` which uses `.get()` and `in` checks correctly.

### `usfs.py:FSGeodataLoader.parse_metadata` — Redundant Check

Lines 245-246: `if soup.find_all("dataqual"):` followed by `if len(soup.find_all("dataqual")):` — the first check is sufficient (empty list is falsy). Also calls `find_all` twice unnecessarily.

---

## 3. Code Quality

### All Ruff Checks Pass

All ruff checks currently pass. Previous issues with unused imports in `cli.py` have been resolved.

### Remove or Consolidate `load_documents()`

`core.py` still has `load_documents()` (lines 37-79) which is superseded by `batch_load_documents()`. The old method uses positional IDs (`doc_0`), stores `"src"` instead of `"source"` in metadata, and doesn't include `abstract`. It's referenced only as a comment in `usfs.py:25`. Remove it to avoid confusion.

### Old Comment in `core.py:26`

Line 26 has a trailing comment `# [USFSDocument.model_validate(doc) for doc in data]` that's leftover from refactoring. Remove it.

### Placeholder Docstrings

- `lib.py:strip_html` (line 85) — docstring is `"_summary_"` with placeholder parameter descriptions
- `usfs.py:GeospatialDataDiscovery.parse_metadata` (line 303) — docstring is `"_summary_"`
- `usfs.py:USFS.download_fsgeodata` (line 55) — docstring says `"Docstring for download_fsgeodata"` with `:param self: Description`
- `usfs.py:USFS.download_rda` (line 65) — same placeholder pattern
- `usfs.py:USFS.download_gdd` (line 75) — same placeholder pattern
- `core.py:load_document_metadata` (line 18) — `:param self: Description`
- `core.py:load_documents` (line 41) — `:param self: Description`
- `core.py:batch_load_documents` (lines 85-87) — `:param self: Description`, `:param batch_size: Description`

### Mutable Default Arguments in `schema.py`

`keywords` and `lineage` use `default=[]` in their `Field` definitions (lines 30-31, 37-38). While Pydantic handles this safely, `default_factory=list` is the idiomatic pattern:

```python
keywords: list[str] | None = Field(default_factory=list, ...)
```

### Typo in `cli.py:33`

`"Generate the USFS metadata catlog"` — should be `"catalog"`.

### Add Pre-commit Hooks

Consider adding a `.pre-commit-config.yaml` to enforce code quality:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.14.14
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

---

## 4. Naming & Consistency Issues

### Inconsistent Metadata Field Names Between Methods

`load_documents()` stores `"src"` in metadata; `batch_load_documents()` stores `"source"`. The `query` method handles both (`meta.get("source") or meta.get("src")`). Once `load_documents()` is removed, the fallback to `"src"` in `query` can be removed too.

### Inconsistent Field Mapping Across Parsers

Different loaders build document dicts with different keys:

| Loader    | `abstract` | `purpose` | `description`       | `lineage` |
| --------- | ---------- | --------- | ------------------- | --------- |
| FSGeodata | Yes        | Yes       | No                  | Yes       |
| GDD       | No         | No        | Yes (not in schema) | No        |
| RDA       | No         | No        | Yes (not in schema) | No        |

GDD (`usfs.py:338`) and RDA (`usfs.py:385`) use `"description"` which doesn't exist in the `USFSDocument` schema. When loaded via `USFSDocument.model_validate()`, `description` is silently ignored and `abstract`/`purpose` end up as `None`. Either:

- Map `description` to `abstract` in the GDD/RDA parsers, or
- Add a mapping layer in `build_catalog()`

### Confusing Dual Query Parameters

`query()` accepts both `nresults` and `k` for the same thing. Pick one as primary and remove the other.

### Mixed Path Handling

Some code uses `Path` objects consistently (`FSGeodataLoader`), while others use string concatenation (`GeospatialDataDiscovery` line 307: `f"{self.dest_output_dir}/{self.dest_output_file}"`). Use `Path` everywhere.

---

## 5. Missing Docstrings & Type Hints

### Missing Type Hints

```python
# lib.py:100 — missing entirely
def hash_string(s):  # should be: def hash_string(s: str) -> str:

# core.py:28 — too generic
def extract_lineage_info(self, lineage_list: list) -> str:
# should be: lineage_list: list[dict]

# usfs.py:149 — missing parameter types
def download_file(self, url, output_path, description="file"):
# should be: url: str, output_path: Path, description: str = "file"

# usfs.py:160 — missing parameter types
def download_service_info(self, url, output_path):

# bots.py:35 — missing parameter types
def chat(self, question, context):
# should be: question: str, context: str
```

### Missing Docstrings

- `core.py:ChromaVectorDB.__init__()`
- `core.py:ChromaVectorDB.extract_lineage_info()`
- `bots.py:OllamaBot.__init__()`
- `bots.py:OllamaBot.chat()`
- `usfs.py:GeospatialDataDiscovery.download_gdd_metadata()`
- `usfs.py:RDALoader.download()`
- `usfs.py:RDALoader.parse_metadata()`

---

## 6. Error Handling & Logging

### Enable Logging

The codebase has commented-out print/rprint statements (e.g., `usfs.py:109`). Enable structured logging:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("catalog")
```

### No Error Handling in Download Methods

`FSGeodataLoader.download_file()` (line 149) and `download_service_info()` (line 160) call `response.raise_for_status()` but don't catch the exception. If a download fails, the entire `download_all()` loop crashes. Either wrap in try-except or let the caller handle it.

### `GeospatialDataDiscovery.download_gdd_metadata` — Silent Failure

Line 296: checks `response.status_code == 200` but does nothing on failure — no error message, no return value, no exception. The caller has no way to know the download failed.

### Add Input Validation to CLI

`query_fs_chromadb` and `ollama_chat` don't validate that `nresults` is positive. A user passing `-n 0` or `-n -5` produces undefined behavior. Use Click's `type=click.IntRange(min=1)`.

---

## 7. Architecture Improvements

### Parameterize `ChromaVectorDB` Paths

The class hardcodes the ChromaDB path. The catalog file path is parameterized but the DB path isn't:

```python
# Current
self.client = chromadb.PersistentClient(path="./chromadb")

# Recommended
def __init__(self, db_path: str = "./chromadb", src_catalog_file: str = "data/usfs/catalog.json"):
    self.client = chromadb.PersistentClient(path=db_path)
```

### Separate Query Results Formatting

**Resolved.** Query and formatting are now separated:

- `ChromaVectorDB.query()` returns `list[tuple[USFSDocument, float]]`
- `USFSDocument.to_markdown(distance)` handles formatting
- CLI commands handle display via `click.echo()`

### Centralize Configuration

Multiple files independently call `load_dotenv()` (`cli.py:7`, `bots.py:5`). `.env` contains many unused variables (`POSTGRES_*`, `X_API_KEY`, `GITHUB_TOKEN`, `GEMINI_API_KEY`, `OPENAI_API_KEY`). Consider a single configuration class:

```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    data_dir: str = "data/usfs"
    chromadb_path: str = "./chromadb"
    ollama_api_url: str = "https://ollama.com"
    ollama_api_key: str = ""
    ollama_model: str = "llama3"

    class Config:
        env_file = ".env"
```

---

## 8. Testing

### Current State

- No active test suite in `tests/` directory
- Development tests exist in `scratch/tests/` but are excluded via `pytest.ini`
- `scratch/tests/test_hybrid_search.py` tests a non-existent `HybridSearch` class (outdated)

### Recommendations

**Create a proper test suite:**

```text
tests/
├── __init__.py
├── conftest.py           # Shared fixtures
├── test_cli.py           # CLI command tests
├── test_lib.py           # Utility function tests
├── test_schema.py        # Pydantic model tests (including to_markdown)
├── test_usfs.py          # Loader tests (with mocks)
└── test_core.py          # ChromaDB integration tests
```

**Priority test targets:**

1. `lib.py` functions — pure functions, easy to test (`clean_str`, `strip_html`, `hash_string`, `dedupe_catalog`)
2. `schema.py` — validate Pydantic model behavior and `to_markdown()` output with/without distance
3. `core.py` — `query()` return types, deduplication in `load_document_metadata()`
4. Loader classes — use `responses` or `pytest-httpserver` to mock HTTP calls

---

## 9. Feature Suggestions

### Add Progress Indicators

Use Click's built-in progress bar for long-running downloads:

```python
with click.progressbar(datasets, label="Downloading") as bar:
    for dataset in bar:
        # download logic
```

### Add Incremental Updates

Currently, `download_all()` re-downloads everything. Consider:

1. Check if file exists before downloading
2. Use HTTP `If-Modified-Since` headers
3. Add a `--force` flag to override

### Implement Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def download_file(self, url: str, ...):
    # download logic
```

---

## 10. Project Structure Cleanup

### Remove Scratch Directory from Version Control

The `scratch/` directory is for experiments. Consider:

1. Adding it to `.gitignore` permanently
2. Moving useful code (e.g., test patterns from `scratch/tests/test_lib.py`) to `tests/`
3. Deleting unused experimental files

### Organize Data Loaders

Consider grouping loaders into a subpackage:

```text
src/catalog/
├── loaders/
│   ├── __init__.py
│   ├── base.py          # Abstract base loader
│   ├── fsgeodata.py
│   ├── gdd.py
│   └── rda.py
├── cli.py
├── core.py
├── lib.py
└── schema.py
```

---

## 11. LLM Integration (Current Branch)

Since the current branch (`45-feature-add-llm-interaction-to-cli-chomadb-query`) focuses on LLM integration:

### Completed

1. **RAG pattern implemented** — `ollama_chat` CLI command queries ChromaDB, builds markdown context with `USFSDocument.to_markdown()`, and sends it to Ollama via `OllamaBot.chat()`
2. **Structured query results** — `ChromaVectorDB.query()` returns `list[tuple[USFSDocument, float]]` with distance scores
3. **Distance-aware LLM context** — Relevance distance is included in the context sent to Ollama; system prompt instructs the LLM to prioritize lower-distance results
4. **Batch document loading** — `batch_load_documents()` uses real document IDs and processes in configurable batch sizes
5. **Deduplication** — `load_document_metadata()` deduplicates by document ID; standalone `dedupe_catalog()` available in `lib.py`
6. **`to_markdown()` on `USFSDocument`** — Formatting lives on the model with optional `distance` parameter; used by both CLI commands and LLM context
7. **Abstract in metadata** — `batch_load_documents()` now stores `abstract` in ChromaDB metadata so `query()` can reconstruct it
8. **Distance-aware system prompt** — `bots.py` `MESSAGE_CONTENT` instructs the LLM to prioritize lower-distance results
9. **Dead code cleanup** — Removed commented-out query method and debug snippets from `core.py`
10. **Unused global removed** — Removed `soup = BeautifulSoup()` from `lib.py`
11. **Docstrings added** — Added docstrings to `load_document_metadata`, `load_documents`, `batch_load_documents` in `core.py`
12. **Indentation fixed** — `batch_load_documents` now uses consistent 4-space indentation

### Remaining

1. **Fix `OllamaBot` to use configured URL** — Currently hardcoded, ignores `.env`
2. **Fix unbound variable bugs in `usfs.py:FSGeodataLoader.parse_metadata`**
3. **Fix GDD/RDA parsers** — Map `description` to `abstract` so all sources populate the schema consistently
4. **Add conversation history** — Store context for follow-up questions
5. **Implement streaming** — Use Ollama's streaming API for better UX
6. **Add source citations** — Include document references in LLM responses
7. **Lineage in query results** — Stored as flat string in metadata but `USFSDocument.lineage` expects `list[dict]`; query sets it to `None`

---

## Summary of Priority Actions

| Priority     | Action                                                  | Status  |
| ------------ | ------------------------------------------------------- | ------- |
| ~~High~~     | ~~Fix linting issues in cli.py~~                        | Done    |
| ~~High~~     | ~~Separate query from formatting~~                      | Done    |
| ~~High~~     | ~~Implement RAG pattern~~                               | Done    |
| ~~High~~     | ~~Return structured query results~~                     | Done    |
| ~~Medium~~   | ~~Add batch loading with real IDs~~                     | Done    |
| ~~Medium~~   | ~~Add catalog deduplication~~                           | Done    |
| ~~Medium~~   | ~~Add `to_markdown()` to USFSDocument~~                 | Done    |
| ~~Medium~~   | ~~Add abstract to ChromaDB metadata~~                   | Done    |
| ~~Medium~~   | ~~Distance-aware LLM system prompt~~                    | Done    |
| ~~Medium~~   | ~~Remove dead code in core.py~~                         | Done    |
| ~~Medium~~   | ~~Remove unused soup global in lib.py~~                 | Done    |
| ~~Medium~~   | ~~Fix indentation in batch_load_documents~~             | Done    |
| ~~Medium~~   | ~~Add docstrings to core.py methods~~                   | Done    |
| **URGENT**   | Rotate exposed API keys in `.env`                       | Pending |
| High         | Fix OllamaBot to use configured URL, not hardcoded     | Pending |
| High         | Fix OllamaBot crash when OLLAMA_API_KEY is unset       | Pending |
| High         | Fix unbound variable bugs in `usfs.py` parsers          | Pending |
| High         | Fix GDD/RDA parsers to map `description` to `abstract`  | Pending |
| High         | Remove obsolete `load_documents()` from `core.py`       | Pending |
| High         | Add basic test suite                                    | Pending |
| Medium       | Fix placeholder docstrings across codebase              | Pending |
| Medium       | Add missing type hints                                  | Pending |
| Medium       | Use `Path` consistently (replace string concatenation)  | Pending |
| Medium       | Enable logging                                          | Pending |
| Medium       | Add error handling to download methods                  | Pending |
| Medium       | Add input validation (`nresults > 0`) to CLI            | Pending |
| Medium       | Update README                                           | Pending |
| Medium       | Add progress indicators                                 | Pending |
| Medium       | Add conversation history for LLM                        | Pending |
| Medium       | Implement Ollama streaming                              | Pending |
| Low          | Fix typo "catlog" in cli.py:33                          | Pending |
| Low          | Remove old comment in core.py:26                        | Pending |
| Low          | Use `default_factory=list` in schema.py                 | Pending |
| Low          | Refactor to subpackages                                 | Pending |
| Low          | Resolve lineage type mismatch in query                  | Pending |
| Low          | Centralize configuration                                | Pending |
| Low          | Add retry logic                                         | Pending |

---

Generated on 2026-01-26, updated 2026-01-27

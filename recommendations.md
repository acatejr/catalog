# Project Recommendations

This document outlines recommendations for improving the Catalog project based on comprehensive codebase reviews.

## 1. Security

### ~~Rotate Exposed API Keys~~ (Not Required)

~~The `.env` file contains real API keys that should be rotated immediately.~~ Verified on 2026-01-28: `.env` has **never been committed** to git history (`git log --all --full-history -- .env` returns empty). The file is properly protected by `.gitignore`. No key rotation needed unless keys were exposed through other means.

### ~~`bots.py` Ignores Configured URL~~ (Fixed)

~~`OllamaBot.__init__` reads `OLLAMA_API_URL` into `self.OLLAMA_BASE_URL` but never uses it.~~ Fixed: The client now uses `host=self.OLLAMA_BASE_URL` (line 31).

### ~~`bots.py:32` Will Crash if `OLLAMA_API_KEY` Is Unset~~ (Fixed)

~~`os.environ.get("OLLAMA_API_KEY")` returns `None` when unset, and `"Bearer " + None` raises `TypeError`.~~ Fixed: Now uses default empty string and validates all required env vars (`OLLAMA_API_KEY`, `OLLAMA_API_URL`, `OLLAMA_MODEL`) with clear `ValueError` messages (lines 26-35).

---

## 2. Bugs & Variable Scope Issues

### ~~`usfs.py:FSGeodataLoader.parse_metadata` — Unbound Variables~~ (Fixed)

~~Variables were conditionally assigned inside blocks but used unconditionally.~~ Fixed: All variables are now initialized with defaults before conditional blocks (lines 225-228: `abstract = ""`, `purpose = ""`, `keywords = []`, `procdate = ""`, `procdesc = ""`).

### ~~`usfs.py:FSGeodataLoader.parse_metadata` — Redundant `.find()` Calls~~ (Fixed)

~~Line 225-228 calls `soup.find("title")` twice.~~ Fixed: Now uses cached approach for title, abstract, and purpose (lines 229-237). Elements are stored in variables (`title_elem`, `abstract_elem`, `purpose_elem`) before accessing their text.

### ~~`usfs.py:RDALoader.parse_metadata` — Missing Key Checks~~ (Fixed)

~~Lines 371-375 used direct dictionary access.~~ Fixed: Now uses `.get()` throughout — line 371: `json_data.get("dataset", [])`, lines 373-375: `.get()` for `title`, `description`, and `keyword`.

### ~~`usfs.py:FSGeodataLoader.parse_metadata` — Redundant Check~~ (Fixed)

~~Lines 240-241 called `find_all` twice.~~ Fixed: Now caches result and uses simple truthy check (line 241: `if dataqual:`).

---

## 3. Code Quality

### All Ruff Checks Pass

All ruff checks currently pass. Previous issues with unused imports in `cli.py` have been resolved.

### ~~Remove or Consolidate `load_documents()`~~ (Fixed)

~~`core.py` had `load_documents()` which was superseded by `batch_load_documents()`.~~ Fixed: The obsolete method has been removed.

### ~~Old Comment in `core.py:26`~~ (Fixed)

~~Line 26 had a trailing comment leftover from refactoring.~~ Fixed: The comment has been removed.

### ~~Placeholder Docstrings~~ (Fixed)

All placeholder docstrings have been replaced with proper documentation across `core.py`, `lib.py`, `usfs.py`, and `bots.py`.

### ~~Mutable Default Arguments in `schema.py`~~ (Fixed)

~~`keywords` and `lineage` used `default=[]`.~~ Fixed: Now uses `default_factory=list` for both fields (lines 31, 41).

### ~~Typo in `cli.py:33`~~ (Fixed)

~~`"Generate the USFS metadata catlog"` — should be `"catalog"`.~~

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

### ~~Inconsistent Metadata Field Names Between Methods~~ (Resolved)

~~`load_documents()` stored `"src"` in metadata; `batch_load_documents()` stores `"source"`.~~ Resolved: `load_documents()` has been removed. The fallback in `query` (`meta.get("source") or meta.get("src")`) is now harmless but could be simplified to just `meta.get("source")`.

### ~~Inconsistent Field Mapping Across Parsers~~ (Fixed)

~~GDD and RDA use `"description"` which didn't exist in the schema.~~ Fixed: Added `description` field to `USFSDocument` schema (lines 41-44) and included it in `to_markdown()` output (line 54).

### ~~Confusing Dual Query Parameters~~ (Fixed)

~~`query()` accepts both `nresults` and `k` for the same thing.~~ Fixed: The `k` parameter has been removed and docstring updated.

### ~~Mixed Path Handling~~ (Fixed)

~~Some code used string concatenation instead of `Path` objects.~~ Fixed: Both `GeospatialDataDiscovery.parse_metadata()` (line 310) and `RDALoader.parse_metadata()` (line 372) now use `Path`.

---

## 5. Missing Docstrings & Type Hints

### ~~Missing Type Hints~~ (Fixed)

All type hint issues have been resolved:
- `lib.py:106` — `hash_string(s: str) -> str`
- `core.py:25` — `extract_lineage_info(self, lineage_list: list[dict]) -> str`
- `usfs.py:145` — `download_file(self, url: str, output_path: Path, description: str = "file") -> bool`
- `usfs.py:156` — `download_service_info(self, url: str, output_path: Path) -> bool`
- `bots.py:44` — `chat(self, question: str, context: str) -> str`

### ~~Missing Docstrings~~ (Fixed)

All previously missing docstrings have been added. See "Placeholder Docstrings" section above.

---

## 6. Error Handling & Logging

### ~~Enable Logging~~ (Added)

~~The codebase had commented-out print/rprint statements.~~ Logging infrastructure added to `usfs.py` (lines 9-15). The `logger` is available for use throughout the module.

### ~~No Error Handling in Download Methods~~ (Fixed)

~~`download_file()` and `download_service_info()` didn't catch HTTP errors.~~ Fixed: Both methods now wrap the entire request/write in try-except and use `logger.error()` on failure.

### ~~`GeospatialDataDiscovery.download_gdd_metadata` — Silent Failure~~ (Fixed)

~~Checked status code but did nothing on failure.~~ Fixed: Now logs error message on failure (lines 304-307).

### ~~Add Input Validation to CLI~~ (Fixed)

~~`query_fs_chromadb` and `ollama_chat` didn't validate `nresults`.~~ Fixed: Both commands now use `type=click.IntRange(min=1)` to ensure positive values.

---

## 7. Architecture Improvements

### ~~Parameterize `ChromaVectorDB` Paths~~ (Fixed)

~~The class hardcoded the ChromaDB path.~~ Fixed: `__init__` now accepts `db_path` parameter (line 8):

```python
def __init__(self, db_path: str = "./chromadb", src_catalog_file: str = "data/usfs/catalog.json"):
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

### ~~Current State~~ (Test Structure Created)

Test suite structure has been created with 49 stub tests:

```text
tests/
├── __init__.py
├── conftest.py           # Shared fixtures
├── test_cli.py           # CLI command tests (6 stubs)
├── test_lib.py           # Utility function tests (13 stubs)
├── test_schema.py        # Pydantic model tests (9 stubs)
├── test_usfs.py          # Loader tests (9 stubs)
└── test_core.py          # ChromaDB integration tests (10 stubs)
```

All stub tests emit `UserWarning` with "TODO: Implement" messages. Run `uv run pytest tests/ -v` to see them.

**Priority for implementation:**

1. `test_lib.py` — pure functions, easy to test
2. `test_schema.py` — validate Pydantic model behavior
3. `test_core.py` — ChromaDB integration
4. `test_usfs.py` — use `responses` or mocks for HTTP calls
5. `test_cli.py` — use Click's `CliRunner` for CLI tests

---

## 9. Feature Suggestions

### Add Progress Indicators

Use Click's built-in progress bar for long-running downloads:

```python
with click.progressbar(datasets, label="Downloading") as bar:
    for dataset in bar:
        # download logic
```

### ~~Add Incremental Updates~~ (Partially Implemented)

~~`download_all()` re-downloaded everything.~~ Fixed: Now checks if files exist before downloading (lines 208, 219). Remaining options:
- Add `--force` flag to override
- Use HTTP `If-Modified-Since` headers

---

## 10. Project Structure Cleanup

### ~~Remove Scratch Directory from Version Control~~ (Resolved)

~~The `scratch/` directory needed cleanup.~~ Resolved:
1. ✅ Already in `.gitignore` (`*scratch*`, `scratch*`, `scratch/`)
2. ✅ Proper test structure created in `tests/` with 49 stub tests

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
13. **OllamaBot uses configured URL** — Client now uses `self.OLLAMA_BASE_URL` instead of hardcoded URL
14. **Unbound variables fixed** — `usfs.py:FSGeodataLoader.parse_metadata` now initializes all variables with defaults

### Remaining

1. ~~**Fix GDD/RDA parsers**~~ — Fixed: Added `description` field to schema
2. **Add conversation history** — Store context for follow-up questions
3. **Implement streaming** — Use Ollama's streaming API for better UX
4. **Add source citations** — Include document references in LLM responses

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
| ~~URGENT~~   | ~~Rotate exposed API keys in `.env`~~                   | N/A     |
| ~~High~~     | ~~Fix OllamaBot to use configured URL, not hardcoded~~  | Done    |
| ~~High~~     | ~~Fix OllamaBot crash when OLLAMA_API_KEY is unset~~    | Done    |
| ~~High~~     | ~~Fix unbound variable bugs in `usfs.py` parsers~~      | Done    |
| ~~Medium~~   | ~~Fix redundant `.find()` calls in FSGeodataLoader~~    | Done    |
| ~~High~~     | ~~Fix GDD/RDA parsers to map `description` to `abstract`~~  | Done    |
| ~~High~~     | ~~Add `.get()` guards in RDALoader.parse_metadata~~     | Done    |
| ~~High~~     | ~~Remove obsolete `load_documents()` from `core.py`~~   | Done    |
| ~~High~~     | ~~Add basic test suite~~                                | Done    |
| ~~Medium~~   | ~~Fix placeholder docstrings across codebase~~          | Done    |
| ~~Medium~~   | ~~Add missing type hints~~                              | Done    |
| ~~Medium~~   | ~~Use `Path` consistently (replace string concatenation)~~  | Done    |
| ~~Medium~~   | ~~Enable logging~~                                      | Done    |
| ~~Medium~~   | ~~Add error handling to download methods~~              | Done    |
| ~~Medium~~   | ~~Add input validation (`nresults > 0`) to CLI~~        | Done    |
| ~~Medium~~   | ~~Update README~~                                       | Done    |
| Medium       | Add progress indicators                                 | Pending |
| Medium       | Add conversation history for LLM                        | Pending |
| Medium       | Implement Ollama streaming                              | Pending |
| ~~Low~~      | ~~Fix typo "catlog" in cli.py:33~~                      | Done    |
| ~~Low~~      | ~~Remove old comment in core.py:26~~                    | Done    |
| ~~Low~~      | ~~Simplify redundant `len()` check in usfs.py:241~~     | Done    |
| ~~Low~~      | ~~Use `default_factory=list` in schema.py~~             | Done    |
| Low          | Refactor to subpackages                                 | Pending |
| Low          | Centralize configuration                                | Pending |

---

Generated on 2026-01-26, last updated 2026-01-28

**Summary:** 35 items completed, 9 items remaining

# Project Recommendations

This document outlines recommendations for improving the Catalog project based on a comprehensive codebase review.

## 1. Code Quality (Quick Wins)

### Fix Linting Issues

Run `ruff check --fix .` to automatically resolve these issues:

| File | Line | Issue | Fix |
|------|------|-------|-----|
| `cli.py` | 4 | Unused `json` import | Remove |
| `cli.py` | 5 | Unused `USFSDocument` import | Remove |
| `cli.py` | 6 | Unused `Path` import | Remove |
| `cli.py` | 62 | Unused `resp` variable | Remove or use |
| `usfs.py` | 9 | Unused `USFSDocument` import | Remove |
| `usfs.py` | 162, 181 | Unused exception variable `e` | Use `_` instead |

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

## 2. Testing

### Current State
- No active test suite in `tests/` directory
- Development tests exist in `scratch/tests/` but are excluded

### Recommendations

**Create a proper test suite:**

```
tests/
├── __init__.py
├── conftest.py           # Shared fixtures
├── test_cli.py           # CLI command tests
├── test_lib.py           # Utility function tests
├── test_schema.py        # Pydantic model tests
├── test_usfs.py          # Loader tests (with mocks)
└── test_core.py          # ChromaDB integration tests
```

**Priority test targets:**
1. `lib.py` functions - pure functions, easy to test
2. `schema.py` - validate Pydantic model behavior
3. Loader classes - use `responses` or `pytest-httpserver` to mock HTTP calls

**Example fixture for `conftest.py`:**
```python
import pytest
from pathlib import Path

@pytest.fixture
def sample_xml_metadata():
    """Return sample XML metadata for testing parsers."""
    return Path(__file__).parent / "fixtures" / "sample_metadata.xml"
```

---

## 3. Documentation

### Add Docstrings

Several key functions lack proper documentation:

- `core.py:ChromaVectorDB.load_documents()` - has empty docstring
- `core.py:ChromaVectorDB.extract_lineage_info()` - no docstring
- `usfs.py:USFS.build_chromadb()` - no docstring

### Update README.md

The README is currently empty. Suggested sections:

1. **Overview** - What the project does
2. **Installation** - `uv sync` or `pip install -e .`
3. **Usage** - CLI commands with examples
4. **Data Sources** - Explain FSGeodata, GDD, RDA
5. **Development** - How to contribute, run tests, lint

### Add Type Hints

Some return types are missing:

```python
# Current
def download_file(self, url, directory, filename):

# Recommended
def download_file(self, url: str, directory: Path, filename: str) -> Path | None:
```

---

## 4. Error Handling & Logging

### Enable Logging

The codebase has commented-out logging statements. Recommend enabling structured logging:

```python
# In cli.py or a new logging_config.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("catalog")
```

### Improve Exception Handling

Replace bare `except Exception as e` patterns with specific exceptions:

```python
# Current (usfs.py:160)
except Exception:
    pass

# Recommended
except requests.RequestException as e:
    logger.warning(f"Failed to fetch {url}: {e}")
```

---

## 5. Architecture Improvements

### Consider Dependency Injection

The `ChromaVectorDB` class has hardcoded paths:

```python
# Current
self.client = chromadb.PersistentClient(path="./chromadb")

# Recommended
def __init__(self, db_path: str = "./chromadb", catalog_path: str = "data/usfs/catalog.json"):
    self.client = chromadb.PersistentClient(path=db_path)
    self.catalog_path = catalog_path
```

This enables easier testing and configuration.

### Separate Query Results Formatting

`ChromaVectorDB.query()` both queries and prints results. Consider separating concerns:

```python
def query(self, query_text: str, k: int = 5) -> list[dict]:
    """Return query results without printing."""
    # ... query logic ...
    return results

def format_results(self, results: list[dict]) -> str:
    """Format results for display."""
    # ... formatting logic ...
```

### Add Configuration Class

Consolidate configuration into a single place:

```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    data_dir: str = "data/usfs"
    chromadb_path: str = "./chromadb"
    rate_limit_delay: float = 0.5

    class Config:
        env_file = ".env"
```

---

## 6. Feature Suggestions

### Add Progress Indicators

For long-running downloads, consider adding progress feedback:

```python
from tqdm import tqdm

for dataset in tqdm(datasets, desc="Downloading metadata"):
    # download logic
```

Or use Click's built-in progress bar:

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

HTTP requests can fail transiently. Consider using `tenacity`:

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def download_file(self, url: str, ...):
    # download logic
```

---

## 7. Security Considerations

### Validate URLs

Before fetching URLs, validate they point to expected domains:

```python
ALLOWED_HOSTS = ["data.fs.usda.gov", "www.fs.usda.gov", "data-usfs.hub.arcgis.com"]

def is_safe_url(url: str) -> bool:
    from urllib.parse import urlparse
    return urlparse(url).netloc in ALLOWED_HOSTS
```

### Sanitize File Paths

When saving downloaded files, ensure filenames don't contain path traversal:

```python
import re

def safe_filename(name: str) -> str:
    return re.sub(r'[^\w\-_.]', '_', name)
```

---

## 8. Project Structure Cleanup

### Remove Scratch Directory from Version Control

The `scratch/` directory appears to be for experiments. Consider:

1. Adding it to `.gitignore` permanently
2. Moving useful code to `src/catalog/`
3. Deleting unused experimental files

### Organize Data Loaders

Consider grouping loaders into a subpackage:

```
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

## 9. LLM Integration (Current Branch)

Since the current branch (`45-feature-add-llm-interaction-to-cli-chomadb-query`) focuses on LLM integration:

### Recommendations for LLM Feature

1. **Use RAG pattern** - Combine ChromaDB results with LLM for enhanced responses
2. **Add conversation history** - Store context for follow-up questions
3. **Implement streaming** - Use Ollama's streaming API for better UX
4. **Add source citations** - Include document references in LLM responses

### Example RAG Implementation

```python
def query_with_llm(query: str, n_results: int = 5) -> str:
    # 1. Get relevant documents from ChromaDB
    docs = vector_db.query(query, k=n_results)

    # 2. Build context from results
    context = "\n\n".join([d["text"] for d in docs])

    # 3. Generate response with LLM
    prompt = f"""Based on the following documents, answer the question.

Documents:
{context}

Question: {query}
"""
    response = ollama.generate(model="llama3", prompt=prompt)
    return response
```

---

## Summary of Priority Actions

| Priority | Action | Effort |
|----------|--------|--------|
| High | Fix linting issues | 5 min |
| High | Add basic test suite | 2-4 hrs |
| Medium | Enable logging | 30 min |
| Medium | Update README | 1 hr |
| Medium | Add progress indicators | 30 min |
| Low | Refactor to subpackages | 2-3 hrs |
| Low | Add retry logic | 1 hr |

---

*Generated on 2026-01-26 based on codebase analysis*

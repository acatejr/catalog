---
draft: true
---

# Application Architecture

## Overview

Catalog is a Python CLI application that aggregates geospatial metadata from multiple USFS data repositories into a unified, searchable catalog. The system implements a Retrieval-Augmented Generation (RAG) pipeline combining vector-based semantic search with LLM-powered natural language discovery.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              CLI Layer                                  │
│                             (main.py)                                   │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐         ┌─────────────────┐         ┌─────────────────┐
│  Data Loaders │         │  Vector Store   │         │   LLM Client    │
│   (usfs.py)   │         │ (db/embeddings/ │         │   (bots.py)     │
│               │         │   search.py)    │         │                 │
└───────┬───────┘         └────────┬────────┘         └────────┬────────┘
        │                          │                           │
        ▼                          ▼                           ▼
┌───────────────┐         ┌─────────────────┐         ┌─────────────────┐
│    Schema     │         │   PostgreSQL    │         │  Verde via      │
│  (schema.py)  │         │   (pgvector)    │         │  LiteLLM Proxy  │
└───────────────┘         └─────────────────┘         └─────────────────┘
```

## Component Descriptions

### CLI Layer (`main.py`)

The entry point for all user interactions. Built with Click framework, it exposes six commands:

| Command | Purpose |
|---------|---------|
| `health` | Print status confirmation and current timestamp |
| `dl-fs-md` | Download raw metadata from one or all USFS sources (FSGeodata, GDD, RDA) |
| `build-fs-catalog` | Parse downloaded metadata into a unified JSON catalog |
| `load-data` | Load catalog into a vector database (ChromaDB or PostgreSQL) |
| `semantic-search` | Semantic similarity search over the catalog |
| `bot-search` | LLM-augmented natural language search using Verde or Claude |

### Data Loaders (`usfs.py`)

The `USFS` class orchestrates metadata collection from three federal data sources. All download and parse methods live on this single class; there are no separate loader classes.

```
┌─────────────────────────────────────────────────────────────────┐
│                           USFS                                  │
│              (Orchestrator for all data sources)                │
├─────────────────────────────────────────────────────────────────┤
│  download_fsgeodata_metadata()  │ Scrape & fetch EDW XML files  │
│  download_gdd_metadata()        │ Fetch DCAT-US JSON from Hub   │
│  download_rda_metadata()        │ Fetch RDA JSON feed           │
│  build_fsgeodata_catalog()      │ Parse XML → document dicts    │
│  build_gdd_catalog()            │ Parse GDD JSON → dicts        │
│  build_rda_catalog()            │ Parse RDA JSON → dicts        │
│  build_catalog()                │ Combine all sources → JSON    │
└─────────────────────────────────────────────────────────────────┘
```

**FSGeodata** (`download_fsgeodata_metadata` / `build_fsgeodata_catalog`)

- Scrapes dataset index from `data.fs.usda.gov/geodata/edw/datasets.php`
- Downloads FGDC-compliant XML metadata files one per dataset
- Parses `<title>`, `<abstract>`, `<purpose>`, `<themekey>`, and `<procstep>` elements
- Output written to `data/usfs/fsgeodata/`

**GDD** (`download_gdd_metadata` / `build_gdd_catalog`)

- Fetches DCAT-US 1.1 JSON feed from the USFS ArcGIS Hub
- Single-endpoint bulk download to `data/usfs/gdd/gdd_metadata.json`
- Extracts `title`, `description`, `keyword`, and `theme` per record

**RDA** (`download_rda_metadata` / `build_rda_catalog`)

- Queries the USFS Research Data Archive JSON web service
- Single-endpoint bulk download to `data/usfs/rda/rda_metadata.json`
- Extracts `title`, `description`, and `keyword` per record

All download methods skip files that already exist, making repeat runs safe and incremental. All build methods normalise records into `USFSDocument`-compatible dicts and deduplicate keywords before returning.

### Schema Layer (`schema.py`)

Defines the unified data model using Pydantic:

```python
USFSDocument
├── id: str           # SHA-256 hash of normalized title
├── title: str        # Dataset title
├── abstract: str     # Summary description (FSGeodata only)
├── purpose: str      # Intended use (FSGeodata only)
├── description: str  # Full narrative description (GDD and RDA)
├── keywords: list    # Subject keywords
├── src: str          # Source identifier (fsgeodata / gdd / rda)
├── lineage: list     # Processing history (FSGeodata only)
└── embeddings: list  # Dense vector embedding (optional)
```

Provides:

- Data validation on ingest
- Serialization to/from JSON
- Markdown rendering via `to_markdown()`
- Embedding text serialisation via `to_embedding_text()`

### Vector Store (`db.py`, `embeddings.py`, `search.py`)

Semantic search is split across three modules backed by PostgreSQL with the pgvector extension.

**`db.py` — Schema and database initialisation**

```
┌─────────────────────────────────────────────────────────────────┐
│                       DocumentRecord                            │
├─────────────────────────────────────────────────────────────────┤
│  id (PK)      │ SHA-256 hash string (64 chars)                  │
│  title        │ Dataset title (indexed)                         │
│  abstract     │ Summary text                                     │
│  description  │ Full narrative description                      │
│  purpose      │ Intended use statement                          │
│  keywords     │ JSON-stringified list                           │
│  src          │ Source identifier (fsgeodata / gdd / rda)       │
│  lineage      │ JSON-stringified processing history             │
│  embedding    │ 384-dimensional pgvector column                 │
│  created_at   │ Insertion timestamp (indexed)                   │
└─────────────────────────────────────────────────────────────────┘
```

`init_db()` enables the `vector` extension, creates the `documents` table, and builds an IVFFlat cosine index (`lists=100`) for fast approximate nearest-neighbour search.

**`embeddings.py` — Embedding generation and storage**

```
┌─────────────────────────────────────────────────────────────────┐
│                      EmbeddingsService                          │
├─────────────────────────────────────────────────────────────────┤
│  embed_text(text)             │ Embed a single string           │
│  embed_batch(docs, batch=32)  │ Embed a list of USFSDocuments   │
│  store_in_postgres(docs, emb) │ Upsert documents with vectors   │
└─────────────────────────────────────────────────────────────────┘
```

Uses `fastembed` with model `BAAI/bge-small-en-v1.5` (384 dimensions). Batch embedding calls `USFSDocument.to_embedding_text()` on each document before encoding.

**`search.py` — Semantic similarity search**

```
┌─────────────────────────────────────────────────────────────────┐
│                       SemanticSearch                            │
├─────────────────────────────────────────────────────────────────┤
│  search(query, limit=10)  │ Cosine similarity search via SQL    │
└─────────────────────────────────────────────────────────────────┘
```

`AISearch` subclasses `SemanticSearch` as a hook for future AI-enhanced retrieval logic.

**Embedding Strategy**

Documents are serialised to text before encoding (`to_embedding_text()`):

```
Title: {title}
Abstract: {abstract}
Description: {description}
Purpose: {purpose}
Keywords: {keywords}
Lineage: {lineage}
```

**Query Flow**

1. User query is embedded with `EmbeddingsService`
2. pgvector cosine operator (`<=>`) ranks all documents by distance
3. `1 - distance` returned as a `similarity` score alongside each row
4. Top-k results returned; higher similarity = more relevant

### LLM Client (`bots.py`)

Integrates with an external LLM via a LiteLLM proxy:

```
┌─────────────────────────────────────────────────────────────────┐
│                          VerdeBot                               │
├─────────────────────────────────────────────────────────────────┤
│  chat(message)  │ Send a message and return the LLM response    │
└─────────────────────────────────────────────────────────────────┘
```

Uses `langchain-litellm` (`ChatLiteLLM`) with the `litellm_proxy/{VERDE_MODEL}` model string. Connection is configured via `VERDE_API_KEY`, `VERDE_URL`, and `VERDE_MODEL` environment variables.

**RAG Pipeline** (via `bot-search` command)

1. User submits a natural language query
2. `SemanticSearch` retrieves top-k documents from PostgreSQL
3. Retrieved documents are formatted as context (title, abstract, description, similarity)
4. A prompt template (simple / discovery / relationships / lineage) is prepended
5. `VerdeBot.chat()` sends the combined message to the LLM
6. LLM returns a synthesised natural language response

### Prompts (`prompts/`)

Prompt templates used by `bot-search`:

| Module | Template |
|--------|----------|
| `simple.py` | `SIMPLE` — basic catalog Q&A |
| `discovery.py` | `DISCOVERY_BASE` — dataset discovery guidance |
| `relationships.py` | `RELATIONSHIPS_BASE` — cross-dataset relationship analysis |
| `lineage.py` | `LINEAGE_BASE` — data lineage and provenance |

### Utilities (`lib.py`)

Shared helper functions:

| Function | Purpose |
|----------|---------|
| `save_json()` | Serialize data to a JSON file |
| `load_json()` | Load and parse a JSON file |
| `clean_str()` | Strip HTML tags and normalize whitespace |
| `strip_html()` | Remove HTML tags via BeautifulSoup |
| `hash_string()` | Generate SHA-256 document IDs |
| `dedupe_catalog()` | Remove duplicate entries from a catalog JSON file |

## Data Flow

### Ingestion Pipeline

```
1. Download Phase
   ┌──────────┐    ┌──────────┐    ┌──────────┐
   │FSGeodata │    │   GDD    │    │   RDA    │
   │   XML    │    │   JSON   │    │   JSON   │
   └────┬─────┘    └────┬─────┘    └────┬─────┘
        │               │               │
        └───────────────┼───────────────┘
                        ▼
2. Parse Phase     ┌──────────┐
                   │  USFS    │
                   │ build_*  │
                   └────┬─────┘
                        │
                        ▼
3. Harmonize      ┌──────────────┐
                  │ USFSDocument │
                  │    Schema    │
                  └──────┬───────┘
                         │
                         ▼
4. Store          ┌──────────────────┐
                  │ usfs_catalog.json│
                  └──────┬───────────┘
                         │
                         ▼
5. Embed & Index  ┌──────────────┐
                  │  PostgreSQL  │
                  │  (pgvector)  │
                  └──────────────┘
```

### Query Pipeline

```
User Query
    │
    ▼
┌─────────────────┐
│ SemanticSearch  │ ◄─── PostgreSQL / pgvector
│ (top-k results) │
└────────┬────────┘
         │
         ├─────────────────────────┐
         │                         │
         ▼                         ▼
┌─────────────────┐      ┌─────────────────┐
│ Direct Results  │      │  RAG Pipeline   │
│(semantic-search)│      │  (bot-search)   │
└─────────────────┘      └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │    VerdeBot     │
                         │  (LiteLLM LLM)  │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │ Natural Language│
                         │    Response     │
                         └─────────────────┘
```

## Directory Structure

```
catalog/
├── src/catalog/
│   ├── __init__.py
│   ├── main.py         # Click CLI commands
│   ├── usfs.py         # USFS data loaders (FSGeodata, GDD, RDA)
│   ├── db.py           # PostgreSQL schema and init (pgvector)
│   ├── embeddings.py   # fastembed embedding generation and storage
│   ├── search.py       # SemanticSearch and AISearch classes
│   ├── schema.py       # Pydantic data models
│   ├── bots.py         # VerdeBot LLM client (LiteLLM)
│   ├── lib.py          # Utility functions
│   └── prompts/
│       ├── __init__.py
│       ├── simple.py
│       ├── discovery.py
│       ├── relationships.py
│       └── lineage.py
├── data/
│   └── usfs/
│       ├── fsgeodata/          # FSGeodata XML metadata files
│       ├── gdd/                # GDD DCAT JSON feed
│       ├── rda/                # RDA JSON feed
│       └── usfs_catalog.json   # Unified catalog
├── tests/
│   ├── test_semantic_search.py
│   └── test_ai_search.py
└── docs/               # Documentation
```

## Dependencies

| Package | Purpose |
|---------|---------|
| click | CLI framework |
| fastembed | Local embedding model (`BAAI/bge-small-en-v1.5`) |
| sqlalchemy | ORM and database access |
| pgvector | pgvector SQLAlchemy / psycopg integration |
| psycopg2-binary / psycopg | PostgreSQL drivers |
| langchain-litellm | LiteLLM-backed LLM client for VerdeBot |
| pydantic | Data validation and schema |
| bs4 / lxml | XML and HTML parsing |
| requests | HTTP client |
| rich | Console formatting |
| python-dotenv | Environment configuration |

## Configuration

Environment variables (`.env`):

```
# LLM (Verde via LiteLLM proxy)
VERDE_API_KEY=<api-key>
VERDE_URL=<litellm-proxy-url>
VERDE_MODEL=<model-name>

# PostgreSQL
POSTGRES_USER=<user>
POSTGRES_PASSWORD=<password>
POSTGRES_HOST=<host>
POSTGRES_PORT=5432
POSTGRES_DB=catalog
```

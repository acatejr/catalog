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
│                             (cli.py)                                    │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐         ┌─────────────────┐         ┌─────────────────┐
│  Data Loaders │         │  Vector Store   │         │   LLM Client    │
│   (usfs.py)   │         │   (core.py)     │         │   (bots.py)     │
└───────┬───────┘         └────────┬────────┘         └────────┬────────┘
        │                          │                           │
        ▼                          ▼                           ▼
┌───────────────┐         ┌─────────────────┐         ┌─────────────────┐
│    Schema     │         │    ChromaDB     │         │     Ollama      │
│  (schema.py)  │         │                 │         │      API        │
└───────────────┘         └─────────────────┘         └─────────────────┘
```

## Component Descriptions

### CLI Layer (`cli.py`)

The entry point for all user interactions. Built with Click framework, it exposes six commands:

| Command | Purpose |
|---------|---------|
| `health` | System health check |
| `download_fs_metadata` | Fetch raw metadata from all sources |
| `build_fs_catalog` | Parse metadata into unified JSON catalog |
| `build_fs_chromadb` | Index catalog into vector database |
| `query_fs_chromadb` | Semantic search queries |
| `ollama_chat` | LLM-augmented natural language discovery |

### Data Loaders (`usfs.py`)

Orchestrates metadata collection from three federal data sources:

```
┌─────────────────────────────────────────────────────────────────┐
│                         USFS Class                              │
│              (Orchestrator for all data sources)                │
└───────────────────────────────┬─────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────────┐
        │                       │                           │
        ▼                       ▼                           ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│ FSGeodataLoader│      │GeospatialData │       │   RDALoader   │
│               │       │  Discovery    │       │               │
├───────────────┤       ├───────────────┤       ├───────────────┤
│ Source: EDW   │       │ Source: Hub   │       │ Source: RDS   │
│ Format: XML   │       │ Format: DCAT  │       │ Format: JSON  │
│ Protocol: HTTP│       │ Protocol: HTTP│       │ Protocol: HTTP│
└───────────────┘       └───────────────┘       └───────────────┘
```

**FSGeodataLoader**

- Scrapes dataset index from `data.fs.usda.gov`
- Downloads FGDC-compliant XML metadata files
- Retrieves associated MapServer service descriptors
- Implements rate limiting (250ms delay)

**GeospatialDataDiscovery**

- Fetches DCAT-US 1.1 JSON feed from ArcGIS Hub
- Single-endpoint bulk download
- Parses standardized federal open data format

**RDALoader**

- Queries Research Data Archive JSON API
- Downloads research dataset metadata
- Handles scientific provenance information

### Schema Layer (`schema.py`)

Defines the unified data model using Pydantic:

```python
USFSDocument
├── id: str           # SHA-256 hash of normalized title
├── title: str        # Dataset title
├── abstract: str     # Summary description
├── purpose: str      # Intended use (FSGeodata only)
├── description: str  # General description
├── keywords: list    # Subject keywords
├── src: str          # Source identifier
└── lineage: list     # Processing history
```

Provides:

- Data validation on ingest
- Serialization to/from JSON
- Markdown rendering for output display

### Vector Store (`core.py`)

Manages semantic search capabilities via ChromaDB:

```
┌─────────────────────────────────────────────────────────────────┐
│                      ChromaVectorDB                             │
├─────────────────────────────────────────────────────────────────┤
│  load_document_metadata()  │ Load catalog JSON                  │
│  batch_load_documents()    │ Index documents in batches of 100  │
│  query()                   │ Semantic similarity search         │
│  extract_lineage_info()    │ Format lineage for embedding       │
└─────────────────────────────────────────────────────────────────┘
```

**Embedding Strategy**

Documents are embedded as concatenated text:

```
Title: {title}
Abstract: {abstract}
Purpose: {purpose}
Source: {src}
Keywords: {keywords}
Lineage: {lineage}
```

**Query Flow**

1. User query is embedded using same model
2. Cosine distance computed against all documents
3. Top-k results returned with distance scores
4. Lower distance = higher semantic relevance

### LLM Client (`bots.py`)

Integrates with Ollama API for natural language responses:

```
┌─────────────────────────────────────────────────────────────────┐
│                        OllamaBot                                │
├─────────────────────────────────────────────────────────────────┤
│  System Prompt: "Data librarian" persona                        │
│  Input: Question + Vector search context                        │
│  Output: Synthesized natural language response                  │
└─────────────────────────────────────────────────────────────────┘
```

**RAG Pipeline**

1. User submits natural language question
2. Question used for vector search (retrieve top-k documents)
3. Retrieved documents formatted as context
4. LLM generates response grounded in catalog data

### Utilities (`lib.py`)

Shared helper functions:

| Function | Purpose |
|----------|---------|
| `save_json()` | Serialize data to JSON file |
| `clean_str()` | Normalize whitespace and Unicode |
| `hash_string()` | Generate SHA-256 document IDs |

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
                   │ Loaders  │
                   │ parse()  │
                   └────┬─────┘
                        │
                        ▼
3. Harmonize      ┌──────────────┐
                  │ USFSDocument │
                  │    Schema    │
                  └──────┬───────┘
                         │
                         ▼
4. Store          ┌──────────────┐
                  │ catalog.json │
                  └──────┬───────┘
                         │
                         ▼
5. Index          ┌──────────────┐
                  │   ChromaDB   │
                  │   Vectors    │
                  └──────────────┘
```

### Query Pipeline

```
User Query
    │
    ▼
┌─────────────────┐
│ Vector Search   │ ◄─── ChromaDB
│ (top-k results) │
└────────┬────────┘
         │
         ├─────────────────────────┐
         │                         │
         ▼                         ▼
┌─────────────────┐      ┌─────────────────┐
│ Direct Results  │      │  RAG Pipeline   │
│ (query command) │      │ (chat command)  │
└─────────────────┘      └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │   Ollama LLM    │
                         │   (synthesis)   │
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
│   ├── cli.py          # Click CLI commands
│   ├── usfs.py         # Data loaders (USFS, FSGeodata, GDD, RDA)
│   ├── core.py         # ChromaDB vector store
│   ├── schema.py       # Pydantic data models
│   ├── bots.py         # Ollama LLM client
│   └── lib.py          # Utility functions
├── data/
│   └── usfs/
│       ├── fsgeodata/  # FSGeodata XML + service JSON
│       │   ├── metadata/
│       │   └── services/
│       ├── gdd/        # GDD DCAT JSON
│       ├── rda/        # RDA JSON
│       └── catalog.json # Unified catalog
├── chromadb/           # Vector database storage
└── docs/               # Documentation
```

## Dependencies

| Package | Purpose |
|---------|---------|
| click | CLI framework |
| chromadb | Vector database |
| ollama | LLM API client |
| pydantic | Data validation |
| beautifulsoup4 | XML/HTML parsing |
| requests | HTTP client |
| rich | Console formatting |
| python-dotenv | Environment configuration |

## Configuration

Environment variables (`.env`):

```
OLLAMA_API_KEY=<api-key>
OLLAMA_API_URL=<ollama-server-url>
OLLAMA_MODEL=<model-name>
```

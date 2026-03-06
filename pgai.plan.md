# pgai vs ChromaDB — Migration Assessment

## Short Answer

**Probably not worth it right now.** The gains are real but modest for a local CLI tool, and the infrastructure cost is high.

---

## What pgai Actually Offers vs. Current Setup

pgai (Timescale's PostgreSQL AI extension) adds vector search and LLM calls directly inside PostgreSQL via pgvector. Here's how it maps to the current setup:

| What You Have | pgai Equivalent | Difference |
|---|---|---|
| `ChromaVectorDB` (local dir) | pgvector table in PostgreSQL | Requires a running PG server |
| `batch_load_documents()` manual load | pgai Vectorizer (auto-embeds on insert) | Genuine improvement |
| `HybridSearch` BM25 + vector | PostgreSQL FTS (`tsvector`) + pgvector | Different implementation, similar result |
| Metadata in ChromaDB | SQL `WHERE` clauses | SQL is more expressive |

---

## Where pgai Would Genuinely Help This Project

### 1. Auto-vectorizer Eliminates `batch_load_documents()`

Right now the entire collection is deleted and recreated on every reload (`core.py:59-62`). pgai's vectorizer watches for new rows and embeds automatically. For a catalog that updates frequently, this is a real win.

### 2. Expressive Metadata Filtering Before Vector Search

The `src` field (`fsgeodata`, `gdd`, `rda`) plus keywords could become pre-filters:

```sql
SELECT * FROM documents
WHERE src = 'fsgeodata'
  AND keywords @> ARRAY['erosion']
ORDER BY embedding <=> query_embedding
LIMIT 5;
```

ChromaDB's metadata filtering works but is less capable than SQL.

### 3. Single Data Store

Currently there are two separate stores: `catalog.json` + `./chromadb/`. PostgreSQL consolidates both.

---

## Where It Doesn't Help (or Hurts)

### 1. Infrastructure Overhead for a Local CLI

ChromaDB is just a directory (`./chromadb`). pgai requires a running PostgreSQL server — either Docker or a local install. That's a significant setup burden for CLI users.

### 2. Dataset Is Small and Batch-Loaded

The catalog is loaded from a JSON file periodically, not continuously written. The auto-vectorizer advantage is most valuable for streaming inserts — less so for a batch-reload workflow.

### 3. Hybrid Search Is Already Built

`search.py` already implements BM25 + vector + RRF. pgai/PostgreSQL FTS would be a rewrite of working code for roughly the same outcome.

---

## When It Would Make Sense to Switch

- The project becomes a **web service** with multiple concurrent users
- The catalog grows to **tens of thousands of documents** and pre-filtering is needed for performance
- PostgreSQL is **already running** for other project needs
- Use of pgai's `ai.openai_chat_complete()` to call the LLM **directly from SQL** as part of query pipelines is desired

---

## Recommendation

Stay with ChromaDB for now. If the **agentic tool use** improvement from the AI roadmap is pursued (letting the LLM drive searches with SQL-like filters), that is the point where PostgreSQL's expressive filtering becomes worth the infrastructure trade-off.

---

Generated 2026-03-03

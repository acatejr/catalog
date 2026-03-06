# Migrating from ChromaDB to pgai

## Current State

Your ChromaDB usage is concentrated in the `ChromaVectorDB` class in [core.py](src/catalog/core.py). It:

1. Stores document embeddings in a single `"documents"` collection
2. Concatenates title, abstract, purpose, keywords, and lineage into embedding text
3. Stores metadata alongside each embedding (id, title, abstract, source, purpose, keywords, lineage)
4. Queries with `collection.query(query_texts=..., n_results=...)` returning documents + distance scores
5. Uses ChromaDB's default embedding model (no custom model configured)

The CLI commands that touch ChromaDB: `build_fs_chromadb`, `query_fs_chromadb`, and `ollama_chat` in [cli.py](src/catalog/cli.py).

---

## What pgai Would Replace

[pgai](https://github.com/timescale/pgai) (by Timescale) is a Python library + PostgreSQL extension that uses **pgvector** under the hood. Instead of a separate vector store, your embeddings live in PostgreSQL tables. The key components:

- **pgvector** extension for the `vector` column type and similarity search operators
- **pgai Vectorizer** to automatically create and sync embeddings when data changes
- A background worker process that asynchronously generates embeddings

---

## High-Level Migration Steps

### 1. Infrastructure: Add PostgreSQL with pgvector + pgai

You'd need a PostgreSQL instance with the `pgvector` extension enabled. Then install the pgai Python library:

```bash
pip install pgai
```

Replace `chromadb>=1.4.1` with `pgai` (and `psycopg2-binary` or `asyncpg`) in [pyproject.toml](pyproject.toml).

### 2. Schema: Create a documents table

Instead of a ChromaDB collection, you'd have a PostgreSQL table:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS ai;

CREATE TABLE documents (
    id TEXT PRIMARY KEY,
    title TEXT,
    abstract TEXT,
    purpose TEXT,
    source TEXT,
    keywords TEXT,
    lineage TEXT,
    embedding_input TEXT  -- the concatenated text that gets embedded
);
```

Then create a vectorizer to auto-embed:

```sql
SELECT ai.create_vectorizer(
    'documents'::regclass,
    destination   => 'documents_embeddings',
    embedding     => ai.embedding_openai('text-embedding-3-small', 1536),
    chunking      => ai.chunking_none(),
    formatting    => ai.formatting_python_template('$chunk')
);
```

This tells pgai to watch the `documents` table and automatically generate embeddings into a `documents_embeddings` table whenever rows are inserted/updated.

### 3. Replace `ChromaVectorDB` class

Your new class would look roughly like:

```python
import psycopg2

class PgaiVectorDB:
    def __init__(self, conn_string: str, src_catalog_file: str = "data/usfs/catalog.json"):
        self.conn = psycopg2.connect(conn_string)
        self.src_catalog_file = src_catalog_file
        self.documents = []

    def load_document_metadata(self):
        # Same as current — loads from catalog.json into self.documents
        ...

    def batch_load_documents(self, batch_size: int = 100):
        """Insert documents into PostgreSQL (pgai vectorizer handles embeddings)."""
        self.load_document_metadata()
        cur = self.conn.cursor()
        cur.execute("TRUNCATE documents CASCADE")

        for i in range(0, len(self.documents), batch_size):
            batch = self.documents[i : i + batch_size]
            for doc in batch:
                embedding_input = f"Title: {doc.title}\nAbstract: {doc.abstract}..."
                cur.execute(
                    """INSERT INTO documents (id, title, abstract, purpose, source, keywords, lineage, embedding_input)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                       ON CONFLICT (id) DO UPDATE SET ...""",
                    (doc.id, doc.title, doc.abstract, ...)
                )
        self.conn.commit()
        # pgai vectorizer worker will async generate embeddings

    def query(self, qstn: str, nresults: int = 5):
        """Semantic search using pgvector similarity."""
        cur = self.conn.cursor()
        cur.execute(
            """SELECT d.id, d.title, d.abstract, d.source, d.purpose,
                      d.keywords, d.lineage,
                      e.embedding <=> ai.openai_embed('text-embedding-3-small', %s) AS distance
               FROM documents d
               JOIN documents_embeddings e ON d.id = e.id
               ORDER BY distance ASC
               LIMIT %s""",
            (qstn, nresults)
        )
        # Reconstruct USFSDocument objects from rows
        ...
```

### 4. Update CLI commands

Rename or update `build_fs_chromadb` → `build_db` and `query_fs_chromadb` → `query_db` in [cli.py](src/catalog/cli.py), swapping `ChromaVectorDB` for `PgaiVectorDB`. The `ollama_chat` command would use the new query method but otherwise stay the same.

### 5. Configuration

Add PostgreSQL connection config to your `.env`:

```
DATABASE_URL=postgresql://user:password@localhost:5432/catalog
OPENAI_API_KEY=...  # pgai vectorizer needs an embedding API key
```

---

## Trade-offs to Consider

| Factor | ChromaDB (current) | pgai + pgvector |
|---|---|---|
| **Infrastructure** | Zero — embedded, file-based | Requires a PostgreSQL server |
| **Embedding model** | Built-in default (free, local) | Requires an API key (OpenAI, etc.) or local model via Ollama |
| **Auto-sync** | Manual rebuild each time | Vectorizer auto-syncs on data changes |
| **SQL queries** | Not possible | Full SQL power — joins, filters, aggregates |
| **Scalability** | Good for small-medium datasets | Better for large datasets with pgvectorscale |
| **Complexity** | Simple pip install | More moving parts (PostgreSQL, worker process, extensions) |

### Key Decision: Embedding Model

Your current setup uses ChromaDB's built-in embedding model (free, local). With pgai, you'd need to choose an embedding provider — OpenAI, Ollama (local), or another supported model. If you're already running Ollama for `ollama_chat`, you could use it for embeddings too, keeping things local and free.

---

## Summary

The core changes are:
1. **Replace the dependency** — `chromadb` → `pgai` + `psycopg2-binary`
2. **Replace the class** — `ChromaVectorDB` → a PostgreSQL-backed equivalent
3. **Replace the storage** — `./chromadb/` directory → PostgreSQL table + vectorizer
4. **Update CLI commands** in [cli.py](src/catalog/cli.py) to use the new class

The query interface for `ollama_chat` in [bots.py](src/catalog/bots.py) wouldn't need to change since it only consumes the results from the vector DB query.

## Sources

- [pgai GitHub Repository](https://github.com/timescale/pgai)
- [pgai Vectorizer - DEV Community](https://dev.to/tigerdata/pgai-vectorizer-automate-ai-embeddings-with-one-sql-command-in-postgresql-11kp)
- [pgai as a Production-Ready AI Retrieval Engine](https://www.blog.brightcoding.dev/2025/08/30/pgai-transforming-postgresql-into-a-production-ready-ai-retrieval-engine-for-rag-applications/)

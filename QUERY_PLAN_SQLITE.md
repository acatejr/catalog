# Vector Database Embedding Strategy - SQLite Proof of Concept

## Overview

This document outlines a proof-of-concept implementation using SQLite for creating vector embeddings of the catalog.json geospatial dataset to enable semantic search and intelligent querying. SQLite provides a simpler, zero-configuration alternative to PostgreSQL.

## Data Structure Analysis

Each catalog item contains:

- **title**: Dataset name (short identifier)
- **abstract**: Detailed description (200-500+ words typically)
- **purpose**: Intended use/rationale (100-300+ words)
- **keywords**: Array of domain-specific terms
- **lineage**: Array of process descriptions with dates
- **src**: Source identifier (e.g., "fsgeodata")

## Architecture

### Hybrid Approach: SQLite + In-Memory Vector Search

```
┌──────────────────────────────────────────┐
│   SQLite Database                        │
│   - Full document metadata               │
│   - Embeddings stored as BLOB           │
│   - Keyword analytics/aggregations       │
└──────────────────────────────────────────┘
                ↓
┌──────────────────────────────────────────┐
│   NumPy/Faiss (In-Memory)               │
│   - Fast vector similarity search        │
│   - Loaded from SQLite on startup        │
└──────────────────────────────────────────┘
```

**Advantages of SQLite:**

- Zero configuration - just a file
- No separate database server to manage
- Perfect for local development and small to medium datasets (<1M items)
- Built-in full-text search (FTS5) for hybrid queries
- Easy to distribute (single .db file)

## Embedding Strategy

### Concatenated Field Approach

Create a single embedding per dataset by concatenating fields in a structured format:

```text
Title: {title}

Purpose: {purpose}

Description: {abstract}

Keywords: {keywords_joined}

Source: {src}
```

This approach:

- Captures holistic semantic meaning
- Enables natural language queries
- Cost-effective (one embedding per document)
- Handles keyword-based and concept-based queries

## Implementation

### 1. Database Schema

```sql
-- Main catalog table
CREATE TABLE catalog_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    abstract TEXT,
    purpose TEXT,
    keywords TEXT,  -- JSON array stored as text
    lineage TEXT,   -- JSON array stored as text
    src TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Vector embeddings table
CREATE TABLE catalog_embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    catalog_item_id INTEGER NOT NULL,
    embedding BLOB NOT NULL,  -- Numpy array stored as binary
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (catalog_item_id) REFERENCES catalog_items(id)
);

-- Create index for fast lookups
CREATE INDEX idx_catalog_item_id ON catalog_embeddings(catalog_item_id);
CREATE INDEX idx_title ON catalog_items(title);
CREATE INDEX idx_src ON catalog_items(src);

-- Full-text search virtual table for keyword/text search
CREATE VIRTUAL TABLE catalog_fts USING fts5(
    title,
    abstract,
    purpose,
    keywords,
    content=catalog_items,
    content_rowid=id
);

-- Triggers to keep FTS index in sync
CREATE TRIGGER catalog_fts_insert AFTER INSERT ON catalog_items BEGIN
    INSERT INTO catalog_fts(rowid, title, abstract, purpose, keywords)
    VALUES (new.id, new.title, new.abstract, new.purpose, new.keywords);
END;

CREATE TRIGGER catalog_fts_delete AFTER DELETE ON catalog_items BEGIN
    DELETE FROM catalog_fts WHERE rowid = old.id;
END;

CREATE TRIGGER catalog_fts_update AFTER UPDATE ON catalog_items BEGIN
    UPDATE catalog_fts SET
        title = new.title,
        abstract = new.abstract,
        purpose = new.purpose,
        keywords = new.keywords
    WHERE rowid = new.id;
END;

-- View for keyword frequency analysis
CREATE VIEW keyword_frequencies AS
WITH split_keywords AS (
    SELECT
        id,
        json_each.value as keyword
    FROM catalog_items,
    json_each(keywords)
)
SELECT
    keyword,
    COUNT(*) as frequency,
    json_group_array(id) as item_ids
FROM split_keywords
GROUP BY keyword
ORDER BY frequency DESC;
```

### 2. Python Proof of Concept

```python
#!/usr/bin/env python3
"""
Vector Embedding POC for Catalog Data using SQLite
Requires: pip install openai numpy
"""

import json
import os
import sqlite3
from typing import List, Dict, Any, Optional
import numpy as np
from openai import OpenAI

# Configuration
EMBEDDING_MODEL = "text-embedding-3-small"  # 1536 dimensions, $0.02/1M tokens
EMBEDDING_DIMENSION = 1536
DATABASE_PATH = "data/catalog.db"


class CatalogEmbedder:
    """Handle embedding generation and storage for catalog data using SQLite."""

    def __init__(self, openai_api_key: str, db_path: str = DATABASE_PATH):
        self.client = OpenAI(api_key=openai_api_key)
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self._embeddings_cache = None  # Cache for in-memory vector search

    def initialize_database(self):
        """Create database schema if it doesn't exist."""
        # Read and execute schema
        schema = open('schema.sql', 'r').read()  # Assuming schema saved separately
        self.conn.executescript(schema)
        self.conn.commit()

    def create_embedding_text(self, item: Dict[str, Any]) -> str:
        """
        Create structured text for embedding from catalog item.

        Args:
            item: Catalog item dictionary

        Returns:
            Formatted text string for embedding
        """
        parts = [
            f"Title: {item.get('title', '')}",
            f"Purpose: {item.get('purpose', '')}",
            f"Description: {item.get('abstract', '')}",
            f"Keywords: {', '.join(item.get('keywords', []))}",
            f"Source: {item.get('src', '')}"
        ]

        # Filter out empty parts and join
        text = "\n\n".join(part for part in parts if part.split(': ', 1)[1])

        # Truncate if needed (embedding models typically have 8K token limit)
        # Rough estimate: 1 token ≈ 4 chars
        max_chars = 30000  # ~7500 tokens, leaving buffer
        if len(text) > max_chars:
            text = text[:max_chars] + "..."

        return text

    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding vector for text using OpenAI API.

        Args:
            text: Input text

        Returns:
            Embedding vector as numpy array
        """
        response = self.client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        return np.array(response.data[0].embedding, dtype=np.float32)

    def batch_generate_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """
        Generate embeddings for multiple texts in batch (more efficient).

        Args:
            texts: List of input texts

        Returns:
            List of embedding vectors as numpy arrays
        """
        response = self.client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=texts
        )
        # Sort by index to ensure order matches input
        sorted_data = sorted(response.data, key=lambda x: x.index)
        return [np.array(item.embedding, dtype=np.float32) for item in sorted_data]

    def store_catalog_item(self, item: Dict[str, Any]) -> int:
        """
        Store catalog item in database.

        Args:
            item: Catalog item dictionary

        Returns:
            Database ID of inserted item
        """
        query = """
            INSERT INTO catalog_items (title, abstract, purpose, keywords, lineage, src)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        self.cursor.execute(
            query,
            (
                item.get('title'),
                item.get('abstract'),
                item.get('purpose'),
                json.dumps(item.get('keywords', [])),
                json.dumps(item.get('lineage', [])),
                item.get('src')
            )
        )
        return self.cursor.lastrowid

    def store_embedding(self, catalog_item_id: int, embedding: np.ndarray):
        """
        Store embedding vector in database.

        Args:
            catalog_item_id: Foreign key to catalog_items
            embedding: Embedding vector as numpy array
        """
        query = """
            INSERT INTO catalog_embeddings (catalog_item_id, embedding)
            VALUES (?, ?)
        """
        # Convert numpy array to binary blob
        embedding_blob = embedding.tobytes()
        self.cursor.execute(query, (catalog_item_id, embedding_blob))

    def process_catalog(self, catalog_path: str, batch_size: int = 10):
        """
        Process entire catalog: load, embed, and store.

        Args:
            catalog_path: Path to catalog.json
            batch_size: Number of items to process in each batch
        """
        # Load catalog
        with open(catalog_path, 'r') as f:
            catalog_items = json.load(f)

        print(f"Processing {len(catalog_items)} catalog items...")

        # Process in batches for efficiency
        for i in range(0, len(catalog_items), batch_size):
            batch = catalog_items[i:i+batch_size]
            print(f"Processing batch {i//batch_size + 1} ({len(batch)} items)...")

            # Store items and collect texts
            item_ids = []
            texts = []
            for item in batch:
                item_id = self.store_catalog_item(item)
                item_ids.append(item_id)
                texts.append(self.create_embedding_text(item))

            # Generate embeddings in batch
            embeddings = self.batch_generate_embeddings(texts)

            # Store embeddings
            for item_id, embedding in zip(item_ids, embeddings):
                self.store_embedding(item_id, embedding)

            self.conn.commit()
            print(f"  ✓ Batch complete")

        print(f"✓ Successfully processed {len(catalog_items)} items")

    def _load_embeddings_cache(self):
        """Load all embeddings into memory for fast similarity search."""
        if self._embeddings_cache is not None:
            return

        query = """
            SELECT catalog_item_id, embedding
            FROM catalog_embeddings
            ORDER BY catalog_item_id
        """
        self.cursor.execute(query)

        ids = []
        embeddings = []
        for row in self.cursor.fetchall():
            ids.append(row[0])
            # Convert binary blob back to numpy array
            embedding = np.frombuffer(row[1], dtype=np.float32)
            embeddings.append(embedding)

        self._embeddings_cache = {
            'ids': np.array(ids),
            'embeddings': np.vstack(embeddings) if embeddings else np.array([])
        }

    def cosine_similarity(
        self,
        query_embedding: np.ndarray,
        embeddings: np.ndarray
    ) -> np.ndarray:
        """
        Calculate cosine similarity between query and all embeddings.

        Args:
            query_embedding: Query vector (1D array)
            embeddings: Matrix of embeddings (2D array)

        Returns:
            Similarity scores (1D array)
        """
        # Normalize vectors
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        embeddings_norm = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

        # Compute cosine similarity
        similarities = np.dot(embeddings_norm, query_norm)
        return similarities

    def semantic_search(
        self,
        query: str,
        top_k: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search on catalog.

        Args:
            query: Natural language query
            top_k: Number of results to return
            similarity_threshold: Minimum cosine similarity (0-1)

        Returns:
            List of matching catalog items with similarity scores
        """
        # Generate embedding for query
        query_embedding = self.generate_embedding(query)

        # Load embeddings cache
        self._load_embeddings_cache()

        if len(self._embeddings_cache['embeddings']) == 0:
            return []

        # Calculate similarities
        similarities = self.cosine_similarity(
            query_embedding,
            self._embeddings_cache['embeddings']
        )

        # Filter by threshold and get top-k
        above_threshold = similarities >= similarity_threshold
        filtered_indices = np.where(above_threshold)[0]

        if len(filtered_indices) == 0:
            return []

        # Sort by similarity and take top-k
        sorted_indices = filtered_indices[
            np.argsort(similarities[filtered_indices])[::-1]
        ][:top_k]

        # Get catalog item IDs
        item_ids = self._embeddings_cache['ids'][sorted_indices]

        # Retrieve full catalog items
        results = []
        for idx, item_id in enumerate(item_ids):
            query = """
                SELECT id, title, abstract, purpose, keywords, lineage, src
                FROM catalog_items
                WHERE id = ?
            """
            self.cursor.execute(query, (int(item_id),))
            row = self.cursor.fetchone()

            if row:
                results.append({
                    'id': row['id'],
                    'title': row['title'],
                    'abstract': row['abstract'],
                    'purpose': row['purpose'],
                    'keywords': json.loads(row['keywords']) if row['keywords'] else [],
                    'lineage': json.loads(row['lineage']) if row['lineage'] else [],
                    'src': row['src'],
                    'similarity': float(similarities[sorted_indices[idx]])
                })

        return results

    def get_lineage(
        self,
        title: Optional[str] = None,
        item_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve lineage information for a specific dataset.
        This is NOT a vector search - it's exact/fuzzy metadata retrieval.

        Args:
            title: Dataset title (fuzzy match using LIKE)
            item_id: Dataset ID (exact match)

        Returns:
            Catalog item with lineage details
        """
        if item_id:
            query = "SELECT * FROM catalog_items WHERE id = ?"
            self.cursor.execute(query, (item_id,))
        elif title:
            query = "SELECT * FROM catalog_items WHERE title LIKE ?"
            self.cursor.execute(query, (f"%{title}%",))
        else:
            raise ValueError("Must provide either title or item_id")

        row = self.cursor.fetchone()
        if not row:
            return None

        return {
            'id': row['id'],
            'title': row['title'],
            'abstract': row['abstract'],
            'purpose': row['purpose'],
            'keywords': json.loads(row['keywords']) if row['keywords'] else [],
            'lineage': json.loads(row['lineage']) if row['lineage'] else [],
            'src': row['src']
        }

    def get_top_keywords(self, top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Get most frequently used keywords.
        This is an analytical query, not a vector search.

        Args:
            top_n: Number of top keywords to return

        Returns:
            List of keywords with frequencies and associated item IDs
        """
        query = """
            SELECT keyword, frequency, item_ids
            FROM keyword_frequencies
            LIMIT ?
        """
        self.cursor.execute(query, (top_n,))

        results = []
        for row in self.cursor.fetchall():
            results.append({
                'keyword': row['keyword'],
                'frequency': row['frequency'],
                'item_ids': json.loads(row['item_ids'])
            })

        return results

    def keyword_search(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """
        Search by exact keyword match (traditional search).
        Can be combined with semantic search for hybrid approach.

        Args:
            keywords: List of keywords to search for

        Returns:
            List of matching catalog items
        """
        # Build SQL to check if any keyword matches
        keyword_conditions = " OR ".join(
            ["keywords LIKE ?" for _ in keywords]
        )
        query = f"""
            SELECT id, title, abstract, purpose, keywords, lineage, src
            FROM catalog_items
            WHERE {keyword_conditions}
            ORDER BY title
        """

        # Create parameters with wildcards
        params = [f'%"{kw}"%' for kw in keywords]

        self.cursor.execute(query, params)

        results = []
        for row in self.cursor.fetchall():
            results.append({
                'id': row['id'],
                'title': row['title'],
                'abstract': row['abstract'],
                'purpose': row['purpose'],
                'keywords': json.loads(row['keywords']) if row['keywords'] else [],
                'lineage': json.loads(row['lineage']) if row['lineage'] else [],
                'src': row['src']
            })

        return results

    def fts_search(self, search_term: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Full-text search using SQLite FTS5.
        Fast text search across title, abstract, purpose, and keywords.

        Args:
            search_term: Search term or phrase
            top_k: Number of results to return

        Returns:
            List of matching catalog items with rank scores
        """
        query = """
            SELECT
                ci.id,
                ci.title,
                ci.abstract,
                ci.purpose,
                ci.keywords,
                ci.lineage,
                ci.src,
                fts.rank
            FROM catalog_fts fts
            JOIN catalog_items ci ON fts.rowid = ci.id
            WHERE catalog_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """

        self.cursor.execute(query, (search_term, top_k))

        results = []
        for row in self.cursor.fetchall():
            results.append({
                'id': row['id'],
                'title': row['title'],
                'abstract': row['abstract'],
                'purpose': row['purpose'],
                'keywords': json.loads(row['keywords']) if row['keywords'] else [],
                'lineage': json.loads(row['lineage']) if row['lineage'] else [],
                'src': row['src'],
                'rank': row['rank']
            })

        return results

    def hybrid_search(
        self,
        query: str,
        top_k: int = 10,
        semantic_weight: float = 0.7,
        fts_weight: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining semantic and full-text search.

        Args:
            query: Search query
            top_k: Number of results to return
            semantic_weight: Weight for semantic search (0-1)
            fts_weight: Weight for FTS search (0-1)

        Returns:
            Combined and reranked results
        """
        # Get semantic results
        semantic_results = self.semantic_search(query, top_k=top_k * 2)

        # Get FTS results
        fts_results = self.fts_search(query, top_k=top_k * 2)

        # Combine and rerank
        combined_scores = {}

        for result in semantic_results:
            item_id = result['id']
            combined_scores[item_id] = {
                'item': result,
                'score': result['similarity'] * semantic_weight
            }

        for result in fts_results:
            item_id = result['id']
            # Normalize FTS rank (negative values, closer to 0 is better)
            normalized_rank = 1.0 / (1.0 - result['rank']) if result['rank'] < 0 else 0

            if item_id in combined_scores:
                combined_scores[item_id]['score'] += normalized_rank * fts_weight
            else:
                combined_scores[item_id] = {
                    'item': result,
                    'score': normalized_rank * fts_weight
                }

        # Sort by combined score
        sorted_results = sorted(
            combined_scores.values(),
            key=lambda x: x['score'],
            reverse=True
        )[:top_k]

        return [r['item'] for r in sorted_results]

    def close(self):
        """Close database connection."""
        self.conn.close()


# Example usage
def main():
    """Example usage of the CatalogEmbedder with SQLite."""

    # Initialize
    embedder = CatalogEmbedder(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        db_path="data/catalog.db"
    )

    # Initialize database schema (run once)
    # embedder.initialize_database()

    # Process catalog (run once)
    # embedder.process_catalog("data/catalog.json", batch_size=10)

    # Query 1: Semantic search for erosion data
    print("\n=== Query: Is there erosion data in the catalog? ===")
    results = embedder.semantic_search(
        "erosion geological soil sediment watershed data",
        top_k=5
    )
    for result in results:
        print(f"- {result['title']} (similarity: {result['similarity']:.3f})")
        print(f"  Keywords: {', '.join(result['keywords'][:5])}")

    # Query 2: Get lineage for specific dataset
    print("\n=== Query: Describe the data lineage ===")
    lineage = embedder.get_lineage(title="Great Basin")
    if lineage:
        print(f"Dataset: {lineage['title']}")
        print(f"Lineage steps: {len(lineage['lineage'])}")
        for i, step in enumerate(lineage['lineage'], 1):
            print(f"  {i}. [{step.get('date', 'unknown')}] {step.get('description', 'N/A')[:100]}...")

    # Query 3: Top keywords
    print("\n=== Query: Top 5 most frequently used keywords ===")
    top_keywords = embedder.get_top_keywords(top_n=5)
    for kw in top_keywords:
        print(f"- {kw['keyword']}: {kw['frequency']} datasets")

    # Query 4: Full-text search
    print("\n=== Full-Text Search: 'fire management' ===")
    fts_results = embedder.fts_search("fire management", top_k=5)
    for result in fts_results:
        print(f"- {result['title']} (rank: {result['rank']:.3f})")

    # Query 5: Hybrid search
    print("\n=== Hybrid Search: 'watershed restoration' ===")
    hybrid_results = embedder.hybrid_search("watershed restoration", top_k=5)
    for result in hybrid_results:
        print(f"- {result['title'][:80]}")

    embedder.close()


if __name__ == "__main__":
    main()
```

### 3. Alternative: Using sqlite-vec Extension

For native vector search in SQLite, use the `sqlite-vec` extension:

```python
import sqlite3
import sqlite_vec

# Load extension
db = sqlite3.connect(':memory:')
db.enable_load_extension(True)
sqlite_vec.load(db)
db.enable_load_extension(False)

# Create virtual table for vector search
db.execute("""
    CREATE VIRTUAL TABLE vec_items USING vec0(
        embedding float[1536]
    )
""")

# Insert embeddings
db.execute(
    "INSERT INTO vec_items(rowid, embedding) VALUES (?, ?)",
    (item_id, embedding.tobytes())
)

# Search
results = db.execute("""
    SELECT
        rowid,
        distance
    FROM vec_items
    WHERE embedding MATCH ?
    ORDER BY distance
    LIMIT 10
""", (query_embedding.tobytes(),)).fetchall()
```

## Query Strategy by Use Case

### Use Case 1: "Is there erosion data in the catalog?"

**Approach**: Semantic vector search

```python
results = embedder.semantic_search(
    "erosion geological soil sediment watershed data",
    top_k=10,
    similarity_threshold=0.7
)
```

**Why**: Natural language concepts that may be expressed differently across documents (erosion, soil loss, sediment transport, etc.)

### Use Case 2: "Describe the data lineage of a dataset"

**Approach**: Exact metadata retrieval (NOT vector search)

```python
# By title (fuzzy match)
lineage = embedder.get_lineage(title="Great Basin")

# By ID (exact match)
lineage = embedder.get_lineage(item_id=42)
```

**Why**: This is asking for a specific field of a specific document. Vector search is unnecessary overhead.

### Use Case 3: "What are the top 5 most frequently used keywords?"

**Approach**: SQL aggregation query (NOT vector search)

```python
top_keywords = embedder.get_top_keywords(top_n=5)
```

**Why**: Statistical analysis of structured metadata. Traditional SQL is perfect for this.

### Use Case 4: Hybrid Search

**Approach**: Combine semantic search with full-text search

```python
# Combines vector similarity with FTS5 full-text search
results = embedder.hybrid_search(
    "water quality monitoring",
    top_k=10,
    semantic_weight=0.7,
    fts_weight=0.3
)
```

**Why**: Combines broad semantic matching with precise text/keyword matching for best results.

## Cost Estimation

### OpenAI Embedding Costs (text-embedding-3-small)

- Price: $0.020 per 1M tokens
- Estimated tokens per document: ~1,000-2,000 tokens
- For 1,000 documents: ~1.5M tokens = **$0.03**
- For 10,000 documents: ~15M tokens = **$0.30**

### Query Costs

- Embedding generation per query: ~20-50 tokens
- 1,000 queries: ~50K tokens = **$0.001**

### Alternative: Open Source Models

Consider **sentence-transformers** (all-MiniLM-L6-v2):

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(texts)
```

**Benefits**:

- Free to run locally
- Dimensions: 384 (smaller than OpenAI's 1536)
- No API calls or rate limits
- Fast inference on CPU

## Performance Considerations

### In-Memory Vector Search

- Query time: O(n) for brute-force cosine similarity
- Expected query latency: <100ms for 10K documents on modern CPU
- Memory usage: ~6MB per 1K documents (1536 dimensions)

### SQLite FTS5 Performance

- Query time: O(log n) with proper indexing
- Expected query latency: <10ms for 100K documents
- Excellent for exact text/keyword matching

### Scaling Strategy

- Up to 100K documents: In-memory NumPy cosine similarity (current approach)
- 100K-1M documents: Use Faiss library for approximate nearest neighbor
- 1M+ documents: Consider specialized vector database (Qdrant, Pinecone)

### Optional: Using Faiss for Large Datasets

```python
import faiss

class FastCatalogEmbedder(CatalogEmbedder):
    """Enhanced embedder using Faiss for fast similarity search."""

    def _load_embeddings_cache(self):
        """Load embeddings into Faiss index."""
        if self._embeddings_cache is not None:
            return

        # Load embeddings from DB
        query = "SELECT catalog_item_id, embedding FROM catalog_embeddings"
        self.cursor.execute(query)

        ids = []
        embeddings = []
        for row in self.cursor.fetchall():
            ids.append(row[0])
            embedding = np.frombuffer(row[1], dtype=np.float32)
            embeddings.append(embedding)

        embeddings_matrix = np.vstack(embeddings)

        # Create Faiss index (IndexFlatIP for cosine similarity)
        # Normalize embeddings for cosine similarity using inner product
        faiss.normalize_L2(embeddings_matrix)
        index = faiss.IndexFlatIP(EMBEDDING_DIMENSION)
        index.add(embeddings_matrix)

        self._embeddings_cache = {
            'ids': np.array(ids),
            'index': index
        }

    def semantic_search(self, query: str, top_k: int = 10, **kwargs):
        """Fast semantic search using Faiss."""
        query_embedding = self.generate_embedding(query)
        query_embedding = query_embedding.reshape(1, -1)

        # Normalize for cosine similarity
        faiss.normalize_L2(query_embedding)

        # Load cache
        self._load_embeddings_cache()

        # Search
        similarities, indices = self._embeddings_cache['index'].search(
            query_embedding,
            top_k
        )

        # Retrieve items
        item_ids = self._embeddings_cache['ids'][indices[0]]
        results = []

        for idx, item_id in enumerate(item_ids):
            # ... fetch from database and build results
            pass

        return results
```

## Integration with Existing CLI

### Add New Commands to `main.py`

```python
import click
from catalog.embedding import CatalogEmbedder

@cli.command()
@click.argument('query')
@click.option('--top-k', default=10, help='Number of results to return')
def search(query: str, top_k: int):
    """Semantic search the catalog."""
    embedder = CatalogEmbedder(
        openai_api_key=os.getenv("LLM_API_KEY"),
        db_path="data/catalog.db"
    )

    results = embedder.semantic_search(query, top_k=top_k)

    click.echo(f"\nFound {len(results)} results for: {query}\n")
    for i, result in enumerate(results, 1):
        click.echo(f"{i}. {result['title']}")
        click.echo(f"   Similarity: {result['similarity']:.3f}")
        click.echo(f"   Keywords: {', '.join(result['keywords'][:5])}")
        click.echo()

    embedder.close()


@cli.command()
@click.argument('title')
def lineage(title: str):
    """Show data lineage for a dataset."""
    embedder = CatalogEmbedder(
        openai_api_key=os.getenv("LLM_API_KEY"),
        db_path="data/catalog.db"
    )

    result = embedder.get_lineage(title=title)

    if not result:
        click.echo(f"Dataset not found: {title}")
        return

    click.echo(f"\nDataset: {result['title']}\n")
    click.echo(f"Source: {result['src']}")
    click.echo(f"\nLineage ({len(result['lineage'])} steps):\n")

    for i, step in enumerate(result['lineage'], 1):
        click.echo(f"{i}. [{step.get('date', 'unknown')}]")
        click.echo(f"   {step.get('description', 'N/A')}\n")

    embedder.close()


@cli.command()
@click.option('--top-n', default=10, help='Number of keywords to show')
def keywords(top_n: int):
    """Show most frequently used keywords."""
    embedder = CatalogEmbedder(
        openai_api_key=os.getenv("LLM_API_KEY"),
        db_path="data/catalog.db"
    )

    results = embedder.get_top_keywords(top_n=top_n)

    click.echo(f"\nTop {top_n} Keywords:\n")
    for i, kw in enumerate(results, 1):
        click.echo(f"{i}. {kw['keyword']}: {kw['frequency']} datasets")

    embedder.close()


@cli.command()
@click.argument('catalog_path', type=click.Path(exists=True))
@click.option('--batch-size', default=10, help='Batch size for processing')
def embed(catalog_path: str, batch_size: int):
    """Generate embeddings for catalog data."""
    embedder = CatalogEmbedder(
        openai_api_key=os.getenv("LLM_API_KEY"),
        db_path="data/catalog.db"
    )

    embedder.initialize_database()
    embedder.process_catalog(catalog_path, batch_size=batch_size)
    embedder.close()

    click.echo("\n✓ Embeddings generated successfully")
```

### Usage Examples

```bash
# Generate embeddings (run once)
cod embed data/catalog.json

# Semantic search
cod search "erosion data"
cod search "fire management watersheds" --top-k 5

# Get lineage
cod lineage "Great Basin"

# Keyword statistics
cod keywords --top-n 20
```

## Implementation Roadmap

### Phase 1: Proof of Concept (1-2 days)

- [ ] Set up SQLite database with schema
- [ ] Create CatalogEmbedder class
- [ ] Process first 100 catalog items
- [ ] Test basic semantic search queries
- [ ] Validate query quality

### Phase 2: Full Implementation (2-3 days)

- [ ] Process entire catalog
- [ ] Optimize batch processing
- [ ] Implement all query types (semantic, FTS, hybrid)
- [ ] Add caching for embeddings
- [ ] Performance testing

### Phase 3: CLI Integration (1-2 days)

- [ ] Add `cod search` command
- [ ] Add `cod lineage` command
- [ ] Add `cod keywords` command
- [ ] Add `cod embed` command for processing
- [ ] Documentation and examples

### Phase 4: Enhancement (ongoing)

- [ ] Monitor query quality
- [ ] Fine-tune similarity thresholds
- [ ] Implement query result reranking
- [ ] Add filtering by date, source, etc.
- [ ] Consider migration to Faiss for large datasets

## Testing Strategy

```python
import pytest

def test_semantic_search(embedder):
    """Test various query types."""
    test_queries = [
        ("erosion data", "should find geological/soil datasets"),
        ("fire management", "should find fire-related datasets"),
        ("watershed boundaries", "should find hydrological datasets"),
        ("vegetation assessment", "should find ecological datasets"),
    ]

    for query, expected in test_queries:
        results = embedder.semantic_search(query, top_k=5)
        assert len(results) > 0, f"No results for query: {query}"
        assert all('similarity' in r for r in results)


def test_lineage_retrieval(embedder):
    """Test lineage retrieval."""
    lineage = embedder.get_lineage(title="Great Basin")
    assert lineage is not None
    assert 'lineage' in lineage
    assert isinstance(lineage['lineage'], list)


def test_keyword_analytics(embedder):
    """Test keyword frequency analysis."""
    top_kw = embedder.get_top_keywords(top_n=10)
    assert len(top_kw) <= 10
    assert all('keyword' in kw and 'frequency' in kw for kw in top_kw)
    # Verify descending order
    frequencies = [kw['frequency'] for kw in top_kw]
    assert frequencies == sorted(frequencies, reverse=True)


def test_fts_search(embedder):
    """Test full-text search."""
    results = embedder.fts_search("watershed", top_k=5)
    assert len(results) > 0
    assert all('rank' in r for r in results)


def test_hybrid_search(embedder):
    """Test hybrid semantic + FTS search."""
    results = embedder.hybrid_search("fire management", top_k=5)
    assert len(results) > 0
```

## Advantages of SQLite Approach

1. **Zero Configuration**
   - No database server to install or configure
   - Single file database
   - Works out of the box

2. **Portability**
   - Database is a single `.db` file
   - Easy to backup, copy, and distribute
   - Platform-independent

3. **Performance**
   - In-memory vector search is fast for moderate datasets
   - FTS5 full-text search is highly optimized
   - No network overhead

4. **Simplicity**
   - Standard Python `sqlite3` module
   - Familiar SQL syntax
   - Easy debugging with SQLite CLI tools

5. **Cost**
   - No database hosting costs
   - Only pay for embedding generation
   - Can use free open-source embedding models

## Limitations and Solutions

### Limitation 1: Large Datasets (>100K items)

**Solution**: Migrate to Faiss for approximate nearest neighbor search (shown in example above)

### Limitation 2: Concurrent Writes

**Solution**: SQLite handles concurrent reads well, but limited concurrent writes. For production with high write concurrency, consider PostgreSQL.

### Limitation 3: No Native Vector Indexing

**Solution**: Use in-memory search with NumPy/Faiss, or use sqlite-vec extension for native vector support.

## Conclusion

This SQLite-based proof of concept provides:

1. **Simple setup** with zero external dependencies
2. **Fast semantic search** using in-memory cosine similarity
3. **Traditional SQL** for exact matches and analytics
4. **Full-text search** using SQLite's FTS5
5. **Hybrid search** combining multiple approaches

**Total setup cost**: < $1 for embedding generation
**Query cost**: ~$0.001 per 1,000 queries
**Implementation time**: 1 week for full integration
**Database size**: ~50-100MB for 10,000 items (including embeddings)

The modular design allows easy migration to more sophisticated solutions (Faiss, PostgreSQL with pgvector) as the dataset grows, while maintaining a simple and effective solution for small to medium-sized catalogs.

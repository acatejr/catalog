# Vector Database Embedding Strategy - Proof of Concept

## Overview

This document outlines a proof-of-concept implementation for creating vector embeddings of the catalog.json geospatial dataset to enable semantic search and intelligent querying.

## Data Structure Analysis

Each catalog item contains:
- **title**: Dataset name (short identifier)
- **abstract**: Detailed description (200-500+ words typically)
- **purpose**: Intended use/rationale (100-300+ words)
- **keywords**: Array of domain-specific terms
- **lineage**: Array of process descriptions with dates
- **src**: Source identifier (e.g., "fsgeodata")

## Architecture

### Hybrid Approach: Vector DB + Relational Store

```
┌──────────────────────────────────────────┐
│   Vector Database (pgvector)            │
│   - Embeddings for semantic search      │
│   - HNSW index for fast similarity      │
└──────────────────────────────────────────┘
                ↓
┌──────────────────────────────────────────┐
│   PostgreSQL Database                    │
│   - Full document metadata               │
│   - Lineage details                      │
│   - Keyword analytics/aggregations       │
└──────────────────────────────────────────┘
```

## Embedding Strategy

### Concatenated Field Approach

Create a single embedding per dataset by concatenating fields in a structured format:

```
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
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Main catalog table
CREATE TABLE catalog_items (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    abstract TEXT,
    purpose TEXT,
    keywords TEXT[],
    lineage JSONB,
    src TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Vector embeddings table
CREATE TABLE catalog_embeddings (
    id SERIAL PRIMARY KEY,
    catalog_item_id INTEGER REFERENCES catalog_items(id),
    embedding vector(1536),  -- dimension depends on model (1536 for OpenAI text-embedding-3-small)
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create HNSW index for fast similarity search
CREATE INDEX ON catalog_embeddings USING hnsw (embedding vector_cosine_ops);

-- Keyword frequency materialized view for analytics
CREATE MATERIALIZED VIEW keyword_frequencies AS
SELECT
    keyword,
    COUNT(*) as frequency,
    ARRAY_AGG(catalog_item_id) as item_ids
FROM catalog_items, UNNEST(keywords) AS keyword
GROUP BY keyword
ORDER BY frequency DESC;
```

### 2. Python Proof of Concept

```python
#!/usr/bin/env python3
"""
Vector Embedding POC for Catalog Data
Requires: pip install openai psycopg2-binary pgvector numpy
"""

import json
import os
from typing import List, Dict, Any
import psycopg2
from psycopg2.extras import execute_values
from openai import OpenAI

# Configuration
EMBEDDING_MODEL = "text-embedding-3-small"  # 1536 dimensions, $0.02/1M tokens
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/catalog")


class CatalogEmbedder:
    """Handle embedding generation and storage for catalog data."""

    def __init__(self, openai_api_key: str, db_url: str):
        self.client = OpenAI(api_key=openai_api_key)
        self.conn = psycopg2.connect(db_url)
        self.cursor = self.conn.cursor()

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

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text using OpenAI API.

        Args:
            text: Input text

        Returns:
            Embedding vector as list of floats
        """
        response = self.client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding

    def batch_generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch (more efficient).

        Args:
            texts: List of input texts

        Returns:
            List of embedding vectors
        """
        response = self.client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=texts
        )
        # Sort by index to ensure order matches input
        sorted_data = sorted(response.data, key=lambda x: x.index)
        return [item.embedding for item in sorted_data]

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
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        self.cursor.execute(
            query,
            (
                item.get('title'),
                item.get('abstract'),
                item.get('purpose'),
                item.get('keywords', []),
                json.dumps(item.get('lineage', [])),
                item.get('src')
            )
        )
        return self.cursor.fetchone()[0]

    def store_embedding(self, catalog_item_id: int, embedding: List[float]):
        """
        Store embedding vector in database.

        Args:
            catalog_item_id: Foreign key to catalog_items
            embedding: Embedding vector
        """
        query = """
            INSERT INTO catalog_embeddings (catalog_item_id, embedding)
            VALUES (%s, %s)
        """
        self.cursor.execute(query, (catalog_item_id, embedding))

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

        # Refresh keyword frequencies view
        self.cursor.execute("REFRESH MATERIALIZED VIEW keyword_frequencies")
        self.conn.commit()

        print(f"✓ Successfully processed {len(catalog_items)} items")

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

        # Search using cosine similarity
        search_query = """
            SELECT
                ci.id,
                ci.title,
                ci.abstract,
                ci.purpose,
                ci.keywords,
                ci.lineage,
                ci.src,
                1 - (ce.embedding <=> %s::vector) AS similarity
            FROM catalog_embeddings ce
            JOIN catalog_items ci ON ce.catalog_item_id = ci.id
            WHERE 1 - (ce.embedding <=> %s::vector) >= %s
            ORDER BY ce.embedding <=> %s::vector
            LIMIT %s
        """

        self.cursor.execute(
            search_query,
            (query_embedding, query_embedding, similarity_threshold, query_embedding, top_k)
        )

        results = []
        for row in self.cursor.fetchall():
            results.append({
                'id': row[0],
                'title': row[1],
                'abstract': row[2],
                'purpose': row[3],
                'keywords': row[4],
                'lineage': json.loads(row[5]) if row[5] else [],
                'src': row[6],
                'similarity': float(row[7])
            })

        return results

    def get_lineage(self, title: str = None, item_id: int = None) -> Dict[str, Any]:
        """
        Retrieve lineage information for a specific dataset.
        This is NOT a vector search - it's exact/fuzzy metadata retrieval.

        Args:
            title: Dataset title (fuzzy match using ILIKE)
            item_id: Dataset ID (exact match)

        Returns:
            Catalog item with lineage details
        """
        if item_id:
            query = "SELECT * FROM catalog_items WHERE id = %s"
            self.cursor.execute(query, (item_id,))
        elif title:
            query = "SELECT * FROM catalog_items WHERE title ILIKE %s"
            self.cursor.execute(query, (f"%{title}%",))
        else:
            raise ValueError("Must provide either title or item_id")

        row = self.cursor.fetchone()
        if not row:
            return None

        return {
            'id': row[0],
            'title': row[1],
            'abstract': row[2],
            'purpose': row[3],
            'keywords': row[4],
            'lineage': json.loads(row[5]) if row[5] else [],
            'src': row[6]
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
            LIMIT %s
        """
        self.cursor.execute(query, (top_n,))

        results = []
        for row in self.cursor.fetchall():
            results.append({
                'keyword': row[0],
                'frequency': row[1],
                'item_ids': row[2]
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
        query = """
            SELECT id, title, abstract, purpose, keywords, lineage, src
            FROM catalog_items
            WHERE keywords && %s
            ORDER BY title
        """
        self.cursor.execute(query, (keywords,))

        results = []
        for row in self.cursor.fetchall():
            results.append({
                'id': row[0],
                'title': row[1],
                'abstract': row[2],
                'purpose': row[3],
                'keywords': row[4],
                'lineage': json.loads(row[5]) if row[5] else [],
                'src': row[6]
            })

        return results

    def close(self):
        """Close database connection."""
        self.cursor.close()
        self.conn.close()


# Example usage
def main():
    """Example usage of the CatalogEmbedder."""

    # Initialize
    embedder = CatalogEmbedder(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        db_url=DATABASE_URL
    )

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

    # Hybrid search: Semantic + keyword filter
    print("\n=== Hybrid Search: Watersheds with 'fire' keyword ===")
    semantic_results = embedder.semantic_search("watershed management", top_k=20)
    filtered = [r for r in semantic_results if 'fire' in r['keywords']]
    for result in filtered[:5]:
        print(f"- {result['title']} (similarity: {result['similarity']:.3f})")

    embedder.close()


if __name__ == "__main__":
    main()
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
**Approach**: Combine semantic search with keyword filtering

```python
# Find semantically similar documents
results = embedder.semantic_search("water quality monitoring", top_k=50)

# Filter by specific keywords
filtered = [r for r in results if 'inlandWaters' in r['keywords']]
```

**Why**: Combines broad semantic matching with precise keyword filtering.

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
Consider **nomic-embed-text** or **all-MiniLM-L6-v2**:
- Free to run locally or self-host
- Dimensions: 384-768 (smaller than OpenAI's 1536)
- Slightly lower quality but sufficient for most use cases

## Performance Considerations

### HNSW Index Performance
- Query time: O(log n) for approximate nearest neighbor
- Expected query latency: <50ms for 10K documents
- Memory usage: ~6MB per 1K documents (1536 dimensions)

### Scaling Strategy
- Up to 100K documents: Single PostgreSQL instance with pgvector
- 100K-1M documents: Consider dedicated vector DB (Qdrant, Weaviate)
- 1M+ documents: Distributed vector search (Milvus, Pinecone)

## Alternative Vector Databases

### 1. ChromaDB
```python
import chromadb
from chromadb.config import Settings

client = chromadb.Client(Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory="./chroma_data"
))

collection = client.create_collection(name="catalog")
collection.add(
    documents=texts,
    embeddings=embeddings,
    metadatas=metadatas,
    ids=ids
)

results = collection.query(
    query_texts=["erosion data"],
    n_results=10
)
```

**Pros**: Python-native, easy to use, no separate server
**Cons**: Less production-ready than PostgreSQL

### 2. Qdrant
```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

client = QdrantClient(path="./qdrant_data")
client.create_collection(
    collection_name="catalog",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
)

results = client.search(
    collection_name="catalog",
    query_vector=query_embedding,
    limit=10
)
```

**Pros**: High performance, production-ready, great API
**Cons**: Another service to manage

## Implementation Roadmap

### Phase 1: Proof of Concept (1-2 days)
- [ ] Set up PostgreSQL with pgvector extension
- [ ] Create database schema
- [ ] Process first 100 catalog items
- [ ] Test basic semantic search queries
- [ ] Validate query quality

### Phase 2: Full Implementation (3-5 days)
- [ ] Process entire catalog
- [ ] Optimize batch processing
- [ ] Implement all query types (semantic, lineage, keyword analytics)
- [ ] Create CLI commands for querying
- [ ] Add caching for common queries

### Phase 3: Integration (2-3 days)
- [ ] Integrate with existing `cod` CLI
- [ ] Add `cod search <query>` command
- [ ] Add `cod lineage <dataset>` command
- [ ] Add `cod stats` command for keyword analytics
- [ ] Documentation and examples

### Phase 4: Enhancement (ongoing)
- [ ] Monitor query quality
- [ ] Fine-tune similarity thresholds
- [ ] Implement query result reranking
- [ ] Add support for filtering by date, source, etc.
- [ ] Consider hybrid search optimizations

## Testing Strategy

```python
def test_semantic_search():
    """Test various query types."""
    test_queries = [
        ("erosion data", "should find geological/soil datasets"),
        ("fire management", "should find fire-related datasets"),
        ("watershed boundaries", "should find hydrological datasets"),
        ("vegetation assessment", "should find ecological datasets"),
    ]

    for query, expected in test_queries:
        results = embedder.semantic_search(query, top_k=5)
        print(f"\nQuery: {query}")
        print(f"Expected: {expected}")
        print(f"Results: {[r['title'][:50] for r in results]}")
        assert len(results) > 0, f"No results for query: {query}"

def test_lineage_retrieval():
    """Test lineage retrieval."""
    lineage = embedder.get_lineage(title="Great Basin")
    assert lineage is not None
    assert 'lineage' in lineage
    assert isinstance(lineage['lineage'], list)

def test_keyword_analytics():
    """Test keyword frequency analysis."""
    top_kw = embedder.get_top_keywords(top_n=10)
    assert len(top_kw) <= 10
    assert all('keyword' in kw and 'frequency' in kw for kw in top_kw)
    # Verify descending order
    frequencies = [kw['frequency'] for kw in top_kw]
    assert frequencies == sorted(frequencies, reverse=True)
```

## Conclusion

This proof of concept demonstrates a practical, cost-effective approach to enabling semantic search on the geospatial catalog. The hybrid architecture leverages:

1. **Vector embeddings** for natural language semantic search
2. **Traditional SQL** for exact matches and analytics
3. **PostgreSQL + pgvector** for unified data management

The implementation handles all three query types efficiently:
- Semantic queries → Vector similarity search
- Lineage queries → Direct metadata retrieval
- Analytics queries → SQL aggregations

Total setup cost: **< $1** for embedding generation
Query cost: **~$0.001 per 1,000 queries**
Implementation time: **1-2 weeks** for full integration

The modular design allows for easy extension and integration with the existing `cod` CLI tool.

# Catalog Project Analysis & Enhancement Suggestions

## Project Summary

**Catalog** is a CLI-driven RAG (Retrieval-Augmented Generation) chatbot for discovering USFS geospatial datasets. It aggregates metadata from three federal data sources and provides semantic search capabilities via two distinct vector database implementations.

---

## Executive Summary

### Two RAG Approaches

1. **ChromaDB** - Built-in embeddings, simpler setup
2. **SQLite-vec** - Manual embeddings with sentence-transformers, more control

### Methodology Strengths

- Clean separation of concerns across layers
- Unified Pydantic schema normalizing 3 heterogeneous sources
- Rate limiting for respectful scraping
- Lineage tracking from FSGeodata XML

### Top Enhancement Recommendations

1. **Hybrid Search** - Combine BM25 + vector for technical terms like "MTBS", "FIA"
2. **Reranking** - Add cross-encoder for better precision (retrieve 20, rerank to 5)
3. **Conversation Memory** - Enable follow-up questions
4. **Evaluation Framework** - Create test queries to measure retrieval quality
5. **Streaming Responses** - Better UX for long outputs

### Blog/LinkedIn Ideas

- "Building a RAG Chatbot for Federal Geospatial Data Discovery"
- "Comparing ChromaDB vs sqlite-vec for Small-Scale RAG"
- Problem/solution posts about fragmented federal data discovery

---

## Architecture Overview

### Data Ingestion Pipeline
Three specialized loaders fetch and normalize metadata from USFS sources:

| Loader | Source | Format | Documents |
|--------|--------|--------|-----------|
| `FSGeodataLoader` | data.fs.usda.gov | XML (scraped) | Metadata + lineage |
| `RDALoader` | fs.usda.gov/rds/archive | JSON API | Research Data Archive |
| `GeospatialDataDiscovery` | ArcGIS Hub | DCAT-US JSON | Geospatial datasets |

### Two RAG Implementations

**1. ChromaDB Approach** (`ChromaVectorDB`)
- Uses ChromaDB's built-in embedding model
- Simpler setup, automatic embedding generation
- Persistent storage in `./chromadb/`

**2. SQLite-vec Approach** (`SqliteVectorDB`)
- Uses `sentence-transformers/all-MiniLM-L6-v2` for embeddings
- Manual embedding generation with full control
- Lightweight, single-file database

### LLM Integration
Two bot implementations for response generation:
- `OpenAIBot`: OpenAI-compatible API (configured for CyVerse LLM API)
- `OllamaBot`: Local/hosted Ollama instance

---

## Blog & LinkedIn Documentation Strategy

### Blog Post Ideas

**1. "Building a RAG Chatbot for Federal Geospatial Data Discovery"**
- Target audience: Data engineers, GIS professionals
- Cover the problem (fragmented federal data sources)
- Walk through the ETL pipeline design
- Discuss tradeoffs between ChromaDB vs sqlite-vec

**2. "Comparing Vector Databases: ChromaDB vs sqlite-vec for Small-Scale RAG"**
- Technical comparison with benchmarks
- When to choose each approach
- Code examples from your implementation

**3. "Democratizing Forest Service Data: A CLI Tool for Researchers"**
- Target audience: Environmental researchers, data scientists
- Focus on the use case and impact
- Include example queries and outputs

### LinkedIn Post Angles

**Technical Achievement Post:**
> Built a CLI tool that aggregates 3 federal geospatial data sources into a unified RAG chatbot. Implemented two vector DB approaches (ChromaDB + sqlite-vec) to compare tradeoffs. Open to feedback from the GIS/ML community.

**Problem-Solution Post:**
> Researchers waste hours searching fragmented USFS data portals. Built a semantic search tool that lets you ask "Is there wildfire boundary data?" instead of manually browsing 3 different catalogs.

**Lessons Learned Post:**
> What I learned building a RAG system from scratch:
> - ChromaDB is faster to prototype, sqlite-vec gives more control
> - Metadata quality matters more than embedding model choice
> - Rate limiting is essential when scraping federal sites

---

## Methodology Analysis

### Strengths
1. **Clean separation of concerns**: Data loading, schema, vector DB, and LLM layers are well-isolated
2. **Unified schema**: `Document` model normalizes heterogeneous sources
3. **Dual implementation approach**: Provides comparison basis and fallback options
4. **Rate limiting**: Respectful 0.5s delay prevents overwhelming federal servers
5. **Lineage tracking**: Captures data provenance from FSGeodata XML

### Areas for Improvement
1. **No conversation memory**: Each query is independent
2. **No reranking**: Results ordered purely by vector similarity
3. **Static context window**: Fixed 5 results passed to LLM
4. **No evaluation framework**: No way to measure retrieval quality
5. **Embedding model is generic**: Not optimized for geospatial domain

---

## Suggested AI Feature Enhancements

### 1. Hybrid Search (BM25 + Vector)

Combine keyword search with semantic search for better retrieval on technical terms.

```python
# Concept: Use rank fusion to combine results
from rank_bm25 import BM25Okapi

class HybridSearch:
    def __init__(self, vector_db, documents):
        self.vector_db = vector_db
        tokenized = [doc.split() for doc in documents]
        self.bm25 = BM25Okapi(tokenized)

    def search(self, query, k=10, alpha=0.5):
        # Get vector results
        vector_results = self.vector_db.query(query, k=k*2)

        # Get BM25 results
        bm25_scores = self.bm25.get_scores(query.split())

        # Reciprocal rank fusion
        return self.fuse_results(vector_results, bm25_scores, alpha)
```

**Why**: Geospatial queries often contain specific terms (e.g., "MTBS", "FIA plots") that benefit from exact matching.

---

### 2. Query Expansion with LLM

Use the LLM to expand queries before retrieval.

```python
def expand_query(self, original_query: str) -> list[str]:
    prompt = f"""Given this search query about USFS geospatial data:
    "{original_query}"

    Generate 3 alternative phrasings that might match relevant datasets.
    Include technical terms, acronyms, and synonyms.
    Return as a JSON list."""

    expanded = self.llm.generate(prompt)
    return [original_query] + json.loads(expanded)
```

**Why**: Users may not know exact dataset names or USFS terminology.

---

### 3. Conversation Memory with LangChain

Add multi-turn conversation support.

```python
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import ConversationalRetrievalChain

class ConversationalCatalogBot:
    def __init__(self, retriever, llm):
        self.memory = ConversationBufferWindowMemory(
            k=5,  # Remember last 5 exchanges
            memory_key="chat_history",
            return_messages=True
        )
        self.chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=retriever,
            memory=self.memory
        )

    def chat(self, question: str) -> str:
        return self.chain.run(question)
```

**Why**: Enables follow-up questions like "What about just for California?" without restating context.

---

### 4. Reranking with Cross-Encoder

Add a reranking step to improve precision.

```python
from sentence_transformers import CrossEncoder

class Reranker:
    def __init__(self):
        self.model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

    def rerank(self, query: str, documents: list[dict], top_k: int = 5):
        pairs = [(query, doc['abstract']) for doc in documents]
        scores = self.model.predict(pairs)

        ranked = sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)
        return [doc for doc, score in ranked[:top_k]]
```

**Why**: Cross-encoders are more accurate than bi-encoders for final ranking; retrieve 20, rerank to 5.

---

### 5. Domain-Specific Embeddings

Fine-tune or use a geospatial-aware embedding model.

**Option A**: Use a scientific embedding model
```python
# Instead of all-MiniLM-L6-v2
model = SentenceTransformer('allenai/specter2')  # Scientific papers
# or
model = SentenceTransformer('BAAI/bge-base-en-v1.5')  # Better general performance
```

**Option B**: Fine-tune on your corpus (if you have labeled query-document pairs)

**Why**: Generic models may not capture geospatial terminology relationships (e.g., "FIA" ≈ "Forest Inventory and Analysis").

---

### 6. Structured Output & Citations

Return structured responses with source citations.

```python
from pydantic import BaseModel

class DatasetRecommendation(BaseModel):
    answer: str
    datasets: list[dict]  # id, title, relevance_reason
    confidence: float
    suggested_followup: list[str]

STRUCTURED_PROMPT = """Based on the context, answer the question and return JSON:
{
  "answer": "Direct answer to the question",
  "datasets": [{"id": "...", "title": "...", "relevance_reason": "..."}],
  "confidence": 0.0-1.0,
  "suggested_followup": ["Related question 1", "Related question 2"]
}"""
```

**Why**: Makes responses more actionable and verifiable.

---

### 7. Evaluation Framework

Add retrieval quality metrics.

```python
class RAGEvaluator:
    def __init__(self, test_queries: list[dict]):
        # test_queries = [{"query": "...", "relevant_doc_ids": [...]}]
        self.test_queries = test_queries

    def evaluate(self, retriever, k=5):
        metrics = {"precision@k": [], "recall@k": [], "mrr": []}

        for test in self.test_queries:
            results = retriever.query(test["query"], k=k)
            result_ids = [r["id"] for r in results]
            relevant = set(test["relevant_doc_ids"])

            # Precision@k
            hits = len(set(result_ids) & relevant)
            metrics["precision@k"].append(hits / k)

            # Recall@k
            metrics["recall@k"].append(hits / len(relevant) if relevant else 0)

            # MRR (Mean Reciprocal Rank)
            for i, rid in enumerate(result_ids):
                if rid in relevant:
                    metrics["mrr"].append(1 / (i + 1))
                    break
            else:
                metrics["mrr"].append(0)

        return {k: sum(v)/len(v) for k, v in metrics.items()}
```

**Why**: Can't improve what you can't measure. Create a small test set of ~20 queries with known relevant documents.

---

### 8. Streaming Responses

Add streaming for better UX on long responses.

```python
def chat_stream(self, question: str, context: str):
    for chunk in self.client.chat.completions.create(
        model=self.model,
        messages=[...],
        stream=True
    ):
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
```

**Why**: Users see responses forming in real-time rather than waiting for complete generation.

---

### 9. Caching Layer

Cache embeddings and common queries.

```python
import hashlib
from functools import lru_cache

class CachedVectorDB:
    def __init__(self, vector_db):
        self.db = vector_db
        self.query_cache = {}

    def query(self, query: str, k: int = 5):
        cache_key = hashlib.md5(f"{query}:{k}".encode()).hexdigest()

        if cache_key not in self.query_cache:
            self.query_cache[cache_key] = self.db.query(query, k)

        return self.query_cache[cache_key]
```

**Why**: Repeated queries (common in demos/testing) don't need to re-compute embeddings.

---

### 10. Agentic RAG with Tool Use

Enable the LLM to decide when to search and what to search for.

```python
TOOLS = [
    {
        "name": "search_catalog",
        "description": "Search the USFS geospatial data catalog",
        "parameters": {
            "query": "Search query string",
            "source_filter": "Optional: 'fsgeodata', 'rda', or 'gdd'"
        }
    },
    {
        "name": "get_dataset_details",
        "description": "Get full details for a specific dataset by ID"
    }
]

# LLM decides: "I need to search for wildfire data, then get details on the top result"
```

**Why**: Enables multi-step reasoning: search → filter → compare → recommend.

---

## Implementation Priority

| Enhancement | Effort | Impact | Priority |
|------------|--------|--------|----------|
| Hybrid Search | Medium | High | 1 |
| Reranking | Low | High | 2 |
| Conversation Memory | Medium | High | 3 |
| Streaming Responses | Low | Medium | 4 |
| Evaluation Framework | Medium | High | 5 |
| Structured Output | Low | Medium | 6 |
| Query Expansion | Medium | Medium | 7 |
| Caching | Low | Low | 8 |
| Domain Embeddings | High | Medium | 9 |
| Agentic RAG | High | High | 10 |

---

## Quick Wins (< 1 day each)

1. Add `--stream` flag to chat commands for streaming output
2. Implement result caching with TTL
3. Add `--source` filter to limit search to specific data sources
4. Create 10-20 test queries for evaluation baseline
5. Switch to `BAAI/bge-base-en-v1.5` for better embeddings

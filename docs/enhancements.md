# Catalog Project Analysis & Enhancement Suggestions

Pending ehancements.

## Project Summary

**Catalog** is a CLI-driven RAG (Retrieval-Augmented Generation) chatbot for discovering USFS geospatial datasets. It aggregates metadata from three federal data sources and provides semantic search capabilities via two distinct vector database implementations.

---

## Suggested AI Feature Enhancements

### 1. Query Expansion with LLM

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

### 2. Conversation Memory with LangChain

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

### 3. Reranking with Cross-Encoder

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

### 4. Domain-Specific Embeddings

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

### 5. Structured Output & Citations

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

### 6. Evaluation Framework

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

### 7. Streaming Responses

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

### 8. Caching Layer

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

### 9. Agentic RAG with Tool Use

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
| Reranking | Low | High | 1 |
| Conversation Memory | Medium | High | 2 |
| Streaming Responses | Low | Medium | 3 |
| Evaluation Framework | Medium | High | 4 |
| Structured Output | Low | Medium | 5 |
| Query Expansion | Medium | Medium | 6 |
| Caching | Low | Low | 7 |
| Domain Embeddings | High | Medium | 8 |
| Agentic RAG | High | High | 9 |

---

## Quick Wins (< 1 day each)

1. Add reranking with `cross-encoder/ms-marco-MiniLM-L-6-v2` (low effort, high impact)
2. Add `--stream` flag to chat commands for streaming output
3. Implement result caching with TTL
4. Add `--source` filter to limit search to specific data sources
5. Create 10-20 test queries for evaluation baseline

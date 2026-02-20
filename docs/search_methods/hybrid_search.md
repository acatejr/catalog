# Hybrid Search and rank_bm25

## Hybrid Search

Hybrid search combines two retrieval strategies into one system:

- **Keyword/sparse search** (e.g., BM25) -- great at exact matches like error codes, SKUs, proper names, and domain-specific terms.
- **Semantic/dense vector search** (e.g., embeddings via Sentence Transformers) -- great at understanding meaning, synonyms, and conceptual similarity.

Neither alone covers all query types. Hybrid search runs both in parallel, then **fuses** the results using methods like:

- **Reciprocal Rank Fusion (RRF)** -- merges based on rank positions, avoiding score-scale mismatch: `RRF_score = sum(1 / (k + rank_i))`
- **Weighted linear combination** -- normalizes scores to [0,1] and blends: `final = alpha * semantic + (1 - alpha) * keyword`

## rank_bm25

A pure-Python library implementing the BM25 ranking algorithm (the same algorithm powering Elasticsearch/Solr). It provides three variants:

| Class | Best for |
|-------|----------|
| `BM25Okapi` | Standard choice, most widely used |
| `BM25L` | When long documents are penalized too much |
| `BM25Plus` | Ensures every term match contributes positively (good for short chunks in RAG) |

Key characteristics:

- **No external search engine needed** -- runs entirely in memory.
- **You must handle tokenization yourself** (lowercasing, stopwords, stemming).
- Simple API: `bm25.get_scores(query)` and `bm25.get_top_n(query, docs, n=k)`.

## How They Fit Together

`rank_bm25` serves as the keyword component in a hybrid search pipeline:

```
Query --> [rank_bm25 BM25Okapi]    --> keyword ranked list  \
      --> [Vector DB + embeddings] --> semantic ranked list  }--> Fusion --> Final results
```

LangChain's `EnsembleRetriever` wraps this pattern with `BM25Retriever` (uses rank_bm25 internally) combined with any vector retriever, with configurable weights.

**Note:** `rank_bm25` is low-maintenance. A faster alternative called **bm25s** exists using scipy sparse matrices, but rank_bm25 remains the most commonly used due to its simplicity and LangChain integration.

---
date: 2026-02-25
title: Semantic Search
---

# Semantic Search - Where it All Started

<!-- more -->
## What is it?

Semantic search is a retrieval technique that finds documents based on
*meaning* rather than exact word matches. Instead of looking for documents
that contain the same words as your query, it looks for documents that are
*about* the same thing — even if they use completely different vocabulary.

This works by converting text into dense numerical vectors called embeddings.
Words and phrases that mean similar things end up close to each other in that
high-dimensional space. At query time, the search engine finds documents whose
embeddings are nearest to the query embedding — a process called nearest
neighbor search.

## Why?

Keyword search breaks down quickly in a domain like USFS geospatial data. The
people searching for datasets and the people who wrote the dataset metadata
rarely use the same words.

A user might search for "forest road conditions" but the relevant dataset
abstract says "unpaved surface transportation infrastructure maintenance
status". Those share almost no words, so a keyword search returns nothing
useful. Semantic search surfaces it anyway, because both phrases encode to
similar vector locations.

There's also the breadth problem. The USFS catalog spans thousands of
datasets — boundaries, hydrology, fire history, wildlife habitat, road
networks, timber, recreation, and more. Without semantic understanding, users
have to guess the right terminology before they can find anything.

## How?

Catalog uses [ChromaDB](https://www.trychroma.com/) as its vector store, with
the default embedding model (all-MiniLM-L6-v2 via sentence-transformers).

When the vector store is built, each dataset record is converted into a
structured text document that concatenates its title, abstract, description,
purpose, source, keywords, and lineage:

```python
documents.append(
    f"Title: {title}\n"
    f"Abstract: {abstract}\n"
    f"Description: {description}\n"
    f"Purpose: {purpose}\n"
    f"Source: {source}\n"
    f"Keywords: {', '.join(doc.keywords) if doc.keywords else ''}\n"
    f"Lineage: {lineage_str}\n"
)
```

ChromaDB embeds each of those text blocks and stores them alongside their
metadata. At query time, the same embedding model converts the user's question
into a vector, and ChromaDB returns the nearest neighbors by cosine distance:

```python
results = self.collection.query(query_texts=[qstn], n_results=nresults)
```

The returned distance score (lower is closer) gives a rough signal of how
relevant each result is. Results are returned as `(USFSDocument, distance)`
tuples so downstream commands can rank or filter them further.

## Examples

Build the vector store after downloading and cataloging metadata:

```bash
uv run catalog build-fs-chromadb
```

Run a semantic query:

```bash
uv run catalog query-fs-chromadb --qstn "wildfire risk data"
uv run catalog query-fs-chromadb -q "watershed boundaries" -n 10
```

The search understands intent, not just keywords. These all find relevant
datasets even though the words don't appear verbatim in most records:

```bash
uv run catalog query-fs-chromadb -q "areas that burned recently"
uv run catalog query-fs-chromadb -q "where can I hike in a national forest"
uv run catalog query-fs-chromadb -q "stream crossings on forest roads"
```

For richer results, semantic search can be combined with BM25 keyword search
via hybrid search, or handed off to an LLM for a natural language answer:

```bash
# Hybrid: BM25 + semantic, fused with Reciprocal Rank Fusion
uv run catalog hybrid-search -q "fire perimeter data"

# LLM-synthesized answer from semantic results
uv run catalog ollama-chat -q "What datasets exist for forest road conditions?"
```


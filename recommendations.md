# Project Recommendations

This document outlines recommendations for improving the Catalog project based on comprehensive codebase reviews.

---

## Priority Actions

| Priority | Action                                          | Status  |
| -------- | ----------------------------------------------- | ------- |
| High     | Query rewriting / expansion before vector search | Done |
| High     | HyDE (Hypothetical Document Embedding)           | Pending |
| Medium   | Conversational memory for follow-up questions    | Pending |
| Medium   | Cross-encoder re-ranking after retrieval         | Pending |
| Medium   | Add progress indicators                          | Pending |
| Medium   | Implement Ollama streaming                       | Pending |
| High     | Agentic tool use (LLM-driven search loop)        | Done |
| Low      | Refactor to subpackages                          | Pending |
| Low      | Add pre-commit hooks                             | Done    |
| Low      | Centralize configuration                         | Done    |

---

## AI / LLM Improvements

The current pipeline is a solid RAG foundation — hybrid search (BM25 + vector + RRF fusion) is well above average. The main weaknesses are:

1. **The question goes into retrieval verbatim** — no pre-processing to improve recall
2. **Retrieval happens once** — no iteration if results are poor
3. **The LLM is only a synthesizer** — it cannot drive the search process
4. **No conversation memory** — each question is independent

### Recommended Roadmap

| Priority | Change                   | Effort | Impact |
| -------- | ------------------------ | ------ | ------ |
| 1        | Query rewriting/expansion | Low    | High   |
| 2        | HyDE                     | Low    | High   |
| 3        | Conversational memory     | Medium | Medium |
| 4        | Agentic tool use          | High   | High   |
| 5        | Cross-encoder re-ranking  | Medium | Medium |

### 1. Query Rewriting / Expansion (Best ROI)

Before hitting ChromaDB, use a fast LLM call to expand the query with domain synonyms. The geospatial/forestry domain has significant jargon mismatch between how users phrase questions and how catalog abstracts are written.

**Example:**
```
User:     "post-wildfire erosion data"
Expanded: "post-fire sediment erosion burn area soil stability
           fire effects hydrology watershed BAER"
```

This improves recall without any schema or architecture changes. Small local models (e.g., `llama3.2:1b`) handle this well. Add the expansion step in `core.py` before calling `ChromaVectorDB.query()`.

### 2. HyDE — Hypothetical Document Embedding

Instead of embedding the question directly, ask the LLM to generate what a *perfect matching dataset abstract* would look like, then embed that. Questions and abstracts live in different embedding spaces; HyDE bridges that gap.

**Example:**
```
Question: "Is there post-wildfire erosion data?"

HyDE:     "This dataset contains field measurements of sediment
           transport and rill erosion collected in burn areas
           following the 2020 fire season across National Forest
           lands in the Pacific Northwest..."
```

The HyDE text is much closer to your actual document embeddings, improving retrieval quality.

### 3. Conversational Memory

Currently each question is stateless. Adding message history lets users ask follow-up questions naturally:

```
> "Is there wildfire erosion data?"
[response]
> "Show me more about the second one"
> "Are there similar datasets from 2020 onwards?"
```

This is a straightforward addition — thread a `messages` list through `OllamaBot.chat()` and `VerdeBot.chat()`. Already listed as a remaining item under LLM Integration below.

### 4. Agentic Tool Use (Biggest Architectural Leap)

Instead of one retrieval pass, give the LLM tools and let it drive the search process. The LLM can decide when results are insufficient and search again with refined terms.

```python
tools = [
    search_vector_db(query, n_results),
    search_by_keyword(keyword),
    get_document_details(doc_id),
    filter_by_source(source),  # fsgeodata, gdd, rda
]
```

Ollama supports tool use with models like `qwen2.5` and `llama3.1`. This turns a single-pass RAG into a reasoning loop.

### 5. Cross-Encoder Re-ranking

RRF fusion ranks by relevance-to-query, but not by how well each document actually answers the question. After retrieval, score each result directly:

```
"On a scale of 0-10, how well does this dataset satisfy:
 'post-wildfire erosion monitoring'? Dataset: {abstract}"
```

Re-sort by these scores before passing context to the LLM. This catches cases where high-ranking docs are topic-adjacent but not truly relevant.

### What Is NOT Worth Adding

- **Fine-tuning an LLM** on the catalog — the catalog changes frequently; RAG is better suited for dynamic data
- **GraphRAG** — significant complexity; useful for richly-connected data, but catalog documents are relatively flat
- **Multiple coordinating agents** — overkill for a dataset discovery use case

---

## Feature Suggestions

### Add Progress Indicators

Use Click's built-in progress bar for long-running downloads:

```python
with click.progressbar(datasets, label="Downloading") as bar:
    for dataset in bar:
        # download logic
```

### Organize Data Loaders

Consider grouping loaders into a subpackage:

```text
src/catalog/
├── loaders/
│   ├── __init__.py
│   ├── base.py          # Abstract base loader
│   ├── fsgeodata.py
│   ├── gdd.py
│   └── rda.py
├── cli.py
├── core.py
├── lib.py
└── schema.py
```

---

## LLM Integration Status

### Completed

1. **RAG pattern implemented** — `ollama_chat` CLI command queries ChromaDB, builds markdown context with `USFSDocument.to_markdown()`, and sends it to Ollama via `OllamaBot.chat()`
2. **Hybrid search** — `HybridSearch` combines BM25 keyword search and vector search via Reciprocal Rank Fusion (RRF)
3. **Structured query results** — `ChromaVectorDB.query()` returns `list[tuple[USFSDocument, float]]` with distance scores
4. **Distance-aware LLM context** — Relevance distance is included in the context sent to Ollama; system prompt instructs the LLM to prioritize lower-distance results
5. **Batch document loading** — `batch_load_documents()` uses real document IDs and processes in configurable batch sizes
6. **Deduplication** — `load_document_metadata()` deduplicates by document ID; standalone `dedupe_catalog()` available in `lib.py`
7. **`to_markdown()` on `USFSDocument`** — Formatting lives on the model with optional `distance` parameter
8. **Abstract in metadata** — `batch_load_documents()` stores `abstract` in ChromaDB metadata so `query()` can reconstruct it
9. **OllamaBot uses configured URL** — Client uses `self.OLLAMA_BASE_URL` instead of hardcoded URL
10. **Unbound variables fixed** — `usfs.py:FSGeodataLoader.parse_metadata` initializes all variables with defaults

### Remaining

1. **Add conversation history** — Store context for follow-up questions
2. **Implement streaming** — Use Ollama's streaming API for better UX
3. **Add source citations** — Include document references in LLM responses

---

Generated on 2026-01-26, last updated 2026-03-03

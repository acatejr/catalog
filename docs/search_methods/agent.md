# Agent Search

Agent search puts the LLM in control of the search process. Rather than
retrieving documents once and handing them to the model, it gives the LLM a
set of tools and lets it decide how to search — iterating until it has enough
information to answer the question.

This addresses a core limitation of single-pass RAG: if the first retrieval
misses the mark, there's no recovery. With agent search, the model can try a
different query, switch search strategies, or drill into a specific record
before synthesizing a final answer.

## How It Works

The `AgentBot` class runs a reasoning loop. On each iteration it sends the
conversation — including any prior tool results — to the LLM. If the model
returns tool calls, those are executed and the results are appended to the
message history. The loop continues until the LLM stops calling tools
(indicating it has a final answer) or a maximum iteration limit is reached:

```
User question
     ↓
LLM calls: search_vector_db("post-fire erosion")
     ↓
"Only 2 results — let me try a different approach"
     ↓
LLM calls: search_hybrid("fire effects sediment BAER watershed")
     ↓
Better results! LLM calls: get_document_details("doc-xyz-123")
     ↓
LLM synthesizes a final answer with citations
```

## Available Tools

The agent has four tools defined in [tools.py](../../src/catalog/tools.py):

| Tool | Purpose |
|---|---|
| `search_vector_db` | Semantic similarity search via ChromaDB |
| `search_hybrid` | BM25 + vector search with Reciprocal Rank Fusion |
| `filter_by_source` | Narrow results to `fsgeodata`, `gdd`, or `rda` |
| `get_document_details` | Fetch full metadata for a specific dataset ID |

The model picks the right tool for each step based on the tool descriptions.
Keyword-heavy queries tend to go to `search_hybrid`; conceptual queries go to
`search_vector_db`; source-specific questions use `filter_by_source`.

## Usage

```bash
uv run catalog agent-search -q "Is there post-wildfire erosion monitoring data?"
uv run catalog agent-search -q "What trail data is available for Region 5?"
```

Agent search requires an Ollama model that supports tool calling. Models known
to work well: `qwen2.5`, `llama3.1`, `mistral-nemo`.

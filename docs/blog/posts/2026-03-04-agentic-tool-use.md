---
date: 2026-03-04
title: From Single-Pass RAG to Agentic Tool Use
---

# From Single-Pass RAG to Agentic Tool Use

<!-- more -->

I've been having a lot of fun working on the Catalog project lately — a Python
CLI tool for discovering geospatial datasets from the USFS Geodata
Clearinghouse. It's one of those projects where every improvement unlocks a
new idea, and this week's improvement was one I've been looking forward to
for a while: **agentic tool use**.

Let me share what that means, why I think it's a meaningful step forward, and
how it came together in practice.

## Where We Started

The pipeline already had some solid foundations — hybrid search combining BM25
keyword matching and ChromaDB vector search, fused with Reciprocal Rank
Fusion. Not bad! But there was a ceiling.

The flow looked like this:

```
User question → ChromaDB query → context string → LLM → answer
```

One shot. If the first retrieval missed the mark, the LLM had no way to
recover. It would just work with whatever landed in front of it.

Geospatial and forestry data makes this especially tricky. A user asking about
"post-fire erosion" may not use the same words as a dataset abstract that says
"burn area soil stability", "BAER assessment", or "sediment transport
monitoring". That jargon gap is real, and a single retrieval pass can't always
bridge it.

## The Idea: Let the LLM Drive

What if, instead of retrieving documents *for* the LLM, we gave the LLM tools
and let it decide *how* to search?

That's the heart of agentic tool use. The LLM enters a reasoning loop — it
calls a tool, looks at the results, decides whether that's enough, and if not,
tries again with a refined approach:

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

It's a small architectural shift, but it changes the character of the
interaction entirely. The LLM becomes an active participant in the search
process rather than a passive synthesizer.

## The Tools

I exposed four tools via Ollama's tool-calling API:

| Tool | Purpose |
|---|---|
| `search_vector_db` | Semantic similarity search via ChromaDB |
| `search_hybrid` | BM25 + vector search with RRF fusion |
| `filter_by_source` | Narrow results to `fsgeodata`, `gdd`, or `rda` |
| `get_document_details` | Fetch full metadata for a specific dataset ID |

Each tool is defined as a JSON schema. Here's what one looks like:

```python
{
    "type": "function",
    "function": {
        "name": "search_hybrid",
        "description": "Search using BM25 keyword + semantic vector search.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "n_results": {"type": "integer", "default": 5}
            },
            "required": ["query"]
        }
    }
}
```

Nothing too exotic — just a clear description so the model knows when and why
to reach for each tool.

## The Reasoning Loop

The `AgentBot` class in `bots.py` ties it together. The loop runs until the
LLM stops calling tools (meaning it has what it needs), or until we hit a
maximum iteration limit as a safety guard:

```python
class AgentBot:
    MAX_ITERATIONS = 5

    def run(self, question: str) -> str:
        messages = [system_prompt, user_message(question)]

        for _ in range(self.MAX_ITERATIONS):
            response = self.client.chat(
                model=self.model,
                messages=messages,
                tools=TOOLS,
            )
            msg = response["message"]
            messages.append(msg)

            tool_calls = msg.get("tool_calls")
            if not tool_calls:
                return msg["content"]  # LLM is satisfied — final answer

            for tc in tool_calls:
                result = execute_tool(
                    tc["function"]["name"],
                    tc["function"]["arguments"],
                    self.db, self.hs
                )
                messages.append({"role": "tool", "content": result})

        return "Maximum iterations reached."
```

The model appends tool results to its message history and reasons over the
growing context on each pass. It's genuinely satisfying to watch it work
through a tricky query.

## Trying It Out

The new `agent-search` CLI command makes it easy to kick the tires:

```bash
catalog agent-search --qstn "Is there post-wildfire erosion monitoring data?"
```

One thing worth noting: you'll want an Ollama model that supports tool calling.
`qwen2.5`, `llama3.1`, and `mistral-nemo` all work well here.

## What Changed in the Code

I tried to keep the footprint small. The existing `ChromaVectorDB` and
`HybridSearch` infrastructure was reused as-is — no changes needed there.

| File | Change |
|---|---|
| `src/catalog/tools.py` | New — tool schemas and executor |
| `src/catalog/bots.py` | Added `AgentBot` class |
| `src/catalog/cli.py` | Added `agent_search` command |

## What's Coming Next

There are a few things I'm excited to tackle next:

- **Conversational memory** — so users can ask natural follow-up questions
  without repeating context
- **Streaming responses** — Ollama supports streaming and it makes a real
  difference in how the tool feels to use
- **HyDE (Hypothetical Document Embedding)** — generating a hypothetical
  matching abstract before searching, to close the vocabulary gap further

If you're working on something similar or have thoughts on the approach, I'd
love to hear from you. And if you want to dig into the code, it's all up on
GitHub at [github.com/forestbytes/catalog](https://github.com/forestbytes/catalog).

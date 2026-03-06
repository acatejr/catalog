---
date: 2026-03-04
title: Query Expansion — Helping Users Say What They Mean
---

# Query Expansion — Helping Users Say What They Mean

One of the quiet challenges in building a dataset discovery tool is that the
people searching for data and the people who wrote the dataset descriptions
rarely use the same words.

A researcher might type "post-fire erosion data" into the search box. But the
dataset abstract they're looking for might say "burn area soil stability",
"BAER assessment", or "sediment transport monitoring following wildfire
disturbance". All of the same thing — completely different vocabulary.

This is the jargon gap problem, and it's especially pronounced in geospatial
and forestry data. Query expansion is one of the most practical ways to address
it.

## What Is Query Expansion?

The idea is simple: before sending a user's query to the search engine, use an
LLM to enrich it with related terms, synonyms, and domain-specific language.
The expanded query casts a wider net and is much more likely to surface
relevant results.

Here's a concrete example of what that looks like in practice:

```
User types:   "post-wildfire erosion data"

Expanded:     "post-fire sediment erosion burn area soil stability
               fire effects hydrology watershed BAER assessment
               erosion monitoring wildfire disturbance recovery"
```

The expanded version speaks the language of the catalog. The user didn't have
to know any of that terminology — the LLM bridges the gap for them.

## How It's Implemented

Query expansion in Catalog is handled by `OllamaBot.expand_query()` in
`bots.py`. It's a focused, single-purpose LLM call:

```python
def expand_query(self, query: str) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant that expands user queries "
                "to include relevant keywords and synonyms for better "
                "dataset discovery. Do not provide instructions on how "
                "to use, just the expanded query."
            ),
        },
        {
            "role": "user",
            "content": f"Expand the following query to include relevant "
                       f"keywords and synonyms:\n\n{query}",
        },
    ]

    resp = self.client.chat(self.OLLAMA_MODEL, messages=messages, stream=False)
    return resp["message"]["content"]
```

The system prompt is deliberately strict — just return the expanded query,
no explanation, no preamble. That output goes straight into the search pipeline
as the new query string.

## Using It from the CLI

Query expansion is available as an optional flag on the `hybrid-search`
command:

```bash
catalog hybrid-search --qstn "post-wildfire erosion data" --expq --bot ollama
```

The `--expq` flag triggers expansion before the search runs. You'll see the
expanded query printed so you know exactly what was sent to the search engine:

```
Expanded query: post-fire sediment erosion burn area soil stability
                fire effects hydrology watershed BAER assessment...
```

From there, the expanded query flows through the full hybrid search pipeline —
BM25 keyword matching combined with ChromaDB vector search, fused with
Reciprocal Rank Fusion — giving it the best possible chance of finding
relevant datasets.

## Why This Approach Works Well

A few things make query expansion a particularly good fit here:

**It's low effort, high impact.** There are no schema changes, no new
infrastructure, and no retraining. It's a single LLM call added before an
existing search step.

**Small models handle it well.** You don't need a large model for this task.
Something lightweight like `llama3.2:1b` does a fine job of synonym expansion,
which keeps latency low.

**It's optional.** Users who know exactly what they're looking for can skip
expansion entirely. It's there when it helps, invisible when it doesn't.

## What's Coming Next

Query expansion is a great first step, but there's more to explore:

- **HyDE (Hypothetical Document Embedding)** — rather than expanding the
  query with keywords, generate a hypothetical dataset abstract that *looks
  like* a real match, then embed that for retrieval. This can be even more
  effective because it closes the gap at the embedding level rather than the
  keyword level.
- **Agentic tool use** — letting the LLM drive the search loop entirely,
  deciding when to search again and with what terms if the first pass comes
  up short. (More on that in a separate post!)

If any of this resonates with problems you've run into in your own search or
discovery work, I'd love to hear about it. The full code is on GitHub at
[github.com/forestbytes/catalog](https://github.com/forestbytes/catalog).

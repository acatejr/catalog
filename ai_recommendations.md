# AI Recommendations: Enhancing Semantic Search with AI Interaction

## What's Already Built

- `SemanticSearch` (`src/catalog/search.py`) — vector similarity search against PostgreSQL/pgvector
- `EmbeddingsService` (`src/catalog/embeddings.py`) — fastembed for local embeddings (BAAI/bge-small-en-v1.5)
- A rich prompt library with 5 personas and functional prompts:
  - `src/catalog/prompts/__init__.py` — `build_system_prompt()` helper that combines a functional prompt with a persona modifier
  - `src/catalog/prompts/personas.py` — `Persona` enum (ANALYST, FORESTER, MANAGER, PUBLIC, POLITICIAN) and `PERSONA_MODIFIERS` dict with audience-specific tone/style instructions
  - `src/catalog/prompts/discovery.py` — `DISCOVERY_BASE` and `DISCOVERY_PROMPTS[Persona]` — system prompts for helping users find datasets
  - `src/catalog/prompts/lineage.py` — prompts for explaining data origin/provenance
  - `src/catalog/prompts/relationships.py` — prompts for discovering connections between datasets

## What's Missing

The prompts module is fully built but **never wired up**. The `semantic-search` command returns raw database rows — it never sends those results to Claude for synthesis.

None of the prompts files are currently imported or used anywhere in `main.py` or `search.py`.

## The Gap

Add an `ai-search` command that:

1. Runs semantic search to get candidate documents from PostgreSQL
2. Formats those results as a context block
3. Calls Claude with the persona-appropriate system prompt (from the existing prompts library)
4. Streams back a synthesized, audience-tailored response

## Implementation Plan

### 1. Add `anthropic` to `pyproject.toml`

```toml
"anthropic>=0.40",
```

### 2. Create `src/catalog/ai_search.py`

A new `AISearchService` class that:
- Wraps `SemanticSearch` to retrieve candidate documents
- Formats results as a structured context block for the LLM
- Calls Claude via the Anthropic SDK with the correct system prompt
- Supports streaming output

### 3. Add `ai-search` CLI command to `src/catalog/main.py`

```
catalog ai-search "show me fire and fuels treatment data" --persona analyst --limit 10
```

Options:
- `--limit` — number of semantic search results to pass as context (default 10)
- `--persona` — one of: analyst, forester, manager, public, politician (default: base prompt)

### 4. Wire up existing prompts

Use `build_system_prompt(DISCOVERY_PROMPTS[persona], persona)` from `catalog.prompts` to select the right system prompt based on the `--persona` flag.

---

## Query Pre-Processing (Before Semantic Search)

Several transformations can be applied to the user's query before it is embedded and sent to the vector database, improving both search recall and response quality.

### 1. Query Expansion
Use Claude to rewrite or enrich the query with domain-specific synonyms and USFS terminology before embedding it. A user typing "wildfire prevention" may get much better results if the query is expanded to also include "hazardous fuels treatment", "prescribed burn", "fuel reduction", "fire risk mitigation" — terms that actually appear in the catalog metadata.

### 2. HyDE (Hypothetical Document Embeddings)
Instead of embedding the raw user question, ask Claude to generate a short hypothetical dataset description that would answer the query. Then embed *that* instead. Since the hypothetical description looks like a real document, it tends to land much closer in vector space to actual catalog records than a terse user question does.

### 3. Intent Detection
Classify whether the question is a **discovery** question ("find me data on X"), a **lineage** question ("where did this data come from"), or a **relationships** question ("what datasets connect to X"). This routes to the correct system prompt rather than always defaulting to the discovery prompt.

### 4. Persona Inference
If `--persona` is not specified, infer it from the way the question is phrased. "What's the coordinate reference system for the timber harvest data?" reads like an analyst. "Is there anything about trails near my town?" reads like the public. This avoids requiring the user to know the `--persona` flag exists.

### 5. Query Clarification
For vague or ambiguous queries, ask a clarifying question before searching. "Are you looking for administrative boundary data, or land management activity data?" — one round-trip that avoids a poor search result.

### Priority

**Query expansion** and **HyDE** have the biggest direct impact on search result quality with minimal added latency. Intent detection and persona inference improve response quality downstream. Clarification is highest-effort but most valuable for very ambiguous inputs.

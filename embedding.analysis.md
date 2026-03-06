# Choosing the Optimal Embedding Model

The right embedding model depends on your data characteristics and constraints. Here's how to think about it for this geospatial metadata use case.

## Key Factors

### 1. Domain Match

The documents are **geospatial metadata** — technical titles, scientific abstracts, and federal agency terminology. Models trained on diverse, technical corpora will outperform general-purpose ones.

- General models (e.g., `all-MiniLM-L6-v2`, ChromaDB's default) handle everyday language well but may struggle with terms like "edaphic" or "FGDC-compliant"
- Models trained on scientific/technical text will better capture similarity between "wildfire burn severity" and "post-fire vegetation assessment"

### 2. Document Length

The embedding input concatenates title + abstract + purpose + keywords + lineage — that can be **several hundred tokens**. Models have maximum input lengths:

| Model | Max Tokens | Notes |
|-------|-----------|-------|
| `all-MiniLM-L6-v2` (ChromaDB default) | 256 | Truncates longer documents |
| OpenAI `text-embedding-3-small` | 8,191 | Handles full documents easily |
| OpenAI `text-embedding-3-large` | 8,191 | Higher dimension, more accurate |
| `nomic-embed-text` (Ollama) | 8,192 | Free, local, good quality |
| `mxbai-embed-large` (Ollama) | 512 | Better than MiniLM but still truncates |

**This is likely the biggest accuracy issue right now.** If ChromaDB's default model is truncating documents at 256 tokens, it's ignoring keywords and lineage entirely.

### 3. Local vs. API

Since Ollama is already running for the chat component:

- **Local (Ollama)**: Free, private, no API key. Models like `nomic-embed-text` or `snowflake-arctic-embed` run well on modest hardware
- **API (OpenAI)**: Higher quality, costs money per request, requires internet. `text-embedding-3-small` is the best value

### 4. Dimensionality

Higher dimensions capture more nuance but use more storage and slightly slower search:

| Model | Dimensions |
|-------|-----------|
| `all-MiniLM-L6-v2` | 384 |
| `nomic-embed-text` | 768 |
| `text-embedding-3-small` | 1,536 |
| `text-embedding-3-large` | 3,072 |

For a catalog of hundreds of documents, dimensionality doesn't matter for speed. Higher is just better.

## How to Actually Evaluate

The only reliable way to pick is to **test with your own queries**. A simple approach:

1. Pick 10-15 realistic questions you'd ask the catalog (e.g., "fire data", "soil surveys in Pacific Northwest", "watershed boundaries")
2. For each question, manually identify which 3-5 documents in the catalog are the "right" answers
3. Run each embedding model, query with the questions, and compare the top-5 results against the ground truth
4. Score each model by how many correct documents appear in the top-5

This is called a **retrieval evaluation** and it doesn't need to be fancy — a spreadsheet works.

## Practical Recommendation

Given the current setup (already using Ollama, geospatial metadata, moderate document lengths):

1. **Quick win now**: Switch to `nomic-embed-text` via Ollama. It's free, local, handles 8k tokens (no truncation), and is significantly better than ChromaDB's default. This can be done without changing vector stores.
2. **If you need the best accuracy**: OpenAI `text-embedding-3-small` — best quality-per-dollar, handles long documents
3. **Don't bother with**: `text-embedding-3-large` unless evaluation shows `3-small` isn't good enough — the cost and storage difference rarely justify it at this scale

The single biggest accuracy improvement is likely switching to a model that doesn't truncate the documents.

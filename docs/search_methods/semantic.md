# Semantic Search

Semantic search finds datasets by meaning rather than exact keywords. A query
like "areas that burned recently" will match records that say "post-fire
disturbance zones" — no shared words required.

It works by converting both the query and each dataset record into numerical
vectors (embeddings). Similar concepts end up close together in that vector
space. At search time, the engine returns the records whose vectors are nearest
to the query vector.

Catalog indexes dataset titles, abstracts, descriptions, keywords, and lineage
into [ChromaDB](https://www.trychroma.com/) and queries it with the
`query-fs-chromadb` command:

```bash
uv run catalog query-fs-chromadb -q "wildfire risk data"
uv run catalog query-fs-chromadb -q "watershed boundaries" -n 10
```

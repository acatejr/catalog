# Catalog

Catalog is a Python CLI that automates discovery and understanding of Government Agency geospatial and tabular data. It harvests XML metadata and MapServer service definitions from three anonymized portals—Research Archive (RA), Geospatial Discovery (GD), and Agency Geodata Portal (AGP)—builds embeddings, and lets you explore datasets with a semantic, RAG-powered search so you can answer questions like “what data exists and how do I use it?” without manual spelunking.

## Why it matters

- Hunting across portals, downloading XML one-by-one, and reconciling service URLs slows research and product teams.
- Explaining lineage and “fit for purpose” to stakeholders is hard without a unified view.
- Traditional keyword search misses nuance; semantic search with LLMs surfaces relevant datasets faster.

## What Catalog does

- Automated harvesting from RA, GD, and AGP (XML + MapServer JSON).
- Embeds metadata with a vector database (table) and uses LLMs in a Retrieval-Augmented Generation (RAG) flow for semantic Q&A.
- Python [Click](https://click.palletsprojects.com/en/stable/)-based CLI (`timbercat`) to harvest, inspect, and query datasets.
- Outputs organized metadata and service URLs you can plug into dashboards or analyses.

## The process (at a glance)

```mermaid
flowchart TB
  Sources[RA / GD / AGP] --> Harvester[timbercat harvest]
  Harvester --> Normalize["Normalize metadata (XML + JSON)"]
  Normalize --> Embed[VectorDB embeddings]
  Embed --> RAG[LLM + RAG pipeline]
  RAG --> Answers[Semantic search & dataset guidance]
```

1. Identify metadata sources:  
   - Research Archive (RA): research-grade datasets from the agency's research directorate and partners.  
   - Geospatial Discovery (GD): current operational GIS layers and services.  
   - Agency Geodata Portal (AGP): authoritative basemaps, boundaries, operational layers, and raster products.

2. Harvest metadata: `timbercat harvest` pulls XML and MapServer JSON, normalizes fields, and stores them for indexing.

3. Build the vector database: embeddings go into vector storage; metadata stays linked for provenance.

4. RAG-based search: the CLI uses the embeddings plus an LLM to answer dataset and lineage questions with grounded citations.

## Where to go next

- Architecture and design decisions: see `docs/architecture.md`.
- Data sources deep dive: see `docs/data-sources.md`.
- CLI usage and examples: see `docs/cli.md`.
- Vector DB details and comparisons: see `docs/vector-db.md`.

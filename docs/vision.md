# Vision: A Pragmatic Search Engine for USFS Data

## The Core Idea

Catalog is not an enterprise software project. It is a focused, practical tool built on a simple premise: **the data and metadata you need already exist—what's missing is a unified way to find and understand them.**

The Forest Service maintains authoritative geospatial data across several portals—FSGeodata Clearinghouse, the Geospatial Data Discovery hub, and the Research Data Archive. Each portal serves a purpose, but none of them talk to each other. Users who need to find the right dataset must know which portal to look in, understand each portal's search interface, and reconcile what they find across incompatible metadata schemas.

Catalog addresses this by treating those existing portals as the source of truth and building a lightweight discovery layer on top of them.

## What This Is (and Isn't)

| This tool is... | This tool is not... |
| --- | --- |
| A search engine over existing USFS metadata | A replacement for existing USFS data portals |
| A thin integration layer | An enterprise data management system |
| Locally runnable by individuals or small teams | A centrally hosted service |
| Built on open, existing standards (FGDC, DCAT-US) | A new metadata standard |
| Extensible as AI capabilities evolve | A finished product requiring sustained IT investment |

## The "Don't Rebuild It" Philosophy

Large federal IT projects frequently attempt to consolidate data by building new systems—new databases, new APIs, new user interfaces. These projects are expensive, slow, and often fail to keep pace with the underlying data and technology trends.

Catalog takes the opposite approach:

1. **Harvest, don't replace.** Metadata is downloaded directly from live sources. There is no separate data store to maintain or keep synchronized beyond running the harvest commands.
2. **Harmonize at the edge.** Schema differences between FSGeodata XML, GDD DCAT-US JSON, and RDA JSON are resolved at ingest time into a minimal common model. The original source data is preserved.
3. **Use existing AI infrastructure.** The tool integrates with Ollama, which can run entirely on-premises. No cloud accounts, no data leaving the network.

## Catalog as an Internal USFS Search Engine

From a user's perspective, Catalog behaves like a search engine scoped to USFS data holdings. It is working towards answering questions that today require navigating multiple portals manually:

- *"What elevation datasets are available for the Pacific Northwest?"*
- *"Is there a road centerline layer that covers the Tongass National Forest?"*
- *"What data exists about fuels treatment history and how do I access it as a service?"*

These queries go beyond simple keyword matching. Catalog uses vector embeddings and a Retrieval-Augmented Generation (RAG) pipeline so that semantically related datasets surface even when the exact words don't match. An LLM then synthesizes a grounded response with citations to the actual metadata records.

This positions Catalog as an internal knowledge tool—something a GIS analyst, researcher, or data steward can run locally to understand what data exists, where it lives, and how to use it.

## The AI Dimension

Catalog's architecture is designed to grow with AI capabilities rather than bet on a specific technology:

- **Embeddings are pluggable.** ChromaDB supports swapping embedding models. As domain-specific geospatial embedding models emerge, they can be substituted without changing the pipeline.
- **LLM integration is local-first.** Using Ollama keeps the tool viable in restricted-network environments and avoids sending sensitive internal data to external APIs.
- **The RAG pattern scales.** As the metadata corpus grows—additional portals, richer metadata fields, tabular data inventories—the same retrieval and generation architecture handles it.

Longer-term, this foundation supports more advanced use cases: automated data lineage summaries, fit-for-purpose recommendations, discovery across agency boundaries (USGS, NOAA, EPA), and integration into analyst workflows as a conversational assistant.

## Current Implementation: Proof of Concept

The current implementation is command-line driven. Every capability—harvesting metadata, building the vector database, querying it, and chatting with the LLM—is exposed as a CLI command that a user runs locally on their machine. This is intentional for a proof of concept: it keeps the system simple, removes infrastructure dependencies, and lets the core ideas be validated quickly without committing to a deployment model.

The CLI design does not constrain the architecture. The vector database querying and LLM integration are already isolated in discrete modules (`core.py` and `bots.py`). Moving those capabilities behind a REST API or web service would be a straightforward next step—the logic stays the same and the CLI becomes one of several possible clients rather than the only one.

A server-based implementation would unlock use cases the CLI cannot support:

- A web interface where analysts query the catalog without installing anything
- Shared, centrally maintained vector index updated on a schedule
- Integration with existing USFS applications and portals via API
- Multi-user access with authentication and usage tracking

The proof-of-concept phase exists to validate that the underlying approach—harvesting existing metadata, embedding it, and querying it with an LLM—produces useful results before investing in that infrastructure. If it does, the path to a hosted service is clear.

## Why This Approach Makes Sense for USFS

- **Low barrier to adoption.** The tool runs on a laptop with a single `uv run` command. There is no infrastructure to provision.
- **No lock-in.** The output is standard JSON and a local ChromaDB directory. The tool does not require any proprietary platform.
- **Respects existing investments.** The portals that data stewards already maintain—FSGeodata, GDD, RDA—remain the authoritative sources. Catalog amplifies them rather than competing with them.
- **Demonstrates AI value concretely.** Rather than abstract AI strategy, Catalog shows a specific, working example of how LLMs improve geospatial data discovery for Forest Service users today.

## Origins and Policy Context

This project was started at a time when USDA/USFS policy restricted employee use of AI tools. The design reflects that constraint deliberately: all metadata sources are public federal open data, AI inference runs locally or on [CyVerse](https://cyverse.org) (an NSF-funded academic compute platform), and no data is sent to commercial AI APIs. That approach remains sound independent of current policy—it keeps sensitive data handling simple and the tool auditable.

USDA/USFS AI policy has since evolved.

For full details on data sources, compute resources, and project status, see the [disclaimer](disclaimer.md).

# Methods

### Data Sources and Collection

Automated downloaders fetch metadata from three USFS geospatial data repositories, each using distinct metadata standards and access mechanisms. All three are implemented as methods on the `USFS` class in `usfs.py`. Files that already exist on disk are skipped, so repeat runs are safe and incremental.

**FSGeodata Clearinghouse.** EDW datasets are accessed via the USFS Geodata portal (https://data.fs.usda.gov/geodata/edw/datasets.php). A BeautifulSoup scraper parses the datasets index page, extracting links to XML metadata files conforming to the FGDC Content Standard for Digital Geospatial Metadata. Each XML file is downloaded to `data/usfs/fsgeodata/`.

**Geospatial Data Discovery (GDD).** The USFS ArcGIS Hub portal exposes a DCAT-US 1.1 compliant feed at a single JSON endpoint (https://data-usfs.hub.arcgis.com/api/feed/dcat-us/1.1.json). This feed provides dataset titles, descriptions, keywords, and thematic classifications in a standardized federal open data format. The feed is saved as a single file to `data/usfs/gdd/gdd_metadata.json`.

**Research Data Archive (RDA).** The USFS Research Data Archive provides a JSON web service (https://www.fs.usda.gov/rds/archive/webservice/datagov) returning dataset metadata including titles, descriptions, and keyword arrays. This source emphasizes research datasets with scientific provenance. The feed is saved to `data/usfs/rda/rda_metadata.json`.

### Schema Harmonization

To enable cross-repository search, all source records are normalised into a unified `USFSDocument` schema (Pydantic):

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | SHA-256 hash of normalized title (lowercase, trimmed) |
| `title` | string | Dataset title |
| `abstract` | string | Summary description (FSGeodata only) |
| `purpose` | string | Intended use statement (FSGeodata only) |
| `description` | string | Full narrative description (GDD and RDA) |
| `keywords` | array | Subject keywords (deduplicated, lowercased) |
| `src` | string | Source identifier: `fsgeodata`, `gdd`, or `rda` |
| `lineage` | array | Processing steps with dates (FSGeodata only) |
| `embeddings` | array | Dense vector embedding (populated at load time) |

The `id` field serves as a deduplication key across repositories. Text fields are normalised by the `clean_str()` utility, which strips HTML tags via BeautifulSoup and collapses whitespace.

**Schema Mapping.** Each source requires distinct parsing logic:

- *FSGeodata*: XML parsing extracts `<title>`, `<descript><abstract>`, `<descript><purpose>`, `<themekey>`, and `<dataqual><procstep>` elements.
- *GDD*: JSON mapping from DCAT fields (`title`, `description`, `keyword`, `theme`).
- *RDA*: Direct JSON field extraction (`title`, `description`, `keyword`).

Keywords from all sources are lowercased, stripped of punctuation, and deduplicated before storage.

### Vector Embedding and Storage

Harmonized documents are loaded into PostgreSQL with the pgvector extension via the `load-data --target pg` command.

**Embedding model.** Each document is embedded using `fastembed` with the `BAAI/bge-small-en-v1.5` model (384 dimensions). Documents are serialised to plain text before encoding using `USFSDocument.to_embedding_text()`:

```
Title: {title}
Abstract: {abstract}
Description: {description}
Purpose: {purpose}
Keywords: {keywords}
Lineage: {lineage}
```

Documents are processed in batches of 32 by `EmbeddingsService.embed_batch()`.

**Storage.** Embeddings and document fields are upserted into the `documents` table via SQLAlchemy. The `embedding` column is a 384-dimensional `pgvector` `vector` type. On initialisation (`init_db()`), an IVFFlat cosine index is created on the `embedding` column (`lists=100`) for fast approximate nearest-neighbour search.

### Retrieval-Augmented Generation

The system supports two query modes exposed as separate CLI commands.

**Semantic Search (`semantic-search`).** Users submit natural language queries, which are embedded with the same `BAAI/bge-small-en-v1.5` model and compared against stored vectors using the pgvector cosine operator (`<=>`). Results are ranked by `1 - cosine_distance`, returned as a `similarity` score. The top-*k* results are returned (configurable via `--limit`, default *k*=10), with higher scores indicating greater semantic relevance. Output can be rendered as plain text or markdown via `--format`.

**LLM-Augmented Discovery (`bot-search`).** For complex discovery questions, a RAG pipeline is used:

1. The user query is used to retrieve top-*k* documents via `SemanticSearch`
2. Retrieved documents (title, abstract, description, similarity score) are formatted as context
3. A prompt template is prepended to the context and query
4. The combined message is sent to `VerdeBot.chat()`, which calls the configured LLM via a LiteLLM proxy
5. The LLM returns a synthesised natural language response grounded in catalog data

**Prompt Templates.** The `--prompt` option selects one of four templates:

| Template | Behaviour |
|----------|-----------|
| `simple` | Geospatial data assistant; answers catalog queries concisely; sorts by similarity score; refuses to speculate beyond catalog contents |
| `discovery` | "Data librarian" persona; surfaces relevant datasets with source, relevance explanation, and gap analysis; supports persona variants (analyst, forester, manager, public, official) |
| `relationships` | Cross-dataset relationship analysis |
| `lineage` | Data lineage and provenance focus |

**LLM configuration.** `VerdeBot` uses `langchain-litellm` (`ChatLiteLLM`) with the `litellm_proxy/{VERDE_MODEL}` model string. The target LLM and endpoint are configured via `VERDE_API_KEY`, `VERDE_URL`, and `VERDE_MODEL` environment variables, making the pipeline model-agnostic.

### Implementation

The system is implemented in Python as a CLI tool using the Click framework. Key dependencies include:

- **fastembed** for local embedding generation (`BAAI/bge-small-en-v1.5`)
- **pgvector + SQLAlchemy** for vector storage and similarity search in PostgreSQL
- **langchain-litellm** for LLM integration via a LiteLLM proxy
- **BeautifulSoup / lxml** for XML and HTML parsing
- **Pydantic** for schema validation
- **Requests** for HTTP operations
- **Rich** for console formatting

The modular architecture separates concerns: data loaders (`usfs.py`), schema (`schema.py`), database schema and init (`db.py`), embedding generation (`embeddings.py`), semantic search (`search.py`), LLM client (`bots.py`), prompt templates (`prompts/`), and shared utilities (`lib.py`).

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Data Collection                          │
├─────────────────┬─────────────────────┬─────────────────────────┤
│   FSGeodata     │        GDD          │          RDA            │
│   (XML/FGDC)    │    (DCAT-US 1.1)    │        (JSON)           │
└────────┬────────┴──────────┬──────────┴────────────┬────────────┘
         │                   │                       │
         ▼                   ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Schema Harmonization                         │
│                      (USFSDocument)                             │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│               Unified Catalog (usfs_catalog.json)               │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│            Vector Embedding & Indexing                          │
│         (fastembed + PostgreSQL / pgvector)                     │
└─────────────────────────┬───────────────────────────────────────┘
                          │
          ┌───────────────┴───────────────┐
          ▼                               ▼
┌─────────────────────┐     ┌─────────────────────────────────────┐
│   Semantic Search   │     │       LLM-Augmented Discovery       │
│  (semantic-search)  │     │           (bot-search)              │
└─────────────────────┘     └─────────────────────────────────────┘
```

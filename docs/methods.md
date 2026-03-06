# Methods

### Data Sources and Collection

We developed automated harvesters for three USFS geospatial data repositories, each employing distinct metadata standards and access mechanisms.

**FSGeodata Clearinghouse.** The Enterprise Data Warehouse (EDW) datasets are accessed via the USFS Geodata portal (https://data.fs.usda.gov/geodata/edw/datasets.php). We implemented a web scraper using BeautifulSoup to parse the datasets index page, extracting links to XML metadata files conforming to FGDC Content Standard for Digital Geospatial Metadata. For each dataset, we retrieve both the metadata XML and, where available, associated ArcGIS MapServer service descriptors in JSON format. A rate limiter (250ms delay) ensures compliance with server policies.

**Geospatial Data Discovery (GDD).** The USFS ArcGIS Hub portal exposes a DCAT-US 1.1 compliant feed at a single JSON endpoint (https://data-usfs.hub.arcgis.com/api/feed/dcat-us/1.1.json). This feed provides dataset titles, descriptions, keywords, and thematic classifications in a standardized federal open data format.

**Research Data Archive (RDA).** The USFS Research Data Archive provides a JSON web service (https://www.fs.usda.gov/rds/archive/webservice/datagov) returning dataset metadata including titles, descriptions, and keyword arrays. This source emphasizes research datasets with scientific provenance.

### Schema Harmonization

To enable cross-repository search, we defined a unified document schema (`USFSDocument`) with the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | SHA-256 hash of normalized title (lowercase, trimmed) |
| `title` | string | Dataset title |
| `abstract` | string | Summary description (mapped from FGDC abstract or DCAT description) |
| `purpose` | string | Intended use statement (FSGeodata only) |
| `description` | string | General description text |
| `keywords` | array | Subject keywords (from themekey, keyword, or theme fields) |
| `src` | string | Source identifier: "fsgeodata", "gdd", or "rda" |
| `lineage` | array | Processing history with dates (FSGeodata only) |

The `id` field serves as a deduplication key, ensuring datasets appearing in multiple repositories are not double-counted. Text fields undergo normalization including whitespace collapsing and Unicode standardization via a `clean_str()` utility function.

**Schema Mapping.** Each source requires distinct parsing logic:

- *FSGeodata*: XML parsing extracts `<title>`, `<descript><abstract>`, `<descript><purpose>`, `<themekey>`, and `<procstep>` elements
- *GDD*: JSON mapping from DCAT fields (`title`, `description`, `keyword`, `theme`)
- *RDA*: Direct JSON field extraction (`title`, `description`, `keyword`)

### Vector Embedding and Storage

Harmonized documents are loaded into ChromaDB, an open-source vector database. For each document, we construct an embedding input string concatenating:

```
Title: {title}
Abstract: {abstract}
Purpose: {purpose}
Source: {src}
Keywords: {keywords}
Lineage: {lineage}
```

ChromaDB's default embedding model generates vector representations stored alongside document metadata. Documents are processed in batches of 100 to optimize memory usage. The collection is rebuilt from scratch on each indexing operation to ensure consistency.

### Retrieval-Augmented Generation

The system supports two query modes:

**Vector Search.** Users submit natural language queries, which are embedded and compared against the document collection using cosine distance. The top-*k* results (configurable, default *k*=5) are returned with relevance distances, where lower distances indicate higher semantic similarity.

**LLM-Augmented Discovery.** For complex discovery questions, we implement a RAG pipeline:

1. The user query is used to retrieve the top-*k* relevant documents via vector search
2. Retrieved documents are formatted as context
3. The query and context are submitted to an LLM (configurable via Ollama API)
4. The LLM generates a natural language response synthesizing the search results

The LLM system prompt frames the model as a "data librarian" with instructions to:

- List relevant datasets with explanations of relevance
- Prioritize results by distance score (lower = more relevant)
- Provide direct yes/no answers for existence queries
- Avoid speculation beyond catalog contents

### Implementation

The system is implemented in Python as a CLI tool using the Click framework. Key dependencies include:

- **ChromaDB** for vector storage and similarity search
- **Ollama** client for LLM integration
- **BeautifulSoup** for XML/HTML parsing
- **Pydantic** for schema validation
- **Requests** for HTTP operations

The modular architecture separates concerns: data loaders (`usfs.py`), schema definitions (`schema.py`), vector operations (`core.py`), and LLM integration (`bots.py`).

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
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Unified Catalog (JSON)                       │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Vector Embedding & Indexing                     │
│                        (ChromaDB)                               │
└─────────────────────────────┬───────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────────────┐
│     Vector Search       │     │      LLM-Augmented Discovery    │
│   (Semantic Queries)    │     │     (Natural Language Q&A)      │
└─────────────────────────┘     └─────────────────────────────────┘
```

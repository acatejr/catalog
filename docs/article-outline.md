---
draft: true
---
# Journal Article Outline

## Title (suggested)
*"A Retrieval-Augmented Generation Approach for Discovering Heterogeneous Federal Geospatial Metadata"*

---

## 1. Introduction

- Problem: Federal geospatial data fragmented across repositories with incompatible schemas
- Motivation: Researchers struggle to discover relevant USFS datasets using keyword search
- Contribution: A RAG-based system that harmonizes metadata and enables semantic discovery
- Research questions:
  1. Can schema harmonization improve cross-repository search?
  2. Does vector-based semantic search outperform keyword matching for geospatial metadata?

---

## 2. Background & Related Work

- Geospatial metadata standards (ISO 19115, DCAT-US, FGDC)
- Federal data discovery challenges (data.gov limitations)
- RAG architectures for information retrieval
- Vector databases for document search

---

## 3. Data Sources

- FSGeodata Clearinghouse (EDW) - XML/FGDC format
- Geospatial Data Discovery (GDD) - DCAT-US 1.1 JSON via ArcGIS Hub
- Research Data Archive (RDA) - Custom JSON API
- Characterization of each source's schema, coverage, and limitations

---

## 4. Methods

- Schema harmonization approach
- Vector embedding and indexing pipeline
- RAG architecture with LLM integration
- System implementation

See `methods-section.md` for the detailed draft.

---

## 5. Results

- Catalog statistics (document counts, field coverage)
- Query evaluation (semantic vs keyword search examples)
- User study or expert evaluation (if applicable)

### Suggested Analyses

- Table: Document counts by source
- Table: Field completeness rates across sources
- Figure: Query response comparison (keyword vs semantic)
- Example queries demonstrating semantic understanding

---

## 6. Discussion

- Implications for federal data discovery
- Limitations:
  - Embedding model choices and their impact on retrieval quality
  - Information loss during schema harmonization
  - Dependency on source API stability
- Generalizability to other federal repositories (EPA, NOAA, USGS)

---

## 7. Conclusion & Future Work

- Summary of contributions
- Extensions:
  - Additional data sources
  - Fine-tuned embedding models for geospatial terminology
  - Quantitative evaluation metrics (precision, recall, NDCG)
  - User interface development

---

## Target Journals (suggestions)

- *Computers & Geosciences*
- *International Journal of Geographical Information Science*
- *Environmental Modelling & Software*
- *Journal of the Association for Information Science and Technology (JASIST)*
- *Earth Science Informatics*

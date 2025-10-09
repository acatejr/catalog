---
title: Catalog Documentation Home
description: Proof-of-concept metadata catalog system using vector database, RAG, and LLM for intelligent search of USFS datasets
tags:
  - catalog
  - metadata
  - rag
  - vector-database
  - llm
  - documentation
search:
  boost: 2.0
---

# Catalog Documentation

Welcome to the documentation for the **Catalog** project—a proof-of-concept system for intelligent search and discovery of USFS datasets using modern AI and database technologies.

## Overview

This project demonstrates how to build a data/metadata catalog that:  

- **Harvests and stores public data** in a vector database  
- **Augments LLM search** using [Retrieval-Augmented Generation (RAG)](https://en.wikipedia.org/wiki/Retrieval-augmented_generation)  
- Enables **natural language queries** over metadata  

## Key Features

- **Vector Database Integration:** Efficient similarity search for metadata and documents.
- **Retrieval-Augmented Generation (RAG):** Combines search results with LLMs for more accurate answers.
- **LLM-Powered Chatbot:** Ask questions in natural language and get intelligent responses.
- **USFS Dataset Focus:** Built using publicly available US Forest Service data.

## Quick Start

1. **Clone the repository:**

   ```sh
   git clone https://github.com/acatejr/catalog.git
   cd catalog
   ```

2. **Install dependencies:**

   ```sh
   pip install -r requirements.txt
   ```

3. **Run the API server:**

   ```sh
   uvicorn src.catalog.main:app --reload
   ```

4. **Start the chatbot UI:**

   ```sh
   streamlit run slclient/app.py
   ```

## Example Usage

- **Ask:** “What datasets are available for wildfire risk?”
- **Ask:** “What is the most frequent type in the `src` field of the document list?”

## Project Structure

```
catalog/
├── src/           # Backend source code (API, database, LLM integration)
├── slclient/      # Streamlit chatbot client
├── docs/          # Documentation (this site)
├── requirements.txt
└── mkdocs.yml     # MkDocs configuration
```

## Learn More

- [API Reference](api.md)
- [Setup Guide](setup.md)
- [Contributing](contributing.md)

---

For more details, explore the sidebar or use the search above.

<!-- ---
title: Catalog Documentation Home
description: Proof-of-concept metadata catalog system using vector database, RAG, and LLM for intelligent search of USFS datasets
tags:
  - catalog
  - metadata
  - rag
  - vector-database
  - llm
  - usfs
  - documentation
search:
  boost: 2.0
---

# Welcome to Catalog Documentation

A proof-of-concept project used to demonstrate the possibilities that may exist in building a data/metadata catalog based on publicly available data harvested and stored in vector database table and used to augment LLM search functionality through [Retrieval-Augmented-Generation (RAG)](https://en.wikipedia.org/wiki/Retrieval-augmented_generation)  -->

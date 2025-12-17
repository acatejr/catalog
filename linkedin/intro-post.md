# Introducing timbercat: Making Enterprise Data Searchable

A fun project I've been working on that tackles a challenge many in the data community face: discovering relevant datasets buried in vast data and metadata repositories. This is a proof-of-concept RAG (Retrieval-Augmented Generation) implementation that explores how vector databases can transform data discovery.

**The Problem:**
Many organizations maintain incredible data resources across multiple platforms -   clearinghouse systems, archive repositories, and a data discovery portals, and geospatial map services. But finding the right dataset often means manually searching through hundreds of XML metadata files or service definitions. Traditional keyword search just doesn't cut it when you're trying to understand what data actually exists.

**The Solution:**
I built Catalog (CLI command: `timbercat`) - a Python tool that:
- Harvests and consolidates metadata from multiple sources
- Stores metadata in ChromaDB, a vector database
- Enables semantic search - ask questions in natural language, get relevant datasets

Instead of searching for exact keywords, you can ask: "What datasets cover wildfire risk in California?" or "Show me recent land inventory data for the Pacific Northwest" and get meaningful results.

**Why This Matters:**
Data is only valuable when people can find and use it. By applying vector search and semantic understanding to enterprise datasets, we're making critical environmental data more accessible to researchers, land managers, and developers who need it.

**Tech Stack:**
- Python CLI built with Click
- ChromaDB for vector storage and semantic search
- Automated harvesting of XML metadata and MapServer service definitions
- OpenAI and LLMs

This project sits at the intersection of open data and modern AI-powered search. I'm looking forward to sharing more about the technical journey, challenges solved, and lessons learned.

The project is open source and available on [GitHub](https://github.com/acatejr/catalog).

What challenges have you faced working with enterprise data? Would love to hear your experiences.

#OpenData #Python #VectorDatabase #DataEngineering #RAG

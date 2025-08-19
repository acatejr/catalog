# RAG (Retrieval-Augmented Generation) Usage Guide

This guide explains how to use the RAG system for natural language queries against your catalog database.

## Overview

The RAG system allows you to ask natural language questions about your catalog data and get intelligent responses. It combines vector similarity search with large language models to provide contextual answers based on your document collection.

## Features

- **Natural Language Queries**: Ask questions in plain English
- **Vector Similarity Search**: Find semantically similar documents
- **Query Classification**: Automatically handles different types of queries
- **LLM Integration**: Get intelligent responses with context
- **Multiple Interfaces**: CLI, interactive mode, and programmatic API
- **Flexible Filtering**: Filter by data source, similarity threshold, etc.

## Quick Start

### Command Line Interface

```bash
# Basic query
catalog rag-query "Show me all forest fire related datasets"

# With options
catalog rag-query "Find erosion data" --top-k 10 --threshold 0.7

# Filter by data source
catalog rag-query "What datasets are available?" --source USGS

# JSON output
catalog rag-query "Climate change studies" --json

# Disable LLM (vector search only)
catalog rag-query "Water quality data" --no-llm
```

### Interactive Mode

```bash
# Start interactive mode
catalog rag-interactive

# Or use the full command
catalog rag-query --interactive
```

In interactive mode, you can:
- Ask multiple queries in sequence
- Use system commands like `help` and `info`
- Adjust settings with `set` commands
- View detailed document content

## Query Types

The system automatically classifies queries and handles them appropriately:

### 1. Vector Search Queries (Default)
These are general questions about your data that use semantic similarity.

**Examples:**
- "Show me all forest fire related datasets"
- "Find records about erosion"
- "What data do you have on climate change?"
- "Water quality studies in rivers"

### 2. Keyword Frequency Queries
Ask about the most common keywords in your database.

**Examples:**
- "What are the most frequent keywords?"
- "Show me the top keywords"
- "Most common keywords in the database"

### 3. Data Source Filter Queries
Queries that specify a particular data source.

**Examples:**
- "What datasets are from USGS?"
- "Show me EPA data"
- "Find records from NOAA"

### 4. Duplicate Title Queries
Find documents with duplicate titles.

**Examples:**
- "Show me duplicate titles"
- "Find documents with same titles"
- "Repeated title documents"

## Programmatic Usage

### Basic Python API

```python
from catalog.lib.rag import run_natural_language_query

# Simple query
result = run_natural_language_query("forest fire datasets")

# With options
result = run_natural_language_query(
    query="erosion data",
    top_k=10,
    data_source="USGS",
    use_llm=True,
    similarity_threshold=0.7
)

# Access results
print(f"Query: {result['query']}")
print(f"Found {len(result['documents'])} documents")
print(f"AI Response: {result['response']}")

# Iterate through documents
for doc in result['documents']:
    print(f"- {doc['title']} (similarity: {doc['similarity']:.3f})")
```

### Advanced Usage with RAG System

```python
from catalog.lib.rag import RAGSystem, RAGConfig

# Custom configuration
config = RAGConfig(
    embedding_model="all-MiniLM-L6-v2",
    similarity_threshold=0.6,
    max_results=15,
    llm_model="ollama/llama3.1",
    temperature=0.5
)

# Initialize RAG system
rag = RAGSystem(config)

# Query with custom parameters
result = rag.query(
    user_query="climate change impacts on forests",
    top_k=5,
    use_llm=True
)

# Get database info
doc_count = rag.get_document_count()
data_sources = rag.get_available_data_sources()
print(f"Database contains {doc_count} documents from {len(data_sources)} sources")
```

### Individual Components

```python
from catalog.lib.rag import (
    EmbeddingManager, 
    VectorSearchEngine, 
    DatabaseManager,
    QueryClassifier
)

# Generate embeddings
embedding_manager = EmbeddingManager()
query_embedding = embedding_manager.get_embedding("forest fires")

# Search similar documents
db_manager = DatabaseManager()
search_engine = VectorSearchEngine(db_manager)
documents = search_engine.search_similar_documents(
    query_embedding, 
    top_k=5, 
    threshold=0.5
)

# Classify queries
query_type, params = QueryClassifier.classify_query("most frequent keywords")
print(f"Query type: {query_type}")
```

## Configuration

### Environment Variables

The RAG system uses these environment variables:

```bash
# Database connection
export PG_DBNAME="your_database"
export POSTGRES_USER="your_username" 
export POSTGRES_PASSWORD="your_password"

# LLM service (optional)
export LITELLM_URL="http://localhost:4000"
export LITELLM_MASTER_KEY="your_api_key"
```

### RAG Configuration Options

```python
from catalog.lib.rag import RAGConfig

config = RAGConfig(
    embedding_model="all-MiniLM-L6-v2",      # Sentence transformer model
    similarity_threshold=0.5,                # Minimum similarity score
    max_results=10,                          # Maximum documents to return
    llm_model="ollama/llama3.1",            # LLM model to use
    llm_url="http://localhost:4000",        # LLM service URL
    temperature=0.7,                         # LLM temperature
    max_tokens=1000                          # Maximum LLM response tokens
)
```

## Response Format

All queries return a structured response:

```python
{
    "query": "forest fire datasets",
    "query_type": "vector_search",
    "documents": [
        {
            "id": 1,
            "doc_id": "doc_123",
            "title": "Forest Fire Risk Assessment",
            "description": "Analysis of forest fire risks...",
            "chunk_text": "Forest fires are a major concern...",
            "chunk_index": 0,
            "data_source": "USGS",
            "keywords": ["fire", "forest", "risk"],
            "authors": ["Dr. Smith"],
            "similarity": 0.85
        }
    ],
    "response": "Based on the documents, there are several forest fire datasets available...",
    "metadata": {
        "total_results": 5,
        "similarity_threshold": 0.5,
        "data_source": null
    }
}
```

## Best Practices

### Query Formulation

1. **Be Specific**: "Forest fire risk in California" vs "fires"
2. **Use Domain Terms**: Include relevant scientific or technical terms
3. **Ask Complete Questions**: "What datasets show water quality in rivers?" vs "water"

### Performance Optimization

1. **Adjust Similarity Threshold**: Higher values (0.7-0.9) for precise matches, lower (0.3-0.5) for broader results
2. **Limit Results**: Use appropriate `top_k` values to balance completeness and performance
3. **Filter by Source**: Use data source filters when you know the origin

### Error Handling

```python
try:
    result = run_natural_language_query("your query")
    if result["query_type"] == "error":
        print(f"Error: {result['response']}")
    else:
        # Process results
        pass
except Exception as e:
    print(f"Query failed: {e}")
```

## Examples by Use Case

### Research Discovery

```python
# Find datasets for a research topic
result = run_natural_language_query(
    "datasets about soil erosion in agricultural areas",
    top_k=10,
    similarity_threshold=0.6
)

# Get detailed information
for doc in result['documents']:
    print(f"Title: {doc['title']}")
    print(f"Source: {doc['data_source']}")
    print(f"Keywords: {', '.join(doc['keywords'])}")
    print(f"Relevance: {doc['similarity']:.2%}")
    print("---")
```

### Data Source Exploration

```python
# Explore what's available from a specific source
result = run_natural_language_query(
    "What environmental datasets are available?",
    data_source="EPA",
    top_k=20
)

print(f"Found {len(result['documents'])} EPA datasets")
print(f"AI Summary: {result['response']}")
```

### Keyword Analysis

```python
# Understand your data collection
result = run_natural_language_query("most frequent keywords")

if "keyword_frequencies" in result["metadata"]:
    keywords = result["metadata"]["keyword_frequencies"]
    print("Top 10 Keywords:")
    for i, kw in enumerate(keywords[:10], 1):
        print(f"{i}. {kw['keyword']} ({kw['frequency']} documents)")
```

## Troubleshooting

### Common Issues

1. **No Results Found**
   - Lower the similarity threshold
   - Try broader or different keywords
   - Check if data exists with `catalog count-docs`

2. **LLM Errors**
   - Verify LLM service is running
   - Check environment variables
   - Use `--no-llm` flag to disable LLM

3. **Database Connection Issues**
   - Verify database credentials
   - Check database is running
   - Ensure vector extension is installed

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.INFO)

# This will show detailed logs
result = run_natural_language_query("your query")
```

## Integration Examples

### Jupyter Notebook

```python
import pandas as pd
from catalog.lib.rag import run_natural_language_query

def search_catalog(query, max_results=10):
    """Search catalog and return results as DataFrame"""
    result = run_natural_language_query(query, top_k=max_results)
    
    if result['documents']:
        df = pd.DataFrame(result['documents'])
        return df[['title', 'data_source', 'similarity', 'keywords']]
    else:
        return pd.DataFrame()

# Usage
df = search_catalog("climate change datasets")
df.head()
```

### Web Application

```python
from fastapi import FastAPI
from catalog.lib.rag import run_natural_language_query

app = FastAPI()

@app.post("/search")
async def search_endpoint(query: str, top_k: int = 5):
    result = run_natural_language_query(query, top_k=top_k)
    return {
        "query": result["query"],
        "documents": result["documents"],
        "summary": result["response"]
    }
```

## Advanced Topics

### Custom Embedding Models

```python
from catalog.lib.rag import RAGSystem, RAGConfig

# Use a different embedding model
config = RAGConfig(embedding_model="sentence-transformers/all-mpnet-base-v2")
rag = RAGSystem(config)
```

### Batch Processing

```python
queries = [
    "forest fire datasets",
    "water quality studies", 
    "climate change impacts"
]

results = []
rag = RAGSystem()

for query in queries:
    result = rag.query(query, top_k=5)
    results.append({
        'query': query,
        'count': len(result['documents']),
        'top_result': result['documents'][0]['title'] if result['documents'] else None
    })
```

This guide should help you get started with the RAG system and make the most of your catalog data through natural language queries.

# RAG Implementation for Catalog System

This document provides a comprehensive overview of the RAG (Retrieval-Augmented Generation) implementation for natural language queries against the catalog database.

## 🎯 Overview

The RAG system enables users to ask natural language questions like:
- "Show me all the forest fire related data sets"
- "Find all records related to erosion"
- "What datasets are available from USGS?"
- "Most frequent keywords in the database"

## 🏗️ Architecture

The implementation consists of several key components:

### Core Components

1. **RAGSystem** (`src/catalog/lib/rag.py`)
   - Main orchestrator that coordinates all RAG operations
   - Handles query classification, vector search, and LLM integration

2. **QueryClassifier**
   - Automatically classifies user queries into different types:
     - Vector search (default)
     - Keyword frequency queries
     - Data source filter queries
     - Duplicate title queries

3. **EmbeddingManager**
   - Manages text embeddings using SentenceTransformers
   - Default model: `all-MiniLM-L6-v2`
   - Generates 384-dimensional vectors

4. **VectorSearchEngine**
   - Performs similarity search using PostgreSQL with pgvector
   - Uses cosine similarity for document ranking
   - Supports filtering by data source and similarity threshold

5. **LLMManager**
   - Integrates with language models via LiteLLM
   - Generates contextual responses based on retrieved documents
   - Supports various LLM providers (Ollama, OpenAI, etc.)

6. **DatabaseManager**
   - Handles PostgreSQL connections and queries
   - Manages document counting and data source enumeration

### Database Schema

The system uses the existing `documents` table with vector embeddings:

```sql
CREATE table documents (
    id SERIAL PRIMARY KEY,
    title TEXT,
    description TEXT,
    keywords TEXT[],
    authors TEXT[],
    chunk_text TEXT,
    chunk_index INTEGER,
    embedding vector(384),
    created_at TIMESTAMP DEFAULT NOW(),
    doc_id varchar(255),
    chunk_type varchar(255),
    data_source varchar(75)
);
```

## 🚀 Usage

### Command Line Interface

```bash
# Basic query
catalog rag-query "Show me all forest fire related datasets"

# With options
catalog rag-query "Find erosion data" --top-k 10 --threshold 0.7 --source USGS

# Interactive mode
catalog rag-interactive

# JSON output
catalog rag-query "Climate change studies" --json
```

### Python API

```python
from catalog.lib.rag import run_natural_language_query

# Simple query
result = run_natural_language_query("forest fire datasets")

# Advanced usage
from catalog.lib.rag import RAGSystem, RAGConfig

config = RAGConfig(
    similarity_threshold=0.6,
    max_results=15,
    temperature=0.5
)

rag = RAGSystem(config)
result = rag.query("climate change impacts on forests")
```

## 📁 File Structure

```
src/catalog/lib/rag.py           # Core RAG implementation
src/catalog/cli/rag_query.py     # Interactive CLI interface
src/catalog/cli/main.py          # CLI command integration
tests/test_rag.py                # Comprehensive test suite
docs/rag-usage-guide.md          # Detailed usage guide
```

## 🔧 Configuration

### Environment Variables

```bash
# Database connection
export PG_DBNAME="your_database"
export POSTGRES_USER="your_username"
export POSTGRES_PASSWORD="your_password"

# LLM service (optional)
export LITELLM_URL="http://localhost:4000"
export LITELLM_MASTER_KEY="your_api_key"
```

### RAG Configuration

```python
from catalog.lib.rag import RAGConfig

config = RAGConfig(
    embedding_model="all-MiniLM-L6-v2",
    similarity_threshold=0.5,
    max_results=10,
    llm_model="ollama/llama3.1",
    llm_url="http://localhost:4000",
    temperature=0.7,
    max_tokens=1000
)
```

## 🧪 Testing

The implementation includes comprehensive tests covering:

- Query classification
- Embedding generation
- Vector search functionality
- LLM integration
- Error handling
- End-to-end workflows

Run tests with:
```bash
python -m pytest tests/test_rag.py -v
```

## 📊 Response Format

All queries return structured responses:

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
            "data_source": "USGS",
            "keywords": ["fire", "forest", "risk"],
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

## 🎯 Query Types Supported

### 1. Vector Search (Default)
- Semantic similarity search using embeddings
- Examples: "forest fire datasets", "erosion studies"

### 2. Keyword Frequency
- Analysis of most common keywords
- Examples: "most frequent keywords", "top keywords"

### 3. Data Source Filtering
- Queries filtered by specific data sources
- Examples: "datasets from USGS", "EPA data"

### 4. Duplicate Detection
- Finding documents with duplicate titles
- Examples: "duplicate titles", "repeated documents"

## 🔍 Key Features

- **Intelligent Query Classification**: Automatically determines the best approach for each query
- **Vector Similarity Search**: Uses state-of-the-art embeddings for semantic search
- **LLM Integration**: Provides contextual, human-readable responses
- **Flexible Configuration**: Customizable similarity thresholds, result counts, and models
- **Multiple Interfaces**: CLI, interactive mode, and programmatic API
- **Comprehensive Error Handling**: Graceful handling of database and LLM errors
- **Extensive Testing**: Full test coverage with mocked dependencies

## 🚦 Getting Started

1. **Ensure Prerequisites**:
   - PostgreSQL with pgvector extension
   - Python environment with required dependencies
   - Optional: LLM service (Ollama, LiteLLM, etc.)

2. **Set Environment Variables**:
   ```bash
   export PG_DBNAME="catalog"
   export POSTGRES_USER="your_user"
   export POSTGRES_PASSWORD="your_password"
   ```

3. **Test the System**:
   ```bash
   # Check if data exists
   catalog count-docs
   
   # Try a simple query
   catalog rag-query "forest fire datasets" --no-llm
   ```

4. **Enable LLM (Optional)**:
   ```bash
   # Start Ollama or LiteLLM service
   export LITELLM_URL="http://localhost:4000"
   
   # Query with LLM responses
   catalog rag-query "forest fire datasets"
   ```

## 📚 Documentation

- **Detailed Usage Guide**: `docs/rag-usage-guide.md`
- **API Documentation**: Inline docstrings in `src/catalog/lib/rag.py`
- **Test Examples**: `tests/test_rag.py`

## 🔮 Future Enhancements

Potential improvements for the RAG system:

1. **Advanced Query Processing**:
   - Named Entity Recognition (NER) for better data source extraction
   - Query expansion and synonym handling
   - Multi-step reasoning for complex queries

2. **Enhanced Search Capabilities**:
   - Hybrid search combining vector and keyword search
   - Temporal filtering (date ranges)
   - Geographic filtering

3. **Improved LLM Integration**:
   - Support for more LLM providers
   - Custom prompt templates
   - Response caching and optimization

4. **User Experience**:
   - Web interface for RAG queries
   - Query history and favorites
   - Result export capabilities

5. **Performance Optimizations**:
   - Embedding caching
   - Batch processing for multiple queries
   - Asynchronous processing

This RAG implementation provides a solid foundation for natural language querying of catalog data, with room for future enhancements based on user needs and feedback.

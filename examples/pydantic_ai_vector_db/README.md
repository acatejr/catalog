# Pydantic-AI Vector Database Example

A comprehensive example demonstrating how to use **pydantic-ai** with vector databases for Retrieval-Augmented Generation (RAG) applications.

## 🚀 Overview

This example showcases:

- **Vector Database Integration**: Simple in-memory vector store using sentence-transformers
- **Pydantic-AI Agents**: AI agents that can query vector databases and generate structured responses
- **Structured Data Models**: Pydantic models for documents, queries, and responses
- **RAG Implementation**: Complete RAG pipeline from document ingestion to AI-powered responses
- **Multiple Approaches**: Both full AI agent and simplified implementations

## 📁 Project Structure

```
examples/pydantic_ai_vector_db/
├── README.md              # This file
├── requirements.txt       # Dependencies
├── models.py             # Pydantic data models
├── vector_store.py       # Vector database implementation
├── agent.py              # Pydantic-AI agents
├── sample_data.py        # Sample documents and queries
├── main.py               # Complete working example
└── test_example.py       # Comprehensive tests
```

## 🛠️ Installation

1. **Install Dependencies**:
   ```bash
   cd examples/pydantic_ai_vector_db
   pip install -r requirements.txt
   ```

2. **Optional: Set up API Keys** (for full AI agent functionality):
   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   # Or use other supported models like Anthropic, etc.
   ```

## 🏃‍♂️ Quick Start

### Run the Complete Example

```bash
python main.py
```

This will demonstrate:
- Vector store setup with sample documents
- Basic vector search functionality
- Simple RAG agent (no API keys required)
- Full pydantic-ai agent (requires API keys)
- Interactive demo

### Run Tests

```bash
python -m pytest test_example.py -v
```

## 📚 Core Components

### 1. Data Models (`models.py`)

Pydantic models that define the structure of your data:

```python
from models import Document, SearchQuery, ChatQuery, ChatResponse

# Create a document
doc = Document(
    id="doc_1",
    title="Machine Learning Basics",
    content="Machine learning is...",
    metadata={"category": "AI", "difficulty": "beginner"}
)

# Create a search query
query = SearchQuery(
    query="machine learning algorithms",
    top_k=5,
    threshold=0.1
)
```

### 2. Vector Store (`vector_store.py`)

Simple in-memory vector database with embedding functionality:

```python
from vector_store import SimpleVectorStore

# Initialize vector store
vector_store = SimpleVectorStore(model_name="all-MiniLM-L6-v2")

# Add documents
doc_id = vector_store.add_document(
    title="Python Programming",
    content="Python is a versatile programming language...",
    metadata={"category": "Programming"}
)

# Search for similar documents
from models import SearchQuery
query = SearchQuery(query="Python programming", top_k=3)
results = vector_store.search(query)
```

### 3. AI Agents (`agent.py`)

Two types of agents for different use cases:

#### Full Pydantic-AI Agent (Requires API Keys)

```python
from agent import RAGAgent
from models import ChatQuery

# Initialize agent
agent = RAGAgent(vector_store)

# Chat with the agent
query = ChatQuery(message="What is machine learning?")
response = await agent.chat(query)
print(response.response)
```

#### Simple RAG Agent (No API Keys Required)

```python
from agent import SimpleRAGAgent

# Initialize simple agent
simple_agent = SimpleRAGAgent(vector_store)

# Get response
response = simple_agent.chat("Tell me about Python data structures")
print(response.response)
```

## 🎯 Usage Examples

### Basic Vector Search

```python
from vector_store import SimpleVectorStore
from models import SearchQuery
from sample_data import get_sample_documents

# Setup
vector_store = SimpleVectorStore()
documents = get_sample_documents()
vector_store.add_documents(documents)

# Search
query = SearchQuery(query="machine learning", top_k=3)
response = vector_store.search(query)

for result in response.results:
    print(f"{result.document.title} (similarity: {result.similarity_score:.3f})")
```

### RAG with Pydantic-AI

```python
import asyncio
from agent import RAGAgent
from models import ChatQuery

async def chat_example():
    agent = RAGAgent(vector_store)
    
    query = ChatQuery(
        message="How do vector databases work?",
        context_limit=3,
        include_sources=True
    )
    
    response = await agent.chat(query)
    
    print(f"Response: {response.response}")
    print(f"Confidence: {response.confidence}")
    print(f"Sources: {len(response.sources)}")

# Run the example
asyncio.run(chat_example())
```

### Simple RAG (No API Keys)

```python
from agent import SimpleRAGAgent

# Setup
agent = SimpleRAGAgent(vector_store)

# Chat
response = agent.chat("What are the benefits of microservices?")
print(response.response)

# View sources
for source in response.sources:
    print(f"- {source.document.title}")
```

## 🔧 Configuration

### Vector Store Configuration

```python
# Different embedding models
vector_store = SimpleVectorStore(model_name="all-mpnet-base-v2")  # Better quality
vector_store = SimpleVectorStore(model_name="all-MiniLM-L6-v2")   # Faster, smaller

# Search parameters
query = SearchQuery(
    query="your query",
    top_k=10,        # Number of results
    threshold=0.3    # Minimum similarity score
)
```

### AI Agent Configuration

```python
# Use different models
agent = RAGAgent(vector_store, model="openai:gpt-4")
agent = RAGAgent(vector_store, model="anthropic:claude-3-sonnet")
agent = RAGAgent(vector_store, model="ollama:llama2")  # Local model
```

## 📊 Sample Data

The example includes 8 sample documents covering:

- **Machine Learning**: Introduction to ML concepts
- **Python Programming**: Data structures and programming
- **Vector Databases**: Embeddings and similarity search
- **Web Development**: REST API design principles
- **Database Design**: Normalization concepts
- **Architecture**: Microservices patterns
- **Development Tools**: Git version control
- **Cloud Computing**: Cloud fundamentals

## 🧪 Testing

Comprehensive test suite covering:

- **Model Validation**: Pydantic model creation and validation
- **Vector Store**: Document storage, search, and management
- **Agent Functionality**: Chat responses and source attribution
- **Integration Tests**: End-to-end workflow testing

Run specific test categories:

```bash
# Test models only
python -m pytest test_example.py::TestModels -v

# Test vector store
python -m pytest test_example.py::TestVectorStore -v

# Test agents
python -m pytest test_example.py::TestSimpleRAGAgent -v

# Integration tests
python -m pytest test_example.py::TestIntegration -v
```

## 🚀 Advanced Usage

### Custom Document Processing

```python
# Add documents with custom metadata
documents = [
    {
        "title": "Custom Document",
        "content": "Your content here...",
        "metadata": {
            "category": "Custom",
            "author": "Your Name",
            "tags": ["tag1", "tag2"],
            "created_date": "2024-01-01"
        }
    }
]

vector_store.add_documents(documents)
```

### Batch Processing

```python
# Process multiple queries
queries = [
    "What is machine learning?",
    "How do databases work?",
    "Explain cloud computing"
]

agent = SimpleRAGAgent(vector_store)
responses = [agent.chat(q) for q in queries]

for query, response in zip(queries, responses):
    print(f"Q: {query}")
    print(f"A: {response.response[:100]}...")
    print(f"Confidence: {response.confidence:.2f}\n")
```

### Custom Similarity Thresholds

```python
# High-precision search (fewer, more relevant results)
precise_query = SearchQuery(
    query="machine learning algorithms",
    top_k=3,
    threshold=0.7  # High threshold
)

# Broad search (more results, potentially less relevant)
broad_query = SearchQuery(
    query="machine learning algorithms", 
    top_k=10,
    threshold=0.1  # Low threshold
)
```

## 🔍 Troubleshooting

### Common Issues

1. **Missing API Keys**: The full pydantic-ai agent requires API keys. Use the `SimpleRAGAgent` for testing without API keys.

2. **Model Download**: First run will download the sentence-transformer model (~90MB for all-MiniLM-L6-v2).

3. **Memory Usage**: Large document collections may use significant memory. Consider using a persistent vector database for production.

### Performance Tips

- Use smaller embedding models for faster processing
- Adjust `top_k` and `threshold` parameters for optimal results
- Consider document chunking for very long texts
- Use batch processing for multiple queries

## 🛣️ Production Considerations

This example uses an in-memory vector store for simplicity. For production use, consider:

### Vector Database Options

- **Pinecone**: Managed vector database service
- **Weaviate**: Open-source vector database
- **Chroma**: Simple vector database for AI applications
- **Qdrant**: Vector similarity search engine
- **FAISS**: Facebook's similarity search library

### Scaling Considerations

- **Document Chunking**: Split large documents into smaller chunks
- **Batch Processing**: Process documents in batches
- **Caching**: Cache embeddings and frequent queries
- **Load Balancing**: Distribute queries across multiple instances

### Security

- **API Key Management**: Use environment variables or secret management
- **Input Validation**: Validate and sanitize user inputs
- **Rate Limiting**: Implement rate limiting for API endpoints
- **Access Control**: Implement proper authentication and authorization

## 📖 Further Reading

- [Pydantic-AI Documentation](https://ai.pydantic.dev/)
- [Sentence Transformers](https://www.sbert.net/)
- [Vector Database Comparison](https://github.com/currentslab/awesome-vector-search)
- [RAG Best Practices](https://docs.llamaindex.ai/en/stable/getting_started/concepts.html)

## 🤝 Contributing

Feel free to extend this example with:

- Additional vector database backends
- More sophisticated chunking strategies
- Advanced retrieval techniques
- Performance optimizations
- Additional test cases

## 📄 License

This example is provided as-is for educational and demonstration purposes.

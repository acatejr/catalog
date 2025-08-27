"""
Pydantic-AI Vector Database Example

A comprehensive example demonstrating how to use pydantic-ai with vector databases
for Retrieval-Augmented Generation (RAG) applications.

This package provides:
- Vector database implementation using sentence-transformers
- Pydantic-AI agents for querying and generating responses
- Structured data models for documents, queries, and responses
- Complete RAG pipeline from document ingestion to AI-powered responses
"""

from .models import (
    Document,
    SearchQuery,
    SearchResult,
    SearchResponse,
    ChatQuery,
    ChatResponse,
    VectorStoreStats,
)

from .vector_store import SimpleVectorStore

from .agent import RAGAgent, SimpleRAGAgent

from .sample_data import (
    get_sample_documents,
    get_sample_queries,
    get_sample_metadata_filters,
)

__version__ = "1.0.0"
__author__ = "Pydantic-AI Example"

__all__ = [
    # Models
    "Document",
    "SearchQuery",
    "SearchResult",
    "SearchResponse",
    "ChatQuery",
    "ChatResponse",
    "VectorStoreStats",
    # Vector Store
    "SimpleVectorStore",
    # Agents
    "RAGAgent",
    "SimpleRAGAgent",
    # Sample Data
    "get_sample_documents",
    "get_sample_queries",
    "get_sample_metadata_filters",
]

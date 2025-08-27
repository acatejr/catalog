"""
Pydantic models for the vector database RAG example.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class Document(BaseModel):
    """Represents a document in the vector database."""

    id: str = Field(..., description="Unique identifier for the document")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Document content/text")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    embedding: Optional[List[float]] = Field(
        None, description="Vector embedding of the document"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation timestamp"
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class SearchQuery(BaseModel):
    """Represents a search query."""

    query: str = Field(..., description="The search query text")
    top_k: int = Field(
        default=5, description="Number of results to return", ge=1, le=20
    )
    threshold: float = Field(
        default=0.0, description="Minimum similarity threshold", ge=0.0, le=1.0
    )


class SearchResult(BaseModel):
    """Represents a single search result."""

    document: Document = Field(..., description="The matched document")
    similarity_score: float = Field(..., description="Similarity score between 0 and 1")
    rank: int = Field(..., description="Rank in the search results")


class SearchResponse(BaseModel):
    """Represents the complete search response."""

    query: str = Field(..., description="Original query")
    results: List[SearchResult] = Field(..., description="List of search results")
    total_results: int = Field(..., description="Total number of results found")
    execution_time_ms: float = Field(
        ..., description="Query execution time in milliseconds"
    )


class ChatQuery(BaseModel):
    """Represents a chat query to the AI agent."""

    message: str = Field(..., description="User's message/question")
    context_limit: int = Field(
        default=3, description="Max number of context documents to use"
    )
    include_sources: bool = Field(
        default=True, description="Whether to include source references"
    )


class ChatResponse(BaseModel):
    """Represents the AI agent's response."""

    response: str = Field(..., description="AI-generated response")
    sources: List[SearchResult] = Field(
        default_factory=list, description="Source documents used"
    )
    confidence: float = Field(
        ..., description="Confidence score of the response", ge=0.0, le=1.0
    )
    processing_time_ms: float = Field(
        ..., description="Total processing time in milliseconds"
    )


class VectorStoreStats(BaseModel):
    """Statistics about the vector store."""

    total_documents: int = Field(..., description="Total number of documents")
    embedding_dimension: int = Field(..., description="Dimension of the embeddings")
    index_size_mb: float = Field(..., description="Approximate index size in MB")
    last_updated: datetime = Field(..., description="Last update timestamp")

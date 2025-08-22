"""
Pydantic-AI agent for querying the vector database and generating responses.
"""

import time
from typing import List, Optional
from pydantic_ai import Agent, RunContext
from pydantic_ai.models import Model, KnownModelName

from .models import ChatQuery, ChatResponse, SearchQuery, SearchResult
from .vector_store import SimpleVectorStore


class VectorDBContext:
    """Context class that holds the vector store for the agent."""

    def __init__(self, vector_store: SimpleVectorStore):
        self.vector_store = vector_store


# Create the pydantic-ai agent
rag_agent = Agent(
    model="openai:gpt-4o-mini",  # You can change this to any supported model
    deps_type=VectorDBContext,
    result_type=ChatResponse,
    system_prompt="""
    You are a helpful AI assistant that answers questions based on information from a vector database.

    Your role is to:
    1. Understand the user's question
    2. Search the vector database for relevant information
    3. Provide accurate, helpful answers based on the retrieved documents
    4. Always cite your sources when possible
    5. Be honest when you don't have enough information to answer

    When searching the vector database:
    - Use relevant keywords from the user's question
    - Consider synonyms and related terms
    - Search for 3-5 documents to get comprehensive context

    When generating responses:
    - Base your answer primarily on the retrieved documents
    - Be concise but thorough
    - Include source references when helpful
    - If the retrieved documents don't contain relevant information, say so clearly
    """,
)


@rag_agent.tool
async def search_vector_db(ctx: RunContext[VectorDBContext], query: str, top_k: int = 3) -> List[SearchResult]:
    """
    Search the vector database for relevant documents.

    Args:
        query: The search query string
        top_k: Number of results to return (default: 3)

    Returns:
        List of search results with documents and similarity scores
    """
    search_query = SearchQuery(query=query, top_k=top_k, threshold=0.1)
    search_response = ctx.deps.vector_store.search(search_query)
    return search_response.results


@rag_agent.tool
async def get_vector_store_stats(ctx: RunContext[VectorDBContext]) -> dict:
    """
    Get statistics about the vector store.

    Returns:
        Dictionary with vector store statistics
    """
    stats = ctx.deps.vector_store.get_stats()
    return {
        "total_documents": stats.total_documents,
        "embedding_dimension": stats.embedding_dimension,
        "index_size_mb": round(stats.index_size_mb, 2),
        "last_updated": stats.last_updated.isoformat()
    }


class RAGAgent:
    """High-level RAG agent that combines pydantic-ai with vector search."""

    def __init__(self, vector_store: SimpleVectorStore, model: Optional[str] = None):
        """
        Initialize the RAG agent.

        Args:
            vector_store: The vector store to use for document retrieval
            model: Optional model name to use (defaults to gpt-4o-mini)
        """
        self.vector_store = vector_store
        self.context = VectorDBContext(vector_store)

        # Update the agent's model if specified
        if model:
            global rag_agent
            rag_agent = Agent(
                model=model,
                deps_type=VectorDBContext,
                result_type=ChatResponse,
                system_prompt=rag_agent.system_prompt,
            )
            # Re-register tools
            rag_agent.tool(search_vector_db)
            rag_agent.tool(get_vector_store_stats)

    async def chat(self, query: ChatQuery) -> ChatResponse:
        """
        Process a chat query and generate a response.

        Args:
            query: The chat query object

        Returns:
            Chat response with answer and sources
        """
        start_time = time.time()

        try:
            # Run the agent with the query
            result = await rag_agent.run(
                query.message,
                deps=self.context,
            )

            # Extract the response
            if hasattr(result, 'data') and isinstance(result.data, ChatResponse):
                response = result.data
            else:
                # If the agent didn't return a ChatResponse, create one
                response = ChatResponse(
                    response=str(result.data) if hasattr(result, 'data') else str(result),
                    sources=[],
                    confidence=0.8,
                    processing_time_ms=0.0
                )

            # Update processing time
            processing_time = (time.time() - start_time) * 1000
            response.processing_time_ms = processing_time

            return response

        except Exception as e:
            # Handle errors gracefully
            processing_time = (time.time() - start_time) * 1000
            return ChatResponse(
                response=f"I apologize, but I encountered an error while processing your question: {str(e)}",
                sources=[],
                confidence=0.0,
                processing_time_ms=processing_time
            )

    def chat_sync(self, query: ChatQuery) -> ChatResponse:
        """
        Synchronous version of chat for easier usage.

        Args:
            query: The chat query object

        Returns:
            Chat response with answer and sources
        """
        import asyncio
        return asyncio.run(self.chat(query))

    def simple_chat(self, message: str, context_limit: int = 3, include_sources: bool = True) -> ChatResponse:
        """
        Simple chat interface that takes just a message string.

        Args:
            message: The user's message/question
            context_limit: Maximum number of context documents to use
            include_sources: Whether to include source references

        Returns:
            Chat response with answer and sources
        """
        query = ChatQuery(
            message=message,
            context_limit=context_limit,
            include_sources=include_sources
        )
        return self.chat_sync(query)


# Alternative implementation using direct function calls (for simpler use cases)
class SimpleRAGAgent:
    """Simplified RAG agent that doesn't use pydantic-ai's full agent system."""

    def __init__(self, vector_store: SimpleVectorStore):
        self.vector_store = vector_store

    def chat(self, message: str, context_limit: int = 3) -> ChatResponse:
        """
        Simple chat implementation using direct vector search.

        Args:
            message: User's message/question
            context_limit: Number of context documents to retrieve

        Returns:
            Chat response
        """
        start_time = time.time()

        # Search for relevant documents
        search_query = SearchQuery(query=message, top_k=context_limit, threshold=0.1)
        search_response = self.vector_store.search(search_query)

        # Create a simple response based on the search results
        if search_response.results:
            # Get the most relevant document
            top_result = search_response.results[0]
            response_text = f"Based on the available information: {top_result.document.content[:200]}..."

            if len(search_response.results) > 1:
                response_text += f"\n\nI found {len(search_response.results)} relevant documents that might help answer your question."

            confidence = top_result.similarity_score
        else:
            response_text = "I couldn't find any relevant information in the database to answer your question."
            confidence = 0.0

        processing_time = (time.time() - start_time) * 1000

        return ChatResponse(
            response=response_text,
            sources=search_response.results,
            confidence=confidence,
            processing_time_ms=processing_time
        )

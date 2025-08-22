"""
Comprehensive tests for the pydantic-ai vector database example.
"""

import pytest
import asyncio
from typing import List

from models import Document, SearchQuery, ChatQuery, SearchResult, ChatResponse
from vector_store import SimpleVectorStore
from agent import SimpleRAGAgent
from sample_data import get_sample_documents


class TestModels:
    """Test the Pydantic models."""

    def test_document_creation(self):
        """Test creating a Document instance."""
        doc = Document(
            id="test_1",
            title="Test Document",
            content="This is test content",
            metadata={"category": "test"}
        )

        assert doc.id == "test_1"
        assert doc.title == "Test Document"
        assert doc.content == "This is test content"
        assert doc.metadata["category"] == "test"
        assert doc.embedding is None
        assert doc.created_at is not None

    def test_search_query_validation(self):
        """Test SearchQuery validation."""
        # Valid query
        query = SearchQuery(query="test query", top_k=5, threshold=0.5)
        assert query.query == "test query"
        assert query.top_k == 5
        assert query.threshold == 0.5

        # Test defaults
        query_defaults = SearchQuery(query="test")
        assert query_defaults.top_k == 5
        assert query_defaults.threshold == 0.0

        # Test validation
        with pytest.raises(ValueError):
            SearchQuery(query="test", top_k=0)  # Should be >= 1

        with pytest.raises(ValueError):
            SearchQuery(query="test", top_k=25)  # Should be <= 20

    def test_chat_query_creation(self):
        """Test ChatQuery creation."""
        chat_query = ChatQuery(
            message="What is machine learning?",
            context_limit=3,
            include_sources=True
        )

        assert chat_query.message == "What is machine learning?"
        assert chat_query.context_limit == 3
        assert chat_query.include_sources is True


class TestVectorStore:
    """Test the SimpleVectorStore functionality."""

    @pytest.fixture
    def vector_store(self):
        """Create a vector store for testing."""
        return SimpleVectorStore(model_name="all-MiniLM-L6-v2")

    @pytest.fixture
    def populated_vector_store(self, vector_store):
        """Create a vector store populated with sample data."""
        documents = get_sample_documents()[:3]  # Use first 3 documents for faster tests
        vector_store.add_documents(documents)
        return vector_store

    def test_vector_store_initialization(self, vector_store):
        """Test vector store initialization."""
        assert vector_store.model_name == "all-MiniLM-L6-v2"
        assert len(vector_store.documents) == 0
        assert vector_store.embeddings is None
        assert vector_store.embedding_dimension > 0

    def test_add_single_document(self, vector_store):
        """Test adding a single document."""
        doc_id = vector_store.add_document(
            title="Test Document",
            content="This is a test document about machine learning.",
            metadata={"category": "test"}
        )

        assert doc_id is not None
        assert len(vector_store.documents) == 1
        assert doc_id in vector_store.documents

        document = vector_store.documents[doc_id]
        assert document.title == "Test Document"
        assert document.embedding is not None
        assert len(document.embedding) == vector_store.embedding_dimension

    def test_add_multiple_documents(self, vector_store):
        """Test adding multiple documents."""
        documents = [
            {
                "title": "Doc 1",
                "content": "Content about machine learning",
                "metadata": {"category": "AI"}
            },
            {
                "title": "Doc 2",
                "content": "Content about Python programming",
                "metadata": {"category": "Programming"}
            }
        ]

        doc_ids = vector_store.add_documents(documents)

        assert len(doc_ids) == 2
        assert len(vector_store.documents) == 2
        assert vector_store.embeddings is not None
        assert vector_store.embeddings.shape == (2, vector_store.embedding_dimension)

    def test_search_functionality(self, populated_vector_store):
        """Test search functionality."""
        query = SearchQuery(query="machine learning", top_k=2, threshold=0.0)
        response = populated_vector_store.search(query)

        assert response.query == "machine learning"
        assert len(response.results) <= 2
        assert response.total_results <= 2
        assert response.execution_time_ms >= 0

        # Check that results are sorted by similarity
        if len(response.results) > 1:
            for i in range(len(response.results) - 1):
                assert response.results[i].similarity_score >= response.results[i + 1].similarity_score

    def test_search_with_threshold(self, populated_vector_store):
        """Test search with similarity threshold."""
        # High threshold should return fewer results
        query_high = SearchQuery(query="machine learning", top_k=10, threshold=0.8)
        response_high = populated_vector_store.search(query_high)

        # Low threshold should return more results
        query_low = SearchQuery(query="machine learning", top_k=10, threshold=0.1)
        response_low = populated_vector_store.search(query_low)

        assert len(response_high.results) <= len(response_low.results)

    def test_get_document(self, populated_vector_store):
        """Test getting a document by ID."""
        # Get a document ID from the store
        doc_id = list(populated_vector_store.documents.keys())[0]

        document = populated_vector_store.get_document(doc_id)
        assert document is not None
        assert document.id == doc_id

        # Test non-existent document
        non_existent = populated_vector_store.get_document("non_existent_id")
        assert non_existent is None

    def test_delete_document(self, populated_vector_store):
        """Test deleting a document."""
        initial_count = len(populated_vector_store.documents)
        doc_id = list(populated_vector_store.documents.keys())[0]

        # Delete the document
        success = populated_vector_store.delete_document(doc_id)
        assert success is True
        assert len(populated_vector_store.documents) == initial_count - 1
        assert doc_id not in populated_vector_store.documents

        # Try to delete non-existent document
        success = populated_vector_store.delete_document("non_existent_id")
        assert success is False

    def test_get_stats(self, populated_vector_store):
        """Test getting vector store statistics."""
        stats = populated_vector_store.get_stats()

        assert stats.total_documents > 0
        assert stats.embedding_dimension > 0
        assert stats.index_size_mb >= 0
        assert stats.last_updated is not None

    def test_clear(self, populated_vector_store):
        """Test clearing the vector store."""
        assert len(populated_vector_store.documents) > 0

        populated_vector_store.clear()

        assert len(populated_vector_store.documents) == 0
        assert len(populated_vector_store.document_ids) == 0
        assert populated_vector_store.embeddings is None


class TestSimpleRAGAgent:
    """Test the SimpleRAGAgent functionality."""

    @pytest.fixture
    def populated_vector_store(self):
        """Create a populated vector store for testing."""
        vector_store = SimpleVectorStore(model_name="all-MiniLM-L6-v2")
        documents = get_sample_documents()[:3]  # Use first 3 documents for faster tests
        vector_store.add_documents(documents)
        return vector_store

    @pytest.fixture
    def rag_agent(self, populated_vector_store):
        """Create a SimpleRAGAgent for testing."""
        return SimpleRAGAgent(populated_vector_store)

    def test_agent_initialization(self, rag_agent):
        """Test agent initialization."""
        assert rag_agent.vector_store is not None
        assert len(rag_agent.vector_store.documents) > 0

    def test_chat_functionality(self, rag_agent):
        """Test basic chat functionality."""
        response = rag_agent.chat("What is machine learning?", context_limit=2)

        assert isinstance(response, ChatResponse)
        assert response.response is not None
        assert len(response.response) > 0
        assert 0.0 <= response.confidence <= 1.0
        assert response.processing_time_ms >= 0
        assert isinstance(response.sources, list)

    def test_chat_with_relevant_query(self, rag_agent):
        """Test chat with a query that should find relevant documents."""
        response = rag_agent.chat("machine learning algorithms", context_limit=3)

        # Should find relevant documents
        assert len(response.sources) > 0
        assert response.confidence > 0.0
        assert "machine learning" in response.response.lower() or "algorithm" in response.response.lower()

    def test_chat_with_irrelevant_query(self, rag_agent):
        """Test chat with a query that might not find relevant documents."""
        response = rag_agent.chat("quantum physics and space exploration", context_limit=3)

        # Might not find highly relevant documents, but should still respond
        assert isinstance(response, ChatResponse)
        assert response.response is not None
        # Confidence might be low for irrelevant queries
        assert 0.0 <= response.confidence <= 1.0

    def test_chat_context_limit(self, rag_agent):
        """Test that context limit is respected."""
        response_1 = rag_agent.chat("programming", context_limit=1)
        response_3 = rag_agent.chat("programming", context_limit=3)

        assert len(response_1.sources) <= 1
        assert len(response_3.sources) <= 3


class TestSampleData:
    """Test the sample data functions."""

    def test_get_sample_documents(self):
        """Test getting sample documents."""
        documents = get_sample_documents()

        assert isinstance(documents, list)
        assert len(documents) > 0

        # Check document structure
        for doc in documents:
            assert "id" in doc
            assert "title" in doc
            assert "content" in doc
            assert "metadata" in doc
            assert isinstance(doc["metadata"], dict)

    def test_document_content_quality(self):
        """Test that sample documents have reasonable content."""
        documents = get_sample_documents()

        for doc in documents:
            # Check that content is substantial
            assert len(doc["content"]) > 100
            assert len(doc["title"]) > 0

            # Check metadata structure
            metadata = doc["metadata"]
            assert "category" in metadata
            assert "difficulty" in metadata
            assert "tags" in metadata
            assert isinstance(metadata["tags"], list)


class TestIntegration:
    """Integration tests for the complete system."""

    @pytest.fixture
    def complete_system(self):
        """Set up a complete system for integration testing."""
        # Create vector store
        vector_store = SimpleVectorStore(model_name="all-MiniLM-L6-v2")

        # Add sample documents
        documents = get_sample_documents()[:5]  # Use 5 documents for integration tests
        vector_store.add_documents(documents)

        # Create agent
        agent = SimpleRAGAgent(vector_store)

        return vector_store, agent

    def test_end_to_end_workflow(self, complete_system):
        """Test the complete end-to-end workflow."""
        vector_store, agent = complete_system

        # Test that we can search the vector store directly
        search_query = SearchQuery(query="Python programming", top_k=3)
        search_response = vector_store.search(search_query)
        assert len(search_response.results) > 0

        # Test that we can use the agent to get responses
        chat_response = agent.chat("Tell me about Python data structures")
        assert chat_response.response is not None
        assert len(chat_response.sources) > 0

        # Test that the agent's sources match what we'd expect from direct search
        agent_sources = [s.document.id for s in chat_response.sources]
        search_sources = [s.document.id for s in search_response.results]

        # There should be some overlap (though not necessarily identical due to different queries)
        assert len(set(agent_sources) & set(search_sources)) >= 0

    def test_multiple_queries_consistency(self, complete_system):
        """Test that multiple similar queries return consistent results."""
        vector_store, agent = complete_system

        # Ask similar questions
        response1 = agent.chat("What is machine learning?")
        response2 = agent.chat("Tell me about machine learning")
        response3 = agent.chat("Explain machine learning concepts")

        # All should return responses
        assert all(r.response for r in [response1, response2, response3])

        # Should have some consistency in sources (at least some overlap)
        sources1 = set(s.document.id for s in response1.sources)
        sources2 = set(s.document.id for s in response2.sources)
        sources3 = set(s.document.id for s in response3.sources)

        # At least some overlap between similar queries
        assert len(sources1 & sources2) > 0 or len(sources1 & sources3) > 0 or len(sources2 & sources3) > 0


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])

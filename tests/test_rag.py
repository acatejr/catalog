"""
Tests for RAG (Retrieval-Augmented Generation) functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

from catalog.lib.rag import (
    RAGSystem,
    RAGConfig,
    QueryClassifier,
    QueryType,
    EmbeddingManager,
    VectorSearchEngine,
    LLMManager,
    DatabaseManager,
    Document,
    run_natural_language_query,
    get_query_embedding,
    search_similar_documents
)


class TestQueryClassifier:
    """Test query classification functionality."""

    def test_classify_keyword_frequency_query(self):
        """Test classification of keyword frequency queries."""
        queries = [
            "most frequent keywords",
            "show me the most common keywords",
            "what are the top keywords",
            "keyword frequencies in the database"
        ]

        for query in queries:
            query_type, params = QueryClassifier.classify_query(query)
            assert query_type == QueryType.KEYWORD_FREQUENCY
            assert isinstance(params, dict)

    def test_classify_duplicate_titles_query(self):
        """Test classification of duplicate titles queries."""
        queries = [
            "duplicate titles",
            "show me documents with same titles",
            "find repeated titles",
            "identical title documents"
        ]

        for query in queries:
            query_type, params = QueryClassifier.classify_query(query)
            assert query_type == QueryType.DUPLICATE_TITLES
            assert isinstance(params, dict)

    def test_classify_data_source_filter_query(self):
        """Test classification of data source filter queries."""
        query = "show me datasets from USGS"
        query_type, params = QueryClassifier.classify_query(query)

        assert query_type == QueryType.DATA_SOURCE_FILTER
        assert "data_source" in params
        assert params["data_source"] == "USGS"

    def test_classify_vector_search_query(self):
        """Test classification of general vector search queries."""
        queries = [
            "forest fire datasets",
            "erosion related data",
            "climate change information",
            "water quality studies"
        ]

        for query in queries:
            query_type, params = QueryClassifier.classify_query(query)
            assert query_type == QueryType.VECTOR_SEARCH
            assert isinstance(params, dict)


class TestEmbeddingManager:
    """Test embedding generation functionality."""

    @patch('catalog.lib.rag.SentenceTransformer')
    def test_embedding_manager_initialization(self, mock_transformer):
        """Test EmbeddingManager initialization."""
        mock_model = Mock()
        mock_transformer.return_value = mock_model

        embedding_manager = EmbeddingManager("test-model")

        assert embedding_manager.model_name == "test-model"
        assert embedding_manager.model == mock_model
        mock_transformer.assert_called_once_with("test-model")

    @patch('catalog.lib.rag.SentenceTransformer')
    def test_get_embedding(self, mock_transformer):
        """Test embedding generation."""
        mock_model = Mock()
        mock_model.encode.return_value = [0.1, 0.2, 0.3]
        mock_transformer.return_value = mock_model

        embedding_manager = EmbeddingManager()
        result = embedding_manager.get_embedding("test text")

        assert result == [0.1, 0.2, 0.3]
        mock_model.encode.assert_called_once_with("test text")

    @patch('catalog.lib.rag.SentenceTransformer')
    def test_get_embedding_model_not_loaded(self, mock_transformer):
        """Test embedding generation when model is not loaded."""
        mock_transformer.side_effect = Exception("Model loading failed")

        with pytest.raises(Exception):
            EmbeddingManager()


class TestDatabaseManager:
    """Test database operations."""

    @patch('catalog.lib.rag.psycopg2.connect')
    def test_count_documents(self, mock_connect):
        """Test document counting."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = [100]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value.__enter__.return_value = mock_conn

        db_manager = DatabaseManager()
        count = db_manager.count_documents()

        assert count == 100
        mock_cursor.execute.assert_called_once_with("SELECT COUNT(*) FROM documents")

    @patch('catalog.lib.rag.psycopg2.connect')
    def test_get_data_sources(self, mock_connect):
        """Test getting available data sources."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [["USGS"], ["EPA"], ["NOAA"]]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value.__enter__.return_value = mock_conn

        db_manager = DatabaseManager()
        sources = db_manager.get_data_sources()

        assert sources == ["USGS", "EPA", "NOAA"]
        mock_cursor.execute.assert_called_once_with(
            "SELECT DISTINCT data_source FROM documents WHERE data_source IS NOT NULL"
        )


class TestVectorSearchEngine:
    """Test vector search functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db_manager = Mock(spec=DatabaseManager)
        self.search_engine = VectorSearchEngine(self.mock_db_manager)

    @patch('catalog.lib.rag.psycopg2.connect')
    def test_search_similar_documents(self, mock_connect):
        """Test vector similarity search."""
        # Mock database response
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            (1, "doc1", "Forest Fire Study", "A study about forest fires",
             "Forest fire content", 0, "USGS", ["fire", "forest"], ["Author1"], 0.85),
            (2, "doc2", "Erosion Analysis", "Analysis of soil erosion",
             "Erosion content", 0, "EPA", ["erosion", "soil"], ["Author2"], 0.75)
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value.__enter__.return_value = mock_conn
        self.mock_db_manager.get_connection.return_value = mock_connect.return_value.__enter__.return_value

        query_embedding = [0.1, 0.2, 0.3]
        documents = self.search_engine.search_similar_documents(
            query_embedding, top_k=2, threshold=0.5
        )

        assert len(documents) == 2
        assert documents[0].title == "Forest Fire Study"
        assert documents[0].similarity == 0.85
        assert documents[1].title == "Erosion Analysis"
        assert documents[1].similarity == 0.75

    @patch('catalog.lib.rag.psycopg2.connect')
    def test_get_keyword_frequencies(self, mock_connect):
        """Test keyword frequency retrieval."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ("fire", 10),
            ("forest", 8),
            ("erosion", 6)
        ]
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value.__enter__.return_value = mock_conn
        self.mock_db_manager.get_connection.return_value = mock_connect.return_value.__enter__.return_value

        keywords = self.search_engine.get_keyword_frequencies(top_k=3)

        assert len(keywords) == 3
        assert keywords[0] == {"keyword": "fire", "frequency": 10}
        assert keywords[1] == {"keyword": "forest", "frequency": 8}
        assert keywords[2] == {"keyword": "erosion", "frequency": 6}


class TestLLMManager:
    """Test LLM interaction functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = RAGConfig()
        self.llm_manager = LLMManager(self.config)

    @patch('catalog.lib.rag.requests.post')
    def test_generate_vector_search_response(self, mock_post):
        """Test LLM response generation for vector search."""
        # Mock LLM API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Based on the documents, forest fires are a major concern..."}}]
        }
        mock_post.return_value = mock_response

        # Create test documents
        documents = [
            Document(
                id=1, doc_id="doc1", title="Forest Fire Study",
                description="A study about forest fires", chunk_text="Forest fire content",
                chunk_index=0, data_source="USGS", keywords=["fire", "forest"],
                authors=["Author1"], similarity=0.85
            )
        ]

        response = self.llm_manager.generate_response(
            "Tell me about forest fires", documents, QueryType.VECTOR_SEARCH
        )

        assert "forest fires are a major concern" in response
        mock_post.assert_called_once()

    @patch('catalog.lib.rag.requests.post')
    def test_generate_response_api_error(self, mock_post):
        """Test LLM response generation with API error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        documents = []
        response = self.llm_manager.generate_response(
            "test query", documents, QueryType.VECTOR_SEARCH
        )

        assert "Error querying LLM: 500" in response


class TestRAGSystem:
    """Test the main RAG system integration."""

    @patch('catalog.lib.rag.DatabaseManager')
    @patch('catalog.lib.rag.EmbeddingManager')
    @patch('catalog.lib.rag.VectorSearchEngine')
    @patch('catalog.lib.rag.LLMManager')
    def test_rag_system_initialization(self, mock_llm, mock_search, mock_embedding, mock_db):
        """Test RAG system initialization."""
        config = RAGConfig()
        rag_system = RAGSystem(config)

        assert rag_system.config == config
        mock_db.assert_called_once()
        mock_embedding.assert_called_once_with(config.embedding_model)
        mock_search.assert_called_once()
        mock_llm.assert_called_once_with(config)

    @patch('catalog.lib.rag.DatabaseManager')
    @patch('catalog.lib.rag.EmbeddingManager')
    @patch('catalog.lib.rag.VectorSearchEngine')
    @patch('catalog.lib.rag.LLMManager')
    def test_vector_search_query(self, mock_llm_class, mock_search_class, mock_embedding_class, mock_db_class):
        """Test vector search query processing."""
        # Set up mocks
        mock_db = Mock()
        mock_embedding = Mock()
        mock_search = Mock()
        mock_llm = Mock()

        mock_db_class.return_value = mock_db
        mock_embedding_class.return_value = mock_embedding
        mock_search_class.return_value = mock_search
        mock_llm_class.return_value = mock_llm

        # Mock embedding generation
        mock_embedding.get_embedding.return_value = [0.1, 0.2, 0.3]

        # Mock search results
        mock_documents = [
            Document(
                id=1, doc_id="doc1", title="Forest Fire Study",
                description="A study about forest fires", chunk_text="Forest fire content",
                chunk_index=0, data_source="USGS", keywords=["fire", "forest"],
                authors=["Author1"], similarity=0.85
            )
        ]
        mock_search.search_similar_documents.return_value = mock_documents

        # Mock LLM response
        mock_llm.generate_response.return_value = "Forest fires are a significant environmental concern."

        # Test the query
        rag_system = RAGSystem()
        result = rag_system.query("forest fire datasets", use_llm=True)

        assert result["query"] == "forest fire datasets"
        assert result["query_type"] == QueryType.VECTOR_SEARCH.value
        assert len(result["documents"]) == 1
        assert result["documents"][0]["title"] == "Forest Fire Study"
        assert "Forest fires are a significant environmental concern" in result["response"]

    @patch('catalog.lib.rag.DatabaseManager')
    @patch('catalog.lib.rag.EmbeddingManager')
    @patch('catalog.lib.rag.VectorSearchEngine')
    @patch('catalog.lib.rag.LLMManager')
    def test_keyword_frequency_query(self, mock_llm_class, mock_search_class, mock_embedding_class, mock_db_class):
        """Test keyword frequency query processing."""
        # Set up mocks
        mock_db = Mock()
        mock_embedding = Mock()
        mock_search = Mock()
        mock_llm = Mock()

        mock_db_class.return_value = mock_db
        mock_embedding_class.return_value = mock_embedding
        mock_search_class.return_value = mock_search
        mock_llm_class.return_value = mock_llm

        # Mock keyword frequency data
        keyword_data = [
            {"keyword": "fire", "frequency": 10},
            {"keyword": "forest", "frequency": 8}
        ]
        mock_search.get_keyword_frequencies.return_value = keyword_data

        # Mock LLM response
        mock_llm._generate_keyword_frequency_response.return_value = "The most frequent keywords are fire and forest."

        # Test the query
        rag_system = RAGSystem()
        result = rag_system.query("most frequent keywords", use_llm=True)

        assert result["query"] == "most frequent keywords"
        assert result["query_type"] == QueryType.KEYWORD_FREQUENCY.value
        assert result["metadata"]["keyword_frequencies"] == keyword_data
        assert "most frequent keywords are fire and forest" in result["response"]


class TestConvenienceFunctions:
    """Test convenience functions for backward compatibility."""

    @patch('catalog.lib.rag.EmbeddingManager')
    def test_get_query_embedding(self, mock_embedding_class):
        """Test get_query_embedding convenience function."""
        mock_embedding = Mock()
        mock_embedding.get_embedding.return_value = [0.1, 0.2, 0.3]
        mock_embedding_class.return_value = mock_embedding

        result = get_query_embedding("test query")

        assert result == [0.1, 0.2, 0.3]
        mock_embedding_class.assert_called_once_with("all-MiniLM-L6-v2")
        mock_embedding.get_embedding.assert_called_once_with("test query")

    @patch('catalog.lib.rag.DatabaseManager')
    @patch('catalog.lib.rag.VectorSearchEngine')
    def test_search_similar_documents(self, mock_search_class, mock_db_class):
        """Test search_similar_documents convenience function."""
        mock_db = Mock()
        mock_search = Mock()
        mock_db_class.return_value = mock_db
        mock_search_class.return_value = mock_search

        # Mock search results
        mock_documents = [
            Document(
                id=1, doc_id="doc1", title="Test Document",
                description="A test document", chunk_text="Test content",
                chunk_index=0, data_source="TEST", keywords=["test"],
                authors=["Author"], similarity=0.85
            )
        ]
        mock_search.search_similar_documents.return_value = mock_documents

        query_embedding = [0.1, 0.2, 0.3]
        result = search_similar_documents(query_embedding, top_k=1)

        assert len(result) == 1
        assert result[0]["title"] == "Test Document"
        assert result[0]["similarity"] == 0.85

    @patch('catalog.lib.rag.RAGSystem')
    def test_run_natural_language_query(self, mock_rag_class):
        """Test run_natural_language_query convenience function."""
        mock_rag = Mock()
        mock_rag.query.return_value = {
            "query": "test query",
            "query_type": "vector_search",
            "documents": [],
            "response": "Test response"
        }
        mock_rag_class.return_value = mock_rag

        result = run_natural_language_query("test query")

        assert result["query"] == "test query"
        assert result["response"] == "Test response"
        mock_rag.query.assert_called_once_with(
            user_query="test query",
            top_k=5,
            data_source=None,
            use_llm=True,
            similarity_threshold=0.5
        )


class TestErrorHandling:
    """Test error handling in RAG system."""

    @patch('catalog.lib.rag.DatabaseManager')
    @patch('catalog.lib.rag.EmbeddingManager')
    @patch('catalog.lib.rag.VectorSearchEngine')
    @patch('catalog.lib.rag.LLMManager')
    def test_query_with_database_error(self, mock_llm_class, mock_search_class, mock_embedding_class, mock_db_class):
        """Test query handling when database error occurs."""
        # Set up mocks to raise an exception
        mock_embedding = Mock()
        mock_embedding.get_embedding.side_effect = Exception("Database connection failed")
        mock_embedding_class.return_value = mock_embedding

        mock_db_class.return_value = Mock()
        mock_search_class.return_value = Mock()
        mock_llm_class.return_value = Mock()

        rag_system = RAGSystem()
        result = rag_system.query("test query")

        assert result["query_type"] == "error"
        assert "Database connection failed" in result["response"]
        assert "error" in result["metadata"]


if __name__ == "__main__":
    pytest.main([__file__])

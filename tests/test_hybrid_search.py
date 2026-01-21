import pytest
from unittest.mock import Mock
from catalog.core import HybridSearch


class TestHybridSearch:
    @pytest.fixture
    def sample_documents(self):
        return [
            "Forest fire damage assessment report",
            "Wildfire burn area boundaries",
            "Timber sale records 2023",
            "Tree harvest data for national forests",
        ]

    @pytest.fixture
    def mock_vector_db(self):
        mock_db = Mock()
        # Mock vector search returning indices with distances
        mock_db.query.return_value = [
            {"id": 0, "distance": 0.1},
            {"id": 1, "distance": 0.2},
        ]
        return mock_db

    @pytest.fixture
    def hybrid_search(self, mock_vector_db, sample_documents):
        return HybridSearch(mock_vector_db, sample_documents)

    def test_bm25_initialized(self, hybrid_search):
        """BM25 index should be created from documents."""
        assert hybrid_search.bm25 is not None

    def test_bm25_scores_query(self, hybrid_search):
        """BM25 should return scores for a query."""
        scores = hybrid_search.bm25.get_scores("forest fire".split())
        assert len(scores) == 4  # one score per document
        assert scores[0] > 0  # "Forest fire damage assessment report" should match

    def test_bm25_finds_exact_matches(self, hybrid_search):
        """BM25 should score exact keyword matches higher."""
        scores = hybrid_search.bm25.get_scores("forest fire".split())
        # Doc 0 has "Forest fire" - should have highest score
        assert scores[0] == max(scores)

    def test_vector_db_called_on_search(self, hybrid_search, mock_vector_db):
        """Search should call the vector database."""
        hybrid_search.search("forest fire", k=5)
        mock_vector_db.query.assert_called_once_with("forest fire", k=10)

    def test_fuse_results_combines_both_sources(self, hybrid_search):
        """Fuse results should include docs from both vector and BM25."""
        vector_results = [
            {"id": 1, "distance": 0.1},  # Wildfire doc ranked first by vector
            {"id": 2, "distance": 0.5},  # Timber doc ranked second by vector
        ]
        bm25_scores = [2.0, 0.5, 0.0, 1.0]  # Doc 0 highest, then doc 3

        results = hybrid_search.fuse_results(vector_results, bm25_scores, k=4)

        # Should include docs from both sources
        assert 0 in results  # From BM25 (highest score)
        assert 1 in results  # From vector (best distance)

    def test_fuse_results_respects_k_limit(self, hybrid_search):
        """Fuse results should return at most k results."""
        vector_results = [
            {"id": 0, "distance": 0.1},
            {"id": 1, "distance": 0.2},
        ]
        bm25_scores = [1.0, 1.0, 1.0, 1.0]

        results = hybrid_search.fuse_results(vector_results, bm25_scores, k=2)
        assert len(results) <= 2

    def test_search_returns_fused_results(self, hybrid_search):
        """Full search should return fused results from both methods."""
        results = hybrid_search.search("forest fire", k=3)

        assert isinstance(results, list)
        assert len(results) <= 3

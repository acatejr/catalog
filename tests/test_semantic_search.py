import pytest
from unittest.mock import MagicMock, patch
from catalog.search import SemanticSearch


FAKE_EMBEDDING = [0.1] * 384


class TestSemanticSearchInit:
    def test_stores_model(self):
        search = SemanticSearch("test-model")
        assert search.model == "test-model"

    def test_accepts_injected_embeddings_service(self):
        svc = MagicMock()
        search = SemanticSearch("test-model", embeddings_service=svc)
        assert search.embeddings_service is svc

    def test_accepts_injected_db_session(self):
        session = MagicMock()
        search = SemanticSearch("test-model", db_session=session)
        assert search.db_session is session


class TestSemanticSearchValidation:
    def test_raises_for_empty_query(self):
        search = SemanticSearch("test-model")
        with pytest.raises(ValueError, match="Query cannot be empty"):
            search.search("")

    def test_raises_for_whitespace_query(self):
        search = SemanticSearch("test-model")
        with pytest.raises(ValueError, match="Query cannot be empty"):
            search.search("   ")

    def test_raises_for_non_string_query(self):
        search = SemanticSearch("test-model")
        with pytest.raises(ValueError, match="Query must be a string"):
            search.search(None)


class TestSemanticSearchEmbedding:
    def _make_search(self):
        svc = MagicMock()
        svc.embed_text.return_value = FAKE_EMBEDDING
        session = MagicMock()
        session.execute.return_value.fetchall.return_value = []
        return SemanticSearch("test-model", embeddings_service=svc, db_session=session), svc, session

    def test_calls_embed_text_with_query(self):
        search, svc, _ = self._make_search()
        search.search("forests near water")
        svc.embed_text.assert_called_once_with("forests near water")

    def test_embed_text_called_once_per_search(self):
        search, svc, _ = self._make_search()
        search.search("query one")
        search.search("query two")
        assert svc.embed_text.call_count == 2

    def test_queries_db_with_embedding(self):
        search, svc, session = self._make_search()
        search.search("find wetlands data")
        session.execute.assert_called_once()
        call_args = session.execute.call_args
        params = call_args.args[1]
        assert params.get("embedding") == FAKE_EMBEDDING

    def test_returns_list(self):
        search, _, _ = self._make_search()
        result = search.search("any query")
        assert isinstance(result, list)

    def test_returns_db_results(self):
        svc = MagicMock()
        svc.embed_text.return_value = FAKE_EMBEDDING
        session = MagicMock()
        fake_row = MagicMock()
        session.execute.return_value.fetchall.return_value = [fake_row]
        search = SemanticSearch("test-model", embeddings_service=svc, db_session=session)
        result = search.search("rivers in Colorado")
        assert result == [fake_row]

    def test_default_limit_applied(self):
        search, svc, session = self._make_search()
        search.search("grasslands")
        call_args = session.execute.call_args
        compiled = str(call_args.args[0])
        assert "10" in compiled or "LIMIT" in compiled.upper()

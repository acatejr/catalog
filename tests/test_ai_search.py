import pytest
from unittest.mock import MagicMock
from catalog.search import SemanticSearch, AISearch

FAKE_EMBEDDING = [0.1] * 384


class TestAISearchInit:

    def test_stores_model(self):
        search = AISearch("test-model")
        assert search.model == "test-model"

    def test_accepts_injected_embeddings_service(self):
        svc = MagicMock()
        search = AISearch("test-model", embeddings_service=svc)
        assert search.embeddings_service is svc

    def test_accepts_injected_db_session(self):
        session = MagicMock()
        search = AISearch("test-model", db_session=session)
        assert search.db_session is session

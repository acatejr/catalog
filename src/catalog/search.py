from typing import List
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from .embeddings import EmbeddingsService
from .db import get_db_url


class SemanticSearch:
    def __init__(self, model: str, embeddings_service=None, db_session=None, db_url: str = None):
        self.model = model
        self._embeddings_service = embeddings_service
        self.db_session = db_session
        self.db_url = db_url

    @property
    def embeddings_service(self):
        if self._embeddings_service is None:
            self._embeddings_service = EmbeddingsService(self.model)
        return self._embeddings_service

    def search(self, query, limit: int = 10) -> List:
        if not isinstance(query, str):
            raise ValueError("Query must be a string.")
        if not query or len(query.strip()) == 0:
            raise ValueError("Query cannot be empty.")

        embedding = self.embeddings_service.embed_text(query)

        stmt = text("""
            SELECT *, 1 - (embedding <=> CAST(:embedding AS vector)) AS similarity
            FROM documents
            ORDER BY embedding <=> CAST(:embedding AS vector)
            LIMIT :limit
        """)
        params = {"embedding": embedding, "limit": limit}

        if self.db_session is not None:
            return self.db_session.execute(stmt, params).fetchall()

        engine = create_engine(self.db_url or get_db_url())
        with Session(engine) as session:
            return session.execute(stmt, params).fetchall()

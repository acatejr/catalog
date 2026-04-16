"""Embeddings generation with PostgreSQL persistence."""

from fastembed import TextEmbedding
from sqlalchemy.orm import Session
from typing import List
from .schema import USFSDocument
from .db import DocumentRecord, get_db_url
from sqlalchemy import create_engine

class EmbeddingsService:
    """Generates and stores embeddings in PostgreSQL."""

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        """Initialize embedding model."""
        self.model = TextEmbedding(model_name)
        self.model_name = model_name
        self.embedding_dim = 384

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        return list(self.model.embed([text]))[0].tolist()

    def embed_batch(
        self,
        docs: List[USFSDocument],
        batch_size: int = 32,
        show_progress: bool = True
    ) -> List[List[float]]:
        """Generate embeddings for multiple documents efficiently."""
        texts = [doc.to_embedding_text() for doc in docs]
        return [emb.tolist() for emb in self.model.embed(texts, batch_size=batch_size)]

    def store_in_postgres(
        self,
        docs: List[USFSDocument],
        embeddings: List[List[float]],
        db_url: str = None
    ):
        """Store documents with embeddings in PostgreSQL."""
        if db_url is None:
            db_url = get_db_url()

        engine = create_engine(db_url)

        with Session(engine) as session:
            for doc, embedding in zip(docs, embeddings):
                record = DocumentRecord.from_usfs_document(doc, embedding)
                session.merge(record)  # Upsert
            session.commit()
            print(f"✓ Stored {len(docs)} documents with embeddings in PostgreSQL")


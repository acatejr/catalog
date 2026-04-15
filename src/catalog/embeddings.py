"""Embeddings generation with PostgreSQL persistence."""

from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session
from typing import List
from .schema import USFSDocument
from .db import DocumentRecord, get_db_url
from sqlalchemy import create_engine

class EmbeddingsService:
    """Generates and stores embeddings in PostgreSQL."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize embedding model."""
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        self.embedding_dim = self.model.get_sentence_embedding_dimension()

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        embedding = self.model.encode(text, convert_to_tensor=False)
        return embedding.tolist()

    def embed_batch(
        self,
        docs: List[USFSDocument],
        batch_size: int = 32,
        show_progress: bool = True
    ) -> List[List[float]]:
        """Generate embeddings for multiple documents efficiently."""
        texts = [doc.to_embedding_text() for doc in docs]
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_tensor=False
        )
        return [emb.tolist() for emb in embeddings]

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

# class VectorSearch:
#     """Query embeddings from PostgreSQL."""

#     def __init__(self, db_url: str = None):
#         """Initialize database connection."""
#         self.db_url = db_url or get_db_url()
#         self.engine = create_engine(self.db_url)
#         self.embeddings_service = EmbeddingsService()

#     def search(
#         self,
#         query: str,
#         limit: int = 10,
#         similarity_threshold: float = None
#     ) -> List[tuple]:
#         """Search for similar documents by semantic similarity.

#         Args:
#             query: Search query text
#             limit: Number of results
#             similarity_threshold: Filter results by minimum cosine similarity (0-1)

#         Returns:
#             List of (document, similarity_score) tuples
#         """
#         query_embedding = self.embeddings_service.embed_text(query)

#         with Session(self.engine) as session:
#             # Cosine distance: 1 - cosine_similarity
#             distance_expr = 1 - (DocumentRecord.embedding.cosine_distance(query_embedding))

#             stmt = (
#                 session.query(DocumentRecord, distance_expr.label('similarity'))
#                 .order_by(distance_expr.desc())
#             )

#             if similarity_threshold is not None:
#                 stmt = stmt.filter(distance_expr >= similarity_threshold)

#             results = stmt.limit(limit).all()

#         return results
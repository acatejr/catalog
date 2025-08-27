"""
Simple in-memory vector database implementation using sentence-transformers.
"""

import time
import numpy as np
from typing import List, Optional, Dict, Any
from sentence_transformers import SentenceTransformer
from datetime import datetime
import uuid

from .models import (
    Document,
    SearchQuery,
    SearchResult,
    SearchResponse,
    VectorStoreStats,
)


class SimpleVectorStore:
    """A simple in-memory vector database using cosine similarity."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the vector store.

        Args:
            model_name: Name of the sentence transformer model to use
        """
        self.model_name = model_name
        self.encoder = SentenceTransformer(model_name)
        self.documents: Dict[str, Document] = {}
        self.embeddings: Optional[np.ndarray] = None
        self.document_ids: List[str] = []
        self.embedding_dimension = self.encoder.get_sentence_embedding_dimension()
        self.last_updated = datetime.now()

    def add_document(
        self,
        title: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        doc_id: Optional[str] = None,
    ) -> str:
        """
        Add a document to the vector store.

        Args:
            title: Document title
            content: Document content
            metadata: Optional metadata dictionary
            doc_id: Optional document ID (will generate one if not provided)

        Returns:
            The document ID
        """
        if doc_id is None:
            doc_id = str(uuid.uuid4())

        if metadata is None:
            metadata = {}

        # Generate embedding
        embedding = self.encoder.encode(content).tolist()

        # Create document
        document = Document(
            id=doc_id,
            title=title,
            content=content,
            metadata=metadata,
            embedding=embedding,
            created_at=datetime.now(),
        )

        # Store document
        self.documents[doc_id] = document
        self.document_ids.append(doc_id)

        # Update embeddings matrix
        self._rebuild_embeddings_matrix()
        self.last_updated = datetime.now()

        return doc_id

    def add_documents(self, documents: List[Dict[str, Any]]) -> List[str]:
        """
        Add multiple documents to the vector store.

        Args:
            documents: List of document dictionaries with 'title', 'content', and optional 'metadata'

        Returns:
            List of document IDs
        """
        doc_ids = []
        for doc in documents:
            doc_id = self.add_document(
                title=doc["title"],
                content=doc["content"],
                metadata=doc.get("metadata", {}),
                doc_id=doc.get("id"),
            )
            doc_ids.append(doc_id)
        return doc_ids

    def search(self, query: SearchQuery) -> SearchResponse:
        """
        Search for similar documents.

        Args:
            query: Search query object

        Returns:
            Search response with results
        """
        start_time = time.time()

        if not self.documents:
            return SearchResponse(
                query=query.query, results=[], total_results=0, execution_time_ms=0.0
            )

        # Generate query embedding
        query_embedding = self.encoder.encode(query.query)

        # Calculate similarities
        similarities = self._calculate_similarities(query_embedding)

        # Filter by threshold and get top-k
        valid_indices = np.where(similarities >= query.threshold)[0]
        valid_similarities = similarities[valid_indices]

        # Sort by similarity (descending)
        sorted_indices = np.argsort(valid_similarities)[::-1]
        top_indices = sorted_indices[: query.top_k]

        # Create results
        results = []
        for rank, idx in enumerate(top_indices):
            original_idx = valid_indices[idx]
            doc_id = self.document_ids[original_idx]
            document = self.documents[doc_id]
            similarity_score = float(valid_similarities[idx])

            result = SearchResult(
                document=document, similarity_score=similarity_score, rank=rank + 1
            )
            results.append(result)

        execution_time = (time.time() - start_time) * 1000

        return SearchResponse(
            query=query.query,
            results=results,
            total_results=len(results),
            execution_time_ms=execution_time,
        )

    def get_document(self, doc_id: str) -> Optional[Document]:
        """Get a document by ID."""
        return self.documents.get(doc_id)

    def delete_document(self, doc_id: str) -> bool:
        """Delete a document by ID."""
        if doc_id in self.documents:
            del self.documents[doc_id]
            self.document_ids.remove(doc_id)
            self._rebuild_embeddings_matrix()
            self.last_updated = datetime.now()
            return True
        return False

    def get_stats(self) -> VectorStoreStats:
        """Get statistics about the vector store."""
        # Rough estimate of memory usage
        index_size_mb = 0.0
        if self.embeddings is not None:
            index_size_mb = self.embeddings.nbytes / (1024 * 1024)

        return VectorStoreStats(
            total_documents=len(self.documents),
            embedding_dimension=self.embedding_dimension,
            index_size_mb=index_size_mb,
            last_updated=self.last_updated,
        )

    def _rebuild_embeddings_matrix(self):
        """Rebuild the embeddings matrix from stored documents."""
        if not self.documents:
            self.embeddings = None
            return

        embeddings_list = []
        for doc_id in self.document_ids:
            document = self.documents[doc_id]
            if document.embedding:
                embeddings_list.append(document.embedding)

        if embeddings_list:
            self.embeddings = np.array(embeddings_list)

    def _calculate_similarities(self, query_embedding: np.ndarray) -> np.ndarray:
        """Calculate cosine similarities between query and all documents."""
        if self.embeddings is None:
            return np.array([])

        # Normalize embeddings
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        doc_norms = self.embeddings / np.linalg.norm(
            self.embeddings, axis=1, keepdims=True
        )

        # Calculate cosine similarities
        similarities = np.dot(doc_norms, query_norm)

        return similarities

    def clear(self):
        """Clear all documents from the vector store."""
        self.documents.clear()
        self.document_ids.clear()
        self.embeddings = None
        self.last_updated = datetime.now()

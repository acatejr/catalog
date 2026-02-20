from rank_bm25 import BM25Okapi
from catalog.core import ChromaVectorDB
from catalog.schema import USFSDocument


class HybridSearch:
    """Combines BM25 keyword search with ChromaDB vector search using Reciprocal Rank Fusion."""

    def __init__(self, vector_db: ChromaVectorDB):
        self.vector_db = vector_db
        self.bm25 = None
        self.doc_texts = []
        self.doc_ids = []
        self._build_bm25_index()

    def _build_bm25_index(self):
        """Build BM25 index from documents already stored in ChromaDB."""
        collection = self.vector_db.collection
        if collection.count() == 0:
            return

        all_docs = collection.get(include=["documents", "metadatas"])
        self.doc_ids = all_docs["ids"]
        self.doc_texts = all_docs["documents"]

        tokenized = [doc.lower().split() for doc in self.doc_texts]
        self.bm25 = BM25Okapi(tokenized)

    def _bm25_search(self, query: str, k: int) -> list[tuple[str, float]]:
        """Return top-k (doc_id, score) pairs from BM25."""
        if self.bm25 is None:
            return []

        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)

        scored_ids = list(zip(self.doc_ids, scores))
        scored_ids.sort(key=lambda x: x[1], reverse=True)
        return scored_ids[:k]

    def _rrf(
        self,
        vector_results: list[tuple[USFSDocument, float]],
        bm25_results: list[tuple[str, float]],
        k_constant: int = 60,
    ) -> list[tuple[str, float]]:
        """Reciprocal Rank Fusion. Returns list of (doc_id, rrf_score) sorted by score descending."""
        rrf_scores: dict[str, float] = {}

        for rank, (doc, _distance) in enumerate(vector_results):
            rrf_scores[doc.id] = rrf_scores.get(doc.id, 0.0) + 1.0 / (
                k_constant + rank + 1
            )

        for rank, (doc_id, _score) in enumerate(bm25_results):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + 1.0 / (
                k_constant + rank + 1
            )

        sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_results

    def query(self, qstn: str, nresults: int = 5) -> list[tuple[USFSDocument, float]]:
        """Run hybrid search and return results in the same format as ChromaVectorDB.query().

        :param qstn: The query text.
        :param nresults: Number of results to return.
        :return: List of (USFSDocument, rrf_score) tuples.
        """
        if not qstn:
            return []

        retrieve_k = nresults * 3

        vector_results = self.vector_db.query(qstn=qstn, nresults=retrieve_k)
        bm25_results = self._bm25_search(qstn, k=retrieve_k)

        fused = self._rrf(vector_results, bm25_results)
        top_ids = [doc_id for doc_id, _score in fused[:nresults]]
        top_scores = {doc_id: score for doc_id, score in fused[:nresults]}

        # Build USFSDocument objects from ChromaDB metadata
        collection_data = self.vector_db.collection.get(
            ids=top_ids, include=["metadatas"]
        )

        meta_by_id = {}
        for doc_id, meta in zip(collection_data["ids"], collection_data["metadatas"]):
            meta_by_id[doc_id] = meta

        results = []
        for doc_id in top_ids:
            meta = meta_by_id.get(doc_id)
            if meta is None:
                continue

            keywords_str = meta.get("keywords", "")
            doc = USFSDocument(
                id=meta.get("id", ""),
                title=meta.get("title"),
                abstract=meta.get("abstract"),
                purpose=meta.get("purpose"),
                src=meta.get("source") or meta.get("src"),
                keywords=keywords_str.split(",") if keywords_str else [],
                lineage=None,
            )
            results.append((doc, top_scores[doc_id]))

        return results

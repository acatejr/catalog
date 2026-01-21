import os
from rich import print as rprint
from catalog.lib import load_json
from catalog.schema import Document
from sentence_transformers import SentenceTransformer
import sqlite3
from pathlib import Path
import sqlite_vec
import logging
import json
import chromadb
from rank_bm25 import BM25Okapi
from dotenv import load_dotenv

load_dotenv()

# Setup logging                                                                                                                            
log_dir = Path("./logs")                                                                                                                   
log_dir.mkdir(exist_ok=True)                                                                                                               
logging.basicConfig(                                                                                                                       
    level=logging.INFO,                                                                                                                    
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",                                                                         
    filename=log_dir / "catalog.log",                                                                                                      
)          

logger = logging.getLogger(__name__)


class ChromaVectorDB:
    
    def __init__(self, src_catalog_file="data/catalog.json"):
        self.src_catalog_file = src_catalog_file
        self.client = chromadb.PersistentClient(path="./chromadb")
        self.collection = self.client.create_collection("documents", get_or_create=True)
        self.documents = []

    def load_document_metadata(self):
        json_file = Path(self.src_catalog_file)

        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.documents = [Document.model_validate(doc) for doc in data]
        except FileNotFoundError as e:
            rprint(f"[red]Source file {self.src_catalog_file} does not exist.[/red]")

    def load_documents(self):

        if not self.documents:
            self.load_document_metadata()
            rprint(
                f"Loaded {len(self.documents)} documents from {self.src_catalog_file}"
            )

        self.client.delete_collection(self.collection.name)
        self.collection = self.client.create_collection(
            name=self.collection.name, get_or_create=True
        )

        documents = []
        ids = []
        metadatas = []

        for idx, doc in enumerate(self.documents):
            title = doc.title or ""
            abstract = doc.abstract or ""
            purpose = doc.purpose or ""
            source = doc.src or ""


            ids.append(f"doc_{idx}")
            documents.append(
                f"Title: {title}\nAbstract: {abstract}\nPurpose: {purpose}\nSource: {source}\n"
            )
            metadatas.append(
                {
                    "id": doc.id,
                    "title": title,
                    "src": doc.src or "unknown",
                    "purpose": doc.purpose or "",
                    "keywords": ",".join(doc.keywords) if doc.keywords else "",
                }
            )

        self.collection.add(documents=documents, metadatas=metadatas, ids=ids)


    def query(self, qstn: str = None, nresults=5, k: int = None) -> None:
        """Query the collection. Supports both nresults and k parameters."""
        if k is not None:
            nresults = k
        if qstn is None:
            return None

        results = None
        if self.collection and self.collection.count() > 0:
            rprint(f"[green]You asked: '{qstn}[/green]'")
            raw_results = self.collection.query(
                query_texts=[qstn],  # Chroma will embed this for you
                n_results=nresults,  # how many results to return
            )
            # Normalize to match SqliteVectorDB format for HybridSearch
            if raw_results and raw_results.get("ids"):
                results = []
                ids = raw_results["ids"][0] if raw_results["ids"] else []
                distances = raw_results["distances"][0] if raw_results.get("distances") else []
                for i, doc_id in enumerate(ids):
                    # Extract numeric index from doc_id (e.g., "doc_123" -> 123)
                    idx = int(doc_id.split("_")[1]) if "_" in doc_id else i
                    dist = distances[i] if i < len(distances) else 0
                    results.append({"id": idx, "distance": dist})

        return results


class SqliteVectorDB:
    def __init__(self, db_path: str = "catalog.sqlite3"):
        self.src_catalog_file = "data/catalog.json"
        self.documents = []
        self.model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2", device="cpu"
        )
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.enable_load_extension(True)
        sqlite_vec.load(self.conn)

    def __exit__(self, exc_type, exc_value, traceback):
        if self.conn:
            self.conn.close()

    def read_metadata(self):
        if not os.path.exists(self.src_catalog_file):
            rprint(f"[red]Source file {self.src_catalog_file} does not exist.[/red]")
            return

        json_data = load_json(self.src_catalog_file)
        rprint(f"Loaded {len(json_data)} raw documents from {self.src_catalog_file}")

        return json_data

    def load_documents(self):
        documents = []

        with open(self.src_catalog_file, "r", encoding="utf-8") as f:
            data = json.load(f)

            documents = [Document.model_validate(doc) for doc in data]

        return documents

    def create_docs_db(self):
        with self.conn as conn:
            cusor = conn.cursor()
            cusor.execute("DROP TABLE IF EXISTS documents")

            sql = """CREATE VIRTUAL TABLE documents USING vec0(
                id TEXT NOT NULL PRIMARY KEY,
                title TEXT,
                abstract TEXT,
                keywords TEXT,
                purpose TEXT,
                src TEXT,
                lineage TEXT,
                embedding float[384]
            )"""

            cusor.execute(sql)

    def query_vector_table(self, query: str = None, limit: int = 5):
        results = None

        with self.conn as conn:
            cursor = conn.cursor()

            if query is None:
                query = """
                SELECT id, title FROM DOCUMENTS
                """
                results = cursor.execute(query).fetchall()
            else:
                query_embedding = self.model.encode([query], show_progress_bar=False)[0]
                results = cursor.execute(
                    f"""
                    SELECT
                        id,
                        title,
                        abstract,
                        keywords,
                        purpose,
                        src AS source,
                        lineage,
                        distance
                    FROM documents
                    WHERE embedding MATCH ?
                    ORDER BY distance
                    LIMIT {limit}
                    """,
                    [query_embedding.tobytes()],
                )

                columns = [col[0] for col in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]

            return results

    def query(self, query: str, k: int = 5):
        """Wrapper for query_vector_table to match HybridSearch interface."""
        return self.query_vector_table(query=query, limit=k)

    def format_lineage(self, lineage: list[dict]) -> str:
        formatted_lineage = []

        if not lineage:
            return ""

        for item in lineage:
            desc = item.get("description", "")
            date = item.get("date", "")

            formatted_lineage.append(f"Date: {date}, Description: {desc})")

        return ", ".join(formatted_lineage)

    def bulk_insert_documents(
        self, db_path: str = "catalog.sqlite3", limit=None
    ) -> None:
        documents = self.load_documents()  # load_json(self.src_catalog_file)

        if not documents:
            print("No documents to save.")
            return

        if limit is None or limit == 0:
            limit = len(documents)

        items = []
        for doc in documents[0:limit]:
            id = doc.id
            abstract = doc.abstract or ""
            title = doc.title or ""
            keywords = ",".join(kw for kw in doc.keywords) or ""
            purpose = doc.purpose or ""
            src = doc.src or ""
            lineage = self.format_lineage(doc.lineage)  # ",".join(doc.lineage) or ""

            combined_text = f"Title: {title}\nAbstract: {abstract}\nKeywords: {keywords}\nPurpose: {purpose}\nSource: {src}\nLineage: {lineage}"
            embeddings = self.model.encode([combined_text], show_progress_bar=False)[0]
            embeddings_bytes = embeddings.tobytes()

            items.append(
                (id, title, abstract, keywords, purpose, src, lineage, embeddings_bytes)
            )

        self.create_docs_db()

        sql = "INSERT INTO documents (id, title, abstract, keywords, purpose, src, lineage, embedding) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
        try:
            with self.conn as conn:
                cursor = conn.cursor()
                cursor.executemany(sql, items)

        except sqlite3.IntegrityError as e:
            logger.info(f"Error inserting {id}, Title: {title}: {e}")


class HybridSearch:
    def __init__(self, vector_db, documents):
        self.vector_db = vector_db
        tokenized = [doc.split() for doc in documents]
        self.bm25 = BM25Okapi(tokenized)

    def search(self, query, k=10, alpha=0.5):
        # Get vector results
        vector_results = self.vector_db.query(query, k=k*2)

        # Get BM25 results
        bm25_scores = self.bm25.get_scores(query.split())

        # Reciprocal rank fusion
        return self.fuse_results(vector_results, bm25_scores, k, alpha)

    def fuse_results(self, vector_results, bm25_scores, k=10, alpha=0.5, rrf_k=60):
        """
        Combine vector and BM25 results using Reciprocal Rank Fusion.

        Args:
            vector_results: List of dicts with 'id' and 'distance' from vector search
            bm25_scores: Array of BM25 scores for each document
            k: Number of results to return
            alpha: Weight for vector results (1-alpha for BM25)
            rrf_k: RRF constant (default 60) to prevent high ranks from dominating

        Returns:
            List of document indices sorted by fused score (descending)
        """
        fused_scores = {}

        # Process vector results (lower distance = better, so rank by distance ascending)
        if vector_results:
            sorted_vector = sorted(vector_results, key=lambda x: x.get("distance", 0))
            for rank, result in enumerate(sorted_vector):
                doc_id = result.get("id")
                if doc_id is not None:
                    rrf_score = alpha * (1 / (rrf_k + rank + 1))
                    fused_scores[doc_id] = fused_scores.get(doc_id, 0) + rrf_score

        # Process BM25 scores (higher score = better, so rank by score descending)
        sorted_bm25_indices = sorted(
            range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True
        )
        for rank, doc_idx in enumerate(sorted_bm25_indices):
            if bm25_scores[doc_idx] > 0:  # Only include docs with non-zero BM25 score
                rrf_score = (1 - alpha) * (1 / (rrf_k + rank + 1))
                fused_scores[doc_idx] = fused_scores.get(doc_idx, 0) + rrf_score

        # Sort by fused score descending and return top k
        sorted_results = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
        return [doc_id for doc_id, score in sorted_results[:k]]

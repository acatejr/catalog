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

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="./logs/catalog.log",
)

logger = logging.getLogger(__name__)


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

        with open(self.src_catalog_file, "r") as f:
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

        documents = self.load_documents() # load_json(self.src_catalog_file)

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
            lineage = self.format_lineage(doc.lineage) # ",".join(doc.lineage) or ""


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

if __name__ == "__main__":
    # vdb = SqliteVectorDB()
    # docs = vdb.load_documents()
    # rprint(f"Loaded {len(docs)} documents from {vdb.src_catalog_file}")
    # for doc in docs:
    #     for e in doc.lineage:
    #         rprint(type(e))
    pass

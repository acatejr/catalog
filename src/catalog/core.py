import os
from rich import print as rprint
from catalog.lib import load_json
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import sqlite3
from pathlib import Path
import sqlite_vec
import logging
from catalog.lib import clean_str
# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="./logs/catalog.log",
)

logger = logging.getLogger(__name__)

class GenVectorData:
    def __init__(self):
        self.src_catalog_file = "data/catalog.json"
        self.documents = []
        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device="cpu")

    def read_metadata(self):
        if not os.path.exists(self.src_catalog_file):
            rprint(f"[red]Source file {self.src_catalog_file} does not exist.[/red]")
            return

        json_data = load_json(self.src_catalog_file)
        rprint(f"Loaded {len(json_data)} raw documents from {self.src_catalog_file}")

        return json_data

    def process(self):
        model = SentenceTransformer("all-MiniLM-L6-v2")
        recursive_text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=65, chunk_overlap=0
        )

        raw_data = load_json(self.src_catalog_file)
        rprint(
            f"Loaded {len(raw_data)} raw documents from [cyan]{self.src_catalog_file}[/cyan]"
        )

        documents = []
        for doc in raw_data:
            id = doc.get("id")
            title = doc.get("title")
            description = doc.get("description")
            keywords = ",".join(kw for kw in doc.get("keywords")) or ""
            src = doc.get("src")
            combined_text = f"Title: {title}\nDescription: {description}\nKeywords: {keywords}\nSource: {src}"

            chunks = recursive_text_splitter.create_documents([combined_text])

            for idx, chunk in enumerate(chunks):
                metadata = {
                    "doc_id": id,  # or fsdoc.doc_id if that's the field name
                    "chunk_type": "title+description+keywords+source",
                    "chunk_index": idx,
                    "chunk_text": chunk.page_content,
                    "title": title,
                    "description": description,
                    "keywords": keywords,
                    "src": src,  # or another source identifier
                }

                embedding = model.encode(chunk.page_content)

                documents.append(
                    {
                        "embedding": embedding,
                        "metadata": metadata,
                        "title": title,
                        "description": description,
                    }
                )

        rprint(
            f"Loaded {len(documents)} documents ready for embedding and saving to a database."
        )
        self.documents = documents

    def create_docs_db(self):
        db = Path("./catalog.sqlite3")

        with sqlite3.connect(db) as conn:
            conn.enable_load_extension(True)
            sqlite_vec.load(conn)
            conn.enable_load_extension(False)

            cusor = conn.cursor()
            cusor.execute("DROP TABLE IF EXISTS documents")

            sql = """CREATE VIRTUAL TABLE documents USING vec0(
                id TEXT NOT NULL PRIMARY KEY,
                title TEXT,
                abstract TEXT,
                keywords TEXT,
                purpose TEXT,
                src TEXT,
                embedding float[384]
            )"""

            cusor.execute(sql)

    def save_docs_to_db(self, limit=None, db_path: str = "catalog.sqlite3") -> None:
        """
        Saves processed documents and embeddings to SQLite.
        """

        documents = load_json(self.src_catalog_file)

        if not documents:
            print("No documents to save.")
            return

        self.create_docs_db()

        db = Path(db_path)

        with sqlite3.connect(db) as conn:
            conn.enable_load_extension(True)
            sqlite_vec.load(conn)
            conn.enable_load_extension(False)

            cursor = conn.cursor()

            if limit is None or limit == 0:
                limit = len(documents)

            for doc in documents[0:limit]:
                id = doc.get("id")
                abstract = doc.get("abstract") or ""
                title = doc.get("title")
                keywords = ",".join(kw for kw in doc.get("keywords")) or ""
                purpose = doc.get("purpose") or ""
                src = doc.get("src") or ""

                combined_text = f"Title: {title}\nAbstract: {abstract}\nKeywords: {keywords}\nPurpose: {purpose}\nSource: {src}"
                embeddings = self.model.encode([combined_text])[0]
                embeddings_bytes = embeddings.tobytes()

                sql = "INSERT INTO documents (id, title, abstract, keywords, purpose, src, embedding) VALUES (?, ?, ?, ?, ?, ?, ?)"
                try:
                    cursor.execute(
                        sql,
                        (id, title, abstract, keywords, purpose, src, embeddings_bytes),
                    )
                except sqlite3.IntegrityError as e:
                    logger.info(f"Error inserting {id}, Title: {title}: {e}")
                    pass
                finally:
                    pass
                conn.commit()

    def query_vector_table(self, query: str = None, limit: int = 5):
        results = None

        db = Path("./catalog.sqlite3")

        with sqlite3.connect(db) as conn:
            conn.enable_load_extension(True)
            sqlite_vec.load(conn)
            conn.enable_load_extension(False)
            cursor = conn.cursor()

            if query is None:
                query = """
                SELECT id, title FROM DOCUMENTS
                """
                results = cursor.execute(query).fetchall()
            else:
                query_embedding = self.model.encode([query])[0]
                results = cursor.execute(
                    f"""
                    SELECT
                        id,
                        title,
                        abstract,
                        keywords,
                        purpose,
                        src,
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


    def bulk_insert_documents(self, db_path: str = "catalog.sqlite3", limit=None) -> None:

        documents = load_json(self.src_catalog_file)

        if not documents:
            print("No documents to save.")
            return

        if limit is None or limit == 0:
            limit = len(documents)

        items = []
        for doc in documents[0:limit]:
            id = doc.get("id")
            abstract = doc.get("abstract") or ""
            title = doc.get("title")
            keywords = ",".join(kw for kw in doc.get("keywords")) or ""
            purpose = doc.get("purpose") or ""
            src = doc.get("src") or ""

            combined_text = f"Title: {title}\nAbstract: {abstract}\nKeywords: {keywords}\nPurpose: {purpose}\nSource: {src}"
            embeddings = self.model.encode([combined_text], show_progress_bar=False)[0]
            embeddings_bytes = embeddings.tobytes()

            items.append(
                (id, title, abstract, keywords, purpose, src, embeddings_bytes)
            )

        db = Path(db_path)
        self.create_docs_db()

        sql = "INSERT INTO documents (id, title, abstract, keywords, purpose, src, embedding) VALUES (?, ?, ?, ?, ?, ?, ?)"
        try:
            with sqlite3.connect(db) as conn:
                conn.enable_load_extension(True)
                sqlite_vec.load(conn)
                conn.enable_load_extension(False)

                cursor = conn.cursor()
                cursor.executemany(sql, items)
                # conn.commit()
        except sqlite3.IntegrityError as e:
            logger.info(f"Error inserting {id}, Title: {title}: {e}")

if __name__ == "__main__":
    gvd = GenVectorData()
    # gvd.bulk_insert_documents()

    # gvd.process()
    # gvd.save_docs_to_db()

    # query = "Forest Health"
    # gvd.query_vector_table(query=query)

    # query = "Is there open data in the catalog?"
    query = "Is there erosion data in the catalog?"
    answers = gvd.query_vector_table(query=query)
    rprint(f"Found {len(answers)} answers for query: {query}")
    for answer in answers:
        rprint(f"Id: {answer["id"]}, Title: {answer["title"]}")

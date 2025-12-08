import os
import json
from rich import print as rprint
from catalog.lib import load_json
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import sqlite3
from pathlib import Path
import numpy as np

class GenVectorData:

    def __init__(self):
        self.src_catalog_file = "data/catalog.json"
        self.documents = []

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


    def save_docs_to_db(self,documents: list, db_path: str = "catalog.sqlite") -> None:
        """
        Saves processed documents and embeddings to SQLite.

        Args:
            documents: List of dictionaries containing 'embedding' and 'metadata'.
                    Expected structure per document:
                    {
                        "embedding": numpy.ndarray,
                        "metadata": {
                            "doc_id": str,
                            "chunk_index": int,
                            "chunk_text": str,
                            "chunk_type": str,
                            "title": str,
                            "description": str,
                            "keywords": str,
                            "src": str
                        },
                        ...
                    }
            db_path: Path to the SQLite database file.
        """
        if not documents:
            print("No documents to save.")
            return

        # Ensure we use the correct path relative to CWD if not absolute
        db_file = Path(db_path)

        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # Create table if it doesn't exist (using the updated schema)
        # We drop the table first to ensure schema matches the new requirements.
        # This allows the schema to update if it was missing columns previously.
        cursor.execute("DROP TABLE IF EXISTS documents")

        create_table_sql = """
        CREATE TABLE documents (
            id TEXT NOT NULL PRIMARY KEY,
            doc_id TEXT,
            chunk_index INTEGER,
            chunk_text TEXT,
            chunk_type TEXT,
            title TEXT,
            description TEXT,
            keywords TEXT,
            src TEXT,
            embedding BLOB
        );
        """
        cursor.execute(create_table_sql)

        print(f"Saving {len(documents)} documents to {db_path}...")

        count = 0
        for doc in documents:
            meta = doc["metadata"]
            embedding = doc["embedding"]

            # Create a unique ID for the chunk
            unique_id = f"{meta['doc_id']}_{meta['chunk_index']}"

            # Serialize embedding
            if hasattr(embedding, 'tobytes'):
                embedding_blob = embedding.tobytes()
            elif isinstance(embedding, list):
                embedding_blob = np.array(embedding, dtype=np.float32).tobytes()
            else:
                # Fallback or error
                embedding_blob = np.array(embedding).tobytes()

            try:
                cursor.execute(
                    """
                    INSERT INTO documents (
                        id, doc_id, chunk_index, chunk_text, chunk_type,
                        title, description, keywords, src, embedding
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        unique_id,
                        meta.get("doc_id"),
                        meta.get("chunk_index"),
                        meta.get("chunk_text"),
                        meta.get("chunk_type"),
                        meta.get("title"),
                        meta.get("description"),
                        meta.get("keywords"),
                        meta.get("src"),
                        embedding_blob
                    )
                )
                count += 1
            except sqlite3.IntegrityError as e:
                print(f"Error inserting {unique_id}: {e}")

        conn.commit()
        conn.close()
        print(f"Successfully saved {count} chunks to database.")


if __name__ == "__main__":
    gvd = GenVectorData()
    gvd.process()
    gvd.save_docs_to_db(gvd.documents)


"""

class GenVectorData:
    def __init__(self):
        self.src_catalog_file = "data/catalog.json"
        self.documents = []

    def load_and_validate_documents(self):

        try:
            raw_data = load_json(self.src_catalog_file)
            rprint(f"Loaded {len(raw_data)} raw documents from [cyan]{self.src_catalog_file}[/cyan]")
        except FileNotFoundError:
            rprint(f"[red]Source file {self.src_catalog_file} does not exist.[/red]")
            rprint("[yellow]Hint: Run the 'get-docs' command first.[/yellow]")
            return

        validated_docs = []
        for item in raw_data:
            source = item.get("source")
            try:
                if source == DataSource.FSGEODATA:
                    doc = CatalogDocument.from_fsgeodata(item)
                elif source == DataSource.GDD:
                    doc = CatalogDocument.from_gdd(item)
                elif source == DataSource.RDA:
                    doc = CatalogDocument.from_rda(item)
                else:
                    continue  # Or handle unknown sources
                validated_docs.append(doc)
            except Exception as e:
                rprint(f"[yellow]Skipping a document due to validation error: {e}[/yellow]")
s
        self.documents = validated_docs
        rprint(f"Successfully validated {len(self.documents)} documents.")

    def process(self):

        self.load_and_validate_documents()
        if not self.documents:
            rprint("[red]No documents to process.[/red]")
            return

        # --- Chunking Strategy 1: Document-Level Chunks (Recommended to start) ---
        # Here, each "chunk" is the full text content of a single document.
        # This is great for keeping the context of each item together.
        document_chunks = []
        for doc in self.documents:
            # Using the `primary_description` property from your schema is a good choice.
            # We can enrich it with other metadata.
            text_content = (
                f"Title: {doc.title}\n"
                f"Description: {doc.primary_description}\n"
                f"Keywords: {', '.join(doc.keywords)}\n"
                f"Source: {doc.source.value}"
            )
            document_chunks.append(text_content)

        rprint(f"\nGenerated {len(document_chunks)} document-level chunks.")
        # You can now pass `document_chunks` to an embedding model.
        # Example: model.encode(document_chunks)

        # --- Chunking Strategy 2: Recursive Character Splitting ---
        # This is useful for very long documents.
        # The chunk_size should be tuned based on your embedding model's context window.
        recursive_splitter = RecursiveCharacterTextSplitter(
            chunk_size=512, chunk_overlap=50
        )
        split_chunks = recursive_splitter.split_text("\n\n".join(document_chunks))
        rprint(f"Split into {len(split_chunks)} recursive chunks (size=512, overlap=50).")


if __name__ == "__main__":
    gvd = GenVectorData()


"""

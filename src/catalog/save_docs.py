import sqlite3
from pathlib import Path
import numpy as np

def save_docs_to_db(documents: list, db_path: str = "catalog.sqlite") -> None:
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

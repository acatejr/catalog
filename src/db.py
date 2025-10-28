import os, json
import psycopg2
from dotenv import load_dotenv
from typing import List
from schema import USFSDocument

load_dotenv()


dbname = os.environ.get("POSTGRES_DB")
dbuser = os.environ.get("POSTGRES_USER")
dbpass = os.environ.get("POSTGRES_PASSWORD")
dbhost = os.environ.get("POSTGRES_HOST")

pg_connection_string = f"dbname={dbname} user={dbuser} password={dbpass} host={dbhost}"


def load_documents_from_json(json_path: str) -> List[USFSDocument]:
    with open(json_path, "r") as f:
        data = json.load(f)
    # If the JSON is a list of dicts:
    return [USFSDocument(**item) for item in data]


def empty_documents_table():
    """
    Deletes all records from the 'documents' table in the vector database and performs a full vacuum to reclaim storage if the deletion was successful.

    This function connects to the PostgreSQL database using the provided connection string, removes all entries from the 'documents' table, and commits the transaction. If the deletion is successful, it then performs a 'VACUUM FULL' operation on the table to optimize storage and performance.

    Raises:
        psycopg2.DatabaseError: If there is an error connecting to the database or executing the SQL commands.
    """

    result = None
    with psycopg2.connect(pg_connection_string) as conn:
        cur = conn.cursor()
        result = cur.execute("DELETE FROM documents")
        conn.commit()
        cur.close()

    if result:
        with psycopg2.connect(pg_connection_string) as conn:
            cur = conn.cursor()
            cur.execute("VACUUM FULL documents")
            conn.commit()
            cur.close()


def count_documents():
    """
    Counts the number of documents in the 'documents' table of the vector database.

    Returns:
        int: The count of documents in the table.
    """

    doc_count = None

    with psycopg2.connect(pg_connection_string) as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM documents")
        rec = cur.fetchone()
        doc_count = rec[0] if rec else 0
        cur.close()

    return doc_count


def save_to_vector_db(embedding, metadata, title="", desc=""):
    """
    Saves a document's embedding and metadata to the 'documents' table in the vector database.
    """

    with psycopg2.connect(pg_connection_string) as conn:
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO documents (doc_id, chunk_type, chunk_index, chunk_text, embedding, title, description, keywords, data_source) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    metadata["doc_id"],
                    metadata["chunk_type"],
                    metadata["chunk_index"],
                    metadata["chunk_text"],
                    embedding.tolist(),
                    title,
                    desc,
                    metadata["keywords"],
                    metadata["src"],
                ),
            )
        except psycopg2.errors.UniqueViolation as e:
            print(f"IntegrityError: {e}, doc_id: {metadata['doc_id']}")
            conn.rollback()

        cur.close()
        conn.commit()


def bulk_upsert_to_vector_db(records: List[dict], use_upsert: bool = False):
    """
    Bulk insert/upsert documents to the 'documents' table using a single SQL transaction.

    Args:
        records: List of dictionaries containing document data with keys:
                 - embedding: numpy array or list
                 - metadata: dict with doc_id, chunk_type, chunk_index, chunk_text, keywords, src
                 - title: str
                 - description: str
        use_upsert: If True, uses ON CONFLICT to update existing records.
                    Requires UNIQUE constraint on (doc_id, chunk_index).
                    Run migrations/001_add_unique_constraint.sql first.

    Note: Set use_upsert=True only after adding the unique constraint:
    ALTER TABLE documents ADD CONSTRAINT documents_doc_id_chunk_idx_key
    UNIQUE (doc_id, chunk_index);
    """
    if not records:
        return

    with psycopg2.connect(pg_connection_string) as conn:
        try:
            cur = conn.cursor()

            # Prepare data for bulk insert
            values = []
            for record in records:
                embedding = record["embedding"]
                metadata = record["metadata"]
                title = record.get("title", "")
                desc = record.get("description", "")

                values.append(
                    (
                        metadata["doc_id"],
                        metadata["chunk_type"],
                        metadata["chunk_index"],
                        metadata["chunk_text"],
                        embedding.tolist()
                        if hasattr(embedding, "tolist")
                        else embedding,
                        title,
                        desc,
                        metadata["keywords"],
                        metadata["src"],
                    )
                )

            # Use execute_values for efficient bulk insert
            from psycopg2.extras import execute_values

            if use_upsert:
                # True upsert - requires unique constraint
                sql = """
                    INSERT INTO documents (doc_id, chunk_type, chunk_index, chunk_text, embedding, title, description, keywords, data_source)
                    VALUES %s
                    ON CONFLICT (doc_id, chunk_index)
                    DO UPDATE SET
                        chunk_type = EXCLUDED.chunk_type,
                        chunk_text = EXCLUDED.chunk_text,
                        embedding = EXCLUDED.embedding,
                        title = EXCLUDED.title,
                        description = EXCLUDED.description,
                        keywords = EXCLUDED.keywords,
                        data_source = EXCLUDED.data_source
                """
            else:
                # Simple bulk insert - faster but will fail on duplicates
                sql = """
                    INSERT INTO documents (doc_id, chunk_type, chunk_index, chunk_text, embedding, title, description, keywords, data_source)
                    VALUES %s
                """

            execute_values(cur, sql, values, page_size=100)

            conn.commit()
            cur.close()

        except Exception as e:
            print(f"Error during bulk {'upsert' if use_upsert else 'insert'}: {e}")
            conn.rollback()
            raise


def search_docs(query_embedding: list[float], limit: int = 10) -> list:
    """
    Search documents using vector similarity with the query embedding.

    Args:
        query_embedding: The embedding vector to search with
        limit: Maximum number of documents to return (default: 10)

    Returns:
        List of dictionaries containing document information and similarity scores
    """

    if not query_embedding:
        return []

    docs = []

    try:
        with psycopg2.connect(pg_connection_string) as conn:
            cur = conn.cursor()

            # SQL query using cosine similarity for vector search
            # The <=> operator computes cosine distance (1 - cosine similarity)
            # Lower distance means higher similarity
            if limit is None:
                sql_query = """
                    SELECT id, title, description, keywords, 1 - (embedding <=> %s::vector) AS similarity_score
                    FROM documents
                    WHERE embedding IS NOT NULL
                    ORDER BY embedding <=> %s::vector;
                    """
            else:
                sql_query = """
                    SELECT id, title, description, keywords, 1 - (embedding <=> %s::vector) AS similarity_score
                    FROM documents
                    WHERE embedding IS NOT NULL
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s;
                    """

            # Execute the query with the embedding vector
            cur.execute(sql_query, (query_embedding, query_embedding, limit))

            # Fetch results and convert to list of dictionaries
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()

            for row in rows:
                doc_dict = dict(zip(columns, row))
                docs.append(doc_dict)

            cur.close()

    except Exception as e:
        print(f"Error searching documents: {e}")
        return []

    return docs


def get_all_distinct_keywords() -> list[str]:
    """
    Get a list of all distinct keywords in the database.

    Returns:
        List of unique keyword strings, sorted alphabetically
    """
    try:
        with psycopg2.connect(pg_connection_string) as conn:
            cur = conn.cursor()

            cur.execute("""
                SELECT DISTINCT unnest(keywords) as keyword
                FROM documents
                WHERE keywords IS NOT NULL AND array_length(keywords, 1) > 0
                ORDER BY keyword
            """)

            results = cur.fetchall()
            cur.close()

            return [row[0] for row in results]

    except Exception as e:
        print(f"Error getting distinct keywords: {e}")
        return []


def get_top_distinct_keywords(limit: int = 10) -> list[str]:
    """
    Get a list of the most frequent distinct keywords in the database.

    Args:
        limit: Maximum number of keywords to return (default: 50)

    Returns:
        List of top keyword strings, sorted by frequency descending
    """
    try:
        with psycopg2.connect(pg_connection_string) as conn:
            cur = conn.cursor()

            sql = f"""
            select kw, count(kw) as freq from (
	            select unnest(keywords) as kw from documents d
            )
            group by kw
            order by count(kw) desc
            limit {str(limit)};
            """

            cur.execute(sql)
            results = cur.fetchall()

            return [row[0] for row in results]

    except Exception as e:
        print(f"Error getting top distinct keywords: {e}")
        return []
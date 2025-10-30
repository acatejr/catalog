# db.py (improved structure)
import logging
from dataclasses import dataclass
import time
from typing import List, Optional
from functools import wraps
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv
import os
# Use execute_values for efficient bulk insert
from psycopg2.extras import execute_values


load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Database connection configuration."""
    dbname: str
    user: str
    password: str
    host: str
    port: int = 5432
    pool_min: int = 1
    pool_max: int = 10
    bulk_insert_page_size: int = 100

    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """Load configuration from environment variables."""
        load_dotenv()

        config = cls(
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host=os.getenv("POSTGRES_HOST"),
        )
        config.validate()
        return config

    def validate(self) -> None:
        """Validate that all required fields are set."""
        missing = [field for field in ["dbname", "user", "password", "host"]
                   if not getattr(self, field)]
        if missing:
            raise ValueError(f"Missing required config: {missing}")

    def get_connection_string(self) -> str:
        """Build psycopg2 connection string."""
        return f"dbname={self.dbname} user={self.user} password={self.password} host={self.host} port={self.port}"


class DatabaseConnection:
    """Manages database connection pool."""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.pool = pool.SimpleConnectionPool(
            minconn=config.pool_min,
            maxconn=config.pool_max,
            dbname=config.dbname,
            user=config.user,
            password=config.password,
            host=config.host,
            port=config.port
        )

    def get_connection(self):
        """Get connection from pool."""
        return self.pool.getconn()

    def return_connection(self, conn):
        """Return connection to pool."""
        self.pool.putconn(conn)

    def close_all(self):
        """Close all connections in pool."""
        self.pool.closeall()


# Global database instance (initialized on first use)
_db: Optional[DatabaseConnection] = None


def get_db() -> DatabaseConnection:
    """Get database connection instance (lazy initialization)."""
    global _db
    if _db is None:
        config = DatabaseConfig.from_env()
        _db = DatabaseConnection(config)
    return _db


def retry_on_db_error(max_retries=3, delay=1):
    """Retry decorator for transient database errors."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except psycopg2.OperationalError as e:
                    if attempt == max_retries - 1:
                        raise
                    logger.warning(
                        f"Database error in {func.__name__}, "
                        f"retrying ({attempt + 1}/{max_retries}): {e}"
                    )
                    time.sleep(delay * (attempt + 1))
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Example refactored function
@retry_on_db_error(max_retries=3)
def count_documents() -> int:
    """
    Counts the number of documents in the 'documents' table.

    Returns:
        int: The count of documents in the table.

    Raises:
        psycopg2.Error: If database operation fails after retries.
    """
    db = get_db()
    conn = db.get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM documents")
            result = cur.fetchone()
            return result[0] if result else 0
    finally:
        db.return_connection(conn)


@retry_on_db_error(max_retries=3)
def empty_documents_table():
    """
    Deletes all records from the 'documents' table in the vector database and performs a full vacuum to reclaim storage if the deletion was successful.

    This function connects to the PostgreSQL database using the provided connection string, removes all entries from the 'documents' table, and commits the transaction. If the deletion is successful, it then performs a 'VACUUM FULL' operation on the table to optimize storage and performance.

    Raises:
        psycopg2.DatabaseError: If there is an error connecting to the database or executing the SQL commands.
    """

    db = get_db()
    conn = db.get_connection()

    try:
        with conn.cursor() as cur:
            result = cur.execute("DELETE FROM documents")
            conn.commit()

        if result:
            cur.execute("VACUUM FULL documents")
            conn.commit()

    finally:
        db.return_connection(conn)


@retry_on_db_error(max_retries=3)
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

    db = get_db()
    conn = db.get_connection()

    try:
        with conn.cursor() as cur:

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

    finally:
        db.return_connection(conn)


@retry_on_db_error(max_retries=3)
def db_health_check() -> list:
    db = get_db()
    conn = db.get_connection()

    try:
        with conn.cursor() as cur:
            sql = """
                SELECT COUNT(*)
                FROM documents
                LIMIT 1
            """

            cur.execute(sql)
            results = cur.fetchall()
            return results[0]

    finally:
        db.return_connection(conn)

    # try:
    #     with psycopg2.connect(_db.config.get_connection_string()) as conn:
    #         cur = conn.cursor()

    #         sql = """
    #             SELECT COUNT(*)
    #             FROM documents
    #             LIMIT 1
    #         """

    #         cur.execute(sql)
    #         results = cur.fetchall()
    #         cur.close()

    #     return results[0]

    # except Exception as e:
    #     print(f"Error checking db health: {e}")
    #     return []

# def search_docs(query_embedding: list[float], limit: int = 10) -> list:
#     """
#     Search documents using vector similarity with the query embedding.

#     Args:
#         query_embedding: The embedding vector to search with
#         limit: Maximum number of documents to return (default: 10)

#     Returns:
#         List of dictionaries containing document information and similarity scores
#     """

#     if not query_embedding:
#         return []

#     docs = []

#     try:
#         with psycopg2.connect(_db.config.get_connection_string()) as conn:
#             cur = conn.cursor()

#             # SQL query using cosine similarity for vector search
#             # The <=> operator computes cosine distance (1 - cosine similarity)
#             # Lower distance means higher similarity
#             if limit is None:
#                 sql_query = """
#                     SELECT id, title, description, keywords, 1 - (embedding <=> %s::vector) AS similarity_score
#                     FROM documents
#                     WHERE embedding IS NOT NULL
#                     ORDER BY embedding <=> %s::vector;
#                     """
#             else:
#                 sql_query = """
#                     SELECT id, title, description, keywords, 1 - (embedding <=> %s::vector) AS similarity_score
#                     FROM documents
#                     WHERE embedding IS NOT NULL
#                     ORDER BY embedding <=> %s::vector
#                     LIMIT %s;
#                     """

#             # Execute the query with the embedding vector
#             cur.execute(sql_query, (query_embedding, query_embedding, limit))

#             # Fetch results and convert to list of dictionaries
#             columns = [desc[0] for desc in cur.description]
#             rows = cur.fetchall()

#             for row in rows:
#                 doc_dict = dict(zip(columns, row))
#                 docs.append(doc_dict)

#             cur.close()

#     except Exception as e:
#         print(f"Error searching documents: {e}")
#         return []

#     return docs


# def get_all_distinct_keywords() -> list[str]:
#     """
#     Get a list of all distinct keywords in the database.

#     Returns:
#         List of unique keyword strings, sorted alphabetically
#     """
#     try:
#         with psycopg2.connect(_db.config.get_connection_string()) as conn:
#             cur = conn.cursor()

#             cur.execute("""
#                 SELECT DISTINCT unnest(keywords) as keyword
#                 FROM documents
#                 WHERE keywords IS NOT NULL AND array_length(keywords, 1) > 0
#                 ORDER BY keyword
#             """)

#             results = cur.fetchall()
#             cur.close()

#             return [row[0] for row in results]

#     except Exception as e:
#         print(f"Error getting distinct keywords: {e}")
#         return []


# def get_top_distinct_keywords(limit: int = 10) -> list[str]:
#     """
#     Get a list of the most frequent distinct keywords in the database.

#     Args:
#         limit: Maximum number of keywords to return (default: 50)

#     Returns:
#         List of top keyword strings, sorted by frequency descending
#     """
#     try:
#         with psycopg2.connect(_db.config.get_connection_string()) as conn:
#             cur = conn.cursor()

#             sql = f"""
#             select kw, count(kw) as freq from (
# 	            select unnest(keywords) as kw from documents d
#             )
#             group by kw
#             order by count(kw) desc
#             limit {str(limit)};
#             """

#             cur.execute(sql)
#             results = cur.fetchall()

#             keywords = []
#             for row in results:
#                 rec = {"keyword": row[0], "count": row[1]}
#                 keywords.append(rec)

#             return keywords

#     except Exception as e:
#         print(f"Error getting top distinct keywords: {e}")
#         return []


# def get_all_keywords(limit: Optional[int] = None) -> list[str]:
#     """
#     Get ALL keywords including duplicates from the database.

#     Args:
#         limit: Maximum number of keywords to return

#     Returns:
#         List of all keyword strings (may contain duplicates)
#     """
#     try:
#         with psycopg2.connect(_db.config.get_connection_string()) as conn:
#             cur = conn.cursor()

#             if limit:
#                 sql = """
#                     SELECT unnest(keywords) as keyword
#                     FROM documents
#                     WHERE keywords IS NOT NULL AND array_length(keywords, 1) > 0
#                     LIMIT %s
#                 """
#                 cur.execute(sql, (limit,))
#             else:
#                 sql = """
#                     SELECT unnest(keywords) as keyword
#                     FROM documents
#                     WHERE keywords IS NOT NULL AND array_length(keywords, 1) > 0
#                 """
#                 cur.execute(sql)

#             results = cur.fetchall()
#             cur.close()

#             return [row[0] for row in results]

#     except Exception as e:
#         print(f"Error getting all keywords: {e}")
#         return []


# def get_keywords_with_counts(
#     limit: Optional[int] = None, sort: Optional[str] = None
# ) -> list[dict]:
#     """
#     Get distinct keywords with their frequency counts.

#     Args:
#         limit: Maximum number of keywords to return
#         sort: Sort order - 'alpha' for alphabetical, 'frequency' for most common

#     Returns:
#         List of dictionaries with 'keyword' and 'count' keys
#     """
#     try:
#         with psycopg2.connect(_db.config.get_connection_string()) as conn:
#             cur = conn.cursor()

#             # Build SQL with appropriate sorting
#             if sort == "alpha":
#                 order_clause = "ORDER BY keyword"
#             else:  # default to frequency
#                 order_clause = "ORDER BY count DESC"

#             sql = f"""
#                 SELECT keyword, COUNT(*) as count
#                 FROM (
#                     SELECT unnest(keywords) as keyword
#                     FROM documents
#                     WHERE keywords IS NOT NULL AND array_length(keywords, 1) > 0
#                 ) AS all_keywords
#                 GROUP BY keyword
#                 {order_clause}
#             """

#             if limit:
#                 sql += f" LIMIT {limit}"

#             cur.execute(sql)
#             results = cur.fetchall()
#             cur.close()

#             return [{"keyword": row[0], "count": row[1]} for row in results]

#     except Exception as e:
#         print(f"Error getting keywords with counts: {e}")
#         return []

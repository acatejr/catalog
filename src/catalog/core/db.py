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
    def from_env(cls) -> "DatabaseConfig":
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
        missing = [
            field
            for field in ["dbname", "user", "password", "host"]
            if not getattr(self, field)
        ]
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
            port=config.port,
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


@retry_on_db_error(max_retries=3)
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
    db = get_db()
    conn = db.get_connection()

    try:
        with conn.cursor() as cur:
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

    finally:
        db.return_connection(conn)

    return docs


@retry_on_db_error(max_retries=3)
def get_all_distinct_keywords() -> list[str]:
    """
    Get a list of all distinct keywords in the database.

    Returns:
        List of unique keyword strings, sorted alphabetically
    """

    db = get_db()
    conn = db.get_connection()

    try:
        with conn.cursor() as cur:
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
        logger.error(f"Error getting all distinct keywords: {e}")
        return []

    finally:
        db.return_connection(conn)


@retry_on_db_error(max_retries=3)
def get_top_distinct_keywords(limit: int = 10) -> list[str]:
    """
    Get a list of the most frequent distinct keywords in the database.

    Args:
        limit: Maximum number of keywords to return (default: 50)

    Returns:
        List of top keyword strings, sorted by frequency descending
    """

    db = get_db()
    conn = db.get_connection()

    try:
        with conn.cursor() as cur:
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

            keywords = []
            for row in results:
                rec = {"keyword": row[0], "count": row[1]}
                keywords.append(rec)

            return keywords

    except Exception as e:
        logger.error(f"Error getting top distinct keywords: {e}")
        return []

    finally:
        db.return_connection(conn)


@retry_on_db_error(max_retries=3)
def get_all_keywords(limit: Optional[int] = None) -> list[str]:
    """
    Get ALL keywords including duplicates from the database.

    Args:
        limit: Maximum number of keywords to return

    Returns:
        List of all keyword strings (may contain duplicates)
    """
    db = get_db()
    conn = db.get_connection()

    try:
        with conn.cursor() as cur:
            if limit:
                sql = """
                    SELECT unnest(keywords) as keyword
                    FROM documents
                    WHERE keywords IS NOT NULL AND array_length(keywords, 1) > 0
                    LIMIT %s
                """
                cur.execute(sql, (limit,))
            else:
                sql = """
                    SELECT unnest(keywords) as keyword
                    FROM documents
                    WHERE keywords IS NOT NULL AND array_length(keywords, 1) > 0
                """
                cur.execute(sql)

            results = cur.fetchall()
            cur.close()

            return [row[0] for row in results]

    except Exception as e:
        logger.error(f"Error getting all keywords: {e}")
        return []

    finally:
        db.return_connection(conn)


@retry_on_db_error(max_retries=3)
def get_keywords_with_counts(
    limit: Optional[int] = None, sort: Optional[str] = None
) -> list[dict]:
    """
    Get distinct keywords with their frequency counts.

    Args:
        limit: Maximum number of keywords to return
        sort: Sort order - 'alpha' for alphabetical, 'frequency' for most common

    Returns:
        List of dictionaries with 'keyword' and 'count' keys
    """
    db = get_db()
    conn = db.get_connection()

    try:
        with conn.cursor() as cur:
            # Build SQL with appropriate sorting
            if sort == "alpha":
                order_clause = "ORDER BY keyword"
            else:  # default to frequency
                order_clause = "ORDER BY count DESC"

            sql = f"""
                SELECT keyword, COUNT(*) as count
                FROM (
                    SELECT unnest(keywords) as keyword
                    FROM documents
                    WHERE keywords IS NOT NULL AND array_length(keywords, 1) > 0
                ) AS all_keywords
                GROUP BY keyword
                {order_clause}
            """

            if limit:
                sql += f" LIMIT {limit}"

            cur.execute(sql)
            results = cur.fetchall()
            cur.close()

            return [{"keyword": row[0], "count": row[1]} for row in results]

    except Exception as e:
        logger.error(f"Error getting keywords with counts: {e}")
        return []

    finally:
        db.return_connection(conn)


@retry_on_db_error(max_retries=3)
def get_distinct_keywords_only(
    limit: Optional[int] = None, sort: Optional[str] = None
) -> list[str]:
    """
    Get distinct keywords without counts.

    Args:
        limit: Maximum number of keywords to return
        sort: Sort order - 'alpha' for alphabetical, 'frequency' for most common

    Returns:
        List of unique keyword strings
    """
    db = get_db()
    conn = db.get_connection()

    try:
        with conn.cursor() as cur:
            # Build SQL with appropriate sorting
            # if sort == "alpha":
            #     order_clause = "ORDER BY keyword"
            # else:  # default to frequency
            #     order_clause = "ORDER BY count DESC"

            sql = """
                SELECT keyword
                FROM (
                    SELECT unnest(keywords) as keyword
                    FROM documents
                    WHERE keywords IS NOT NULL AND array_length(keywords, 1) > 0
                ) AS all_keywords
                GROUP BY keyword
                ORDER BY keyword
            """

            if limit:
                sql += f" LIMIT {limit}"

            cur.execute(sql)
            results = cur.fetchall()
            cur.close()

            return [row[0] for row in results]

    except Exception as e:
        logger.error(f"Error getting distinct keywords only: {e}")
        return []

    finally:
        db.return_connection(conn)


# ============================================================================
# EAINFO (Entity and Attribute Information) FUNCTIONS
# ============================================================================


@retry_on_db_error(max_retries=3)
def save_eainfo(eainfo: "EntityAttributeInfo") -> int:
    """
    Save an EntityAttributeInfo instance to the database.

    Args:
        eainfo: EntityAttributeInfo instance to save

    Returns:
        int: The ID of the created eainfo record

    Raises:
        psycopg2.Error: If database operation fails after retries

    Note:
        Requires the eainfo tables to be created first. Run sql/migrations/001_add_eainfo_tables.sql
    """
    import json

    db = get_db()
    conn = db.get_connection()

    try:
        with conn.cursor() as cur:
            # Insert root eainfo record
            cur.execute(
                """
                INSERT INTO eainfo (overview, citation, parsed_at, source_file)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """,
                (
                    eainfo.overview,
                    eainfo.citation,
                    eainfo.parsed_at,
                    eainfo.source_file,
                ),
            )

            eainfo_id = cur.fetchone()[0]
            logger.info(f"Created eainfo record with id={eainfo_id}")

            # If detailed information exists, save it
            if eainfo.has_detailed_info and eainfo.detailed:
                # Insert entity_type
                cur.execute(
                    """
                    INSERT INTO entity_type (eainfo_id, label, definition, definition_source)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """,
                    (
                        eainfo_id,
                        eainfo.detailed.entity_type.label,
                        eainfo.detailed.entity_type.definition,
                        eainfo.detailed.entity_type.definition_source,
                    ),
                )

                entity_type_id = cur.fetchone()[0]
                logger.info(
                    f"Created entity_type record with id={entity_type_id} for '{eainfo.detailed.entity_type.label}'"
                )

                # Insert attributes and their domain values
                for attr in eainfo.detailed.attributes:
                    cur.execute(
                        """
                        INSERT INTO attribute (entity_type_id, label, definition, definition_source)
                        VALUES (%s, %s, %s, %s)
                        RETURNING id
                    """,
                        (
                            entity_type_id,
                            attr.label,
                            attr.definition,
                            attr.definition_source,
                        ),
                    )

                    attribute_id = cur.fetchone()[0]

                    # Insert domain values for this attribute
                    for domain_value in attr.domain_values:
                        # Convert domain value to dict and store as JSONB
                        domain_data = domain_value.model_dump(exclude={"type"})

                        cur.execute(
                            """
                            INSERT INTO attribute_domain (attribute_id, domain_type, domain_data)
                            VALUES (%s, %s, %s)
                        """,
                            (
                                attribute_id,
                                domain_value.type.value,
                                json.dumps(domain_data),
                            ),
                        )

                logger.info(
                    f"Saved {len(eainfo.detailed.attributes)} attributes for entity '{eainfo.detailed.entity_type.label}'"
                )

            conn.commit()
            return eainfo_id

    except Exception as e:
        conn.rollback()
        logger.error(f"Error saving eainfo: {e}")
        raise

    finally:
        db.return_connection(conn)


@retry_on_db_error(max_retries=3)
def get_eainfo_by_id(eainfo_id: int) -> Optional[dict]:
    """
    Retrieve eainfo record with all related data by ID.

    Args:
        eainfo_id: The ID of the eainfo record

    Returns:
        Dictionary containing eainfo data with nested entity, attributes, and domain values
        None if not found
    """
    db = get_db()
    conn = db.get_connection()

    try:
        with conn.cursor() as cur:
            # Get eainfo root record
            cur.execute(
                """
                SELECT id, overview, citation, parsed_at, source_file, created_at
                FROM eainfo
                WHERE id = %s
            """,
                (eainfo_id,),
            )

            eainfo_row = cur.fetchone()
            if not eainfo_row:
                return None

            result = {
                "id": eainfo_row[0],
                "overview": eainfo_row[1],
                "citation": eainfo_row[2],
                "parsed_at": eainfo_row[3],
                "source_file": eainfo_row[4],
                "created_at": eainfo_row[5],
                "entity_type": None,
            }

            # Get entity_type
            cur.execute(
                """
                SELECT id, label, definition, definition_source
                FROM entity_type
                WHERE eainfo_id = %s
            """,
                (eainfo_id,),
            )

            entity_row = cur.fetchone()
            if entity_row:
                entity_type_id = entity_row[0]
                result["entity_type"] = {
                    "id": entity_row[0],
                    "label": entity_row[1],
                    "definition": entity_row[2],
                    "definition_source": entity_row[3],
                    "attributes": [],
                }

                # Get attributes
                cur.execute(
                    """
                    SELECT id, label, definition, definition_source
                    FROM attribute
                    WHERE entity_type_id = %s
                """,
                    (entity_type_id,),
                )

                for attr_row in cur.fetchall():
                    attribute_id = attr_row[0]
                    attribute = {
                        "id": attr_row[0],
                        "label": attr_row[1],
                        "definition": attr_row[2],
                        "definition_source": attr_row[3],
                        "domain_values": [],
                    }

                    # Get domain values for this attribute
                    cur.execute(
                        """
                        SELECT domain_type, domain_data
                        FROM attribute_domain
                        WHERE attribute_id = %s
                    """,
                        (attribute_id,),
                    )

                    for domain_row in cur.fetchall():
                        attribute["domain_values"].append(
                            {"type": domain_row[0], "data": domain_row[1]}
                        )

                    result["entity_type"]["attributes"].append(attribute)

            return result

    except Exception as e:
        logger.error(f"Error getting eainfo by id: {e}")
        return None

    finally:
        db.return_connection(conn)


@retry_on_db_error(max_retries=3)
def get_eainfo_by_source_file(source_file: str) -> Optional[dict]:
    """
    Retrieve eainfo record by source file path.

    Args:
        source_file: The source file path

    Returns:
        Dictionary containing eainfo data or None if not found
    """
    db = get_db()
    conn = db.get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id
                FROM eainfo
                WHERE source_file = %s
                ORDER BY created_at DESC
                LIMIT 1
            """,
                (source_file,),
            )

            row = cur.fetchone()
            if row:
                return get_eainfo_by_id(row[0])
            return None

    except Exception as e:
        logger.error(f"Error getting eainfo by source file: {e}")
        return None

    finally:
        db.return_connection(conn)


@retry_on_db_error(max_retries=3)
def list_all_entities() -> list[dict]:
    """
    List all entity types in the database with their basic information.

    Returns:
        List of dictionaries with entity_type information
    """
    db = get_db()
    conn = db.get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    et.id,
                    et.label,
                    et.definition,
                    ea.source_file,
                    COUNT(a.id) as attribute_count
                FROM entity_type et
                JOIN eainfo ea ON et.eainfo_id = ea.id
                LEFT JOIN attribute a ON a.entity_type_id = et.id
                GROUP BY et.id, et.label, et.definition, ea.source_file
                ORDER BY et.label
            """)

            results = []
            for row in cur.fetchall():
                results.append(
                    {
                        "id": row[0],
                        "label": row[1],
                        "definition": row[2],
                        "source_file": row[3],
                        "attribute_count": row[4],
                    }
                )

            return results

    except Exception as e:
        logger.error(f"Error listing all entities: {e}")
        return []

    finally:
        db.return_connection(conn)


@retry_on_db_error(max_retries=3)
def empty_eainfo_tables():
    """
    Deletes all records from eainfo and all related tables (entity_type, attribute, attribute_domain).
    Uses CASCADE deletes automatically via foreign key constraints, so only need to delete from parent table.

    Raises:
        psycopg2.DatabaseError: If there is an error connecting to the database or executing the SQL commands.
    """
    db = get_db()
    conn = db.get_connection()

    try:
        with conn.cursor() as cur:
            # Delete from eainfo only - CASCADE will handle related tables
            # This is more efficient and safer than manual deletion
            cur.execute("DELETE FROM eainfo")
            conn.commit()
            logger.info("Emptied eainfo and all related tables via CASCADE.")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error emptying eainfo tables: {e}")
        raise
    finally:
        db.return_connection(conn)


# ============================================================================
# DATA LIBRARIAN ENHANCED FUNCTIONS
# ============================================================================


@retry_on_db_error(max_retries=3)
def search_entity_by_name(dataset_name: str) -> Optional[dict]:
    """
    Search for a dataset by name (exact or fuzzy match).

    Returns complete entity information including schema.
    Uses pg_trgm for fuzzy matching if exact match not found.

    Args:
        dataset_name: Name to search for

    Returns:
        Dict with entity metadata, attributes, and domain values
    """
    db = get_db()
    conn = db.get_connection()

    try:
        with conn.cursor() as cur:
            # Try exact match on dataset_name or label
            cur.execute(
                """
                SELECT id, label, definition, definition_source, eainfo_id,
                       dataset_name, display_name, dataset_type, source_system,
                       record_count, last_updated_at, metadata
                FROM entity_type
                WHERE LOWER(dataset_name) = LOWER(%s)
                   OR LOWER(label) = LOWER(%s)
            """,
                (dataset_name, dataset_name),
            )

            result = cur.fetchone()

            if not result:
                # Try fuzzy match using similarity (requires pg_trgm extension)
                cur.execute(
                    """
                    SELECT id, label, definition, definition_source, eainfo_id,
                           dataset_name, display_name, dataset_type, source_system,
                           record_count, last_updated_at, metadata,
                           GREATEST(
                               similarity(COALESCE(dataset_name, ''), %s),
                               similarity(label, %s)
                           ) as score
                    FROM entity_type
                    WHERE similarity(COALESCE(dataset_name, ''), %s) > 0.3
                       OR similarity(label, %s) > 0.3
                    ORDER BY score DESC
                    LIMIT 1
                """,
                    (dataset_name, dataset_name, dataset_name, dataset_name),
                )
                result = cur.fetchone()

            if not result:
                return None

            entity = {
                "id": result[0],
                "label": result[1],
                "definition": result[2],
                "definition_source": result[3],
                "eainfo_id": result[4],
                "dataset_name": result[5],
                "display_name": result[6],
                "dataset_type": result[7],
                "source_system": result[8],
                "record_count": result[9],
                "last_updated_at": result[10],
                "metadata": result[11],
            }

            # Get attributes with technical metadata
            entity["attributes"] = get_entity_attributes_extended(entity["id"])

            return entity

    finally:
        db.return_connection(conn)


@retry_on_db_error(max_retries=3)
def get_entity_attributes_extended(entity_type_id: int) -> list[dict]:
    """
    Get all attributes for an entity with technical metadata and domain values.

    Args:
        entity_type_id: ID of the entity type

    Returns:
        List of attribute dicts with complete metadata
    """
    db = get_db()
    conn = db.get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    a.id, a.label, a.definition, a.definition_source,
                    a.data_type, a.is_nullable, a.is_primary_key, a.is_foreign_key,
                    a.max_length, a.field_precision, a.field_scale, a.default_value,
                    a.completeness_percent, a.uniqueness_percent,
                    a.min_value, a.max_value, a.sample_values,
                    a.last_profiled_at, a.field_metadata
                FROM attribute a
                WHERE a.entity_type_id = %s
                ORDER BY
                    CASE WHEN a.is_primary_key THEN 0 ELSE 1 END,
                    a.id
            """,
                (entity_type_id,),
            )

            attributes = []
            for row in cur.fetchall():
                attr = {
                    "id": row[0],
                    "label": row[1],
                    "definition": row[2],
                    "definition_source": row[3],
                    "technical": {
                        "data_type": row[4],
                        "is_nullable": row[5],
                        "is_primary_key": row[6],
                        "is_foreign_key": row[7],
                        "max_length": row[8],
                        "precision": row[9],
                        "scale": row[10],
                        "default_value": row[11],
                    },
                    "quality": {
                        "completeness_percent": float(row[12]) if row[12] else None,
                        "uniqueness_percent": float(row[13]) if row[13] else None,
                        "min_value": row[14],
                        "max_value": row[15],
                        "sample_values": row[16],
                        "last_profiled_at": row[17],
                    },
                    "metadata": row[18],
                }

                # Get domain values for this attribute
                cur.execute(
                    """
                    SELECT domain_type, domain_data
                    FROM attribute_domain
                    WHERE attribute_id = %s
                """,
                    (row[0],),
                )

                attr["domain_values"] = [
                    {"type": dv[0], "data": dv[1]} for dv in cur.fetchall()
                ]

                attributes.append(attr)

            return attributes

    finally:
        db.return_connection(conn)


@retry_on_db_error(max_retries=3)
def get_field_lineage(dataset_name: str, field_name: str) -> Optional[dict]:
    """
    Get complete lineage for a specific field.

    Returns both upstream sources and downstream dependents.

    Args:
        dataset_name: Name of the dataset
        field_name: Name of the field

    Returns:
        Dict with upstream sources and downstream dependents
    """
    db = get_db()
    conn = db.get_connection()

    try:
        with conn.cursor() as cur:
            # Find the target attribute
            cur.execute(
                """
                SELECT a.id, et.label as entity_label
                FROM attribute a
                JOIN entity_type et ON a.entity_type_id = et.id
                WHERE (LOWER(et.dataset_name) = LOWER(%s) OR LOWER(et.label) = LOWER(%s))
                  AND LOWER(a.label) = LOWER(%s)
            """,
                (dataset_name, dataset_name, field_name),
            )

            result = cur.fetchone()
            if not result:
                return None

            attribute_id = result[0]
            entity_label = result[1]

            # Get upstream sources (where this field comes from)
            cur.execute(
                """
                SELECT
                    src_et.dataset_name,
                    src_et.label as entity_label,
                    src_a.label as field_name,
                    fl.transformation_type,
                    fl.transformation_logic,
                    fl.confidence_score,
                    fl.is_verified,
                    fl.notes
                FROM field_lineage fl
                JOIN attribute src_a ON fl.source_attribute_id = src_a.id
                JOIN entity_type src_et ON src_a.entity_type_id = src_et.id
                WHERE fl.target_attribute_id = %s
                ORDER BY fl.created_at
            """,
                (attribute_id,),
            )

            upstream = []
            for row in cur.fetchall():
                upstream.append(
                    {
                        "source_dataset": row[0] or row[1],
                        "source_field": row[2],
                        "transformation_type": row[3],
                        "transformation_logic": row[4],
                        "confidence_score": float(row[5]) if row[5] else None,
                        "is_verified": row[6],
                        "notes": row[7],
                    }
                )

            # Get downstream dependents (what uses this field)
            cur.execute(
                """
                SELECT
                    tgt_et.dataset_name,
                    tgt_et.label as entity_label,
                    tgt_a.label as field_name,
                    fl.transformation_type,
                    fl.transformation_logic,
                    fl.is_verified
                FROM field_lineage fl
                JOIN attribute tgt_a ON fl.target_attribute_id = tgt_a.id
                JOIN entity_type tgt_et ON tgt_a.entity_type_id = tgt_et.id
                WHERE fl.source_attribute_id = %s
                ORDER BY fl.created_at
            """,
                (attribute_id,),
            )

            downstream = []
            for row in cur.fetchall():
                downstream.append(
                    {
                        "target_dataset": row[0] or row[1],
                        "target_field": row[2],
                        "transformation_type": row[3],
                        "transformation_logic": row[4],
                        "is_verified": row[5],
                    }
                )

            return {
                "dataset": dataset_name,
                "entity_label": entity_label,
                "field": field_name,
                "upstream_sources": upstream,
                "downstream_dependents": downstream,
                "is_source_field": len(upstream) == 0,
            }

    finally:
        db.return_connection(conn)


@retry_on_db_error(max_retries=3)
def get_dataset_relationships(dataset_name: str) -> Optional[dict]:
    """
    Get all relationships for a dataset (foreign keys, references).

    Args:
        dataset_name: Name of the dataset

    Returns:
        Dict with outgoing and incoming relationships
    """
    db = get_db()
    conn = db.get_connection()

    try:
        with conn.cursor() as cur:
            # Find the entity
            cur.execute(
                """
                SELECT id FROM entity_type
                WHERE LOWER(dataset_name) = LOWER(%s) OR LOWER(label) = LOWER(%s)
            """,
                (dataset_name, dataset_name),
            )

            result = cur.fetchone()
            if not result:
                return None

            entity_id = result[0]

            # Get outgoing relationships (this dataset references others)
            cur.execute(
                """
                SELECT
                    from_a.label as from_field,
                    to_et.dataset_name as to_dataset,
                    to_et.label as to_entity_label,
                    to_a.label as to_field,
                    dr.relationship_type,
                    dr.relationship_name,
                    dr.is_enforced,
                    dr.notes
                FROM dataset_relationships dr
                JOIN attribute from_a ON dr.from_attribute_id = from_a.id
                JOIN entity_type to_et ON dr.to_entity_id = to_et.id
                JOIN attribute to_a ON dr.to_attribute_id = to_a.id
                WHERE dr.from_entity_id = %s
            """,
                (entity_id,),
            )

            outgoing = []
            for row in cur.fetchall():
                outgoing.append(
                    {
                        "from_field": row[0],
                        "to_dataset": row[1] or row[2],
                        "to_field": row[3],
                        "relationship_type": row[4],
                        "relationship_name": row[5],
                        "is_enforced": row[6],
                        "notes": row[7],
                    }
                )

            # Get incoming relationships (other datasets reference this one)
            cur.execute(
                """
                SELECT
                    from_et.dataset_name as from_dataset,
                    from_et.label as from_entity_label,
                    from_a.label as from_field,
                    to_a.label as to_field,
                    dr.relationship_type,
                    dr.relationship_name,
                    dr.is_enforced,
                    dr.notes
                FROM dataset_relationships dr
                JOIN entity_type from_et ON dr.from_entity_id = from_et.id
                JOIN attribute from_a ON dr.from_attribute_id = from_a.id
                JOIN attribute to_a ON dr.to_attribute_id = to_a.id
                WHERE dr.to_entity_id = %s
            """,
                (entity_id,),
            )

            incoming = []
            for row in cur.fetchall():
                incoming.append(
                    {
                        "from_dataset": row[0] or row[1],
                        "from_field": row[2],
                        "to_field": row[3],
                        "relationship_type": row[4],
                        "relationship_name": row[5],
                        "is_enforced": row[6],
                        "notes": row[7],
                    }
                )

            return {
                "dataset": dataset_name,
                "outgoing_relationships": outgoing,
                "incoming_relationships": incoming,
            }

    finally:
        db.return_connection(conn)


@retry_on_db_error(max_retries=3)
def list_all_datasets(
    dataset_type: Optional[str] = None,
    source_system: Optional[str] = None,
    limit: int = 100,
) -> list[dict]:
    """
    List all datasets with optional filtering.

    Args:
        dataset_type: Filter by dataset type
        source_system: Filter by source system
        limit: Maximum number of results

    Returns:
        List of dataset summary dicts
    """
    db = get_db()
    conn = db.get_connection()

    try:
        with conn.cursor() as cur:
            query = """
                SELECT
                    et.id,
                    COALESCE(et.dataset_name, et.label) as name,
                    et.display_name,
                    et.dataset_type,
                    et.source_system,
                    et.record_count,
                    et.last_updated_at,
                    COUNT(a.id) as attribute_count
                FROM entity_type et
                LEFT JOIN attribute a ON a.entity_type_id = et.id
                WHERE 1=1
            """

            params = []
            if dataset_type:
                query += " AND et.dataset_type = %s"
                params.append(dataset_type)

            if source_system:
                query += " AND et.source_system = %s"
                params.append(source_system)

            query += """
                GROUP BY et.id, et.dataset_name, et.label, et.display_name,
                         et.dataset_type, et.source_system, et.record_count, et.last_updated_at
                ORDER BY COALESCE(et.dataset_name, et.label)
                LIMIT %s
            """
            params.append(limit)

            cur.execute(query, params)

            datasets = []
            for row in cur.fetchall():
                datasets.append(
                    {
                        "id": row[0],
                        "name": row[1],
                        "display_name": row[2],
                        "dataset_type": row[3],
                        "source_system": row[4],
                        "record_count": row[5],
                        "last_updated_at": row[6],
                        "attribute_count": row[7],
                    }
                )

            return datasets

    finally:
        db.return_connection(conn)


@retry_on_db_error(max_retries=3)
def update_entity_extended_metadata(entity_type_id: int, metadata: dict) -> None:
    """
    Update extended metadata fields for an entity_type.

    Args:
        entity_type_id: ID of the entity_type to update
        metadata: Dictionary containing dataset_name, display_name, dataset_type, source_system, etc.
    """
    db = get_db()
    conn = db.get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE entity_type
                SET dataset_name = %s,
                    display_name = %s,
                    dataset_type = %s,
                    source_system = %s,
                    source_url = %s
                WHERE id = %s
            """,
                (
                    metadata.get("dataset_name"),
                    metadata.get("display_name"),
                    metadata.get("dataset_type"),
                    metadata.get("source_system"),
                    metadata.get("source_url"),
                    entity_type_id,
                ),
            )
            conn.commit()
            logger.info(
                f"Updated extended metadata for entity_type id={entity_type_id}"
            )

    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating entity extended metadata: {e}")
        raise

    finally:
        db.return_connection(conn)

# Database Configuration Improvements for db.py

## Major Issues

### 1. No Connection Pooling
**Location**: Throughout file - every function creates new connections

**Problem**: Every function creates a new database connection, which is expensive and inefficient.

**Solution**: Implement connection pooling using `psycopg2.pool`:

```python
from psycopg2 import pool

connection_pool = pool.SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    dbname=dbname,
    user=dbuser,
    password=dbpass,
    host=dbhost
)

def get_connection():
    return connection_pool.getconn()

def return_connection(conn):
    connection_pool.putconn(conn)
```

**Priority**: High - Significant performance impact

---

### 2. SQL Injection Vulnerability
**Location**: `src/catalog/core/db.py:288-294` in `get_top_distinct_keywords()`

**Problem**: Direct string interpolation of user input into SQL query:
```python
sql = f"""
    ...
    limit {str(limit)};
    """
```

**Solution**: Use parameterized queries:
```python
sql = """
    SELECT kw, count(kw) as freq
    FROM (
        SELECT unnest(keywords) as kw FROM documents d
    )
    GROUP BY kw
    ORDER BY count(kw) DESC
    LIMIT %s;
"""
cur.execute(sql, (limit,))
```

**Priority**: Critical - Security vulnerability

---

### 3. Global Connection String Built at Import Time
**Location**: `src/catalog/core/db.py:11-16`

**Problem**: Connection string is built when module loads. If environment variables aren't loaded yet, this fails silently with empty values.

```python
# Current implementation - runs at import time
dbname = os.environ.get("POSTGRES_DB")
dbuser = os.environ.get("POSTGRES_USER")
dbpass = os.environ.get("POSTGRES_PASSWORD")
dbhost = os.environ.get("POSTGRES_HOST")

pg_connection_string = f"dbname={dbname} user={dbuser} password={dbpass} host={dbhost}"
```

**Solution**: Create a function to build connection string on-demand:
```python
def get_connection_string() -> str:
    """Build connection string from environment variables."""
    dbname = os.getenv("POSTGRES_DB")
    dbuser = os.getenv("POSTGRES_USER")
    dbpass = os.getenv("POSTGRES_PASSWORD")
    dbhost = os.getenv("POSTGRES_HOST")

    # Validate required variables
    missing = [var for var, val in [
        ("POSTGRES_DB", dbname),
        ("POSTGRES_USER", dbuser),
        ("POSTGRES_PASSWORD", dbpass),
        ("POSTGRES_HOST", dbhost)
    ] if not val]

    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    return f"dbname={dbname} user={dbuser} password={dbpass} host={dbhost}"
```

**Priority**: High - Prevents silent failures

---

### 4. Manual Cursor Management
**Location**: Throughout file - all functions manually call `cur.close()`

**Problem**: Manual cursor management is error-prone and verbose.

**Current Pattern**:
```python
cur = conn.cursor()
cur.execute(...)
results = cur.fetchall()
cur.close()
```

**Solution**: Use context managers for automatic cleanup:
```python
with conn.cursor() as cur:
    cur.execute(...)
    results = cur.fetchall()
    # cursor auto-closes
```

**Priority**: Medium - Code quality and safety

---

## Medium Priority Issues

### 5. Inconsistent Error Handling
**Location**: Various functions throughout file

**Problem**:
- Some functions print errors and return empty lists (lines 240, 270, 308)
- Some catch specific exceptions (line 93: `psycopg2.errors.UniqueViolation`)
- Some catch broad `Exception` (line 180)
- No centralized logging

**Solution**: Implement consistent error handling strategy:

```python
import logging

logger = logging.getLogger(__name__)

def search_docs(query_embedding: list[float], limit: int = 10) -> list:
    """Search documents using vector similarity."""
    if not query_embedding:
        return []

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # ... query logic
                return docs
    except psycopg2.OperationalError as e:
        logger.error(f"Database connection error in search_docs: {e}")
        raise  # Let caller handle connection issues
    except Exception as e:
        logger.exception(f"Unexpected error in search_docs: {e}")
        return []
```

**Priority**: Medium - Debugging and reliability

---

### 6. Missing Configuration Class
**Location**: Module level (lines 11-16)

**Problem**: Database configuration is scattered in global variables.

**Solution**: Create a configuration class:

```python
from dataclasses import dataclass
from typing import Optional

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

    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """Load configuration from environment variables."""
        load_dotenv()
        return cls(
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host=os.getenv("POSTGRES_HOST"),
            port=int(os.getenv("POSTGRES_PORT", "5432"))
        )

    def validate(self) -> None:
        """Validate that all required fields are set."""
        missing = [field for field in ["dbname", "user", "password", "host"]
                   if not getattr(self, field)]
        if missing:
            raise ValueError(f"Missing required config fields: {missing}")
```

**Priority**: Medium - Better architecture for testing and dependency injection

---

### 7. No Retry Logic
**Location**: All database operations

**Problem**: Database operations can fail transiently (network issues, connection resets), but there's no retry mechanism.

**Solution**: Add retry decorator for transient failures:

```python
from functools import wraps
import time

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
                    logger.warning(f"Database error in {func.__name__}, "
                                 f"retrying ({attempt + 1}/{max_retries}): {e}")
                    time.sleep(delay * (attempt + 1))  # Exponential backoff
            return func(*args, **kwargs)
        return wrapper
    return decorator

@retry_on_db_error(max_retries=3)
def count_documents():
    # ... existing implementation
```

**Priority**: Medium - Improves reliability in production

---

### 8. Hardcoded Values
**Location**:
- Line 175: `page_size=100` in `bulk_upsert_to_vector_db`
- Various query patterns

**Problem**: Magic numbers make tuning difficult.

**Solution**: Make configurable:

```python
class DatabaseConfig:
    # ... existing fields
    bulk_insert_page_size: int = 100
    default_search_limit: int = 10

# Usage
execute_values(cur, sql, values, page_size=config.bulk_insert_page_size)
```

**Priority**: Low - Nice to have for tuning

---

## Minor Improvements

### 9. Use Proper Logging
**Location**: Throughout file - multiple `print()` statements

**Problem**: Using `print()` for error messages (lines 94, 181, 240, 270, 308, 470)

**Solution**: Replace with logging module:

```python
import logging

logger = logging.getLogger(__name__)

# Replace print statements
logger.error(f"IntegrityError: {e}, doc_id: {metadata['doc_id']}")
logger.exception(f"Error during bulk upsert: {e}")
```

**Priority**: Low - Better for production monitoring

---

### 10. Type Hints Inconsistency
**Location**: Various function signatures

**Problems**:
- `dbhealth()` returns `list` but should be `Optional[int]` or `int`
- Some functions use modern type hints (`list[str]`), others use old style
- Missing return type hints in some places

**Solution**: Consistent type hints:

```python
from typing import List, Optional, Dict, Any

def dbhealth() -> Optional[int]:
    """Returns document count or None on error."""
    try:
        with psycopg2.connect(pg_connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM documents LIMIT 1")
                result = cur.fetchone()
                return result[0] if result else 0
    except Exception as e:
        logger.exception(f"Error checking db health: {e}")
        return None

def search_docs(
    query_embedding: List[float],
    limit: int = 10
) -> List[Dict[str, Any]]:
    """Search documents using vector similarity."""
    # ...
```

**Priority**: Low - Code quality and IDE support

---

### 11. Duplicate Query Patterns
**Location**: Functions like `get_all_distinct_keywords()`, `get_top_distinct_keywords()`, `get_keywords_with_counts()`, `get_distinct_keywords_only()`

**Problem**: Similar query patterns repeated across multiple functions.

**Solution**: Create a shared query builder:

```python
def _get_keywords_query(
    distinct: bool = True,
    with_counts: bool = False,
    sort_by: str = "alpha",
    limit: Optional[int] = None
) -> str:
    """Build keyword query based on parameters."""

    if with_counts:
        base = """
            SELECT keyword, COUNT(*) as count
            FROM (
                SELECT unnest(keywords) as keyword
                FROM documents
                WHERE keywords IS NOT NULL AND array_length(keywords, 1) > 0
            ) AS all_keywords
            GROUP BY keyword
        """
    else:
        unnest = "DISTINCT unnest" if distinct else "unnest"
        base = f"""
            SELECT {unnest}(keywords) as keyword
            FROM documents
            WHERE keywords IS NOT NULL AND array_length(keywords, 1) > 0
        """

    # Add sorting
    if sort_by == "frequency" and not with_counts:
        # Need to add count for sorting
        base = """
            SELECT keyword
            FROM (
                SELECT keyword, COUNT(*) as freq
                FROM (
                    SELECT unnest(keywords) as keyword
                    FROM documents
                    WHERE keywords IS NOT NULL AND array_length(keywords, 1) > 0
                ) AS all_keywords
                GROUP BY keyword
                ORDER BY freq DESC
            ) AS counted_keywords
        """
    elif sort_by == "frequency":
        base += " ORDER BY count DESC"
    else:
        base += " ORDER BY keyword"

    if limit:
        base += f" LIMIT %s"

    return base
```

**Priority**: Low - Code maintainability

---

### 12. Environment Variable Validation
**Location**: Module initialization (lines 11-14)

**Problem**: No validation that required environment variables are set.

**Solution**: Validate on module load or provide clear errors:

```python
def validate_env_vars():
    """Validate required environment variables are set."""
    required_vars = [
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_HOST"
    ]

    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}. "
            f"Please check your .env file."
        )

# Call during initialization
load_dotenv()
validate_env_vars()
```

**Priority**: Low - Better error messages for setup

---

### 13. Transaction Handling Unclear
**Location**: `src/catalog/core/db.py:96-98` in `save_to_vector_db()`

**Problem**: `conn.commit()` is called after `cur.close()`, which is confusing:

```python
cur.close()
conn.commit()  # Commit after cursor close?
```

**Solution**: Follow standard pattern:

```python
with conn.cursor() as cur:
    cur.execute(...)
    # cursor auto-closes here
conn.commit()  # Clear that commit happens after cursor operations
```

**Priority**: Low - Code clarity

---

## Recommended Implementation Order

### Phase 1: Critical Security and Performance
1. Fix SQL injection vulnerability (#2)
2. Implement connection pooling (#1)
3. Add environment variable validation (#3, #12)

### Phase 2: Reliability
4. Implement consistent error handling with logging (#5, #9)
5. Add retry logic for transient failures (#7)
6. Use cursor context managers (#4)

### Phase 3: Architecture
7. Create DatabaseConfig class (#6)
8. Improve type hints (#10)
9. Refactor duplicate code (#11)

### Phase 4: Polish
10. Make hardcoded values configurable (#8)
11. Clarify transaction handling (#13)

---

## Recommended Refactored Structure

```python
# db.py (improved structure)
import logging
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from functools import wraps
import psycopg2
from psycopg2 import pool

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
```

## Usage Example

```python
# Old way
from catalog.core import db
count = db.count_documents()

# New way (same interface)
from catalog.core import db
count = db.count_documents()

# With custom config (for testing)
from catalog.core.db import DatabaseConfig, DatabaseConnection

test_config = DatabaseConfig(
    dbname="test_db",
    user="test_user",
    password="test_pass",
    host="localhost"
)
test_db = DatabaseConnection(test_config)
```

## Testing Improvements

With the new structure, testing becomes much easier:

```python
# tests/test_db.py
import pytest
from catalog.core.db import DatabaseConfig, DatabaseConnection

@pytest.fixture
def test_db_config():
    return DatabaseConfig(
        dbname="test_catalog",
        user="test_user",
        password="test_pass",
        host="localhost",
        pool_min=1,
        pool_max=2
    )

@pytest.fixture
def test_db(test_db_config):
    db = DatabaseConnection(test_db_config)
    yield db
    db.close_all()

def test_count_documents(test_db):
    # Test with dependency injection
    pass
```

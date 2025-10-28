# Keyword API URL Suggestions

1. API Endpoint (api.py) - A complete /keywords endpoint that handles:

    - All keywords (with duplicates)
    - Distinct keywords only
    - Distinct keywords with counts
    - Limit and sort options

2. Three Database Methods (db.py):

- get_all_keywords() - Returns all keywords including duplicates
- get_distinct_keywords_only() - Returns unique keywords without counts
- get_keywords_with_counts() - Returns unique keywords with frequency counts

3. Import Statement - Shows what to add to api.py to use the new db methods

  The implementations follow the existing code patterns in your project and support all the query parameter combinations from the URL scheme.
## Best Option for ALL Keywords:
```
GET /keywords
```

This is the standard RESTful approach - the base resource endpoint returns all items.

## Complete URL Scheme:

You can build a flexible system with query parameters:

```
GET /keywords                                    # All keywords (with duplicates)
GET /keywords?distinct=true                      # Unique keywords only
GET /keywords?distinct=true&include_counts=true  # Unique keywords with counts
GET /keywords?limit=100                          # Paginate results
GET /keywords?sort=alpha                         # Sort alphabetically
GET /keywords?sort=frequency                     # Sort by frequency (requires counts)
```

## Example Responses:

**All keywords** (`GET /keywords`):
```json
{
  "total": 1523,
  "keywords": ["GIS", "Forest", "GIS", "Wildlife", "Forest", ...]
}
```

**Distinct with counts** (`GET /keywords?distinct=true&include_counts=true`):
```json
{
  "total_keywords": 1523,
  "unique_keywords": 245,
  "data": [
    {"keyword": "GIS", "count": 156},
    {"keyword": "Forest", "count": 143},
    {"keyword": "Wildlife", "count": 98}
  ]
}
```

## REST Conventions

This follows REST conventions where:
- Collections are plural (`/keywords` not `/keyword`)
- The base path returns all items
- Query parameters filter/modify the results

---

## Implementation Examples

### API Endpoint (api.py)

```python
from fastapi import Query
from typing import Optional

@api.get("/keywords", tags=["Keywords"])
async def get_keywords(
    distinct: bool = Query(False, description="Return only unique keywords"),
    include_counts: bool = Query(False, description="Include frequency counts (requires distinct=true)"),
    limit: Optional[int] = Query(None, description="Limit number of results"),
    sort: Optional[str] = Query(None, description="Sort by 'alpha' or 'frequency'"),
    api_key: str = Depends(verify_api_key)
):
    """
    Get keywords from the catalog.

    Query parameters:
    - distinct: If true, returns only unique keywords
    - include_counts: If true, includes frequency counts (only with distinct=true)
    - limit: Maximum number of keywords to return
    - sort: Sort order - 'alpha' for alphabetical, 'frequency' for most common first
    """

    # Case 1: All keywords (with duplicates)
    if not distinct:
        keywords = get_all_keywords(limit=limit)
        return {
            "total": len(keywords),
            "keywords": keywords
        }

    # Case 2: Distinct keywords with counts
    if distinct and include_counts:
        data = get_keywords_with_counts(limit=limit, sort=sort)
        return {
            "total_keywords": sum(item["count"] for item in data),
            "unique_keywords": len(data),
            "data": data
        }

    # Case 3: Distinct keywords only (no counts)
    keywords = get_distinct_keywords_only(limit=limit, sort=sort)
    return {
        "unique_keywords": len(keywords),
        "keywords": keywords
    }
```

### Database Methods (db.py)

```python
def get_all_keywords(limit: Optional[int] = None) -> list[str]:
    """
    Get ALL keywords including duplicates from the database.

    Args:
        limit: Maximum number of keywords to return

    Returns:
        List of all keyword strings (may contain duplicates)
    """
    try:
        with psycopg2.connect(pg_connection_string) as conn:
            cur = conn.cursor()

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
        print(f"Error getting all keywords: {e}")
        return []


def get_distinct_keywords_only(
    limit: Optional[int] = None,
    sort: Optional[str] = None
) -> list[str]:
    """
    Get distinct keywords without counts.

    Args:
        limit: Maximum number of keywords to return
        sort: Sort order - 'alpha' for alphabetical, 'frequency' for most common

    Returns:
        List of unique keyword strings
    """
    try:
        with psycopg2.connect(pg_connection_string) as conn:
            cur = conn.cursor()

            # Base query with sorting
            if sort == "frequency":
                sql = """
                    SELECT keyword, COUNT(*) as freq
                    FROM (
                        SELECT unnest(keywords) as keyword
                        FROM documents
                        WHERE keywords IS NOT NULL AND array_length(keywords, 1) > 0
                    ) AS all_keywords
                    GROUP BY keyword
                    ORDER BY freq DESC
                """
            else:  # default to alphabetical
                sql = """
                    SELECT DISTINCT unnest(keywords) as keyword
                    FROM documents
                    WHERE keywords IS NOT NULL AND array_length(keywords, 1) > 0
                    ORDER BY keyword
                """

            if limit:
                sql += f" LIMIT {limit}"

            cur.execute(sql)
            results = cur.fetchall()
            cur.close()

            # Return just the keyword (first column)
            return [row[0] for row in results]

    except Exception as e:
        print(f"Error getting distinct keywords: {e}")
        return []


def get_keywords_with_counts(
    limit: Optional[int] = None,
    sort: Optional[str] = None
) -> list[dict]:
    """
    Get distinct keywords with their frequency counts.

    Args:
        limit: Maximum number of keywords to return
        sort: Sort order - 'alpha' for alphabetical, 'frequency' for most common

    Returns:
        List of dictionaries with 'keyword' and 'count' keys
    """
    try:
        with psycopg2.connect(pg_connection_string) as conn:
            cur = conn.cursor()

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

            return [
                {"keyword": row[0], "count": row[1]}
                for row in results
            ]

    except Exception as e:
        print(f"Error getting keywords with counts: {e}")
        return []
```

### Import Statement for api.py

```python
from catalog.core.db import (
    get_all_keywords,
    get_distinct_keywords_only,
    get_keywords_with_counts
)
```

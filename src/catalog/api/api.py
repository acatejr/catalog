from fastapi import FastAPI
from fastapi import Depends, HTTPException
from fastapi.security.api_key import APIKeyHeader
from typing import Optional
from fastapi import Query
import datetime
from catalog.api.llm import ChatBot
import os
from catalog.core.db import (
    get_all_keywords,
    get_keywords_with_counts,
    get_distinct_keywords_only,
    db_health_check,
)
from catalog.api.query_classifier import classify_query, format_keyword_response

X_API_KEY = os.environ.get("X_API_KEY")

api = FastAPI(title="Catalog API", version="0.0.1")

# Create API key header dependency
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)


def verify_api_key(api_key: Optional[str] = Depends(api_key_header)):
    """Verify the API key from the x-api-key header"""
    if api_key is None or api_key != X_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key


@api.get("/health", tags=["Health"])
async def health():
    """Simple API health check

    Args:
        api_key (str, optional): _description_. Defaults to Depends(verify_api_key).

    Returns:
        _type_: _description_
    """

    now = datetime.datetime.now()

    return {"status": "ok - " + now.strftime("%Y-%m-%d %H:%M:%S")}


@api.get("/dbhealth", tags=["Health"])
async def get_dbhealth():
    """Get basic health information about the database connection"""

    rec_count = db_health_check()

    return {
        "data": {
            "record_count": rec_count[0],
        },
    }


@api.get("/info", tags=["Info"])
async def info():
    """Get basic information about the API"""

    return {
        "api_name": "Catalog API",
        "version": "0.0.1",
        "description": "An API for querying the catalog and retrieving keywords.",
    }


# @api.get("/query", tags=["Query"])
# async def query(q: str, api_key: str = Depends(verify_api_key)):
#     """A simple query endpoint that passes the query string onto the ai agent and returns the result."""

#     response = ""
#     bot = ChatBot()
#     response = bot.chat(message=q)

#     return {"query": q, "response": response}


@api.get("/keywords", tags=["Keywords"])
async def get_keywords(
    distinct: bool = Query(False, description="Return only unique keywords"),
    include_counts: bool = Query(
        False, description="Include frequency counts (requires distinct=true)"
    ),
    limit: Optional[int] = Query(None, description="Limit number of results"),
    sort: Optional[str] = Query(None, description="Sort by 'alpha' or 'frequency'"),
    api_key: str = Depends(verify_api_key),
):
    """
    Get keywords from the catalog.

    Query parameters:
    - distinct: If true, returns only unique keywords
    - include_counts: If true, includes frequency counts (only with distinct=true)
    - limit: Maximum number of keywords to return
    - sort: Sort order - 'alpha' for alphabetical, 'frequency' for most common first
    """

    if not distinct:
        # Implementation for all keywords including duplicates
        keywords = get_all_keywords(limit=limit)
        return {"total": len(keywords), "keywords": keywords}
        return keywords

    if distinct and include_counts:
        data = get_keywords_with_counts(limit=limit, sort=sort)
        return {
            "total_keywords": sum(item["count"] for item in data),
            "unique_keywords": len(data),
            "data": data,
        }

    keywords = get_distinct_keywords_only(limit=limit, sort=sort)
    return {"unique_keywords": len(keywords), "keywords": keywords}


@api.get("/query", tags=["Query"])
async def query(q: str, api_key: str = Depends(verify_api_key)):
    """
    Natural language query endpoint with intelligent routing.

    Implements the pattern from commented code (lines 77-146) using
    a clean, maintainable architecture.
    """

    # Classify the query using our new classifier
    query_type = classify_query(q)

    if query_type["type"] == "list_keywords":
        # Get structured data based on classification
        params = query_type["params"]

        # Route to appropriate database function (fixes reference code issues)
        if params["distinct"] and params["count"]:
            data = get_keywords_with_counts(limit=params.get("limit"), sort="frequency")
        elif params["distinct"]:
            data = get_distinct_keywords_only(limit=params.get("limit"), sort="alpha")
        else:
            data = get_all_keywords(limit=params.get("limit"))

        # Format the response
        formatted_response = format_keyword_response(data, params)

        # Option A: Return structured data directly (recommended for start)
        return {"query": q, "response": formatted_response, "data": data}

        # Option B: Enhance with LLM for natural language (future enhancement)
        # bot = ChatBot()
        # llm_response = bot.chat(
        #     message=f"User asked: '{q}'. Data: {formatted_response}"
        # )
        # return {"query": q, "response": llm_response, "raw_data": data}

    else:
        # Fall back to full LLM chat for complex queries (ref: lines 144-146)
        bot = ChatBot()
        response = bot.chat(message=q)
        return {"query": q, "response": response}

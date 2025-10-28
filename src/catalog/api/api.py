from fastapi import FastAPI
from fastapi import Depends, HTTPException
from fastapi.security.api_key import APIKeyHeader
from typing import Optional
from fastapi import Query
from typing import Optional
import datetime
from catalog.api.llm import ChatBot
import os, json
from catalog.core.db import (
    get_all_distinct_keywords,
    get_top_distinct_keywords,
    get_all_keywords,
    get_keywords_with_counts,
    get_distinct_keywords_only,
)

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


@api.get("/query", tags=["Query"])
async def query(q: str, api_key: str = Depends(verify_api_key)):
    """A simple query endpoint that passes the query string onto the ai agent and returns the result."""

    response = ""

    query_type = {}

    if any(
        phrase in q.lower()
        for phrase in [
            "list keywords",
            "keyword list",
            "show keywords",
            "all keywords",
            "all the keywords",
            "keywords in the catalog",
            "keywords catalog",
            "all unique keywords",
            "unique keywords",
            "distinct keywords",
            "keywords list",
        ]
    ):
        if any(
            phrase in q.lower()
            for phrase in ["unique", "distinct", "no duplicates", "without duplicates"]
        ):
            if any(
                phrase in q.lower()
                for phrase in [
                    "how many",
                    "number of",
                    "count of",
                    "total",
                    "top",
                    "count",
                    "most frequent",
                    "frequent",
                    "frequencies",
                ]
            ):
                query_type = {
                    "type": "list_keywords",
                    "params": {"distinct": True, "count": True},
                }
            else:
                query_type = {"type": "list_keywords", "params": {"distinct": True}}
        else:
            query_type = {"type": "list_keywords", "params": {}}
    else:
        query_type = {"type": "llm_chat", "params": {}}

    if query_type["type"] == "list_keywords":
        if query_type["params"].get("distinct", False):
            keywords = get_all_distinct_keywords()
            keyword_dict = {}
            for kw in keywords:
                if kw.lower() not in keyword_dict:
                    keyword_dict[kw.lower()] = kw

            bot = ChatBot()
            response = bot.keyword_chat(
                message=f"Distince keywords in the catalog: {', '.join(keyword_dict.values())}."
            )
        else:
            if query_type["params"].get("count", False):
                keywords = get_all_distinct_keywords()
                response = "\n\n".join(kw for kw in keywords)
            else:
                keywords = get_top_distinct_keywords()
                response = "\n\n".join(kw for kw in keywords)

    if query_type["type"] == "llm_chat":
        bot = ChatBot()
        response = bot.chat(message=q)

    return {"query": q, "response": response}


@api.get("/keywords", tags=["Keywords"])
async def get_keywords(
    distinct: bool = Query(False, description="Return only unique keywords"),
    include_counts: bool = Query(
        False, description="Include frequency counts (requires distinct=true)"
    ),
    limit: Optional[int] = Query(None, description="Limit number of results"),
    sort: Optional[str] = Query(None, description="Sort by 'alpha' or 'frequency'"),
    # api_key: str = Depends(verify_api_key)
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

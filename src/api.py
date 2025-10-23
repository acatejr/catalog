from fastapi import FastAPI
from fastapi import Depends, HTTPException
from fastapi.security.api_key import APIKeyHeader
from typing import Optional
import datetime
from llm import ChatBot
import os, json
from db import get_all_distinct_keywords

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
    now = datetime.datetime.now()

    return {"status": "ok - " + now.strftime("%Y-%m-%d %H:%M:%S")}


@api.get("/query", tags=["Query"])
async def query(q: str, api_key: str = Depends(verify_api_key)):
    """A simple query endpoint that passes the query string onto the ai agent and returns the result."""

    response = ""

    query_type = {}

    if any(phrase in q.lower() for phrase in [
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
    ]):
        if any(phrase in q.lower() for phrase in [
            "unique",
            "distinct",
            "no duplicates",
            "without duplicates"
        ]):
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
            keywords = get_all_distinct_keywords()
            response = '\n\n'.join(kw for kw in keywords)

    if query_type["type"] == "llm_chat":
        bot = ChatBot()
        response = bot.chat(message=q)

    return {"query": q, "response": response}

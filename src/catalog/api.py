from fastapi import FastAPI
from fastapi import Depends, HTTPException
from fastapi.security.api_key import APIKeyHeader
from typing import Optional
import datetime
from catalog.llm import ChatBot
import os

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

    response = None

    bot = ChatBot()
    response = bot.chat(q)

    return {"query": q, "response": response}

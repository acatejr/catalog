from fastapi import FastAPI
import datetime
import os
from fastapi.security import APIKeyHeader
from fastapi import FastAPI, Header, HTTPException, Depends
from typing import Optional

from catalog.llm.client import ChatBot

X_API_KEY = os.getenv("X_API_KEY")

app = FastAPI(title="Catalog API", version="0.0.1")

# Create API key header dependency
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)

def verify_api_key(api_key: Optional[str] = Depends(api_key_header)):
    """Verify the API key from the x-api-key header"""
    if api_key is None or api_key != X_API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    return api_key

@app.get("/health", tags=["Health"])
async def health(api_key: str = Depends(verify_api_key)):
    now = datetime.datetime.now()

    return {"status": "ok - " + now.strftime("%Y-%m-%d %H:%M:%S")}


@app.get("/query", tags=["Query"])
async def query(q: str, api_key: str = Depends(verify_api_key)):
    """A simple query endpoint that passes the query string onto the ai agent and returns the result."""

    response = None

    bot = ChatBot()
    response = bot.chat(q)
    print(f"Received query: {q}, response: {response}")

    return {"query": q, "response": response}

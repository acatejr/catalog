from fastapi import FastAPI
import datetime
from catalog.llm import ChatBot

api = FastAPI(title="Catalog API", version="0.0.1")


@api.get("/health", tags=["Health"])
async def health():
    now = datetime.datetime.now()

    return {"status": "ok - " + now.strftime("%Y-%m-%d %H:%M:%S")}


@api.get("/query", tags=["Query"])
async def query(q: str):
    """A simple query endpoint that passes the query string onto the ai agent and returns the result."""

    response = None

    bot = ChatBot()
    response = bot.chat(q)

    return {"query": q, "response": response}

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import datetime

origins = ["*"]

api = FastAPI(title="USFS Data Catalog API")

api.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@api.get("/health")
async def health():
    """API health check"""

    now = datetime.datetime.now()
    return {"message": "ok", "data": now}


@api.get("/simple-search/{term}")
async def simple_search(term: str) -> dict:
    """API simple document search"""

    data = [
        {"id": "1", "description": "Metadata description 1"},
        {"id": "2", "description": "Metadata description 2"},
        {"id": "3", "description": "Metadata description 3"},
        {"id": "4", "description": "Metadata description 4"},
        {"id": "5", "description": "Metadata description 5"},
        {"id": "6", "description": "Metadata description 6"},
        {"id": "7", "description": "Metadata description 7"},
        {"id": "8", "description": "Metadata description 8"},
        {"id": "9", "description": "Metadata description 9"},
        {"id": "10", "description": "Metadata description 10"},
    ]

    return {
        "message": "ok",
        "term": term,
        "data": data,
    }


@api.get("/advanced-search/{term}")
async def advanced_search(term: str) -> dict:
    """API advanced document search"""

    data = []

    return {
        "message": "ok",
        "term": term,
        "data": data,
    }

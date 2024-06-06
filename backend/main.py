from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import datetime
import os
#  from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, load_only
# import psycopg2
# from fastapi.encoders import jsonable_encoder
from .models import Document, SearchTermLog
from dotenv import load_dotenv

load_dotenv()

origins = ["*"]

api = FastAPI(title="USFS Data Catalog API")

api.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

POSTGRES_USER = os.environ.get("POSTGRES_USER")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD")
POSTGRES_HOST = os.environ.get("POSTGRES_HOST")
db_url = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:5432"
engine = create_engine(db_url)

def log_search_term(session, term):
    search_term = SearchTermLog(term=term)
    session.add(search_term)
    session.commit()

@api.get("/health")
async def health():
    """API health check"""

    now = datetime.datetime.now()
    return {"message": "ok", "data": now}


@api.get("/simple-search/{term}")
async def simple_search(term: str):
    """API simple document search"""

    data = {
        "msg": "ok",
        "term": term,
    }

    with Session(engine) as session:

        # The search term has to be saved first in this session
        log_search_term(session, term)

        query = (
            session.query(Document)
            .options(
                load_only(
                    Document.id, Document.metadata_url, Document.description
                )
            )
            .filter(Document.description.like(f"%{term}%"))
        )
        data["data"] = query.all()



    return data

@api.get("/advanced-search/{term}")
async def advanced_search(term: str) -> dict:
    """API advanced document search"""

    data = []

    return {
        "message": "ok",
        "term": term,
        "data": data,
    }

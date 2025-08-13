import os
from fastapi.responses import RedirectResponse
from sqlmodel import SQLModel, create_engine, Session
from fastapi import FastAPI, Depends, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select
from catalog.adhoc.models import Document, Keyword, KeywordLink
from contextlib import asynccontextmanager
import uvicorn

DATABASE_URL = "sqlite:///./adhoc_catalog.db"
engine = create_engine(DATABASE_URL)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

app = FastAPI(title="USFS AdHoc Data Catalog")
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))
# app.mount("/static", StaticFiles(directory="static"), name="static")

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

    # Clean up the ML models and release the resources
    # app shutdown logic....


app = FastAPI(lifespan=lifespan)

@app.get("/")
def home(request: Request, session: Session = Depends(get_session)):
    documents = session.exec(select(Document)).all()

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "documents": documents}
    )

@app.post("/documents")
def create_document(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    keywords: str = Form(...),
    session: Session = Depends(get_session)
):
    # Create document
    doc = Document(title=title, description=description)
    session.add(doc)

    # Handle keywords
    keyword_names = [k.strip() for k in keywords.split(",")]
    for name in keyword_names:
        keyword = session.exec(
            select(Keyword).where(Keyword.name == name)
        ).first()
        if not keyword:
            keyword = Keyword(name=name)
            session.add(keyword)
        doc.keywords.append(keyword)

    session.commit()

    return RedirectResponse(url="/", status_code=303)

@app.post("/documents/{document_id}/delete")
def delete_document(
    document_id: int,
    session: Session = Depends(get_session)
):
    # Find the document
    document = session.get(Document, document_id)
    if document:
        # Remove associated keywords
        document.keywords = []
        # Delete the document
        session.delete(document)
        session.commit()

    return RedirectResponse(url="/", status_code=303)


@app.get("/documents/{document_id}/edit")
def edit_document_form(
    document_id: int,
    request: Request,
    session: Session = Depends(get_session)
):
    document = session.get(Document, document_id)
    if not document:
        return RedirectResponse(url="/", status_code=303)

    # Format keywords as comma-separated string
    keywords = ", ".join([keyword.name for keyword in document.keywords])

    return templates.TemplateResponse(
        "edit.html",
        {"request": request, "document": document, "keywords": keywords}
    )

@app.post("/documents/{document_id}/edit")
def update_document(
    document_id: int,
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    keywords: str = Form(...),
    session: Session = Depends(get_session)
):
    document = session.get(Document, document_id)
    if document:
        # Update basic fields
        document.title = title
        document.description = description

        # Clear existing keywords
        document.keywords = []

        # Add new keywords
        keyword_names = [k.strip() for k in keywords.split(",") if k.strip()]
        for name in keyword_names:
            keyword = session.exec(
                select(Keyword).where(Keyword.name == name)
            ).first()
            if not keyword:
                keyword = Keyword(name=name)
                session.add(keyword)
            document.keywords.append(keyword)

        session.commit()

    return RedirectResponse(url="/", status_code=303)

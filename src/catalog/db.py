"""PostgreSQL database operations with pgvector support."""

from sqlalchemy import create_engine, Column, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from pgvector.sqlalchemy import Vector
from datetime import datetime
from typing import Optional, List
import os
import json

Base = declarative_base()

class DocumentRecord(Base):
    """PostgreSQL table mapping for USFSDocument with embeddings."""
    __tablename__ = "documents"

    id = Column(String(64), primary_key=True)
    title = Column(String(512), nullable=False, index=True)
    abstract = Column(Text)
    description = Column(Text)
    purpose = Column(Text)
    keywords = Column(Text)  # JSON stringified list
    src = Column(String(50))
    lineage = Column(Text)   # JSON stringified
    embedding = Column(Vector(384))  # all-MiniLM-L6-v2 is 384-dim
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    @classmethod
    def from_usfs_document(cls, doc, embedding: List[float]):
        """Convert USFSDocument + embedding vector to database record."""

        return cls(
            id=doc.id,
            title=doc.title,
            abstract=doc.abstract,
            description=doc.description,
            purpose=doc.purpose,
            keywords=json.dumps(doc.keywords or []),
            src=doc.src,
            lineage=json.dumps(doc.lineage or []),
            embedding=embedding,
        )

def get_db_url() -> str:
    """Build PostgreSQL connection string from environment."""

    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DB", "catalog")

    if password:
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"
    return f"postgresql://{user}@{host}:{port}/{database}"

def init_db():
    """Create tables and enable pgvector extension."""
    engine = create_engine(get_db_url())

    # Enable pgvector extension
    with engine.connect() as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        conn.commit()

    # Create tables
    Base.metadata.create_all(engine)

    # Create vector similarity index for fast search
    with engine.connect() as conn:
        conn.execute(
            "CREATE INDEX IF NOT EXISTS ix_embedding_cosine "
            "ON usfs_documents USING ivfflat (embedding vector_cosine_ops) "
            "WITH (lists = 100);"
        )
        conn.commit()
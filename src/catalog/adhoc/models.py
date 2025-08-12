from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel

class KeywordLink(SQLModel, table=True):
    """Link table for Document-Keyword many-to-many relationship"""
    document_id: Optional[int] = Field(default=None, foreign_key="document.id", primary_key=True)
    keyword_id: Optional[int] = Field(default=None, foreign_key="keyword.id", primary_key=True)

class Keyword(SQLModel, table=True):
    """Keyword model"""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    documents: List["Document"] = Relationship(back_populates="keywords", link_model=KeywordLink)

class Document(SQLModel, table=True):
    """Document model"""
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    description: str
    keywords: List[Keyword] = Relationship(back_populates="documents", link_model=KeywordLink)
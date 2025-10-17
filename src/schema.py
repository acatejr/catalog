"""
schema.py

Defines data models for USFS document metadata using Pydantic.
"""

from pydantic import BaseModel
from typing import List, Optional


class USFSDocument(BaseModel):
    """
    Represents a USFS (United States Forest Service) metadata document.

    Attributes:
        id (str): Unique identifier for the document.
        title (str): Title of the document.
        description (str): Description or summary of the document.
        keywords (Optional[List[str]]): List of keywords associated with the document.
        src (Optional[str]): Source or URL of the document.
    """

    id: str
    title: str
    description: str
    keywords: Optional[List[str]] = None
    src: Optional[str] = None
"""
Unified schema for geospatial catalog documents from FSGeodata, GDD, and RDA sources.
"""

from pydantic import BaseModel, Field
from typing import Optional


class Document(BaseModel):
    """
    Represents a USFS (United States Forest Service) metadata document.

    Attributes:
        id (str): Unique identifier for the document.
        title (str): Title of the document.
        abstract (str): Description or summary of the document.
        purpose (str): Description or summary of the document.
        keywords (Optional[List[str]]): List of keywords associated with the document.
        src (Optional[str]): Source or the document's metadata.
        lineage (Optional[List[str]]): List of the data set's lineage.
    """

    # Required fields (common to all sources)
    id: str = Field(..., description="The primary key field.  Unique identifier.")
    title: Optional[str] = Field(..., description="The document title.")
    abstract: str | None = Field(default=None, description="The document's abstract.")
    purpose: str | None = Field(
        default=None, description="Description of the document's purpose."
    )
    keywords: list[str] | None = Field(
        default=[], description="List of the document's keywords."
    )
    src: str | None = Field(
        default=None,
        description="Description of the document's source (e.g., fsgeodata, gdd, rda ).",
    )
    lineage: list[dict] | None = Field(
        default=[], description="List of the metadata's lineage."
    )



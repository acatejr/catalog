"""
Unified schema for geospatial catalog documents from FSGeodata, GDD, and RDA sources.
"""

from pydantic import BaseModel, Field
from typing import Optional


class USFSDocument(BaseModel):
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
        default=None, description="Description of the data source's purpose."
    )
    keywords: list[str] | None = Field(
        default=[], description="List of the data source's keywords."
    )
    src: str | None = Field(
        default=None,
        description="Description of the data source's source (e.g., fsgeodata, gdd, rda ).",
    )
    lineage: list[dict] | None = Field(
        default=[], description="List of the metadata's lineage."
    )

    def to_markdown(self, distance: float | None = None) -> str:
        """Convert the document to a markdown representation."""

        md = f"# {self.title}\n\n"
        if distance is not None:
            md += f"**Relevance Distance:** {distance:.4f}\n\n"
        md += f"**ID:** {self.id}\n\n"
        md += f"**Abstract:** {self.abstract}\n\n"
        md += f"**Purpose:** {self.purpose}\n\n"
        md += f"**Source:** {self.src}\n\n"
        if self.keywords:
            md += f"**Keywords:** {', '.join(self.keywords)}\n\n"
        if self.lineage:
            md += "## Lineage\n"
            for item in self.lineage:
                desc = item.get("description", "")
                date = item.get("date", "")
                md += f"- {desc} ({date})\n"
        return md

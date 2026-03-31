"""
Unified schema for geospatial catalog documents.

This module defines the canonical ``USFSDocument`` model used throughout the
Catalog tool.  All three USFS metadata sources — FSGeodata (XML), the
Geodata Discovery Database (GDD, JSON), and the Research Data Archive
(RDA, JSON) — are normalised into this single structure before being written
to the output catalog file.

Using a shared schema ensures that downstream consumers (search indexes,
dashboards, AI retrieval pipelines) can treat every record uniformly
regardless of which source it originated from.
"""

from pydantic import BaseModel, Field
from typing import Optional


class USFSDocument(BaseModel):
    """Canonical representation of a single USFS geospatial dataset record.

    This model is the common output type for all three metadata pipelines:

    * **FSGeodata** — populated from XML metadata files downloaded from the
      USFS Geodata Clearinghouse.  Fields ``abstract``, ``purpose``, and
      ``lineage`` are typically present; ``description`` is not used.
    * **GDD** — populated from the USFS ArcGIS Hub DCAT-US JSON feed.
      ``description`` and ``keywords`` are the primary content fields;
      ``abstract``, ``purpose``, and ``lineage`` are left empty.
    * **RDA** — populated from the USFS Research Data Archive JSON web
      service.  Similar to GDD: ``description`` and ``keywords`` are used;
      ``abstract``, ``purpose``, and ``lineage`` are left empty.

    The ``src`` field records which pipeline produced the document so that
    consumers can apply source-specific logic when needed.

    Attributes:
        id: SHA-256 hash of the lower-cased, stripped title.  Acts as a
            stable, deterministic primary key across pipeline runs.
        title: Human-readable name of the dataset as provided by the source.
        abstract: Executive summary of the dataset (FSGeodata only).
        purpose: Statement of why the dataset was created (FSGeodata only).
        keywords: Controlled-vocabulary tags and free-text terms that describe
            the subject matter of the dataset.
        src: Source identifier — one of ``"fsgeodata"``, ``"gdd"``, or
            ``"rda"``.
        lineage: Ordered list of processing steps, each a dict with
            ``"description"`` and ``"date"`` keys (FSGeodata only).
        description: Full narrative description of the dataset (GDD and RDA).
    """

    # Required fields (common to all sources)
    id: str = Field(..., description="The primary key field.  Unique identifier.")
    title: Optional[str] = Field(..., description="The document title.")
    abstract: str | None = Field(default=None, description="The document's abstract.")
    purpose: str | None = Field(
        default=None, description="Description of the data source's purpose."
    )
    keywords: list[str] | None = Field(
        default_factory=list, description="List of the data source's keywords."
    )
    src: str | None = Field(
        default=None,
        description="Description of the data source's source (e.g., fsgeodata, gdd, rda ).",
    )
    lineage: list[dict] | None = Field(
        default_factory=list, description="List of the metadata's lineage."
    )
    description: str | None = Field(
        default=None,
        description="Description of the data.",
    )

    def to_markdown(self, distance: float | None = None) -> str:
        """Render the document as a Markdown-formatted string.

        Produces a human-readable summary of the document suitable for display
        in terminals, notebooks, or report generation pipelines.  All populated
        fields are included; empty optional fields are rendered as blank lines.

        Args:
            distance: Optional relevance score (e.g. vector-search cosine
                distance) to include in the output.  When provided, a
                **Relevance Distance** line is inserted immediately after the
                title heading.  Lower values indicate higher similarity.

        Returns:
            A Markdown string beginning with a level-1 heading (the document
            title), followed by labelled sections for each populated field.
            Lineage steps are rendered as a bulleted list under a level-2
            ``## Lineage`` heading.
        """

        md = f"# {self.title}\n\n"
        if distance is not None:
            md += f"**Relevance Distance:** {distance:.4f}\n\n"
        md += f"**ID:** {self.id}\n\n"
        md += f"**Abstract:** {self.abstract}\n\n"
        md += f"**Description:** {self.description}\n\n"
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

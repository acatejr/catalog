"""
Unified schema for geospatial catalog documents from FSGeodata, GDD, and RDA sources.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from enum import Enum


class DataSource(str, Enum):
    """Enumeration of data sources"""

    FSGEODATA = "fsgeodata"
    GDD = "gdd"
    RDA = "rda"


class LineageStep(BaseModel):
    """Represents a single processing step in data lineage (FSGeodata)"""

    description: str = Field(..., description="Description of the processing step")
    date: str = Field(..., description="Date of the processing step")


class CatalogDocument(BaseModel):
    """
    Unified document model for geospatial catalog entries.

    Merges document structures from:
    - FSGeodata: metadata XML files with title, abstract, purpose, lineage, keywords
    - GDD: DCAT-US JSON with title, description, keywords, themes
    - RDA: Data.gov JSON with title, description, keywords
    """

    # Required fields (common to all sources)
    title: str = Field(..., description="Document title")

    # Core description fields
    description: Optional[str] = Field(
        None,
        description="General description (from GDD/RDA) or abstract (from FSGeodata)",
    )
    abstract: Optional[str] = Field(
        None, description="Detailed abstract from FSGeodata metadata"
    )

    # Keywords and themes
    keywords: list[str] = Field(
        default_factory=list,
        description="List of keywords/tags associated with the dataset",
    )
    themes: list[str] = Field(
        default_factory=list, description="Thematic categories (primarily from GDD)"
    )

    # FSGeodata-specific fields
    purpose: Optional[str] = Field(
        None, description="Purpose of the dataset (FSGeodata)"
    )
    lineage: list[LineageStep] = Field(
        default_factory=list, description="Data processing lineage steps (FSGeodata)"
    )

    # Metadata about the document
    source: DataSource = Field(..., description="Source system: fsgeodata, gdd, or rda")
    source_id: Optional[str] = Field(
        None, description="Original identifier from source system"
    )

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        """Ensure title is not empty"""
        if not v or not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()

    @field_validator("keywords", "themes")
    @classmethod
    def remove_empty_strings(cls, v: list[str]) -> list[str]:
        """Remove empty strings from keyword and theme lists"""
        return [item.strip() for item in v if item and item.strip()]

    @property
    def has_lineage(self) -> bool:
        """Check if document has lineage information"""
        return len(self.lineage) > 0

    @property
    def primary_description(self) -> str:
        """Get the best available description/abstract"""
        return self.abstract or self.description or ""

    @classmethod
    def from_fsgeodata(
        cls, data: dict, source_id: Optional[str] = None
    ) -> "CatalogDocument":
        """
        Create a CatalogDocument from FSGeodata parsed metadata.

        Expected data structure from FSGeodataLoader.parse_metadata():
        {
            "title": str,
            "abstract": str,
            "purpose": str,
            "keywords": list[str],
            "lineage": [{"description": str, "date": str}, ...]
        }

        Example:
            fsgeodata = FSGeodataLoader()
            docs_data = fsgeodata.parse_metadata()
            for doc_data in docs_data:
                doc = CatalogDocument.from_fsgeodata(doc_data)
        """
        lineage_steps = [
            LineageStep(description=step["description"], date=step["date"])
            for step in data.get("lineage", [])
        ]

        return cls(
            title=data["title"],
            abstract=data.get("abstract"),
            purpose=data.get("purpose"),
            keywords=data.get("keywords", []),
            lineage=lineage_steps,
            source=DataSource.FSGEODATA,
            source_id=source_id,
        )

    @classmethod
    def from_gdd(cls, data: dict, source_id: Optional[str] = None) -> "CatalogDocument":
        """
        Create a CatalogDocument from GDD (Geospatial Data Discovery) parsed metadata.

        Expected data structure from GeospatialDataDiscovery.parse_metadata():
        {
            "title": str,
            "description": str,
            "keywords": list[str],
            "themes": list[str]
        }

        Example:
            gdd = GeospatialDataDiscovery()
            docs_data = gdd.parse_metadata()
            for doc_data in docs_data:
                doc = CatalogDocument.from_gdd(doc_data)
        """
        return cls(
            title=data["title"],
            description=data.get("description"),
            keywords=data.get("keywords", []),
            themes=data.get("themes", []),
            source=DataSource.GDD,
            source_id=source_id,
        )

    @classmethod
    def from_rda(cls, data: dict, source_id: Optional[str] = None) -> "CatalogDocument":
        """
        Create a CatalogDocument from RDA (Research Data Archive) parsed metadata.

        Expected data structure from RDALoader.parse_metadata():
        {
            "title": str,
            "description": str,
            "keywords": list[str]
        }

        Example:
            rda = RDALoader()
            docs_data = rda.parse_metadata()
            for doc_data in docs_data:
                doc = CatalogDocument.from_rda(doc_data)
        """
        return cls(
            title=data["title"],
            description=data.get("description"),
            keywords=data.get("keywords", []),
            source=DataSource.RDA,
            source_id=source_id,
        )

    def to_dict(self, exclude_none: bool = True) -> dict:
        """
        Convert to dictionary with optional exclusion of None values

        Args:
            exclude_none: If True, exclude fields with None values

        Returns:
            Dictionary representation of the document
        """
        return self.model_dump(exclude_none=exclude_none)

    class Config:
        """Pydantic model configuration"""

        use_enum_values = True
        validate_assignment = True
        json_schema_extra = {
            "example": {
                "title": "National Forest System Lands",
                "description": "Boundaries of National Forest System lands",
                "abstract": "This dataset represents the boundaries...",
                "keywords": ["forest", "boundaries", "USFS"],
                "themes": ["environment", "boundaries"],
                "purpose": "To delineate National Forest System lands",
                "lineage": [
                    {"description": "Initial data compilation", "date": "20230101"}
                ],
                "source": "fsgeodata",
                "source_id": "S_USA.NFS_Lands",
            }
        }

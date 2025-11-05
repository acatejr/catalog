from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Union, Literal
from enum import Enum
from datetime import datetime
from xml.etree import ElementTree as ET
from pathlib import Path
import logging
from catalog.core.db import save_eainfo, get_eainfo_by_id, list_all_entities

logger = logging.getLogger(__name__)


class DomainType(str, Enum):
    """Types of attribute domain values in FGDC metadata"""

    UNREPRESENTABLE = "unrepresentable"  # udom - free text description
    ENUMERATED = "enumerated"  # edom - specific allowed values
    CODESET = "codeset"  # codesetd - external reference
    RANGE = "range"  # rdom - numeric range


class EntityType(BaseModel):
    """Entity type information describing the feature class or table

    Corresponds to FGDC <enttyp> element
    """

    label: str = Field(
        ..., description="Entity Type Label (enttypl) - name of the feature class/table"
    )
    definition: Optional[str] = Field(
        None, description="Entity Type Definition (enttypd)"
    )
    definition_source: Optional[str] = Field(
        None, description="Entity Type Definition Source (enttypds)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "label": "S_USA.Activity_BrushDisposal",
                "definition": "A collection of geographic features with the same geometry type",
                "definition_source": "http://support.esri.com/en/knowledgebase/GISDictionary/term/feature%20class",
            }
        }


class UnrepresentableDomain(BaseModel):
    """Free-text domain description for attributes without specific constraints

    Corresponds to FGDC <udom> element
    Used when values don't fit enumerated/range/codeset patterns
    """

    type: Literal[DomainType.UNREPRESENTABLE] = DomainType.UNREPRESENTABLE
    description: str = Field(
        ..., min_length=1, description="Free-text description of valid values"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "type": "unrepresentable",
                "description": "Sequential unique whole numbers that are automatically generated.",
            }
        }


class EnumeratedDomain(BaseModel):
    """Enumerated domain with specific allowed values

    Corresponds to FGDC <edom> element
    Used for fields with discrete, predefined values (e.g., status codes, categories)
    """

    type: Literal[DomainType.ENUMERATED] = DomainType.ENUMERATED
    value: str = Field(..., description="Enumerated Domain Value (edomv)")
    value_definition: str = Field(
        ..., min_length=1, description="Enumerated Domain Value Definition (edomvd)"
    )
    value_definition_source: Optional[str] = Field(
        None, description="Enumerated Domain Value Definition Source (edomvds)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "type": "enumerated",
                "value": "1111",
                "value_definition": "Broadcast Burning - Covers a majority of the unit",
                "value_definition_source": "FACTS User Guide, Appendix B: Activity Codes",
            }
        }


class CodesetDomain(BaseModel):
    """Reference to external codeset or controlled vocabulary

    Corresponds to FGDC <codesetd> element
    Used when values are defined in external standards (e.g., ISO codes, FIPS codes)
    """

    type: Literal[DomainType.CODESET] = DomainType.CODESET
    codeset_name: str = Field(
        ..., min_length=1, description="Name of the codeset (codesetn)"
    )
    codeset_source: str = Field(
        ..., description="URL or reference to codeset documentation (codesets)"
    )

    @field_validator("codeset_source")
    @classmethod
    def validate_source(cls, v: str) -> str:
        """Ensure source is provided and non-empty"""
        if not v or not v.strip():
            raise ValueError("Codeset source must be provided")
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "type": "codeset",
                "codeset_name": "List of U.S. State Abbreviations",
                "codeset_source": "http://www.census.gov/geo/reference/ansi_statetables.html",
            }
        }


class RangeDomain(BaseModel):
    """Numeric range domain for continuous values

    Corresponds to FGDC <rdom> element
    Used for numeric fields with min/max constraints
    """

    type: Literal[DomainType.RANGE] = DomainType.RANGE
    min_value: Optional[float] = Field(None, description="Minimum value (rdommin)")
    max_value: Optional[float] = Field(None, description="Maximum value (rdommax)")
    units: Optional[str] = Field(None, description="Units of measurement (attrunit)")

    @model_validator(mode="after")
    def validate_range(self):
        """Ensure min <= max if both provided"""
        if (
            self.min_value is not None
            and self.max_value is not None
            and self.min_value > self.max_value
        ):
            raise ValueError(
                f"min_value ({self.min_value}) cannot be greater than max_value ({self.max_value})"
            )
        return self

    class Config:
        json_schema_extra = {
            "example": {
                "type": "range",
                "min_value": 0.0,
                "max_value": 100.0,
                "units": "percent",
            }
        }


# Union type for all possible domain value types
AttributeDomainValue = Union[
    UnrepresentableDomain, EnumeratedDomain, CodesetDomain, RangeDomain
]


class Attribute(BaseModel):
    """Individual attribute/field definition

    Corresponds to FGDC <attr> element
    Describes a single column in a feature class or table
    """

    label: str = Field(
        ..., min_length=1, description="Attribute Label (attrlabl) - column name"
    )
    definition: str = Field(
        ..., min_length=1, description="Attribute Definition (attrdef)"
    )
    definition_source: Optional[str] = Field(
        None, description="Attribute Definition Source (attrdefs)"
    )
    domain_values: List[AttributeDomainValue] = Field(
        default_factory=list,
        description="List of domain value specifications (attrdomv) - can have multiple",
    )

    @property
    def has_enumerated_values(self) -> bool:
        """Check if attribute has enumerated domain values"""
        return any(isinstance(dv, EnumeratedDomain) for dv in self.domain_values)

    @property
    def enumerated_values(self) -> List[EnumeratedDomain]:
        """Get all enumerated domain values"""
        return [dv for dv in self.domain_values if isinstance(dv, EnumeratedDomain)]

    @property
    def allowed_values(self) -> Optional[List[str]]:
        """Get list of allowed values if enumerated, None otherwise"""
        if self.has_enumerated_values:
            return [ed.value for ed in self.enumerated_values]
        return None

    def get_domain_by_type(self, domain_type: DomainType) -> List[AttributeDomainValue]:
        """Get domain values filtered by type"""
        return [dv for dv in self.domain_values if dv.type == domain_type]

    class Config:
        json_schema_extra = {
            "example": {
                "label": "ACTIVITY_CODE",
                "definition": "Activity code from FACTS system",
                "definition_source": "U.S. Forest Service",
                "domain_values": [
                    {
                        "type": "enumerated",
                        "value": "1111",
                        "value_definition": "Broadcast Burning",
                        "value_definition_source": "FACTS User Guide",
                    }
                ],
            }
        }


class DetailedEntityInfo(BaseModel):
    """Detailed entity and attribute information

    Corresponds to FGDC <detailed> element
    Contains entity type and all attribute definitions
    """

    entity_type: EntityType = Field(..., description="Entity type information")
    attributes: List[Attribute] = Field(
        default_factory=list, description="List of attribute definitions"
    )

    @property
    def attribute_count(self) -> int:
        """Get total number of attributes"""
        return len(self.attributes)

    @property
    def attribute_labels(self) -> List[str]:
        """Get list of all attribute labels (column names)"""
        return [attr.label for attr in self.attributes]

    def get_attribute(self, label: str) -> Optional[Attribute]:
        """Get attribute by label (case-insensitive)"""
        label_lower = label.lower()
        for attr in self.attributes:
            if attr.label.lower() == label_lower:
                return attr
        return None

    def get_attributes_with_enumerated_domains(self) -> List[Attribute]:
        """Get all attributes that have enumerated domain values"""
        return [attr for attr in self.attributes if attr.has_enumerated_values]


class DatasetMetadata(BaseModel):
    """Dataset-level metadata to extend EntityType

    Additional metadata not present in FGDC XML but useful for data librarian features
    """

    dataset_name: Optional[str] = Field(
        None, description="Short name for lookups (e.g., 'BrushDisposal')"
    )
    display_name: Optional[str] = Field(None, description="Human-friendly display name")
    dataset_type: Optional[str] = Field(
        None, description="Type: feature_class, table, view, raster, etc."
    )
    source_system: Optional[str] = Field(
        None, description="Source system (e.g., 'USFS GIS', 'ArcGIS Online')"
    )
    source_url: Optional[str] = Field(None, description="URL to source data or service")
    record_count: Optional[int] = Field(None, description="Number of records/features")
    last_updated_at: Optional[datetime] = Field(
        None, description="Last data update timestamp"
    )
    spatial_extent: Optional[dict] = Field(
        None, description="Bounding box or extent as GeoJSON"
    )
    tags: Optional[List[str]] = Field(default_factory=list, description="Search tags")

    class Config:
        json_schema_extra = {
            "example": {
                "dataset_name": "BrushDisposal",
                "display_name": "Brush Disposal Sites",
                "dataset_type": "feature_class",
                "source_system": "USFS GIS",
                "record_count": 1247,
                "tags": ["fire management", "disposal", "geospatial"],
            }
        }


class TechnicalFieldMetadata(BaseModel):
    """Technical field metadata to extend Attribute

    Technical details about fields not typically in FGDC XML
    """

    data_type: Optional[str] = Field(
        None, description="Data type: Integer, String, Float, Date, Geometry, etc."
    )
    is_nullable: bool = Field(True, description="Can this field contain NULL values?")
    is_primary_key: bool = Field(False, description="Is this a primary key field?")
    is_foreign_key: bool = Field(
        False, description="Is this a foreign key to another table?"
    )
    max_length: Optional[int] = Field(
        None, description="Maximum length (for string fields)"
    )
    precision: Optional[int] = Field(None, description="Numeric precision")
    scale: Optional[int] = Field(None, description="Numeric scale")
    default_value: Optional[str] = Field(
        None, description="Default value if not provided"
    )

    # Quality metrics (computed from data profiling)
    completeness_percent: Optional[float] = Field(
        None, description="Percentage of non-null values"
    )
    uniqueness_percent: Optional[float] = Field(
        None, description="Percentage of unique values"
    )
    min_value: Optional[str] = Field(None, description="Minimum observed value")
    max_value: Optional[str] = Field(None, description="Maximum observed value")
    sample_values: Optional[List[str]] = Field(
        None, description="Example values from the data"
    )
    last_profiled_at: Optional[datetime] = Field(
        None, description="When profiling was last run"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "data_type": "Integer",
                "is_nullable": False,
                "is_primary_key": True,
                "completeness_percent": 100.0,
                "uniqueness_percent": 100.0,
                "min_value": "1",
                "max_value": "1247",
            }
        }


class FieldLineage(BaseModel):
    """Field-level lineage information"""

    source_dataset: str
    source_field: str
    transformation_type: str = Field(
        ..., description="direct_copy, calculation, aggregation, etc."
    )
    transformation_logic: Optional[str] = None
    confidence_score: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Confidence score 0.0-1.0"
    )
    is_verified: bool = Field(False, description="Manually verified lineage?")
    notes: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "source_dataset": "DisposalSites_Raw",
                "source_field": "SITE_ID",
                "transformation_type": "direct_copy",
                "transformation_logic": "Copied without transformation during ETL",
                "confidence_score": 1.0,
                "is_verified": True,
            }
        }


class EntityAttributeInfo(BaseModel):
    """Top-level eainfo structure

    Corresponds to FGDC <eainfo> element
    Root container for entity and attribute information
    """

    detailed: Optional[DetailedEntityInfo] = Field(
        None, description="Detailed entity and attribute information"
    )
    overview: Optional[str] = Field(
        None, description="Overview description (eaover) - optional general description"
    )
    citation: Optional[str] = Field(
        None,
        description="Entity and attribute detail citation (eadetcit) - optional reference",
    )

    # Metadata about the parsing/creation
    parsed_at: Optional[datetime] = Field(
        None, description="Timestamp when this metadata was parsed"
    )
    source_file: Optional[str] = Field(None, description="Source XML file path")

    # Extended metadata (not from XML)
    dataset_metadata: Optional[DatasetMetadata] = Field(
        None, description="Additional dataset-level metadata"
    )

    @property
    def has_detailed_info(self) -> bool:
        """Check if detailed information is available"""
        return self.detailed is not None

    @property
    def total_attributes(self) -> int:
        """Get total number of attributes across all entities"""
        if not self.has_detailed_info:
            return 0
        return self.detailed.attribute_count

    def to_schema_dict(self) -> dict:
        """Convert to simplified schema dictionary for database storage"""
        if not self.has_detailed_info:
            return {}

        return {
            "entity_label": self.detailed.entity_type.label,
            "entity_definition": self.detailed.entity_type.definition,
            "attributes": [
                {
                    "name": attr.label,
                    "definition": attr.definition,
                    "source": attr.definition_source,
                    "domain_type": attr.domain_values[0].type
                    if attr.domain_values
                    else None,
                    "allowed_values": attr.allowed_values,
                }
                for attr in self.detailed.attributes
            ],
        }

    class Config:
        json_schema_extra = {
            "example": {
                "detailed": {
                    "entity_type": {
                        "label": "S_USA.Activity_BrushDisposal",
                        "definition": "Feature class for brush disposal activities",
                    },
                    "attributes": [
                        {
                            "label": "OBJECTID",
                            "definition": "Internal feature number",
                            "definition_source": "Esri",
                        }
                    ],
                },
                "parsed_at": "2025-11-04T10:30:00Z",
                "source_file": "scratch.xml",
            }
        }


class EAInfoParser:
    """Parser for FGDC Entity and Attribute Information (eainfo) sections"""

    @staticmethod
    def parse_domain_value(domv_elem: ET.Element) -> Optional[AttributeDomainValue]:
        """Parse a single attrdomv element into appropriate domain type"""
        try:
            # Check for unrepresentable domain (udom)
            if (udom_elem := domv_elem.find("udom")) is not None:
                text = udom_elem.text or ""
                if text.strip():
                    return UnrepresentableDomain(description=text.strip())

            # Check for enumerated domain (edom)
            elif (edom_elem := domv_elem.find("edom")) is not None:
                value = edom_elem.findtext("edomv", "").strip()
                definition = edom_elem.findtext("edomvd", "").strip()
                if value and definition:
                    return EnumeratedDomain(
                        value=value,
                        value_definition=definition,
                        value_definition_source=edom_elem.findtext("edomvds"),
                    )

            # Check for codeset domain (codesetd)
            elif (codesetd_elem := domv_elem.find("codesetd")) is not None:
                name = codesetd_elem.findtext("codesetn", "").strip()
                source = codesetd_elem.findtext("codesets", "").strip()
                if name and source:
                    return CodesetDomain(codeset_name=name, codeset_source=source)

            # Check for range domain (rdom)
            elif (rdom_elem := domv_elem.find("rdom")) is not None:
                min_val = rdom_elem.findtext("rdommin")
                max_val = rdom_elem.findtext("rdommax")
                units = rdom_elem.findtext("attrunit")

                return RangeDomain(
                    min_value=float(min_val) if min_val else None,
                    max_value=float(max_val) if max_val else None,
                    units=units,
                )

        except Exception as e:
            logger.warning(f"Failed to parse domain value: {e}")
            return None

        return None

    @staticmethod
    def parse_attribute(attr_elem: ET.Element) -> Optional[Attribute]:
        """Parse a single attr element into Attribute object"""
        try:
            label = attr_elem.findtext("attrlabl", "").strip()
            definition = attr_elem.findtext("attrdef", "").strip()

            if not label or not definition:
                logger.warning(f"Skipping attribute with missing label or definition")
                return None

            # Parse all domain values
            domain_values = []
            for domv_elem in attr_elem.findall("attrdomv"):
                domain_val = EAInfoParser.parse_domain_value(domv_elem)
                if domain_val:
                    domain_values.append(domain_val)

            return Attribute(
                label=label,
                definition=definition,
                definition_source=attr_elem.findtext("attrdefs"),
                domain_values=domain_values,
            )

        except Exception as e:
            logger.error(f"Failed to parse attribute: {e}")
            return None

    @staticmethod
    def parse_entity_type(enttyp_elem: ET.Element) -> Optional[EntityType]:
        """Parse enttyp element into EntityType object"""
        try:
            label = enttyp_elem.findtext("enttypl", "").strip()
            if not label:
                logger.warning("Entity type missing label")
                return None

            return EntityType(
                label=label,
                definition=enttyp_elem.findtext("enttypd"),
                definition_source=enttyp_elem.findtext("enttypds"),
            )

        except Exception as e:
            logger.error(f"Failed to parse entity type: {e}")
            return None

    @staticmethod
    def parse_detailed(detailed_elem: ET.Element) -> Optional[DetailedEntityInfo]:
        """Parse detailed element into DetailedEntityInfo object"""
        try:
            # Parse entity type
            enttyp_elem = detailed_elem.find("enttyp")
            if enttyp_elem is None:
                logger.warning("No entity type found in detailed section")
                return None

            entity_type = EAInfoParser.parse_entity_type(enttyp_elem)
            if not entity_type:
                return None

            # Parse all attributes
            attributes = []
            for attr_elem in detailed_elem.findall("attr"):
                attr = EAInfoParser.parse_attribute(attr_elem)
                if attr:
                    attributes.append(attr)

            logger.info(
                f"Parsed {len(attributes)} attributes for entity {entity_type.label}"
            )

            return DetailedEntityInfo(entity_type=entity_type, attributes=attributes)

        except Exception as e:
            logger.error(f"Failed to parse detailed section: {e}")
            return None

    @staticmethod
    def parse_eainfo(
        eainfo_elem: ET.Element, source_file: Optional[str] = None
    ) -> EntityAttributeInfo:
        """Parse eainfo element into EntityAttributeInfo object

        Args:
            eainfo_elem: XML element containing eainfo data
            source_file: Optional path to source XML file

        Returns:
            EntityAttributeInfo object
        """
        try:
            detailed = None
            detailed_elem = eainfo_elem.find("detailed")
            if detailed_elem is not None:
                detailed = EAInfoParser.parse_detailed(detailed_elem)

            # Parse optional overview and citation
            overview = eainfo_elem.findtext("overview/eaover")
            citation = eainfo_elem.findtext("overview/eadetcit")

            return EntityAttributeInfo(
                detailed=detailed,
                overview=overview,
                citation=citation,
                parsed_at=datetime.now(),
                source_file=source_file,
            )

        except Exception as e:
            logger.error(f"Failed to parse eainfo: {e}")
            return EntityAttributeInfo(source_file=source_file)

    @staticmethod
    def parse_xml_file(xml_file_path: str) -> EntityAttributeInfo:
        """Parse XML file and extract eainfo section

        Args:
            xml_file_path: Path to FGDC XML metadata file

        Returns:
            EntityAttributeInfo object

        Example:
            >>> parser = EAInfoParser()
            >>> eainfo = parser.parse_xml_file('scratch.xml')
            >>> print(f"Found {eainfo.total_attributes} attributes")
        """
        file_path = Path(xml_file_path)
        if not file_path.exists():
            logger.error(f"File not found: {xml_file_path}")
            return EntityAttributeInfo(source_file=xml_file_path)

        try:
            tree = ET.parse(xml_file_path)
            eainfo_elem = tree.find(".//eainfo")

            if eainfo_elem is None:
                logger.warning(f"No eainfo element found in {xml_file_path}")
                return EntityAttributeInfo(source_file=xml_file_path)

            return EAInfoParser.parse_eainfo(eainfo_elem, source_file=xml_file_path)

        except ET.ParseError as e:
            logger.error(f"XML parsing error in {xml_file_path}: {e}")
            return EntityAttributeInfo(source_file=xml_file_path)
        except Exception as e:
            logger.error(f"Unexpected error parsing {xml_file_path}: {e}")
            return EntityAttributeInfo(source_file=xml_file_path)


if __name__ == "__main__":
    SOURCE_DIR = "data/catalog"
    xml_file_path = f"{SOURCE_DIR}/Actv_BrushDisposal.xml"

    # Parse XML file
    parser = EAInfoParser()
    eainfo = parser.parse_xml_file(xml_file_path)

    # Parse and save
    parser = EAInfoParser()
    eainfo = parser.parse_xml_file("data/catalog/Actv_BrushDisposal.xml")
    eainfo_id = save_eainfo(eainfo)

    # Retrieve
    saved_eainfo = get_eainfo_by_id(eainfo_id)
    print(f"Entity: {saved_eainfo['entity_type']['label']}")
    print(f"Attributes: {len(saved_eainfo['entity_type']['attributes'])}")

    # List all
    entities = list_all_entities()
    for entity in entities:
        print(f"{entity['label']}: {entity['attribute_count']} attributes")

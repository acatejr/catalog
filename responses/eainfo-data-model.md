# EAINFO Data Model - Refined Design

## Overview

This document presents a refined Python data model for representing FGDC metadata's `<eainfo>` (Entity and Attribute Information) section. The model is based on analysis of the `scratch.xml` file and designed for integration with the Catalog project.

## Design Goals

1. **Type Safety**: Leverage Python type hints and Pydantic validation
2. **Flexibility**: Support all FGDC domain value types (udom, edom, codesetd, rdom)
3. **Extensibility**: Easy to add new fields or domain types
4. **Integration**: Compatible with existing Catalog schema and database structure
5. **Performance**: Efficient parsing and serialization for large metadata files
6. **Developer Experience**: Clear structure with helpful methods and documentation

## Data Model

### Using Pydantic for Validation

```python
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Union, Literal
from enum import Enum
from datetime import datetime


class DomainType(str, Enum):
    """Types of attribute domain values in FGDC metadata"""
    UNREPRESENTABLE = "unrepresentable"  # udom - free text description
    ENUMERATED = "enumerated"            # edom - specific allowed values
    CODESET = "codeset"                  # codesetd - external reference
    RANGE = "range"                      # rdom - numeric range


class EntityType(BaseModel):
    """Entity type information describing the feature class or table

    Corresponds to FGDC <enttyp> element
    """
    label: str = Field(..., description="Entity Type Label (enttypl) - name of the feature class/table")
    definition: Optional[str] = Field(None, description="Entity Type Definition (enttypd)")
    definition_source: Optional[str] = Field(None, description="Entity Type Definition Source (enttypds)")

    class Config:
        json_schema_extra = {
            "example": {
                "label": "S_USA.Activity_BrushDisposal",
                "definition": "A collection of geographic features with the same geometry type",
                "definition_source": "http://support.esri.com/en/knowledgebase/GISDictionary/term/feature%20class"
            }
        }


class UnrepresentableDomain(BaseModel):
    """Free-text domain description for attributes without specific constraints

    Corresponds to FGDC <udom> element
    Used when values don't fit enumerated/range/codeset patterns
    """
    type: Literal[DomainType.UNREPRESENTABLE] = DomainType.UNREPRESENTABLE
    description: str = Field(..., min_length=1, description="Free-text description of valid values")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "unrepresentable",
                "description": "Sequential unique whole numbers that are automatically generated."
            }
        }


class EnumeratedDomain(BaseModel):
    """Enumerated domain with specific allowed values

    Corresponds to FGDC <edom> element
    Used for fields with discrete, predefined values (e.g., status codes, categories)
    """
    type: Literal[DomainType.ENUMERATED] = DomainType.ENUMERATED
    value: str = Field(..., description="Enumerated Domain Value (edomv)")
    value_definition: str = Field(..., min_length=1, description="Enumerated Domain Value Definition (edomvd)")
    value_definition_source: Optional[str] = Field(None, description="Enumerated Domain Value Definition Source (edomvds)")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "enumerated",
                "value": "1111",
                "value_definition": "Broadcast Burning - Covers a majority of the unit",
                "value_definition_source": "FACTS User Guide, Appendix B: Activity Codes"
            }
        }


class CodesetDomain(BaseModel):
    """Reference to external codeset or controlled vocabulary

    Corresponds to FGDC <codesetd> element
    Used when values are defined in external standards (e.g., ISO codes, FIPS codes)
    """
    type: Literal[DomainType.CODESET] = DomainType.CODESET
    codeset_name: str = Field(..., min_length=1, description="Name of the codeset (codesetn)")
    codeset_source: str = Field(..., description="URL or reference to codeset documentation (codesets)")

    @field_validator('codeset_source')
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
                "codeset_source": "http://www.census.gov/geo/reference/ansi_statetables.html"
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

    @model_validator(mode='after')
    def validate_range(self):
        """Ensure min <= max if both provided"""
        if (self.min_value is not None and
            self.max_value is not None and
            self.min_value > self.max_value):
            raise ValueError(f"min_value ({self.min_value}) cannot be greater than max_value ({self.max_value})")
        return self

    class Config:
        json_schema_extra = {
            "example": {
                "type": "range",
                "min_value": 0.0,
                "max_value": 100.0,
                "units": "percent"
            }
        }


# Union type for all possible domain value types
AttributeDomainValue = Union[
    UnrepresentableDomain,
    EnumeratedDomain,
    CodesetDomain,
    RangeDomain
]


class Attribute(BaseModel):
    """Individual attribute/field definition

    Corresponds to FGDC <attr> element
    Describes a single column in a feature class or table
    """
    label: str = Field(..., min_length=1, description="Attribute Label (attrlabl) - column name")
    definition: str = Field(..., min_length=1, description="Attribute Definition (attrdef)")
    definition_source: Optional[str] = Field(None, description="Attribute Definition Source (attrdefs)")
    domain_values: List[AttributeDomainValue] = Field(
        default_factory=list,
        description="List of domain value specifications (attrdomv) - can have multiple"
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
                        "value_definition_source": "FACTS User Guide"
                    }
                ]
            }
        }


class DetailedEntityInfo(BaseModel):
    """Detailed entity and attribute information

    Corresponds to FGDC <detailed> element
    Contains entity type and all attribute definitions
    """
    entity_type: EntityType = Field(..., description="Entity type information")
    attributes: List[Attribute] = Field(
        default_factory=list,
        description="List of attribute definitions"
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


class EntityAttributeInfo(BaseModel):
    """Top-level eainfo structure

    Corresponds to FGDC <eainfo> element
    Root container for entity and attribute information
    """
    detailed: Optional[DetailedEntityInfo] = Field(
        None,
        description="Detailed entity and attribute information"
    )
    overview: Optional[str] = Field(
        None,
        description="Overview description (eaover) - optional general description"
    )
    citation: Optional[str] = Field(
        None,
        description="Entity and attribute detail citation (eadetcit) - optional reference"
    )

    # Metadata about the parsing/creation
    parsed_at: Optional[datetime] = Field(
        None,
        description="Timestamp when this metadata was parsed"
    )
    source_file: Optional[str] = Field(
        None,
        description="Source XML file path"
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
                    "domain_type": attr.domain_values[0].type if attr.domain_values else None,
                    "allowed_values": attr.allowed_values
                }
                for attr in self.detailed.attributes
            ]
        }

    class Config:
        json_schema_extra = {
            "example": {
                "detailed": {
                    "entity_type": {
                        "label": "S_USA.Activity_BrushDisposal",
                        "definition": "Feature class for brush disposal activities"
                    },
                    "attributes": [
                        {
                            "label": "OBJECTID",
                            "definition": "Internal feature number",
                            "definition_source": "Esri"
                        }
                    ]
                },
                "parsed_at": "2025-11-04T10:30:00Z",
                "source_file": "scratch.xml"
            }
        }
```

## XML Parser Implementation

```python
from xml.etree import ElementTree as ET
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class EAInfoParser:
    """Parser for FGDC Entity and Attribute Information (eainfo) sections"""

    @staticmethod
    def parse_domain_value(domv_elem: ET.Element) -> Optional[AttributeDomainValue]:
        """Parse a single attrdomv element into appropriate domain type"""
        try:
            # Check for unrepresentable domain (udom)
            if (udom_elem := domv_elem.find('udom')) is not None:
                text = udom_elem.text or ''
                if text.strip():
                    return UnrepresentableDomain(description=text.strip())

            # Check for enumerated domain (edom)
            elif (edom_elem := domv_elem.find('edom')) is not None:
                value = edom_elem.findtext('edomv', '').strip()
                definition = edom_elem.findtext('edomvd', '').strip()
                if value and definition:
                    return EnumeratedDomain(
                        value=value,
                        value_definition=definition,
                        value_definition_source=edom_elem.findtext('edomvds')
                    )

            # Check for codeset domain (codesetd)
            elif (codesetd_elem := domv_elem.find('codesetd')) is not None:
                name = codesetd_elem.findtext('codesetn', '').strip()
                source = codesetd_elem.findtext('codesets', '').strip()
                if name and source:
                    return CodesetDomain(
                        codeset_name=name,
                        codeset_source=source
                    )

            # Check for range domain (rdom)
            elif (rdom_elem := domv_elem.find('rdom')) is not None:
                min_val = rdom_elem.findtext('rdommin')
                max_val = rdom_elem.findtext('rdommax')
                units = rdom_elem.findtext('attrunit')

                return RangeDomain(
                    min_value=float(min_val) if min_val else None,
                    max_value=float(max_val) if max_val else None,
                    units=units
                )

        except Exception as e:
            logger.warning(f"Failed to parse domain value: {e}")
            return None

        return None

    @staticmethod
    def parse_attribute(attr_elem: ET.Element) -> Optional[Attribute]:
        """Parse a single attr element into Attribute object"""
        try:
            label = attr_elem.findtext('attrlabl', '').strip()
            definition = attr_elem.findtext('attrdef', '').strip()

            if not label or not definition:
                logger.warning(f"Skipping attribute with missing label or definition")
                return None

            # Parse all domain values
            domain_values = []
            for domv_elem in attr_elem.findall('attrdomv'):
                domain_val = EAInfoParser.parse_domain_value(domv_elem)
                if domain_val:
                    domain_values.append(domain_val)

            return Attribute(
                label=label,
                definition=definition,
                definition_source=attr_elem.findtext('attrdefs'),
                domain_values=domain_values
            )

        except Exception as e:
            logger.error(f"Failed to parse attribute: {e}")
            return None

    @staticmethod
    def parse_entity_type(enttyp_elem: ET.Element) -> Optional[EntityType]:
        """Parse enttyp element into EntityType object"""
        try:
            label = enttyp_elem.findtext('enttypl', '').strip()
            if not label:
                logger.warning("Entity type missing label")
                return None

            return EntityType(
                label=label,
                definition=enttyp_elem.findtext('enttypd'),
                definition_source=enttyp_elem.findtext('enttypds')
            )

        except Exception as e:
            logger.error(f"Failed to parse entity type: {e}")
            return None

    @staticmethod
    def parse_detailed(detailed_elem: ET.Element) -> Optional[DetailedEntityInfo]:
        """Parse detailed element into DetailedEntityInfo object"""
        try:
            # Parse entity type
            enttyp_elem = detailed_elem.find('enttyp')
            if enttyp_elem is None:
                logger.warning("No entity type found in detailed section")
                return None

            entity_type = EAInfoParser.parse_entity_type(enttyp_elem)
            if not entity_type:
                return None

            # Parse all attributes
            attributes = []
            for attr_elem in detailed_elem.findall('attr'):
                attr = EAInfoParser.parse_attribute(attr_elem)
                if attr:
                    attributes.append(attr)

            logger.info(f"Parsed {len(attributes)} attributes for entity {entity_type.label}")

            return DetailedEntityInfo(
                entity_type=entity_type,
                attributes=attributes
            )

        except Exception as e:
            logger.error(f"Failed to parse detailed section: {e}")
            return None

    @staticmethod
    def parse_eainfo(eainfo_elem: ET.Element, source_file: Optional[str] = None) -> EntityAttributeInfo:
        """Parse eainfo element into EntityAttributeInfo object

        Args:
            eainfo_elem: XML element containing eainfo data
            source_file: Optional path to source XML file

        Returns:
            EntityAttributeInfo object
        """
        try:
            detailed = None
            detailed_elem = eainfo_elem.find('detailed')
            if detailed_elem is not None:
                detailed = EAInfoParser.parse_detailed(detailed_elem)

            # Parse optional overview and citation
            overview = eainfo_elem.findtext('overview/eaover')
            citation = eainfo_elem.findtext('overview/eadetcit')

            return EntityAttributeInfo(
                detailed=detailed,
                overview=overview,
                citation=citation,
                parsed_at=datetime.now(),
                source_file=source_file
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
            eainfo_elem = tree.find('.//eainfo')

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
```

## Integration with Catalog Project

### Database Schema Extension

Add to `sql/schema.sql`:

```sql
-- Table to store entity attribute information
CREATE TABLE IF NOT EXISTS entity_attribute_info (
    id SERIAL PRIMARY KEY,
    dataset_id INTEGER REFERENCES datasets(id) ON DELETE CASCADE,
    entity_label VARCHAR(255) NOT NULL,
    entity_definition TEXT,
    entity_definition_source TEXT,
    parsed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source_file TEXT,
    UNIQUE(dataset_id, entity_label)
);

CREATE INDEX idx_eainfo_dataset ON entity_attribute_info(dataset_id);

-- Table to store individual attributes
CREATE TABLE IF NOT EXISTS attributes (
    id SERIAL PRIMARY KEY,
    eainfo_id INTEGER REFERENCES entity_attribute_info(id) ON DELETE CASCADE,
    label VARCHAR(255) NOT NULL,
    definition TEXT NOT NULL,
    definition_source TEXT,
    position INTEGER,  -- Order in the table
    UNIQUE(eainfo_id, label)
);

CREATE INDEX idx_attributes_eainfo ON attributes(eainfo_id);

-- Table to store domain values (normalized)
CREATE TABLE IF NOT EXISTS attribute_domains (
    id SERIAL PRIMARY KEY,
    attribute_id INTEGER REFERENCES attributes(id) ON DELETE CASCADE,
    domain_type VARCHAR(50) NOT NULL,  -- 'unrepresentable', 'enumerated', 'codeset', 'range'

    -- Unrepresentable domain fields
    description TEXT,

    -- Enumerated domain fields
    enum_value VARCHAR(255),
    enum_value_definition TEXT,
    enum_value_definition_source TEXT,

    -- Codeset domain fields
    codeset_name VARCHAR(255),
    codeset_source TEXT,

    -- Range domain fields
    min_value DOUBLE PRECISION,
    max_value DOUBLE PRECISION,
    units VARCHAR(100),

    position INTEGER  -- Order in domain list
);

CREATE INDEX idx_domains_attribute ON attribute_domains(attribute_id);
CREATE INDEX idx_domains_type ON attribute_domains(domain_type);

-- Create view for easy querying
CREATE OR REPLACE VIEW v_attribute_summary AS
SELECT
    eai.dataset_id,
    eai.entity_label,
    a.label as attribute_label,
    a.definition as attribute_definition,
    COUNT(DISTINCT ad.id) as domain_count,
    STRING_AGG(DISTINCT ad.domain_type, ', ') as domain_types,
    COUNT(CASE WHEN ad.domain_type = 'enumerated' THEN 1 END) as enum_value_count
FROM entity_attribute_info eai
JOIN attributes a ON a.eainfo_id = eai.id
LEFT JOIN attribute_domains ad ON ad.attribute_id = a.id
GROUP BY eai.dataset_id, eai.entity_label, a.label, a.definition;
```

### Database Operations (db.py extension)

```python
# Add to src/catalog/core/db.py

from typing import Optional, List
from .schema_parser import EntityAttributeInfo, Attribute, AttributeDomainValue
from .schema_parser import UnrepresentableDomain, EnumeratedDomain, CodesetDomain, RangeDomain

def store_eainfo(conn, dataset_id: int, eainfo: EntityAttributeInfo) -> Optional[int]:
    """Store EntityAttributeInfo in database

    Args:
        conn: Database connection
        dataset_id: ID of associated dataset
        eainfo: EntityAttributeInfo object to store

    Returns:
        ID of inserted entity_attribute_info record, or None if no detailed info
    """
    if not eainfo.has_detailed_info:
        return None

    cursor = conn.cursor()

    try:
        # Insert entity info
        cursor.execute("""
            INSERT INTO entity_attribute_info
            (dataset_id, entity_label, entity_definition, entity_definition_source, source_file, parsed_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (dataset_id, entity_label)
            DO UPDATE SET
                entity_definition = EXCLUDED.entity_definition,
                entity_definition_source = EXCLUDED.entity_definition_source,
                parsed_at = EXCLUDED.parsed_at
            RETURNING id
        """, (
            dataset_id,
            eainfo.detailed.entity_type.label,
            eainfo.detailed.entity_type.definition,
            eainfo.detailed.entity_type.definition_source,
            eainfo.source_file,
            eainfo.parsed_at
        ))

        eainfo_id = cursor.fetchone()[0]

        # Insert attributes
        for position, attr in enumerate(eainfo.detailed.attributes):
            cursor.execute("""
                INSERT INTO attributes
                (eainfo_id, label, definition, definition_source, position)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (eainfo_id, label)
                DO UPDATE SET
                    definition = EXCLUDED.definition,
                    definition_source = EXCLUDED.definition_source,
                    position = EXCLUDED.position
                RETURNING id
            """, (
                eainfo_id,
                attr.label,
                attr.definition,
                attr.definition_source,
                position
            ))

            attr_id = cursor.fetchone()[0]

            # Insert domain values
            for dom_pos, domain in enumerate(attr.domain_values):
                _store_domain_value(cursor, attr_id, domain, dom_pos)

        conn.commit()
        return eainfo_id

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()


def _store_domain_value(cursor, attribute_id: int, domain: AttributeDomainValue, position: int):
    """Store a single domain value"""
    base_values = {
        'attribute_id': attribute_id,
        'domain_type': domain.type,
        'position': position
    }

    if isinstance(domain, UnrepresentableDomain):
        cursor.execute("""
            INSERT INTO attribute_domains
            (attribute_id, domain_type, description, position)
            VALUES (%(attribute_id)s, %(domain_type)s, %(description)s, %(position)s)
        """, {**base_values, 'description': domain.description})

    elif isinstance(domain, EnumeratedDomain):
        cursor.execute("""
            INSERT INTO attribute_domains
            (attribute_id, domain_type, enum_value, enum_value_definition,
             enum_value_definition_source, position)
            VALUES (%(attribute_id)s, %(domain_type)s, %(enum_value)s,
                    %(enum_value_definition)s, %(enum_value_definition_source)s, %(position)s)
        """, {
            **base_values,
            'enum_value': domain.value,
            'enum_value_definition': domain.value_definition,
            'enum_value_definition_source': domain.value_definition_source
        })

    elif isinstance(domain, CodesetDomain):
        cursor.execute("""
            INSERT INTO attribute_domains
            (attribute_id, domain_type, codeset_name, codeset_source, position)
            VALUES (%(attribute_id)s, %(domain_type)s, %(codeset_name)s, %(codeset_source)s, %(position)s)
        """, {
            **base_values,
            'codeset_name': domain.codeset_name,
            'codeset_source': domain.codeset_source
        })

    elif isinstance(domain, RangeDomain):
        cursor.execute("""
            INSERT INTO attribute_domains
            (attribute_id, domain_type, min_value, max_value, units, position)
            VALUES (%(attribute_id)s, %(domain_type)s, %(min_value)s, %(max_value)s, %(units)s, %(position)s)
        """, {
            **base_values,
            'min_value': domain.min_value,
            'max_value': domain.max_value,
            'units': domain.units
        })


def get_eainfo_for_dataset(conn, dataset_id: int) -> Optional[EntityAttributeInfo]:
    """Retrieve EntityAttributeInfo from database

    Args:
        conn: Database connection
        dataset_id: ID of dataset

    Returns:
        EntityAttributeInfo object or None if not found
    """
    # Implementation left as exercise - reverse of store_eainfo
    pass
```

## Usage Examples

### Basic Parsing

```python
from catalog.core.schema_parser import EAInfoParser

# Parse XML file
parser = EAInfoParser()
eainfo = parser.parse_xml_file('scratch.xml')

# Access entity information
if eainfo.has_detailed_info:
    print(f"Entity: {eainfo.detailed.entity_type.label}")
    print(f"Attributes: {eainfo.total_attributes}")

    # List all attributes
    for attr in eainfo.detailed.attributes:
        print(f"  - {attr.label}: {attr.definition}")
```

### Working with Enumerated Values

```python
# Get attributes with enumerated domains
enum_attrs = eainfo.detailed.get_attributes_with_enumerated_domains()

for attr in enum_attrs:
    print(f"\n{attr.label} allowed values:")
    for enum_val in attr.enumerated_values:
        print(f"  {enum_val.value}: {enum_val.value_definition}")
```

### Database Integration

```python
from catalog.core.db import get_connection, store_eainfo
from catalog.core.schema_parser import EAInfoParser

# Parse and store
parser = EAInfoParser()
eainfo = parser.parse_xml_file('scratch.xml')

with get_connection() as conn:
    dataset_id = 123  # existing dataset ID
    eainfo_id = store_eainfo(conn, dataset_id, eainfo)
    print(f"Stored eainfo with ID: {eainfo_id}")
```

### Export to JSON

```python
# Export for API responses
eainfo_dict = eainfo.model_dump(exclude_none=True)
import json
print(json.dumps(eainfo_dict, indent=2))

# Simplified schema for frontend
schema = eainfo.to_schema_dict()
print(schema)
```

## Testing Strategy

### Unit Tests

```python
# tests/test_schema_parser.py

import pytest
from catalog.core.schema_parser import (
    EntityAttributeInfo, Attribute, EnumeratedDomain,
    UnrepresentableDomain, EAInfoParser
)
from xml.etree import ElementTree as ET


def test_enumerated_domain_validation():
    """Test EnumeratedDomain validation"""
    # Valid domain
    domain = EnumeratedDomain(
        value="1111",
        value_definition="Broadcast Burning"
    )
    assert domain.value == "1111"

    # Invalid - empty definition should fail
    with pytest.raises(ValueError):
        EnumeratedDomain(value="1111", value_definition="")


def test_range_domain_validation():
    """Test RangeDomain min/max validation"""
    from catalog.core.schema_parser import RangeDomain

    # Valid range
    domain = RangeDomain(min_value=0, max_value=100)
    assert domain.min_value == 0

    # Invalid - min > max should fail
    with pytest.raises(ValueError):
        RangeDomain(min_value=100, max_value=0)


def test_attribute_properties():
    """Test Attribute helper properties"""
    attr = Attribute(
        label="STATUS",
        definition="Status code",
        domain_values=[
            EnumeratedDomain(value="A", value_definition="Active"),
            EnumeratedDomain(value="I", value_definition="Inactive")
        ]
    )

    assert attr.has_enumerated_values
    assert attr.allowed_values == ["A", "I"]
    assert len(attr.enumerated_values) == 2


def test_parser_with_sample_xml():
    """Test parsing actual XML"""
    xml_str = """
    <eainfo>
        <detailed>
            <enttyp>
                <enttypl>TestEntity</enttypl>
                <enttypd>Test definition</enttypd>
            </enttyp>
            <attr>
                <attrlabl>TEST_FIELD</attrlabl>
                <attrdef>Test field definition</attrdef>
                <attrdefs>Test Source</attrdefs>
                <attrdomv>
                    <udom>Any text value</udom>
                </attrdomv>
            </attr>
        </detailed>
    </eainfo>
    """

    elem = ET.fromstring(xml_str)
    eainfo = EAInfoParser.parse_eainfo(elem)

    assert eainfo.has_detailed_info
    assert eainfo.detailed.entity_type.label == "TestEntity"
    assert len(eainfo.detailed.attributes) == 1
    assert eainfo.detailed.attributes[0].label == "TEST_FIELD"


def test_parse_scratch_xml():
    """Integration test with actual scratch.xml file"""
    eainfo = EAInfoParser.parse_xml_file('scratch.xml')

    assert eainfo.has_detailed_info
    assert eainfo.total_attributes > 0
    assert eainfo.source_file == 'scratch.xml'

    # Check for known attributes from USFS data
    attr = eainfo.detailed.get_attribute('OBJECTID')
    assert attr is not None
    assert 'feature number' in attr.definition.lower()
```

### Performance Considerations

```python
# For large XML files, consider streaming parser
from lxml import etree

def parse_large_xml_streaming(xml_file_path: str):
    """Memory-efficient parsing for large XML files"""
    context = etree.iterparse(xml_file_path, events=('end',), tag='eainfo')

    for event, elem in context:
        eainfo = EAInfoParser.parse_eainfo(elem)
        yield eainfo

        # Clear element to free memory
        elem.clear()
        while elem.getprevious() is not None:
            del elem.getparent()[0]
```

## CLI Integration

Add to `src/catalog/cli/cli.py`:

```python
@app.command()
def parse_schema(
    xml_file: str = typer.Argument(..., help="Path to XML metadata file"),
    output: Optional[str] = typer.Option(None, help="Output JSON file path"),
    store_db: bool = typer.Option(False, help="Store in database"),
    dataset_id: Optional[int] = typer.Option(None, help="Dataset ID for database storage")
):
    """Parse entity and attribute information from XML metadata"""
    from catalog.core.schema_parser import EAInfoParser
    from catalog.core.db import get_connection, store_eainfo
    import json

    parser = EAInfoParser()
    eainfo = parser.parse_xml_file(xml_file)

    if not eainfo.has_detailed_info:
        typer.echo("No entity/attribute information found in XML file", err=True)
        raise typer.Exit(1)

    typer.echo(f"✓ Parsed entity: {eainfo.detailed.entity_type.label}")
    typer.echo(f"✓ Found {eainfo.total_attributes} attributes")

    # Display enumerated attributes
    enum_attrs = eainfo.detailed.get_attributes_with_enumerated_domains()
    if enum_attrs:
        typer.echo(f"✓ {len(enum_attrs)} attributes have enumerated values")

    # Output to JSON
    if output:
        with open(output, 'w') as f:
            json.dump(eainfo.model_dump(exclude_none=True), f, indent=2, default=str)
        typer.echo(f"✓ Saved to {output}")

    # Store in database
    if store_db:
        if not dataset_id:
            typer.echo("Error: --dataset-id required when using --store-db", err=True)
            raise typer.Exit(1)

        with get_connection() as conn:
            eainfo_id = store_eainfo(conn, dataset_id, eainfo)
            typer.echo(f"✓ Stored in database with ID: {eainfo_id}")
```

Usage:

```bash
# Parse and display
./run-cli.sh parse-schema scratch.xml

# Parse and save to JSON
./run-cli.sh parse-schema scratch.xml --output schema.json

# Parse and store in database
./run-cli.sh parse-schema scratch.xml --store-db --dataset-id 123
```

## API Endpoints

Add to `src/catalog/api/api.py`:

```python
from fastapi import HTTPException
from catalog.core.schema_parser import EntityAttributeInfo

@app.get("/datasets/{dataset_id}/schema")
async def get_dataset_schema(dataset_id: int) -> dict:
    """Get entity and attribute information for a dataset"""
    conn = get_connection()

    try:
        eainfo = get_eainfo_for_dataset(conn, dataset_id)
        if not eainfo or not eainfo.has_detailed_info:
            raise HTTPException(status_code=404, detail="Schema not found")

        return eainfo.to_schema_dict()

    finally:
        conn.close()


@app.get("/datasets/{dataset_id}/attributes/{attribute_label}")
async def get_attribute_detail(dataset_id: int, attribute_label: str) -> dict:
    """Get detailed information about a specific attribute"""
    conn = get_connection()

    try:
        eainfo = get_eainfo_for_dataset(conn, dataset_id)
        if not eainfo or not eainfo.has_detailed_info:
            raise HTTPException(status_code=404, detail="Schema not found")

        attr = eainfo.detailed.get_attribute(attribute_label)
        if not attr:
            raise HTTPException(status_code=404, detail="Attribute not found")

        return attr.model_dump(exclude_none=True)

    finally:
        conn.close()
```

## Future Enhancements

1. **Validation Rules**: Generate data validation rules from domain constraints
2. **Schema Comparison**: Compare schemas across different versions
3. **Documentation Generation**: Auto-generate data dictionaries
4. **Search Enhancement**: Index attribute definitions for better search
5. **Data Quality Checks**: Validate actual data against domain constraints
6. **Visualization**: Generate ER diagrams from entity relationships
7. **Import/Export**: Support other metadata formats (ISO 19115, DCAT)

## References

- [FGDC Content Standard for Digital Geospatial Metadata](https://www.fgdc.gov/standards/projects/metadata/base-metadata/v2_0698.pdf)
- [USGS Metadata Creation Guide](https://www.usgs.gov/data-management/metadata-creation)
- [Pydantic Documentation](https://docs.pydantic.dev/)

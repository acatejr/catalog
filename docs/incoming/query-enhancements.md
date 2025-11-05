# Query Enhancement Design: Data Librarian Capabilities

## Executive Summary

This document outlines enhancements to enable the Catalog API to function as an intelligent data librarian, capable of answering sophisticated queries about schema definitions, data lineage, field-level metadata, and dataset relationships.

The system already has robust schema storage via `schema_parser.py` and the `eainfo` database tables. This enhancement focuses on:

1. Adding query classification and intelligent routing
2. Implementing data lineage tracking
3. Enhancing dataset-level metadata capture
4. Building cross-dataset relationship tracking
5. Adding specialized retrieval strategies for structured queries

### Target Query Types

1. **Schema Queries**: "Is there a schema definition for BrushDisposal? If so, what is that schema?"
2. **Lineage Queries**: "What is the data lineage of the field OBJECTID in BrushDisposal?"
3. **Relationship Queries**: "What datasets reference the BrushDisposal table?"
4. **Quality Queries**: "What is the data quality profile for the OBJECTID field?"
5. **Discovery Queries**: "Show me all datasets that contain geospatial coordinates"

---

## Current State Analysis

### Existing Schema Infrastructure (schema_parser.py)

The system already has comprehensive Pydantic models for metadata storage:

**Data Models** (`src/catalog/core/schema_parser.py`):

- **EntityAttributeInfo** - Top-level container for entity/attribute metadata
  - `overview`: Optional description text
  - `citation`: Optional reference citation
  - `parsed_at`: Timestamp of parsing
  - `source_file`: Path to source XML file
  - `detailed`: DetailedEntityInfo object

- **DetailedEntityInfo** - Contains entity type and attribute list
  - `entity_type`: EntityType object
  - `attributes`: List of Attribute objects
  - Helper methods: `get_attribute()`, `get_attributes_with_enumerated_domains()`

- **EntityType** - Dataset/table definition
  - `label`: Name of the feature class/table
  - `definition`: Description of the entity
  - `definition_source`: Source of the definition

- **Attribute** - Individual field/column definition
  - `label`: Column name
  - `definition`: Field description
  - `definition_source`: Source of definition
  - `domain_values`: List of domain value constraints
  - Helper methods: `has_enumerated_values`, `allowed_values`

- **AttributeDomainValue** - Union of domain types:
  - **UnrepresentableDomain**: Free-text description
  - **EnumeratedDomain**: Discrete allowed values (e.g., status codes)
  - **CodesetDomain**: External codeset reference
  - **RangeDomain**: Numeric min/max constraints with units

**Database Tables** (already implemented):

- **eainfo** - Top-level metadata container
  - `overview`, `citation`, `parsed_at`, `source_file`

- **entity_type** - Entity definitions
  - `label`, `definition`, `definition_source`, `eainfo_id`

- **attribute** - Field definitions
  - `label`, `definition`, `definition_source`, `entity_type_id`

- **attribute_domain** - Domain constraints (stored as JSONB)
  - `domain_type`, `domain_data`, `attribute_id`

**Existing Database Functions** (`src/catalog/core/db.py`):

- `save_eainfo()` - Saves EntityAttributeInfo to database
- `get_eainfo_by_id()` - Retrieves full eainfo with nested structure
- `get_eainfo_by_source_file()` - Finds eainfo by source file path
- `list_all_entities()` - Lists all entity types with attribute counts

### What's Already Working

✅ **Schema Storage**: Complete entity and attribute definitions with domain constraints

✅ **Parser**: Robust XML parser for FGDC metadata (EAInfoParser)

✅ **Database Persistence**: Full CRUD operations for schema metadata

✅ **Data Librarian Persona**: LLM system prompt already configured

✅ **Vector Search**: RAG-based document retrieval for general queries

### What's Missing

❌ **Query Classification**: No intelligent routing based on query intent

❌ **Structured Retrieval**: Can't efficiently answer "What's the schema for X?"

❌ **Data Lineage**: No tracking of field origins or transformations

❌ **Cross-Dataset Relationships**: No foreign key or reference tracking

❌ **Dataset-Level Metadata**: Missing source system, record counts, update timestamps

❌ **Technical Field Metadata**: No explicit data types, nullable flags, or primary key indicators

❌ **Quality Metrics**: No completeness, uniqueness, or distribution statistics

---

## Enhancement Architecture

### 1. Leverage Existing Schema Infrastructure

Rather than creating new parallel structures, we'll extend the existing `eainfo` tables with additional metadata.

#### 1.1 Extend entity_type with Dataset Metadata

Add dataset-level fields to the existing `entity_type` table:

```sql
-- Add dataset-level metadata to existing entity_type table
ALTER TABLE entity_type ADD COLUMN dataset_name VARCHAR(255);
ALTER TABLE entity_type ADD COLUMN display_name VARCHAR(255);
ALTER TABLE entity_type ADD COLUMN dataset_type VARCHAR(50);  -- feature_class, table, view, etc.
ALTER TABLE entity_type ADD COLUMN source_system VARCHAR(100);
ALTER TABLE entity_type ADD COLUMN source_url TEXT;
ALTER TABLE entity_type ADD COLUMN record_count INTEGER;
ALTER TABLE entity_type ADD COLUMN last_updated_at TIMESTAMP;
ALTER TABLE entity_type ADD COLUMN spatial_extent JSONB;  -- Store as GeoJSON
ALTER TABLE entity_type ADD COLUMN metadata JSONB;  -- Flexible extra metadata

-- Create indexes for efficient lookups
CREATE INDEX idx_entity_type_dataset_name ON entity_type(dataset_name);
CREATE INDEX idx_entity_type_dataset_type ON entity_type(dataset_type);
CREATE INDEX idx_entity_type_source_system ON entity_type(source_system);

-- Enable fuzzy text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX idx_entity_type_dataset_name_trgm ON entity_type USING gin (dataset_name gin_trgm_ops);
```

#### 1.2 Extend attribute with Technical Metadata

Add technical field information to the existing `attribute` table:

```sql
-- Add technical field metadata to existing attribute table
ALTER TABLE attribute ADD COLUMN data_type VARCHAR(50);  -- Integer, String, Float, Date, Geometry
ALTER TABLE attribute ADD COLUMN is_nullable BOOLEAN DEFAULT true;
ALTER TABLE attribute ADD COLUMN is_primary_key BOOLEAN DEFAULT false;
ALTER TABLE attribute ADD COLUMN is_foreign_key BOOLEAN DEFAULT false;
ALTER TABLE attribute ADD COLUMN max_length INTEGER;
ALTER TABLE attribute ADD COLUMN field_precision INTEGER;
ALTER TABLE attribute ADD COLUMN field_scale INTEGER;
ALTER TABLE attribute ADD COLUMN default_value TEXT;

-- Quality metrics (computed from actual data if available)
ALTER TABLE attribute ADD COLUMN completeness_percent DECIMAL(5,2);
ALTER TABLE attribute ADD COLUMN uniqueness_percent DECIMAL(5,2);
ALTER TABLE attribute ADD COLUMN min_value TEXT;
ALTER TABLE attribute ADD COLUMN max_value TEXT;
ALTER TABLE attribute ADD COLUMN sample_values TEXT[];
ALTER TABLE attribute ADD COLUMN last_profiled_at TIMESTAMP;
ALTER TABLE attribute ADD COLUMN field_metadata JSONB;  -- Flexible stats storage

CREATE INDEX idx_attribute_data_type ON attribute(data_type);
CREATE INDEX idx_attribute_is_primary_key ON attribute(is_primary_key) WHERE is_primary_key = true;
CREATE INDEX idx_attribute_is_foreign_key ON attribute(is_foreign_key) WHERE is_foreign_key = true;
```

#### 1.3 New: Data Lineage Tables

Add new tables to track field-level lineage:

```sql
-- Track field-level lineage and transformations
CREATE TABLE field_lineage (
    id SERIAL PRIMARY KEY,
    target_attribute_id INTEGER REFERENCES attribute(id) ON DELETE CASCADE,
    source_attribute_id INTEGER REFERENCES attribute(id) ON DELETE CASCADE,
    transformation_type VARCHAR(50),  -- direct_copy, calculation, aggregation, concatenation, etc.
    transformation_logic TEXT,  -- SQL formula, description, or algorithm
    confidence_score DECIMAL(3,2),  -- 0.00 to 1.00 (for inferred lineage)
    is_verified BOOLEAN DEFAULT false,  -- manually verified vs. auto-detected
    created_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100),  -- system, user, or process name
    notes TEXT,
    metadata JSONB
);

CREATE INDEX idx_lineage_target ON field_lineage(target_attribute_id);
CREATE INDEX idx_lineage_source ON field_lineage(source_attribute_id);
CREATE INDEX idx_lineage_confidence ON field_lineage(confidence_score);

-- Track dataset-level dependencies
CREATE TABLE dataset_lineage (
    id SERIAL PRIMARY KEY,
    downstream_entity_id INTEGER REFERENCES entity_type(id) ON DELETE CASCADE,
    upstream_entity_id INTEGER REFERENCES entity_type(id) ON DELETE CASCADE,
    dependency_type VARCHAR(50),  -- foreign_key, view_source, derived_table, data_flow, etc.
    description TEXT,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB,
    UNIQUE(downstream_entity_id, upstream_entity_id)
);

CREATE INDEX idx_dataset_lineage_downstream ON dataset_lineage(downstream_entity_id);
CREATE INDEX idx_dataset_lineage_upstream ON dataset_lineage(upstream_entity_id);
```

#### 1.4 New: Cross-Dataset Relationships

Track relationships between datasets:

```sql
-- Track foreign key and reference relationships
CREATE TABLE dataset_relationships (
    id SERIAL PRIMARY KEY,
    from_entity_id INTEGER REFERENCES entity_type(id) ON DELETE CASCADE,
    from_attribute_id INTEGER REFERENCES attribute(id) ON DELETE CASCADE,
    to_entity_id INTEGER REFERENCES entity_type(id) ON DELETE CASCADE,
    to_attribute_id INTEGER REFERENCES attribute(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50),  -- one_to_one, one_to_many, many_to_many
    relationship_name VARCHAR(255),  -- descriptive name (e.g., "disposal_site_monitoring")
    is_enforced BOOLEAN DEFAULT false,  -- database constraint exists?
    cardinality VARCHAR(50),  -- optional, required, etc.
    created_at TIMESTAMP DEFAULT NOW(),
    notes TEXT,
    metadata JSONB
);

CREATE INDEX idx_rel_from_entity ON dataset_relationships(from_entity_id);
CREATE INDEX idx_rel_to_entity ON dataset_relationships(to_entity_id);
CREATE INDEX idx_rel_from_attribute ON dataset_relationships(from_attribute_id);
CREATE INDEX idx_rel_to_attribute ON dataset_relationships(to_attribute_id);
```

---

### 2. Enhanced Pydantic Models

Extend the existing models in `schema_parser.py`:

```python
# Add to schema_parser.py - Extended models

class DatasetMetadata(BaseModel):
    """Dataset-level metadata to extend EntityType"""

    dataset_name: Optional[str] = Field(None, description="Short name for lookups (e.g., 'BrushDisposal')")
    display_name: Optional[str] = Field(None, description="Human-friendly display name")
    dataset_type: Optional[str] = Field(None, description="Type: feature_class, table, view, raster, etc.")
    source_system: Optional[str] = Field(None, description="Source system (e.g., 'USFS GIS', 'ArcGIS Online')")
    source_url: Optional[str] = Field(None, description="URL to source data or service")
    record_count: Optional[int] = Field(None, description="Number of records/features")
    last_updated_at: Optional[datetime] = Field(None, description="Last data update timestamp")
    spatial_extent: Optional[dict] = Field(None, description="Bounding box or extent as GeoJSON")
    tags: Optional[List[str]] = Field(default_factory=list, description="Search tags")

    class Config:
        json_schema_extra = {
            "example": {
                "dataset_name": "BrushDisposal",
                "display_name": "Brush Disposal Sites",
                "dataset_type": "feature_class",
                "source_system": "USFS GIS",
                "record_count": 1247,
                "tags": ["fire management", "disposal", "geospatial"]
            }
        }


class TechnicalFieldMetadata(BaseModel):
    """Technical field metadata to extend Attribute"""

    data_type: Optional[str] = Field(None, description="Data type: Integer, String, Float, Date, Geometry, etc.")
    is_nullable: bool = Field(True, description="Can this field contain NULL values?")
    is_primary_key: bool = Field(False, description="Is this a primary key field?")
    is_foreign_key: bool = Field(False, description="Is this a foreign key to another table?")
    max_length: Optional[int] = Field(None, description="Maximum length (for string fields)")
    precision: Optional[int] = Field(None, description="Numeric precision")
    scale: Optional[int] = Field(None, description="Numeric scale")
    default_value: Optional[str] = Field(None, description="Default value if not provided")

    # Quality metrics (computed from data profiling)
    completeness_percent: Optional[float] = Field(None, description="Percentage of non-null values")
    uniqueness_percent: Optional[float] = Field(None, description="Percentage of unique values")
    min_value: Optional[str] = Field(None, description="Minimum observed value")
    max_value: Optional[str] = Field(None, description="Maximum observed value")
    sample_values: Optional[List[str]] = Field(None, description="Example values from the data")
    last_profiled_at: Optional[datetime] = Field(None, description="When profiling was last run")

    class Config:
        json_schema_extra = {
            "example": {
                "data_type": "Integer",
                "is_nullable": False,
                "is_primary_key": True,
                "completeness_percent": 100.0,
                "uniqueness_percent": 100.0,
                "min_value": "1",
                "max_value": "1247"
            }
        }


class FieldLineage(BaseModel):
    """Field-level lineage information"""

    source_dataset: str
    source_field: str
    transformation_type: str  # direct_copy, calculation, aggregation, etc.
    transformation_logic: Optional[str] = None
    confidence_score: Optional[float] = None
    is_verified: bool = False
    notes: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "source_dataset": "DisposalSites_Raw",
                "source_field": "SITE_ID",
                "transformation_type": "direct_copy",
                "transformation_logic": "Copied without transformation during ETL",
                "confidence_score": 1.0,
                "is_verified": True
            }
        }
```

---

### 3. Enhanced Database Functions

Add new retrieval functions to `db.py` that work with the extended schema:

```python
# Add to src/catalog/core/db.py

@retry_on_db_error(max_retries=3)
def search_entity_by_name(dataset_name: str) -> Optional[dict]:
    """
    Search for a dataset by name (exact or fuzzy match).

    Returns complete entity information including schema.
    Uses pg_trgm for fuzzy matching if exact match not found.

    Args:
        dataset_name: Name to search for

    Returns:
        Dict with entity metadata, attributes, and domain values
    """
    db = get_db()
    conn = db.get_connection()

    try:
        with conn.cursor() as cur:
            # Try exact match on dataset_name or label
            cur.execute("""
                SELECT id, label, definition, definition_source, eainfo_id,
                       dataset_name, display_name, dataset_type, source_system,
                       record_count, last_updated_at, metadata
                FROM entity_type
                WHERE LOWER(dataset_name) = LOWER(%s)
                   OR LOWER(label) = LOWER(%s)
            """, (dataset_name, dataset_name))

            result = cur.fetchone()

            if not result:
                # Try fuzzy match using similarity
                cur.execute("""
                    SELECT id, label, definition, definition_source, eainfo_id,
                           dataset_name, display_name, dataset_type, source_system,
                           record_count, last_updated_at, metadata,
                           GREATEST(
                               similarity(COALESCE(dataset_name, ''), %s),
                               similarity(label, %s)
                           ) as score
                    FROM entity_type
                    WHERE similarity(COALESCE(dataset_name, ''), %s) > 0.3
                       OR similarity(label, %s) > 0.3
                    ORDER BY score DESC
                    LIMIT 1
                """, (dataset_name, dataset_name, dataset_name, dataset_name))
                result = cur.fetchone()

            if not result:
                return None

            entity = {
                'id': result[0],
                'label': result[1],
                'definition': result[2],
                'definition_source': result[3],
                'eainfo_id': result[4],
                'dataset_name': result[5],
                'display_name': result[6],
                'dataset_type': result[7],
                'source_system': result[8],
                'record_count': result[9],
                'last_updated_at': result[10],
                'metadata': result[11]
            }

            # Get attributes with technical metadata
            entity['attributes'] = get_entity_attributes_extended(entity['id'])

            return entity

    finally:
        db.return_connection(conn)


@retry_on_db_error(max_retries=3)
def get_entity_attributes_extended(entity_type_id: int) -> list[dict]:
    """
    Get all attributes for an entity with technical metadata and domain values.

    Args:
        entity_type_id: ID of the entity type

    Returns:
        List of attribute dicts with complete metadata
    """
    db = get_db()
    conn = db.get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    a.id, a.label, a.definition, a.definition_source,
                    a.data_type, a.is_nullable, a.is_primary_key, a.is_foreign_key,
                    a.max_length, a.field_precision, a.field_scale, a.default_value,
                    a.completeness_percent, a.uniqueness_percent,
                    a.min_value, a.max_value, a.sample_values,
                    a.last_profiled_at, a.field_metadata
                FROM attribute a
                WHERE a.entity_type_id = %s
                ORDER BY
                    CASE WHEN a.is_primary_key THEN 0 ELSE 1 END,
                    a.id
            """, (entity_type_id,))

            attributes = []
            for row in cur.fetchall():
                attr = {
                    'id': row[0],
                    'label': row[1],
                    'definition': row[2],
                    'definition_source': row[3],
                    'technical': {
                        'data_type': row[4],
                        'is_nullable': row[5],
                        'is_primary_key': row[6],
                        'is_foreign_key': row[7],
                        'max_length': row[8],
                        'precision': row[9],
                        'scale': row[10],
                        'default_value': row[11]
                    },
                    'quality': {
                        'completeness_percent': float(row[12]) if row[12] else None,
                        'uniqueness_percent': float(row[13]) if row[13] else None,
                        'min_value': row[14],
                        'max_value': row[15],
                        'sample_values': row[16],
                        'last_profiled_at': row[17]
                    },
                    'metadata': row[18]
                }

                # Get domain values for this attribute
                cur.execute("""
                    SELECT domain_type, domain_data
                    FROM attribute_domain
                    WHERE attribute_id = %s
                """, (row[0],))

                attr['domain_values'] = [
                    {'type': dv[0], 'data': dv[1]}
                    for dv in cur.fetchall()
                ]

                attributes.append(attr)

            return attributes

    finally:
        db.return_connection(conn)


@retry_on_db_error(max_retries=3)
def get_field_lineage(dataset_name: str, field_name: str) -> Optional[dict]:
    """
    Get complete lineage for a specific field.

    Returns both upstream sources and downstream dependents.

    Args:
        dataset_name: Name of the dataset
        field_name: Name of the field

    Returns:
        Dict with upstream sources and downstream dependents
    """
    db = get_db()
    conn = db.get_connection()

    try:
        with conn.cursor() as cur:
            # Find the target attribute
            cur.execute("""
                SELECT a.id, et.label as entity_label
                FROM attribute a
                JOIN entity_type et ON a.entity_type_id = et.id
                WHERE (LOWER(et.dataset_name) = LOWER(%s) OR LOWER(et.label) = LOWER(%s))
                  AND LOWER(a.label) = LOWER(%s)
            """, (dataset_name, dataset_name, field_name))

            result = cur.fetchone()
            if not result:
                return None

            attribute_id = result[0]
            entity_label = result[1]

            # Get upstream sources (where this field comes from)
            cur.execute("""
                SELECT
                    src_et.dataset_name,
                    src_et.label as entity_label,
                    src_a.label as field_name,
                    fl.transformation_type,
                    fl.transformation_logic,
                    fl.confidence_score,
                    fl.is_verified,
                    fl.notes
                FROM field_lineage fl
                JOIN attribute src_a ON fl.source_attribute_id = src_a.id
                JOIN entity_type src_et ON src_a.entity_type_id = src_et.id
                WHERE fl.target_attribute_id = %s
                ORDER BY fl.created_at
            """, (attribute_id,))

            upstream = []
            for row in cur.fetchall():
                upstream.append({
                    'source_dataset': row[0] or row[1],
                    'source_field': row[2],
                    'transformation_type': row[3],
                    'transformation_logic': row[4],
                    'confidence_score': float(row[5]) if row[5] else None,
                    'is_verified': row[6],
                    'notes': row[7]
                })

            # Get downstream dependents (what uses this field)
            cur.execute("""
                SELECT
                    tgt_et.dataset_name,
                    tgt_et.label as entity_label,
                    tgt_a.label as field_name,
                    fl.transformation_type,
                    fl.transformation_logic,
                    fl.is_verified
                FROM field_lineage fl
                JOIN attribute tgt_a ON fl.target_attribute_id = tgt_a.id
                JOIN entity_type tgt_et ON tgt_a.entity_type_id = tgt_et.id
                WHERE fl.source_attribute_id = %s
                ORDER BY fl.created_at
            """, (attribute_id,))

            downstream = []
            for row in cur.fetchall():
                downstream.append({
                    'target_dataset': row[0] or row[1],
                    'target_field': row[2],
                    'transformation_type': row[3],
                    'transformation_logic': row[4],
                    'is_verified': row[5]
                })

            return {
                'dataset': dataset_name,
                'entity_label': entity_label,
                'field': field_name,
                'upstream_sources': upstream,
                'downstream_dependents': downstream,
                'is_source_field': len(upstream) == 0
            }

    finally:
        db.return_connection(conn)


@retry_on_db_error(max_retries=3)
def get_dataset_relationships(dataset_name: str) -> Optional[dict]:
    """
    Get all relationships for a dataset (foreign keys, references).

    Args:
        dataset_name: Name of the dataset

    Returns:
        Dict with outgoing and incoming relationships
    """
    db = get_db()
    conn = db.get_connection()

    try:
        with conn.cursor() as cur:
            # Find the entity
            cur.execute("""
                SELECT id FROM entity_type
                WHERE LOWER(dataset_name) = LOWER(%s) OR LOWER(label) = LOWER(%s)
            """, (dataset_name, dataset_name))

            result = cur.fetchone()
            if not result:
                return None

            entity_id = result[0]

            # Get outgoing relationships (this dataset references others)
            cur.execute("""
                SELECT
                    from_a.label as from_field,
                    to_et.dataset_name as to_dataset,
                    to_et.label as to_entity_label,
                    to_a.label as to_field,
                    dr.relationship_type,
                    dr.relationship_name,
                    dr.is_enforced,
                    dr.notes
                FROM dataset_relationships dr
                JOIN attribute from_a ON dr.from_attribute_id = from_a.id
                JOIN entity_type to_et ON dr.to_entity_id = to_et.id
                JOIN attribute to_a ON dr.to_attribute_id = to_a.id
                WHERE dr.from_entity_id = %s
            """, (entity_id,))

            outgoing = []
            for row in cur.fetchall():
                outgoing.append({
                    'from_field': row[0],
                    'to_dataset': row[1] or row[2],
                    'to_field': row[3],
                    'relationship_type': row[4],
                    'relationship_name': row[5],
                    'is_enforced': row[6],
                    'notes': row[7]
                })

            # Get incoming relationships (other datasets reference this one)
            cur.execute("""
                SELECT
                    from_et.dataset_name as from_dataset,
                    from_et.label as from_entity_label,
                    from_a.label as from_field,
                    to_a.label as to_field,
                    dr.relationship_type,
                    dr.relationship_name,
                    dr.is_enforced,
                    dr.notes
                FROM dataset_relationships dr
                JOIN entity_type from_et ON dr.from_entity_id = from_et.id
                JOIN attribute from_a ON dr.from_attribute_id = from_a.id
                JOIN attribute to_a ON dr.to_attribute_id = to_a.id
                WHERE dr.to_entity_id = %s
            """, (entity_id,))

            incoming = []
            for row in cur.fetchall():
                incoming.append({
                    'from_dataset': row[0] or row[1],
                    'from_field': row[2],
                    'to_field': row[3],
                    'relationship_type': row[4],
                    'relationship_name': row[5],
                    'is_enforced': row[6],
                    'notes': row[7]
                })

            return {
                'dataset': dataset_name,
                'outgoing_relationships': outgoing,
                'incoming_relationships': incoming
            }

    finally:
        db.return_connection(conn)


@retry_on_db_error(max_retries=3)
def list_all_datasets(
    dataset_type: Optional[str] = None,
    source_system: Optional[str] = None,
    limit: int = 100
) -> list[dict]:
    """
    List all datasets with optional filtering.

    Args:
        dataset_type: Filter by dataset type
        source_system: Filter by source system
        limit: Maximum number of results

    Returns:
        List of dataset summary dicts
    """
    db = get_db()
    conn = db.get_connection()

    try:
        with conn.cursor() as cur:
            query = """
                SELECT
                    et.id,
                    COALESCE(et.dataset_name, et.label) as name,
                    et.display_name,
                    et.dataset_type,
                    et.source_system,
                    et.record_count,
                    et.last_updated_at,
                    COUNT(a.id) as attribute_count
                FROM entity_type et
                LEFT JOIN attribute a ON a.entity_type_id = et.id
                WHERE 1=1
            """

            params = []
            if dataset_type:
                query += " AND et.dataset_type = %s"
                params.append(dataset_type)

            if source_system:
                query += " AND et.source_system = %s"
                params.append(source_system)

            query += """
                GROUP BY et.id, et.dataset_name, et.label, et.display_name,
                         et.dataset_type, et.source_system, et.record_count, et.last_updated_at
                ORDER BY COALESCE(et.dataset_name, et.label)
                LIMIT %s
            """
            params.append(limit)

            cur.execute(query, params)

            datasets = []
            for row in cur.fetchall():
                datasets.append({
                    'id': row[0],
                    'name': row[1],
                    'display_name': row[2],
                    'dataset_type': row[3],
                    'source_system': row[4],
                    'record_count': row[5],
                    'last_updated_at': row[6],
                    'attribute_count': row[7]
                })

            return datasets

    finally:
        db.return_connection(conn)
```

---

### 4. Enhanced ChatBot with Query Classification

Update `src/catalog/api/llm.py`:

```python
# Add to src/catalog/api/llm.py

from enum import Enum

class QueryType(str, Enum):
    """Types of queries the system can handle"""
    GENERAL = "general"
    SCHEMA = "schema"
    LINEAGE = "lineage"
    RELATIONSHIPS = "relationships"
    QUALITY = "quality"
    DISCOVERY = "discovery"


def classify_query(self, query: str) -> QueryType:
    """
    Classify the user's query intent using the LLM.

    This routes queries to appropriate retrieval strategies.
    """
    classification_prompt = f"""Classify this data catalog query into ONE category:

1. SCHEMA - Asking about table/dataset structure, fields, data types, or schema definitions
   Examples: "What is the schema for X?", "What fields are in Y?", "Show me the structure of Z"

2. LINEAGE - Asking about data origins, transformations, or field derivation
   Examples: "Where does field X come from?", "What is the lineage of Y?", "How is Z calculated?"

3. RELATIONSHIPS - Asking about connections between datasets
   Examples: "What datasets reference X?", "How is Y related to Z?", "Show foreign keys"

4. QUALITY - Asking about data quality, completeness, or statistics
   Examples: "What is the quality of X?", "How complete is field Y?", "Show stats for Z"

5. DISCOVERY - Searching for datasets by characteristics
   Examples: "Find datasets with coordinates", "Show me spatial data", "What has timestamps?"

6. GENERAL - General questions or document search

Query: "{query}"

Respond with ONLY the category name."""

    response = self.client.chat.completions.create(
        model=self.model,
        messages=[{"role": "user", "content": classification_prompt}],
        max_tokens=10
    )

    classification = response.choices[0].message.content.strip().upper()

    try:
        return QueryType[classification]
    except KeyError:
        return QueryType.GENERAL


def chat(self, message: str = "Hello, how can you help me?") -> str:
    """
    Enhanced chat with query classification and specialized retrieval.
    """
    # Classify the query
    query_type = self.classify_query(message)

    # Route to appropriate handler
    if query_type == QueryType.SCHEMA:
        return self._handle_schema_query(message)
    elif query_type == QueryType.LINEAGE:
        return self._handle_lineage_query(message)
    elif query_type == QueryType.RELATIONSHIPS:
        return self._handle_relationship_query(message)
    elif query_type == QueryType.QUALITY:
        return self._handle_quality_query(message)
    elif query_type == QueryType.DISCOVERY:
        return self._handle_discovery_query(message)
    else:
        return self._handle_general_query(message)


def _handle_schema_query(self, message: str) -> str:
    """Handle schema-specific queries with structured retrieval."""
    # Extract dataset name using LLM
    extraction_prompt = f"""Extract the dataset/table name from this query.
Respond with ONLY the dataset name, nothing else.

Query: "{message}"

Dataset name:"""

    response = self.client.chat.completions.create(
        model=self.model,
        messages=[{"role": "user", "content": extraction_prompt}],
        max_tokens=20
    )

    dataset_name = response.choices[0].message.content.strip()

    # Search for the dataset using existing infrastructure
    from catalog.core.db import search_entity_by_name
    entity = search_entity_by_name(dataset_name)

    if not entity:
        return f"I couldn't find a dataset named '{dataset_name}' in the catalog. Would you like me to search for similar datasets?"

    # Format schema information
    schema_context = f"""Dataset: {entity.get('dataset_name') or entity['label']}
Display Name: {entity.get('display_name', 'N/A')}
Type: {entity.get('dataset_type', 'N/A')}
Description: {entity.get('definition', 'N/A')}
Source System: {entity.get('source_system', 'N/A')}
Record Count: {entity.get('record_count', 'Unknown')}

Schema (Fields):
"""

    for attr in entity.get('attributes', []):
        tech = attr.get('technical', {})
        schema_context += f"""
- {attr['label']} ({tech.get('data_type', 'Unknown')})
  Definition: {attr.get('definition', 'N/A')}
  Nullable: {tech.get('is_nullable', 'Yes')}
  Primary Key: {'Yes' if tech.get('is_primary_key') else 'No'}
  Foreign Key: {'Yes' if tech.get('is_foreign_key') else 'No'}
"""

        # Add domain constraints if present
        domain_values = attr.get('domain_values', [])
        if domain_values:
            schema_context += f"  Domain: {len(domain_values)} constraint(s) defined\n"

    # Use LLM to format a natural response
    response = self.client.chat.completions.create(
        model=self.model,
        messages=[
            {
                "role": "system",
                "content": "You are a professional data librarian. Provide clear, well-organized information about dataset schemas."
            },
            {
                "role": "user",
                "content": f"Context:\n{schema_context}\n\nQuestion: {message}\n\nProvide a clear, professional response about this dataset's schema."
            }
        ]
    )

    return response.choices[0].message.content


def _handle_lineage_query(self, message: str) -> str:
    """Handle data lineage queries."""
    # Extract dataset and field name
    extraction_prompt = f"""Extract the dataset name and field name from this lineage query.
Respond in the format: "dataset_name|field_name"

Query: "{message}"

Answer:"""

    response = self.client.chat.completions.create(
        model=self.model,
        messages=[{"role": "user", "content": extraction_prompt}],
        max_tokens=50
    )

    answer = response.choices[0].message.content.strip()

    try:
        dataset_name, field_name = answer.split('|')
        dataset_name = dataset_name.strip()
        field_name = field_name.strip()
    except:
        return "I couldn't identify the dataset and field name. Please ask like: 'What is the lineage of field OBJECTID in BrushDisposal?'"

    # Get lineage information
    from catalog.core.db import get_field_lineage
    lineage = get_field_lineage(dataset_name, field_name)

    if not lineage:
        return f"I couldn't find lineage information for field '{field_name}' in dataset '{dataset_name}'."

    # Format lineage context
    lineage_context = f"""Field: {lineage['entity_label']}.{lineage['field']}

Upstream Sources (where this field comes from):
"""

    if lineage['upstream_sources']:
        for source in lineage['upstream_sources']:
            verified = " [VERIFIED]" if source['is_verified'] else ""
            lineage_context += f"""
- Source: {source['source_dataset']}.{source['source_field']}{verified}
  Transformation: {source['transformation_type']}
  Logic: {source.get('transformation_logic', 'N/A')}
  Confidence: {source.get('confidence_score', 'N/A')}
"""
            if source.get('notes'):
                lineage_context += f"  Notes: {source['notes']}\n"
    else:
        lineage_context += "  (No upstream sources - this is a source field)\n"

    lineage_context += "\nDownstream Dependents (what uses this field):\n"

    if lineage['downstream_dependents']:
        for dep in lineage['downstream_dependents']:
            verified = " [VERIFIED]" if dep['is_verified'] else ""
            lineage_context += f"""
- Target: {dep['target_dataset']}.{dep['target_field']}{verified}
  Transformation: {dep['transformation_type']}
  Logic: {dep.get('transformation_logic', 'N/A')}
"""
    else:
        lineage_context += "  (No downstream dependents recorded)\n"

    # Use LLM to format response
    response = self.client.chat.completions.create(
        model=self.model,
        messages=[
            {
                "role": "system",
                "content": "You are a professional data librarian specializing in data lineage and provenance."
            },
            {
                "role": "user",
                "content": f"Context:\n{lineage_context}\n\nQuestion: {message}\n\nProvide a clear explanation of this field's data lineage."
            }
        ]
    )

    return response.choices[0].message.content


def _handle_relationship_query(self, message: str) -> str:
    """Handle dataset relationship queries."""
    # Extract dataset name
    extraction_prompt = f"""Extract the dataset/table name from this query.
Respond with ONLY the dataset name.

Query: "{message}"

Dataset name:"""

    response = self.client.chat.completions.create(
        model=self.model,
        messages=[{"role": "user", "content": extraction_prompt}],
        max_tokens=20
    )

    dataset_name = response.choices[0].message.content.strip()

    # Get relationships
    from catalog.core.db import get_dataset_relationships
    relationships = get_dataset_relationships(dataset_name)

    if not relationships:
        return f"I couldn't find the dataset '{dataset_name}' in the catalog."

    # Format relationships context
    rel_context = f"""Dataset: {relationships['dataset']}

Outgoing Relationships (this dataset references):
"""

    if relationships['outgoing_relationships']:
        for rel in relationships['outgoing_relationships']:
            enforced = " [ENFORCED]" if rel['is_enforced'] else ""
            rel_context += f"""
- {rel['from_field']} → {rel['to_dataset']}.{rel['to_field']}{enforced}
  Type: {rel['relationship_type']}
  Name: {rel.get('relationship_name', 'N/A')}
"""
    else:
        rel_context += "  (No outgoing relationships)\n"

    rel_context += "\nIncoming Relationships (other datasets reference this one):\n"

    if relationships['incoming_relationships']:
        for rel in relationships['incoming_relationships']:
            enforced = " [ENFORCED]" if rel['is_enforced'] else ""
            rel_context += f"""
- {rel['from_dataset']}.{rel['from_field']} → {rel['to_field']}{enforced}
  Type: {rel['relationship_type']}
  Name: {rel.get('relationship_name', 'N/A')}
"""
    else:
        rel_context += "  (No incoming relationships)\n"

    # Use LLM to format response
    response = self.client.chat.completions.create(
        model=self.model,
        messages=[
            {
                "role": "system",
                "content": "You are a professional data librarian explaining dataset relationships."
            },
            {
                "role": "user",
                "content": f"Context:\n{rel_context}\n\nQuestion: {message}\n\nExplain this dataset's relationships."
            }
        ]
    )

    return response.choices[0].message.content


def _handle_quality_query(self, message: str) -> str:
    """Handle data quality queries."""
    # Implementation would extract dataset/field and return quality metrics
    # from the extended attribute metadata
    return "Quality query handling - to be implemented"


def _handle_discovery_query(self, message: str) -> str:
    """Handle dataset discovery queries."""
    # Would search across entity_type metadata, tags, etc.
    return "Discovery query handling - to be implemented"


def _handle_general_query(self, message: str) -> str:
    """Handle general queries using existing RAG approach."""
    # Use the existing implementation
    documents = self.get_documents(message)

    if len(documents) > 0:
        context = "\n\n".join([
            f"Title: {doc['title']}\nDescription: {doc['description']}\nKeywords: {doc['keywords']}"
            for doc in documents
        ])

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional data librarian specializing in scientific data discovery and metadata curation. "
                        "Provide clear, organized, evidence-based responses using the catalog context."
                    )
                },
                {
                    "role": "user",
                    "content": f"Context: {context}\n\nQuestion: {message}"
                }
            ]
        )

        return response.choices[0].message.content
    else:
        return "I couldn't find any relevant information in the catalog for your query."
```

---

### 5. Enhanced Harvesting Process

Update the metadata extraction to populate the new fields:

```python
# Extend src/catalog/core/schema_parser.py or create new harvester module

def extract_dataset_metadata_from_xml(xml_file: str) -> dict:
    """
    Extract comprehensive metadata including dataset-level info.

    This extends the existing EAInfoParser to also extract:
    - Dataset name (extracted from entity label or filename)
    - Source system info
    - Additional metadata fields
    """
    # Use existing parser
    parser = EAInfoParser()
    eainfo = parser.parse_xml_file(xml_file)

    # Extract dataset name from entity label or filename
    dataset_name = None
    if eainfo.has_detailed_info:
        # Try to extract short name from label (e.g., "S_USA.Activity_BrushDisposal" → "BrushDisposal")
        label = eainfo.detailed.entity_type.label
        if '.' in label:
            dataset_name = label.split('.')[-1]
        else:
            dataset_name = label

    if not dataset_name:
        # Fall back to filename
        from pathlib import Path
        dataset_name = Path(xml_file).stem

    # Parse additional metadata from XML (would need to extend parser)
    # For now, return basic metadata
    return {
        'eainfo': eainfo,
        'dataset_name': dataset_name,
        'display_name': dataset_name.replace('_', ' ').title(),
        'dataset_type': 'feature_class',  # Could parse from XML metadata
        'source_system': 'USFS GIS',  # Could parse from XML idinfo
        'source_file': xml_file
    }


def save_entity_with_extended_metadata(metadata: dict):
    """
    Save entity using existing save_eainfo, then update with extended metadata.
    """
    from catalog.core.db import save_eainfo, get_db

    # Save using existing function
    eainfo_id = save_eainfo(metadata['eainfo'])

    # Update entity_type with extended metadata
    db = get_db()
    conn = db.get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE entity_type
                SET dataset_name = %s,
                    display_name = %s,
                    dataset_type = %s,
                    source_system = %s
                WHERE eainfo_id = %s
            """, (
                metadata['dataset_name'],
                metadata['display_name'],
                metadata['dataset_type'],
                metadata['source_system'],
                eainfo_id
            ))
            conn.commit()

    finally:
        db.return_connection(conn)

    return eainfo_id
```

---

### 6. New API Endpoints

Add specialized endpoints in `src/catalog/api/api.py`:

```python
# Add to src/catalog/api/api.py

@app.get("/api/datasets")
async def list_datasets(
    dataset_type: Optional[str] = None,
    source_system: Optional[str] = None,
    limit: int = 100
):
    """
    List all datasets with optional filtering.

    Query Parameters:
    - dataset_type: Filter by type (feature_class, table, etc.)
    - source_system: Filter by source system
    - limit: Maximum results (default 100)
    """
    from catalog.core.db import list_all_datasets

    datasets = list_all_datasets(
        dataset_type=dataset_type,
        source_system=source_system,
        limit=limit
    )

    return {"datasets": datasets, "count": len(datasets)}


@app.get("/api/datasets/{dataset_name}")
async def get_dataset_schema(dataset_name: str):
    """
    Get complete schema definition for a dataset.

    Path Parameters:
    - dataset_name: Name of the dataset

    Example: GET /api/datasets/BrushDisposal
    """
    from catalog.core.db import search_entity_by_name

    entity = search_entity_by_name(dataset_name)

    if not entity:
        raise HTTPException(
            status_code=404,
            detail=f"Dataset '{dataset_name}' not found"
        )

    return entity


@app.get("/api/datasets/{dataset_name}/fields/{field_name}/lineage")
async def get_field_lineage_endpoint(dataset_name: str, field_name: str):
    """
    Get data lineage for a specific field.

    Path Parameters:
    - dataset_name: Name of the dataset
    - field_name: Name of the field

    Example: GET /api/datasets/BrushDisposal/fields/OBJECTID/lineage
    """
    from catalog.core.db import get_field_lineage

    lineage = get_field_lineage(dataset_name, field_name)

    if not lineage:
        raise HTTPException(
            status_code=404,
            detail=f"Field '{field_name}' not found in dataset '{dataset_name}'"
        )

    return lineage


@app.get("/api/datasets/{dataset_name}/relationships")
async def get_dataset_relationships_endpoint(dataset_name: str):
    """
    Get all relationships for a dataset.

    Path Parameters:
    - dataset_name: Name of the dataset

    Example: GET /api/datasets/BrushDisposal/relationships
    """
    from catalog.core.db import get_dataset_relationships

    relationships = get_dataset_relationships(dataset_name)

    if not relationships:
        raise HTTPException(
            status_code=404,
            detail=f"Dataset '{dataset_name}' not found"
        )

    return relationships
```

---

### 7. Implementation Phases

#### Phase 1: Extend Database Schema (Week 1)

- Run migration to add columns to `entity_type` and `attribute` tables
- Create `field_lineage`, `dataset_lineage`, and `dataset_relationships` tables
- Update existing data with dataset names extracted from entity labels
- Test schema changes

#### Phase 2: Enhance Database Functions (Week 2)

- Implement `search_entity_by_name()` with fuzzy matching
- Implement `get_entity_attributes_extended()`
- Implement `get_field_lineage()`
- Implement `get_dataset_relationships()`
- Implement `list_all_datasets()`
- Write unit tests for all functions

#### Phase 3: Query Classification (Week 3)

- Implement `classify_query()` in ChatBot
- Implement specialized query handlers (`_handle_schema_query`, etc.)
- Test classification accuracy
- Refine prompts based on testing

#### Phase 4: Enhanced Harvesting (Week 4)

- Extend metadata extraction to populate new fields
- Update harvesting scripts to call extended functions
- Re-harvest existing data with new metadata
- Validate data quality

#### Phase 5: API Enhancement (Week 5)

- Add new REST endpoints
- Update existing chat endpoint to use classification
- Add API documentation
- Integration testing

#### Phase 6: Quality & Optimization (Week 6)

- Performance optimization
- Add caching for frequently accessed schemas
- User acceptance testing
- Documentation and training materials

---

### 8. Example Query Flows

#### Example 1: Schema Query

**User Query**: "Is there a schema definition for BrushDisposal? If so, what is that schema?"

**System Flow**:

1. Query classifier identifies this as `SCHEMA` query
2. LLM extracts dataset name: "BrushDisposal"
3. System calls `search_entity_by_name("BrushDisposal")`
4. Retrieves entity_type + attributes from database using existing structure
5. LLM formats natural language response with schema details

**Expected Response**:

```text
Yes, I found the schema definition for BrushDisposal:

**Dataset**: BrushDisposal (Brush Disposal Sites)
**Type**: Feature Class
**Source**: USFS GIS
**Records**: 1,247

**Schema** (15 fields):

- OBJECTID (Integer) [Primary Key]
  Unique identifier for each disposal site

- SITE_NAME (String, max 100)
  Name of the disposal site

- ACTIVITY_CODE (String, max 4)
  Activity code from FACTS system
  Domain: 12 enumerated values (1111, 1112, etc.)

- LATITUDE (Float)
  Latitude coordinate in decimal degrees
  Range: 32.5 to 49.0

[... additional fields ...]

This dataset was last updated on 2024-12-15.
```

#### Example 2: Lineage Query

**User Query**: "What is the data lineage of the field OBJECTID in BrushDisposal?"

**System Flow**:

1. Query classifier identifies this as `LINEAGE` query
2. LLM extracts dataset="BrushDisposal" and field="OBJECTID"
3. System calls `get_field_lineage("BrushDisposal", "OBJECTID")`
4. Retrieves lineage from `field_lineage` table
5. LLM formats lineage information

**Expected Response**:

```text
The OBJECTID field in BrushDisposal has the following data lineage:

**Field Type**: Source field (no upstream transformations)

**Origin**:
This is a system-generated primary key field created automatically by ArcGIS
when the BrushDisposal feature class was created. It is not derived from any
source data.

**Downstream Usage** (2 datasets depend on this field):

1. DisposalMonitoring.DISPOSAL_SITE_ID [VERIFIED]
   - Relationship: Foreign key reference (one-to-many)
   - Transformation: Direct copy
   - Purpose: Links monitoring records to disposal sites

2. BrushDisposalHistory.ORIGINAL_OBJECTID
   - Relationship: Historical reference
   - Transformation: Archived copy
   - Purpose: Preserves original ID when records are archived

**Summary**: OBJECTID serves as the primary key and is referenced by 2
downstream datasets for data integration purposes.
```

---

### 9. Migration SQL Script

```sql
-- sql/migrations/002_add_librarian_enhancements.sql

BEGIN;

-- ============================================================================
-- EXTEND EXISTING TABLES
-- ============================================================================

-- Add dataset-level metadata to entity_type
ALTER TABLE entity_type
  ADD COLUMN IF NOT EXISTS dataset_name VARCHAR(255),
  ADD COLUMN IF NOT EXISTS display_name VARCHAR(255),
  ADD COLUMN IF NOT EXISTS dataset_type VARCHAR(50),
  ADD COLUMN IF NOT EXISTS source_system VARCHAR(100),
  ADD COLUMN IF NOT EXISTS source_url TEXT,
  ADD COLUMN IF NOT EXISTS record_count INTEGER,
  ADD COLUMN IF NOT EXISTS last_updated_at TIMESTAMP,
  ADD COLUMN IF NOT EXISTS spatial_extent JSONB,
  ADD COLUMN IF NOT EXISTS metadata JSONB;

-- Add technical metadata to attribute
ALTER TABLE attribute
  ADD COLUMN IF NOT EXISTS data_type VARCHAR(50),
  ADD COLUMN IF NOT EXISTS is_nullable BOOLEAN DEFAULT true,
  ADD COLUMN IF NOT EXISTS is_primary_key BOOLEAN DEFAULT false,
  ADD COLUMN IF NOT EXISTS is_foreign_key BOOLEAN DEFAULT false,
  ADD COLUMN IF NOT EXISTS max_length INTEGER,
  ADD COLUMN IF NOT EXISTS field_precision INTEGER,
  ADD COLUMN IF NOT EXISTS field_scale INTEGER,
  ADD COLUMN IF NOT EXISTS default_value TEXT,
  ADD COLUMN IF NOT EXISTS completeness_percent DECIMAL(5,2),
  ADD COLUMN IF NOT EXISTS uniqueness_percent DECIMAL(5,2),
  ADD COLUMN IF NOT EXISTS min_value TEXT,
  ADD COLUMN IF NOT EXISTS max_value TEXT,
  ADD COLUMN IF NOT EXISTS sample_values TEXT[],
  ADD COLUMN IF NOT EXISTS last_profiled_at TIMESTAMP,
  ADD COLUMN IF NOT EXISTS field_metadata JSONB;

-- ============================================================================
-- CREATE NEW TABLES
-- ============================================================================

-- Field-level lineage
CREATE TABLE IF NOT EXISTS field_lineage (
    id SERIAL PRIMARY KEY,
    target_attribute_id INTEGER REFERENCES attribute(id) ON DELETE CASCADE,
    source_attribute_id INTEGER REFERENCES attribute(id) ON DELETE CASCADE,
    transformation_type VARCHAR(50),
    transformation_logic TEXT,
    confidence_score DECIMAL(3,2),
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100),
    notes TEXT,
    metadata JSONB
);

-- Dataset-level lineage
CREATE TABLE IF NOT EXISTS dataset_lineage (
    id SERIAL PRIMARY KEY,
    downstream_entity_id INTEGER REFERENCES entity_type(id) ON DELETE CASCADE,
    upstream_entity_id INTEGER REFERENCES entity_type(id) ON DELETE CASCADE,
    dependency_type VARCHAR(50),
    description TEXT,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB,
    UNIQUE(downstream_entity_id, upstream_entity_id)
);

-- Dataset relationships (foreign keys, etc.)
CREATE TABLE IF NOT EXISTS dataset_relationships (
    id SERIAL PRIMARY KEY,
    from_entity_id INTEGER REFERENCES entity_type(id) ON DELETE CASCADE,
    from_attribute_id INTEGER REFERENCES attribute(id) ON DELETE CASCADE,
    to_entity_id INTEGER REFERENCES entity_type(id) ON DELETE CASCADE,
    to_attribute_id INTEGER REFERENCES attribute(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50),
    relationship_name VARCHAR(255),
    is_enforced BOOLEAN DEFAULT false,
    cardinality VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    notes TEXT,
    metadata JSONB
);

-- ============================================================================
-- CREATE INDEXES
-- ============================================================================

-- entity_type indexes
CREATE INDEX IF NOT EXISTS idx_entity_type_dataset_name ON entity_type(dataset_name);
CREATE INDEX IF NOT EXISTS idx_entity_type_dataset_type ON entity_type(dataset_type);
CREATE INDEX IF NOT EXISTS idx_entity_type_source_system ON entity_type(source_system);

-- attribute indexes
CREATE INDEX IF NOT EXISTS idx_attribute_data_type ON attribute(data_type);
CREATE INDEX IF NOT EXISTS idx_attribute_is_primary_key ON attribute(is_primary_key) WHERE is_primary_key = true;
CREATE INDEX IF NOT EXISTS idx_attribute_is_foreign_key ON attribute(is_foreign_key) WHERE is_foreign_key = true;

-- lineage indexes
CREATE INDEX IF NOT EXISTS idx_lineage_target ON field_lineage(target_attribute_id);
CREATE INDEX IF NOT EXISTS idx_lineage_source ON field_lineage(source_attribute_id);
CREATE INDEX IF NOT EXISTS idx_lineage_confidence ON field_lineage(confidence_score);

CREATE INDEX IF NOT EXISTS idx_dataset_lineage_downstream ON dataset_lineage(downstream_entity_id);
CREATE INDEX IF NOT EXISTS idx_dataset_lineage_upstream ON dataset_lineage(upstream_entity_id);

-- relationship indexes
CREATE INDEX IF NOT EXISTS idx_rel_from_entity ON dataset_relationships(from_entity_id);
CREATE INDEX IF NOT EXISTS idx_rel_to_entity ON dataset_relationships(to_entity_id);
CREATE INDEX IF NOT EXISTS idx_rel_from_attribute ON dataset_relationships(from_attribute_id);
CREATE INDEX IF NOT EXISTS idx_rel_to_attribute ON dataset_relationships(to_attribute_id);

-- Enable fuzzy text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX IF NOT EXISTS idx_entity_type_dataset_name_trgm ON entity_type USING gin (dataset_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_entity_type_label_trgm ON entity_type USING gin (label gin_trgm_ops);

-- ============================================================================
-- POPULATE DATASET NAMES FROM EXISTING DATA
-- ============================================================================

-- Extract dataset names from entity labels
-- This handles labels like "S_USA.Activity_BrushDisposal" → "BrushDisposal"
UPDATE entity_type
SET dataset_name =
  CASE
    WHEN position('.' in label) > 0 THEN split_part(label, '.', array_length(string_to_array(label, '.'), 1))
    ELSE label
  END
WHERE dataset_name IS NULL;

-- Set display names
UPDATE entity_type
SET display_name = replace(dataset_name, '_', ' ')
WHERE display_name IS NULL AND dataset_name IS NOT NULL;

COMMIT;

-- Verify migration
SELECT
  'entity_type' as table_name,
  COUNT(*) as row_count,
  COUNT(dataset_name) as with_dataset_name,
  COUNT(display_name) as with_display_name
FROM entity_type
UNION ALL
SELECT
  'attribute' as table_name,
  COUNT(*) as row_count,
  COUNT(data_type) as with_data_type,
  COUNT(is_primary_key) as with_pk_flag
FROM attribute;
```

---

### 10. Testing Strategy

#### Unit Tests

```python
# tests/test_enhanced_db.py

def test_search_entity_by_exact_name():
    """Test exact name matching"""
    entity = search_entity_by_name("BrushDisposal")
    assert entity is not None
    assert entity['dataset_name'] == "BrushDisposal"
    assert 'attributes' in entity


def test_search_entity_by_fuzzy_name():
    """Test fuzzy name matching"""
    entity = search_entity_by_name("BrushDisposl")  # typo
    assert entity is not None
    assert "BrushDisposal" in entity['dataset_name']


def test_get_field_lineage_source_field():
    """Test lineage for source field (no upstream)"""
    lineage = get_field_lineage("BrushDisposal", "OBJECTID")
    assert lineage is not None
    assert lineage['is_source_field'] == True
    assert len(lineage['upstream_sources']) == 0


def test_get_field_lineage_derived_field():
    """Test lineage for derived field"""
    # Setup: Create test lineage
    # ... test code ...
    lineage = get_field_lineage("DerivedTable", "COMPUTED_FIELD")
    assert len(lineage['upstream_sources']) > 0


def test_query_classification():
    """Test query intent classification"""
    chatbot = ChatBot()

    assert chatbot.classify_query("What is the schema for X?") == QueryType.SCHEMA
    assert chatbot.classify_query("Where does field Y come from?") == QueryType.LINEAGE
    assert chatbot.classify_query("Tell me about X") == QueryType.GENERAL
```

#### Integration Tests

- Test end-to-end schema queries through API
- Test lineage queries with multi-hop relationships
- Test relationship queries
- Test classification accuracy on real user queries

#### Performance Tests

- Schema retrieval: < 100ms
- Complex lineage query: < 500ms
- Dataset listing: < 200ms
- Concurrent queries: 50+ simultaneous users

---

## Conclusion

This enhancement design builds directly on top of the existing `schema_parser.py` infrastructure rather than creating parallel structures. By extending the existing `entity_type` and `attribute` tables with additional metadata columns, we maintain backward compatibility while adding powerful new capabilities.

### Key Benefits

✅ **Leverages Existing Infrastructure**: Builds on proven schema_parser.py models

✅ **Backward Compatible**: Existing code continues to work

✅ **Structured Metadata**: Complete entity and attribute definitions already in place

✅ **Intelligent Query Routing**: Classification-based routing to specialized handlers

✅ **Lineage Tracking**: New field-level lineage with transformation logic

✅ **Natural Language Interface**: Users ask questions in plain English

✅ **Scalable Architecture**: Designed to handle large catalogs

### What We're Adding

1. **Dataset-level metadata** columns to `entity_type`
2. **Technical field metadata** columns to `attribute`
3. **New lineage tables** for tracking data provenance
4. **New relationship tables** for cross-dataset references
5. **Query classification** logic in ChatBot
6. **Specialized retrieval** functions for structured queries
7. **New API endpoints** for direct access

### Next Steps

1. Review and approve this design
2. Run database migration (Phase 1)
3. Implement enhanced database functions (Phase 2)
4. Implement query classification (Phase 3)
5. Extend harvesting process (Phase 4)
6. Add new API endpoints (Phase 5)
7. Test and optimize (Phase 6)

---

**Document Version**: 2.0
**Created**: 2025-01-05
**Updated**: 2025-01-05
**Author**: Claude Code (AI Assistant)
**Status**: Proposal - Pending Review

# Entity and Attribute Information Database Storage

## Overview

Implementation for saving FGDC Entity and Attribute Information (eainfo) instances to PostgreSQL database.

## Files Created

### 1. Database Migration
**Location:** `sql/migrations/001_add_eainfo_tables.sql`

Creates four normalized tables to store the hierarchical eainfo structure:

- **eainfo**: Root table storing overview, citation, parsed timestamp, and source file
- **entity_type**: Entity type definitions (feature classes, tables)
- **attribute**: Attribute/field definitions for entities
- **attribute_domain**: Domain value specifications stored as JSONB

#### Schema Design Highlights

- Normalized structure with proper foreign key relationships
- CASCADE deletes to maintain referential integrity
- JSONB storage for flexible domain value types (enumerated, range, codeset, unrepresentable)
- Indexes on foreign keys and JSONB fields for efficient queries
- Comprehensive documentation via SQL comments

### 2. Database Functions
**Location:** `proposed/db_proposed.py`

Added four new functions to handle eainfo operations:

#### `save_eainfo(eainfo: EntityAttributeInfo) -> int`
Saves a complete eainfo instance with all nested entities, attributes, and domain values.

**Features:**
- Transactional operation (all-or-nothing)
- Automatic handling of nested relationships
- Returns the created eainfo ID
- Proper error handling and rollback

**Example:**
```python
from catalog.core.schema_parser import EAInfoParser
from catalog.core.db import save_eainfo

# Parse XML file
parser = EAInfoParser()
eainfo = parser.parse_xml_file('data/catalog/Actv_BrushDisposal.xml')

# Save to database
eainfo_id = save_eainfo(eainfo)
print(f"Saved eainfo with ID: {eainfo_id}")
```

#### `get_eainfo_by_id(eainfo_id: int) -> Optional[dict]`
Retrieves complete eainfo data by ID with all nested relationships.

**Returns:**
```python
{
    'id': 1,
    'overview': '...',
    'citation': '...',
    'parsed_at': datetime(...),
    'source_file': 'path/to/file.xml',
    'created_at': datetime(...),
    'entity_type': {
        'id': 1,
        'label': 'S_USA.Activity_BrushDisposal',
        'definition': '...',
        'definition_source': '...',
        'attributes': [
            {
                'id': 1,
                'label': 'OBJECTID',
                'definition': '...',
                'definition_source': '...',
                'domain_values': [
                    {
                        'type': 'unrepresentable',
                        'data': {'description': '...'}
                    }
                ]
            }
        ]
    }
}
```

#### `get_eainfo_by_source_file(source_file: str) -> Optional[dict]`
Finds the most recent eainfo record for a given source file path.

**Use case:** Check if metadata has already been imported from a specific XML file

#### `list_all_entities() -> list[dict]`
Lists all entity types with basic statistics.

**Returns:**
```python
[
    {
        'id': 1,
        'label': 'S_USA.Activity_BrushDisposal',
        'definition': '...',
        'source_file': 'path/to/file.xml',
        'attribute_count': 42
    },
    ...
]
```

## Implementation Steps

### 1. Run the Migration

```bash
psql -U your_user -d your_database -f sql/migrations/001_add_eainfo_tables.sql
```

Or using the project's connection:
```bash
source .env
psql "dbname=$POSTGRES_DB user=$POSTGRES_USER password=$POSTGRES_PASSWORD host=$POSTGRES_HOST" -f sql/migrations/001_add_eainfo_tables.sql
```

### 2. Copy Functions to db.py

Replace `src/catalog/core/db.py` with `proposed/db_proposed.py`:

```bash
cp proposed/db_proposed.py src/catalog/core/db.py
```

### 3. Usage Example

```python
from catalog.core.schema_parser import EAInfoParser
from catalog.core.db import save_eainfo, get_eainfo_by_id, list_all_entities

# Parse and save
parser = EAInfoParser()
eainfo = parser.parse_xml_file('data/catalog/Actv_BrushDisposal.xml')
eainfo_id = save_eainfo(eainfo)

# Retrieve
saved_eainfo = get_eainfo_by_id(eainfo_id)
print(f"Entity: {saved_eainfo['entity_type']['label']}")
print(f"Attributes: {len(saved_eainfo['entity_type']['attributes'])}")

# List all
entities = list_all_entities()
for entity in entities:
    print(f"{entity['label']}: {entity['attribute_count']} attributes")
```

## Design Decisions

### JSONB for Domain Values
Domain values are stored as JSONB rather than separate tables because:
- Each domain type has different fields (enumerated vs range vs codeset)
- JSONB provides flexibility without complex JOIN operations
- GIN index enables efficient querying
- Schema evolution is simpler

### Normalized Structure
Despite JSONB usage, the main entities remain normalized:
- Easier to query entities and attributes independently
- Foreign key constraints ensure data integrity
- Better support for future features (e.g., entity relationships)

### Error Handling
All functions use the `@retry_on_db_error` decorator:
- Automatic retry on transient failures
- Proper connection pooling
- Transaction rollback on errors

## Testing Recommendations

1. **Unit Tests** - Test each function independently
2. **Integration Tests** - Test complete save/retrieve cycle
3. **Edge Cases** - Test with missing optional fields, empty attributes, etc.
4. **Performance** - Test with large XML files containing many attributes

## Next Steps

1. Run the migration to create tables
2. Copy functions to db.py
3. Create a CLI command to bulk import XML files
4. Add tests for the new functionality
5. Consider adding update/delete functions if needed

---

## Summary

### 1. Database Schema Migration

**File:** `sql/migrations/001_add_eainfo_tables.sql`

Creates four normalized tables:

- `eainfo` - Root table with overview, citation, timestamps
- `entity_type` - Entity definitions
- `attribute` - Attribute/field definitions
- `attribute_domain` - Domain values stored as JSONB for flexibility

### 2. Database Functions

**File:** `proposed/db_proposed.py`

Added four new functions:

- `save_eainfo(eainfo)` - Saves complete eainfo instance with all nested data
- `get_eainfo_by_id(eainfo_id)` - Retrieves eainfo with full hierarchy
- `get_eainfo_by_source_file(source_file)` - Finds eainfo by XML file path
- `list_all_entities()` - Lists all entities with attribute counts

### 3. Documentation

**File:** `responses/eainfo_database_storage.md`

Complete documentation with:

- Implementation steps
- Usage examples
- Design decisions
- Testing recommendations

### Key Features

- **Transactional saves** - All-or-nothing with automatic rollback
- **Normalized schema** - Proper relationships and referential integrity
- **JSONB flexibility** - Handles multiple domain value types efficiently
- **Error handling** - Retry logic for transient failures
- **Comprehensive logging** - Tracks operations at each level

### Getting Started

1. Run the migration: `psql -f sql/migrations/001_add_eainfo_tables.sql`
2. Copy proposed functions to db.py: `cp proposed/db_proposed.py src/catalog/core/db.py`
3. Test with your XML files

# Data Librarian Quick Reference

Quick reference guide for using the enhanced Catalog API "data librarian" features.

## Table of Contents
- [Natural Language Queries](#natural-language-queries)
- [REST API Endpoints](#rest-api-endpoints)
- [Python Functions](#python-functions)
- [CLI Commands](#cli-commands)

## Natural Language Queries

### Using the ChatBot Interface

```python
from catalog.api.llm import ChatBot

bot = ChatBot()
response = bot.chat("your question here")
print(response)
```

### Schema Queries

Ask about dataset structure and field definitions:

```python
# Basic schema inquiry
bot.chat("What is the schema for BrushDisposal?")

# Field-specific questions
bot.chat("What fields are in the Activity table?")

# Dataset existence check
bot.chat("Is there a dataset called UserDefinedFireReport?")

# Data types and constraints
bot.chat("Show me the structure of Location dataset")
```

**Example Response**:
```
The BrushDisposal dataset is a feature class from USFS GIS containing
15 fields. Key fields include:
- OBJECTID (Integer, Primary Key): Unique identifier
- ActivityDate (Date): When the activity occurred
- Acres (Float): Size of the disposal area
- Status (String): Current status with 5 domain values
...
```

### Lineage Queries

Ask about data origins and transformations:

```python
# Field lineage
bot.chat("What is the lineage of OBJECTID in BrushDisposal?")

# Data source questions
bot.chat("Where does the STATUS field come from?")

# Transformation tracking
bot.chat("Show me what fields use the GEOMETRY column")

# Full data flow
bot.chat("Explain the lineage of the TotalAcres field")
```

**Example Response**:
```
The OBJECTID field in BrushDisposal is a source field with no
upstream dependencies. It serves as the primary key and is used by
3 downstream datasets:
- ActivitySummary.SourceID (direct copy)
- FireHistory.DisposalID (foreign key reference)
...
```

### Relationship Queries

Ask about connections between datasets:

```python
# Dataset relationships
bot.chat("What datasets reference BrushDisposal?")

# Foreign key questions
bot.chat("How is Activity related to Location?")

# Connection discovery
bot.chat("Show me all relationships for the FireReport table")

# Dependency checking
bot.chat("What datasets depend on UserActivity?")
```

**Example Response**:
```
BrushDisposal has the following relationships:

Outgoing relationships (references other datasets):
- Field LOCATION_ID → Location.OBJECTID [ENFORCED]

Incoming relationships (referenced by other datasets):
- ActivitySummary.DISPOSAL_ID → OBJECTID [NOT ENFORCED]
- HistoricalActivity.SOURCE_ID → OBJECTID [ENFORCED]
```

## REST API Endpoints

All endpoints require authentication with `x-api-key` header.

### List All Datasets

```bash
# List all datasets
curl -H "x-api-key: YOUR_API_KEY" \
  http://localhost:8000/datasets

# Filter by type
curl -H "x-api-key: YOUR_API_KEY" \
  "http://localhost:8000/datasets?dataset_type=feature_class&limit=20"

# Filter by source system
curl -H "x-api-key: YOUR_API_KEY" \
  "http://localhost:8000/datasets?source_system=USFS+GIS"
```

**Response**:
```json
{
  "total": 185,
  "datasets": [
    {
      "id": 1,
      "dataset_name": "BrushDisposal",
      "display_name": "Brush Disposal",
      "dataset_type": "feature_class",
      "source_system": "USFS GIS",
      "record_count": 15234,
      "last_updated_at": "2024-10-15T10:30:00"
    },
    ...
  ]
}
```

### Get Dataset Schema

```bash
curl -H "x-api-key: YOUR_API_KEY" \
  http://localhost:8000/datasets/BrushDisposal
```

**Response**:
```json
{
  "id": 1,
  "dataset_name": "BrushDisposal",
  "display_name": "Brush Disposal",
  "dataset_type": "feature_class",
  "definition": "Records of brush disposal activities...",
  "attributes": [
    {
      "id": 100,
      "label": "OBJECTID",
      "definition": "Unique identifier",
      "technical": {
        "data_type": "Integer",
        "is_nullable": false,
        "is_primary_key": true,
        "is_foreign_key": false
      },
      "domain_values": []
    },
    {
      "id": 101,
      "label": "Status",
      "definition": "Current activity status",
      "technical": {
        "data_type": "String",
        "max_length": 50,
        "is_nullable": true
      },
      "domain_values": [
        {"value": "Active", "definition": "Activity in progress"},
        {"value": "Complete", "definition": "Activity finished"},
        ...
      ]
    },
    ...
  ]
}
```

### Get Field Lineage

```bash
curl -H "x-api-key: YOUR_API_KEY" \
  http://localhost:8000/datasets/BrushDisposal/fields/OBJECTID/lineage
```

**Response**:
```json
{
  "entity_label": "BrushDisposal",
  "field": "OBJECTID",
  "upstream_sources": [],
  "downstream_dependents": [
    {
      "target_dataset": "ActivitySummary",
      "target_field": "SOURCE_ID",
      "transformation_type": "direct_copy",
      "transformation_logic": "1:1 mapping from source",
      "is_verified": true
    },
    ...
  ]
}
```

### Get Dataset Relationships

```bash
curl -H "x-api-key: YOUR_API_KEY" \
  http://localhost:8000/datasets/BrushDisposal/relationships
```

**Response**:
```json
{
  "dataset": "BrushDisposal",
  "outgoing_relationships": [
    {
      "from_field": "LOCATION_ID",
      "to_dataset": "Location",
      "to_field": "OBJECTID",
      "relationship_type": "foreign_key",
      "is_enforced": true,
      "cardinality": "many_to_one"
    }
  ],
  "incoming_relationships": [
    {
      "from_dataset": "ActivitySummary",
      "from_field": "DISPOSAL_ID",
      "to_field": "OBJECTID",
      "relationship_type": "foreign_key",
      "is_enforced": false,
      "cardinality": "many_to_one"
    }
  ]
}
```

## Python Functions

Direct access to database functions from Python code.

### Import Functions

```python
from catalog.core.db import (
    list_all_datasets,
    search_entity_by_name,
    get_field_lineage,
    get_dataset_relationships,
    update_entity_extended_metadata
)
```

### List All Datasets

```python
# List all datasets
datasets = list_all_datasets(limit=100)

# Filter by type
datasets = list_all_datasets(
    dataset_type="feature_class",
    limit=50
)

# Filter by source system
datasets = list_all_datasets(
    source_system="USFS GIS",
    limit=100
)

# Combined filters
datasets = list_all_datasets(
    dataset_type="table",
    source_system="ArcGIS Online",
    limit=25
)
```

### Search Entity by Name

```python
# Exact match
entity = search_entity_by_name("BrushDisposal")

# Fuzzy match (uses pg_trgm similarity > 0.3)
entity = search_entity_by_name("BrshDsposal")  # Will find "BrushDisposal"

# Check if dataset exists
if entity:
    print(f"Found: {entity['dataset_name']}")
    print(f"Type: {entity['dataset_type']}")
    print(f"Fields: {len(entity['attributes'])}")
else:
    print("Dataset not found")
```

**Returns**:
```python
{
    'id': 1,
    'dataset_name': 'BrushDisposal',
    'display_name': 'Brush Disposal',
    'label': 'S_USA.Activity_BrushDisposal',
    'definition': 'Records of brush disposal activities...',
    'dataset_type': 'feature_class',
    'source_system': 'USFS GIS',
    'source_url': 'https://data.fs.usda.gov/...',
    'record_count': 15234,
    'attributes': [
        {
            'id': 100,
            'label': 'OBJECTID',
            'definition': 'Unique identifier',
            'technical': {
                'data_type': 'Integer',
                'is_nullable': False,
                'is_primary_key': True,
                'is_foreign_key': False
            },
            'domain_values': []
        },
        ...
    ]
}
```

### Get Field Lineage

```python
# Get lineage for a field
lineage = get_field_lineage("BrushDisposal", "OBJECTID")

if lineage:
    print(f"Field: {lineage['field']}")

    # Check upstream sources
    if lineage['upstream_sources']:
        print("\nUpstream Sources:")
        for source in lineage['upstream_sources']:
            print(f"  - {source['source_dataset']}.{source['source_field']}")
            print(f"    Type: {source['transformation_type']}")
            if source['is_verified']:
                print("    [VERIFIED]")

    # Check downstream dependents
    if lineage['downstream_dependents']:
        print("\nDownstream Dependents:")
        for dep in lineage['downstream_dependents']:
            print(f"  - {dep['target_dataset']}.{dep['target_field']}")
else:
    print("Lineage information not found")
```

### Get Dataset Relationships

```python
# Get all relationships for a dataset
relationships = get_dataset_relationships("BrushDisposal")

if relationships:
    # Outgoing relationships (this dataset references others)
    print("Outgoing Relationships:")
    for rel in relationships['outgoing_relationships']:
        print(f"  {rel['from_field']} → "
              f"{rel['to_dataset']}.{rel['to_field']}")
        if rel['is_enforced']:
            print("    [ENFORCED]")

    # Incoming relationships (others reference this dataset)
    print("\nIncoming Relationships:")
    for rel in relationships['incoming_relationships']:
        print(f"  {rel['from_dataset']}.{rel['from_field']} → "
              f"{rel['to_field']}")
```

### Update Entity Extended Metadata

```python
# Update extended metadata for a dataset
from catalog.core.db import (
    search_entity_by_name,
    update_entity_extended_metadata
)

# Find the entity
entity = search_entity_by_name("BrushDisposal")

if entity:
    entity_id = entity['id']

    # Update metadata
    metadata = {
        'dataset_name': 'BrushDisposal',
        'display_name': 'Brush Disposal Activities',
        'dataset_type': 'feature_class',
        'source_system': 'USFS GIS',
        'source_url': 'https://data.fs.usda.gov/geodata/...',
        'record_count': 15234,
        'last_updated_at': '2024-10-15 10:30:00'
    }

    update_entity_extended_metadata(entity_id, metadata)
    print("Metadata updated successfully")
```

## CLI Commands

### Parse Schema Files

Parse all XML metadata files and populate extended metadata:

```bash
# Using the run-cli.sh wrapper
./run-cli.sh parse_all_schema

# Or directly
PYTHONPATH=src python -m catalog.cli.cli parse_all_schema
```

**Output**:
```
Parsing 185 schema files...
✓ BrushDisposal (15 attributes)
✓ Activity (23 attributes)
✓ Location (8 attributes)
⚠ InvalidSchema.xml: No detailed info
✗ CorruptFile.xml: XML parse error
...
Parsed 183 schemas successfully
Failed to parse 2 schemas
```

### Database Health Check

```bash
./run-cli.sh db-health
```

**Output**:
```
Database connection is healthy!
```

### Document Count

```bash
./run-cli.sh doc-count
```

**Output**:
```
Document count: 15234
```

### Clear Tables (Caution!)

```bash
# Clear eainfo tables
./run-cli.sh clear_eainfo

# Clear documents table
./run-cli.sh clear_docs_table
```

## Query Classification Reference

The system automatically classifies queries into these types:

| Query Type | Description | Example |
|------------|-------------|---------|
| `SCHEMA` | Questions about dataset structure, fields, data types | "What is the schema for X?" |
| `LINEAGE` | Questions about data origins and transformations | "Where does field X come from?" |
| `RELATIONSHIPS` | Questions about connections between datasets | "What datasets reference X?" |
| `QUALITY` | Questions about data completeness and statistics | "What is the quality of X?" |
| `DISCOVERY` | Searching for datasets by characteristics | "Find datasets with coordinates" |
| `GENERAL` | General questions using RAG search | "Tell me about fire data" |

## Error Handling

All functions include comprehensive error handling:

```python
from catalog.core.db import search_entity_by_name

try:
    entity = search_entity_by_name("DatasetName")
    if entity:
        # Process entity
        print(entity['dataset_name'])
    else:
        print("Dataset not found")
except Exception as e:
    print(f"Error: {e}")
```

API endpoints return appropriate HTTP status codes:
- `200 OK` - Success
- `404 Not Found` - Dataset/field not found
- `401 Unauthorized` - Invalid API key
- `500 Internal Server Error` - Server error

## Tips and Best Practices

1. **Dataset Name Format**: Use the short name extracted from the label (e.g., "BrushDisposal" not "S_USA.Activity_BrushDisposal")

2. **Fuzzy Matching**: If you're not sure of the exact name, the search will find close matches (similarity > 0.3)

3. **API Key**: Always include the `x-api-key` header when calling REST endpoints

4. **Pagination**: Use the `limit` parameter to control result size for large queries

5. **Error Messages**: Natural language queries will return helpful error messages if data isn't found

6. **Verification Status**: Check `is_verified` flag in lineage data to distinguish between inferred and manually verified relationships

## Integration Examples

### Flask Application

```python
from flask import Flask, jsonify, request
from catalog.api.llm import ChatBot

app = Flask(__name__)
bot = ChatBot()

@app.route('/api/ask', methods=['POST'])
def ask_question():
    data = request.get_json()
    question = data.get('question')

    if not question:
        return jsonify({'error': 'Question required'}), 400

    response = bot.chat(question)
    return jsonify({'answer': response})
```

### Jupyter Notebook

```python
from catalog.api.llm import ChatBot
from catalog.core.db import search_entity_by_name
import pandas as pd

# Interactive exploration
bot = ChatBot()

# Ask questions
answer = bot.chat("What datasets contain fire data?")
print(answer)

# Get structured data
entity = search_entity_by_name("BrushDisposal")

# Convert to DataFrame for analysis
if entity:
    df = pd.DataFrame(entity['attributes'])
    print(df[['label', 'data_type', 'is_primary_key']])
```

### Command-line Script

```python
#!/usr/bin/env python3
import sys
from catalog.api.llm import ChatBot

def main():
    if len(sys.argv) < 2:
        print("Usage: ./ask.py 'your question'")
        sys.exit(1)

    question = ' '.join(sys.argv[1:])
    bot = ChatBot()
    answer = bot.chat(question)
    print(answer)

if __name__ == '__main__':
    main()
```

Usage:
```bash
./ask.py "What is the schema for BrushDisposal?"
```

## Support

For issues or questions:
- Check the implementation summary: `docs/incoming/implementation-summary.md`
- Review the design document: `docs/incoming/query-enhancements.md`
- Check the project documentation: `CLAUDE.md`

---
**Quick Reference Version**: 1.0
**Last Updated**: 2025-11-05

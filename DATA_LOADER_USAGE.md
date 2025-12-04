# Data Loader Usage Guide

This guide demonstrates how to use the unified `CatalogDocument` schema with data loaders for FSGeodata, GDD, and RDA sources.

## Overview

The `CatalogDocument` class in `src/catalog/schema.py` provides a unified interface for geospatial catalog documents from three different sources:
- **FSGeodata**: USFS Geodata Clearinghouse (XML metadata)
- **GDD**: Geospatial Data Discovery (DCAT-US JSON)
- **RDA**: Research Data Archive (Data.gov JSON)

Each source has a dedicated factory method (`from_fsgeodata()`, `from_gdd()`, `from_rda()`) that handles the source-specific data format.

## Usage Examples

### 1. FSGeodata (XML metadata)

```python
from catalog.fsgeodata import FSGeodataLoader
from catalog.schema import CatalogDocument

# Load and parse FSGeodata
loader = FSGeodataLoader()
docs_data = loader.parse_metadata()

# Convert to CatalogDocument objects
documents = []
for doc_data in docs_data:
    doc = CatalogDocument.from_fsgeodata(doc_data)
    documents.append(doc)

# Access FSGeodata-specific fields
for doc in documents:
    print(f"Title: {doc.title}")
    print(f"Abstract: {doc.abstract}")
    print(f"Purpose: {doc.purpose}")

    if doc.has_lineage:
        print(f"Lineage steps: {len(doc.lineage)}")
        for step in doc.lineage:
            print(f"  - {step.date}: {step.description}")
```

### 2. GDD (Geospatial Data Discovery)

```python
from catalog.gdd import GeospatialDataDiscovery
from catalog.schema import CatalogDocument

# Load and parse GDD
gdd = GeospatialDataDiscovery()
docs_data = gdd.parse_metadata()

# Convert to CatalogDocument objects
documents = []
for doc_data in docs_data:
    doc = CatalogDocument.from_gdd(doc_data)
    documents.append(doc)

# Access GDD-specific fields
for doc in documents:
    print(f"Title: {doc.title}")
    print(f"Description: {doc.description}")
    print(f"Themes: {', '.join(doc.themes)}")
    print(f"Keywords: {', '.join(doc.keywords)}")
```

### 3. RDA (Research Data Archive)

```python
from catalog.rda import RDALoader
from catalog.schema import CatalogDocument

# Load and parse RDA
rda = RDALoader()
docs_data = rda.parse_metadata()

# Convert to CatalogDocument objects
documents = []
for doc_data in docs_data:
    doc = CatalogDocument.from_rda(doc_data)
    documents.append(doc)

# Access common fields
for doc in documents:
    print(f"Title: {doc.title}")
    print(f"Description: {doc.description}")
    print(f"Keywords: {', '.join(doc.keywords)}")
```

### 4. Working with Unified Documents

Once converted to `CatalogDocument` objects, all documents from different sources can be processed uniformly:

```python
from catalog.schema import CatalogDocument, DataSource

# Combine documents from all sources
all_documents = []

# FSGeodata
loader = FSGeodataLoader()
for doc_data in loader.parse_metadata():
    all_documents.append(CatalogDocument.from_fsgeodata(doc_data))

# GDD
gdd = GeospatialDataDiscovery()
for doc_data in gdd.parse_metadata():
    all_documents.append(CatalogDocument.from_gdd(doc_data))

# RDA
rda = RDALoader()
for doc_data in rda.parse_metadata():
    all_documents.append(CatalogDocument.from_rda(doc_data))

# Process uniformly
for doc in all_documents:
    print(f"Title: {doc.title}")
    print(f"Source: {doc.source}")  # 'fsgeodata', 'gdd', or 'rda'
    print(f"Description: {doc.primary_description}")  # Best available description
    print(f"Keywords: {', '.join(doc.keywords)}")

    # Check lineage (only FSGeodata has this)
    if doc.has_lineage:
        print(f"Has {len(doc.lineage)} lineage steps")

    # Check themes (primarily from GDD)
    if doc.themes:
        print(f"Themes: {', '.join(doc.themes)}")
```

### 5. Exporting Documents

#### Export to Dictionary

```python
# Export with all fields (including None values)
doc_dict = doc.to_dict(exclude_none=False)

# Export excluding None values (cleaner output)
doc_dict = doc.to_dict(exclude_none=True)
```

#### Export to JSON

```python
import json

# Using Pydantic's built-in JSON export
json_str = doc.model_dump_json(exclude_none=True, indent=2)

# Or use standard json library with to_dict()
doc_dict = doc.to_dict(exclude_none=True)
json_str = json.dumps(doc_dict, indent=2)

# Save to file
with open("output.json", "w") as f:
    f.write(json_str)
```

#### Batch Export

```python
# Export all documents to JSON Lines format
with open("all_documents.jsonl", "w") as f:
    for doc in all_documents:
        f.write(doc.model_dump_json(exclude_none=True) + "\n")

# Export to single JSON array
documents_data = [doc.to_dict(exclude_none=True) for doc in all_documents]
with open("all_documents.json", "w") as f:
    json.dump(documents_data, f, indent=2)
```

### 6. Filtering and Querying

```python
# Filter by source
fsgeodata_docs = [doc for doc in all_documents if doc.source == DataSource.FSGEODATA]

# Search by keyword
forest_docs = [doc for doc in all_documents if "forest" in [k.lower() for k in doc.keywords]]

# Find documents with lineage
docs_with_lineage = [doc for doc in all_documents if doc.has_lineage]

# Find documents by theme
env_docs = [doc for doc in all_documents if "environment" in doc.themes]
```

### 7. Validation

The `CatalogDocument` class includes automatic validation:

```python
from pydantic import ValidationError

try:
    # This will fail - title cannot be empty
    doc = CatalogDocument(
        title="",
        source=DataSource.FSGEODATA
    )
except ValidationError as e:
    print(f"Validation error: {e}")

try:
    # This will succeed
    doc = CatalogDocument(
        title="Valid Title",
        description="A valid description",
        keywords=["keyword1", "keyword2"],
        source=DataSource.RDA
    )
    print("Document created successfully!")
except ValidationError as e:
    print(f"Validation error: {e}")
```

## Data Structure Reference

### FSGeodata Document Structure
```python
{
    "title": "Forest Boundary Dataset",
    "abstract": "Detailed abstract...",
    "purpose": "To delineate forest boundaries",
    "keywords": ["forest", "boundaries", "USFS"],
    "lineage": [
        {
            "description": "Initial data compilation",
            "date": "20230101"
        }
    ]
}
```

### GDD Document Structure
```python
{
    "title": "National Forest Inventory",
    "description": "Comprehensive forest data",
    "keywords": ["forest", "inventory"],
    "themes": ["environment", "biota"]
}
```

### RDA Document Structure
```python
{
    "title": "Research Dataset Title",
    "description": "Dataset description",
    "keywords": ["research", "data"]
}
```

## Tips and Best Practices

1. **Always use factory methods**: Use `from_fsgeodata()`, `from_gdd()`, or `from_rda()` instead of direct instantiation
2. **Use `primary_description`**: This property returns the best available description/abstract across sources
3. **Check source type**: Use the `source` field to determine which source-specific fields are populated
4. **Use `exclude_none=True`**: When exporting, exclude None values for cleaner output
5. **Validate early**: Let Pydantic catch data issues early in the pipeline
6. **Batch processing**: Process documents in batches for better performance with large datasets

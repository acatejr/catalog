# Data Schema & Lineage Support Enhancement Plan

**Date:** November 3, 2025
**Project:** Catalog - Metadata Catalog with AI-Enhanced Search

## Overview

Enhancement plan to enable natural language queries about data schemas and lineage, such as:
- "Describe the data lineage of Actv_BrushDisposal.xml?"
- "What fields are in the Brush Disposal dataset?"
- "What is the data type for REGION_CODE?"

## Current Data Structure Analysis

### XML Metadata Files Location
`data/catalog/*.xml` - 191 XML files containing USFS dataset metadata

### Key XML Sections (Example: Actv_BrushDisposal.xml)

#### 1. Entity and Attribute Information (`<eainfo>`)
Located at line 139+, contains:
- **Field names** (`<attrlabl>`): e.g., OBJECTID, REGION_CODE, ADMIN_FOREST_CODE
- **Field definitions** (`<attrdef>`): Detailed descriptions of each field
- **Data types/domains** (`<attrdomv>`): Type constraints and value ranges
- **Enumerated values** (`<edom>`): Coded values with descriptions
  - Example: Activity codes (1000=Fire, 2000=Range, etc.)

Example structure:
```xml
<attr>
    <attrlabl>REGION_CODE</attrlabl>
    <attrdef>U.S. Forest Service Region, consisting of Region 01...</attrdef>
    <attrdefs>U.S. Forest Service</attrdefs>
    <attrdomv>
        <udom>Region numbers as text.</udom>
    </attrdomv>
</attr>
```

#### 2. Data Lineage (`<lineage>`)
Located at line 115+, contains:
- **Process steps** (`<procstep>`): Processing methodology
- **Process dates** (`<procdate>`): When processing occurred
- **Process descriptions** (`<procdesc>`): Detailed processing steps

Example:
```xml
<procstep>
    <procdesc>Forest Service Activity Tracking (FACTS) spatial features in
        ActivityPolygon_Subunit and tabular data from ACTIVITY_FACTS_ATTRIBUTES are
        merged based on like spatial identification codes (SUID)...</procdesc>
    <procdate>20160101</procdate>
</procstep>
```

#### 3. Data Quality (`<dataqual>`)
Located at line 102+, contains:
- **Logic**: Data entry methodology
- **Completeness**: Currency and accuracy information
- **Positional accuracy**: Spatial data quality

## Current System Architecture

### Existing Components

**CLI Module** (`src/catalog/cli/cli.py`)
- Downloads metadata from 3 sources (fsgeodata, datahub, RDA)
- Parses XML/JSON metadata
- Creates embeddings and stores in vector DB

**API Module** (`src/catalog/api/api.py`)
- FastAPI endpoints: `/query`, `/keywords`, `/health`
- Query classification system
- LLM-enhanced search via ChatBot

**Database** (`src/catalog/core/db.py`)
- PostgreSQL with pgvector extension
- Current schema: documents table with:
  - `doc_id`, `title`, `description`, `keywords`
  - `embedding` (vector)
  - `chunk_text`, `chunk_type`, `chunk_index`
  - `data_source`

**LLM Integration** (`src/catalog/api/llm.py`)
- ChatBot class with RAG pattern
- Retrieves relevant documents via vector search
- Sends context + query to LLM (ESIIL or OpenAI)
- System prompt: "professional data librarian"

**Schema Models** (`src/catalog/core/schema.py`)
- USFSDocument Pydantic model
- Fields: id, title, description, keywords, src

## Proposed Enhancement

### Task 1: Schema Parser Module

**New file:** `src/catalog/core/schema_parser.py`

**Functions:**
```python
def parse_xml_schema(xml_file_path: str) -> DatasetSchema:
    """Extract field definitions from XML <eainfo> section"""

def parse_xml_lineage(xml_file_path: str) -> DatasetLineage:
    """Extract processing steps from XML <lineage> section"""

def parse_data_quality(xml_file_path: str) -> DataQualityInfo:
    """Extract data quality information"""
```

**Data Models:**
```python
class FieldDefinition(BaseModel):
    field_name: str
    field_definition: str
    field_source: Optional[str]
    domain_type: str  # "udom", "edom", "rdom"
    domain_values: Optional[List[EnumeratedValue]]

class EnumeratedValue(BaseModel):
    code: str
    description: str
    source: Optional[str]

class DatasetSchema(BaseModel):
    dataset_id: str
    entity_type: str
    entity_definition: str
    fields: List[FieldDefinition]

class DatasetLineage(BaseModel):
    dataset_id: str
    process_steps: List[ProcessStep]

class ProcessStep(BaseModel):
    description: str
    date: Optional[str]
    sources: Optional[List[str]]
```

### Task 2: Database Schema Enhancement

**New tables to add via migration:**

```sql
-- Table for dataset schemas
CREATE TABLE dataset_schemas (
    id SERIAL PRIMARY KEY,
    dataset_id VARCHAR(255) NOT NULL,
    entity_type VARCHAR(255),
    entity_definition TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dataset_id) REFERENCES documents(doc_id)
);

-- Table for field definitions
CREATE TABLE dataset_fields (
    id SERIAL PRIMARY KEY,
    schema_id INTEGER REFERENCES dataset_schemas(id),
    field_name VARCHAR(255) NOT NULL,
    field_definition TEXT,
    field_source VARCHAR(255),
    domain_type VARCHAR(50),
    domain_values JSONB,  -- Store enumerated values as JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for lineage information
CREATE TABLE dataset_lineage (
    id SERIAL PRIMARY KEY,
    dataset_id VARCHAR(255) NOT NULL,
    process_step TEXT NOT NULL,
    process_date VARCHAR(50),
    process_sources TEXT[],
    step_order INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dataset_id) REFERENCES documents(doc_id)
);

-- Indexes for performance
CREATE INDEX idx_dataset_fields_schema_id ON dataset_fields(schema_id);
CREATE INDEX idx_dataset_lineage_dataset_id ON dataset_lineage(dataset_id);
```

**New DB functions in** `db.py`:
```python
def store_dataset_schema(schema: DatasetSchema) -> int
def store_dataset_lineage(lineage: DatasetLineage) -> int
def get_schema_by_dataset_id(dataset_id: str) -> Optional[DatasetSchema]
def get_lineage_by_dataset_id(dataset_id: str) -> Optional[DatasetLineage]
def search_fields(field_name_pattern: str) -> List[FieldDefinition]
```

### Task 3: Embedding Enhancement

**Update** `cli.py` `embed_and_store()` function:

```python
def embed_and_store():
    """Enhanced to include schema information in embeddings"""

    # Existing code...

    for doc in fsdocs:
        # Parse schema from XML
        schema = parse_xml_schema(xml_file_path)
        lineage = parse_xml_lineage(xml_file_path)

        # Store schema separately
        store_dataset_schema(schema)
        store_dataset_lineage(lineage)

        # Create schema summary for embedding
        schema_text = format_schema_for_embedding(schema)
        lineage_text = format_lineage_for_embedding(lineage)

        # Create chunks with different types
        chunks = [
            # Existing title+desc+keywords chunk
            create_metadata_chunk(doc),
            # New schema chunk
            create_schema_chunk(schema_text, chunk_type="schema"),
            # New lineage chunk
            create_lineage_chunk(lineage_text, chunk_type="lineage")
        ]

        # Embed and store all chunks
```

**Benefits:**
- Schema information becomes searchable via vector similarity
- Separate chunk types allow targeted retrieval
- Maintains backward compatibility with existing embeddings

### Task 4: Query Classification Enhancement

**Update** `src/catalog/api/query_classifier.py`:

```python
def classify_query(query: str) -> dict:
    """Enhanced to detect schema and lineage queries"""

    # Existing patterns...

    # New patterns
    schema_patterns = [
        r"(what|which|list)\s+(fields|columns|attributes|variables)",
        r"(describe|explain|show)\s+.*\s+(schema|structure|fields)",
        r"(data\s+type|field\s+type|column\s+type)",
        r"(field\s+definition|attribute\s+definition)",
    ]

    lineage_patterns = [
        r"(data\s+lineage|data\s+provenance)",
        r"(where.*come\s+from|data\s+source)",
        r"(how.*processed|processing\s+steps)",
        r"(data\s+pipeline|data\s+flow)",
    ]

    # Classification logic...
    if matches_any(query, schema_patterns):
        return {
            "type": "schema_query",
            "dataset": extract_dataset_name(query),
            "specific_field": extract_field_name(query)
        }

    if matches_any(query, lineage_patterns):
        return {
            "type": "lineage_query",
            "dataset": extract_dataset_name(query)
        }
```

### Task 5: LLM Prompt Enhancement

**Update** `src/catalog/api/llm.py` ChatBot class:

```python
def chat_with_schema(self, message: str, include_schema: bool = True) -> str:
    """Enhanced chat with schema context"""

    # Detect dataset being asked about
    dataset_id = extract_dataset_id_from_query(message)

    # Retrieve schema and lineage if available
    schema = get_schema_by_dataset_id(dataset_id) if dataset_id else None
    lineage = get_lineage_by_dataset_id(dataset_id) if dataset_id else None

    # Build enhanced context
    context = self.get_documents(message)

    if schema:
        context += f"\n\nDATASET SCHEMA:\n{format_schema_for_llm(schema)}"

    if lineage:
        context += f"\n\nDATA LINEAGE:\n{format_lineage_for_llm(lineage)}"

    # Enhanced system prompt
    system_prompt = """
    You are a professional data librarian specializing in scientific data discovery,
    metadata curation, and data governance. You have expertise in:
    - Dataset discovery and evaluation
    - Data schema interpretation (field types, domains, constraints)
    - Data lineage and provenance tracking
    - Data quality assessment

    When answering questions about:
    - SCHEMAS: Provide clear field-by-field descriptions, data types, and valid values
    - LINEAGE: Explain data sources, processing steps, and update frequency
    - QUALITY: Describe completeness, accuracy, and known limitations

    Use the provided schema and lineage information to give precise, technical answers.
    """

    # Rest of chat logic...
```

### Task 6: API Endpoint Enhancement

**Add new endpoints in** `api.py`:

```python
@api.get("/schema/{dataset_id}", tags=["Schema"])
async def get_dataset_schema(
    dataset_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Get structured schema information for a specific dataset.

    Returns:
    - Entity type and definition
    - List of all fields with definitions
    - Enumerated domain values where applicable
    """
    schema = get_schema_by_dataset_id(dataset_id)

    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found")

    return {
        "dataset_id": dataset_id,
        "schema": schema.dict()
    }

@api.get("/lineage/{dataset_id}", tags=["Lineage"])
async def get_dataset_lineage(
    dataset_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Get data lineage information for a specific dataset.

    Returns:
    - Processing steps in order
    - Data sources
    - Process dates
    """
    lineage = get_lineage_by_dataset_id(dataset_id)

    if not lineage:
        raise HTTPException(status_code=404, detail="Lineage not found")

    return {
        "dataset_id": dataset_id,
        "lineage": lineage.dict()
    }

@api.get("/query", tags=["Query"])
async def query(q: str, api_key: str = Depends(verify_api_key)):
    """Enhanced query endpoint with schema/lineage support"""

    query_type = classify_query(q)

    if query_type["type"] == "schema_query":
        # Handle schema-specific queries
        dataset_id = query_type["dataset"]
        schema = get_schema_by_dataset_id(dataset_id)

        # Format for LLM
        bot = ChatBot()
        response = bot.chat_with_schema(message=q, include_schema=True)

        return {
            "query": q,
            "response": response,
            "schema": schema.dict() if schema else None
        }

    elif query_type["type"] == "lineage_query":
        # Handle lineage-specific queries
        dataset_id = query_type["dataset"]
        lineage = get_lineage_by_dataset_id(dataset_id)

        bot = ChatBot()
        response = bot.chat_with_schema(message=q, include_schema=True)

        return {
            "query": q,
            "response": response,
            "lineage": lineage.dict() if lineage else None
        }

    # Existing query handling...
```

## Example Query Flows

### Example 1: Schema Query

**User Query:** "What fields are in the Actv_BrushDisposal dataset?"

**Flow:**
1. Query classifier detects "schema_query"
2. Extract dataset name: "Actv_BrushDisposal"
3. Retrieve schema from `dataset_schemas` + `dataset_fields` tables
4. Format schema context for LLM
5. LLM generates natural language response listing all fields

**Expected Response:**
```
The Actv_BrushDisposal dataset contains the following fields:

1. OBJECTID - Internal feature number (auto-generated sequential ID)
2. REGION_CODE - U.S. Forest Service Region (01-10, text format)
3. ADMIN_FOREST_CODE - Numerical code of administering forest
4. ADMIN_FOREST_NAME - Name of administering forest
5. PROCLAIMED_FOREST_CODE - Physical location forest code
6. ADMIN_DISTRICT_NAME - Ranger District name
7. DISTRICT_CODE - Unique district identifier (format: XX-XX-XX)
8. HOME_ORG - Home organization code (6 digits: region-forest-district)
9. ACTIVITY_UNIT_ORG - Activity unit organization code
10. SUID - Subunit ID (19-digit concatenated identifier)
11. FACTS_ID - Activity unit identifier (10 alphanumeric chars)
12. SUBUNIT - Activity subunit portion identifier
13. SALE_NAME - Timber sale contract name
14. ACTIVITY_CODE - 4-digit activity code (1000=Fire, 2000=Range, etc.)

[... additional fields ...]

This schema represents brush disposal activities tracked through the Forest Service
Activity Tracking System (FACTS).
```

### Example 2: Lineage Query

**User Query:** "Describe the data lineage of Actv_BrushDisposal.xml"

**Flow:**
1. Query classifier detects "lineage_query"
2. Extract dataset name: "Actv_BrushDisposal"
3. Retrieve lineage from `dataset_lineage` table
4. Format lineage context for LLM
5. LLM generates natural language response explaining provenance

**Expected Response:**
```
The Actv_BrushDisposal dataset has the following data lineage:

**Source Systems:**
- Forest Service Activity Tracking System (FACTS) - tabular data
- ActivityPolygon_Subunit - spatial features

**Processing Steps:**
1. Spatial features from ActivityPolygon_Subunit and tabular data from
   ACTIVITY_FACTS_ATTRIBUTES are merged based on Subunit ID (SUID)

2. A spatial feature is created for every activity record in the
   Activity_Facts_Attribute table

3. Only changed or new data from sources are processed incrementally

4. Features deleted from source are also deleted from Activity_BrushDisposal

5. GIS acres are calculated nightly for each feature

**Update Frequency:** Weekly (as of publication date 2025-10-24)

**Data Quality Notes:**
- Spatial data entry is optional but becoming required
- Not all brush disposal activities may be represented
- Quality expected to improve as spatial requirements are enforced

**Processing Start Date:** 2016-01-01
```

### Example 3: Field-Specific Query

**User Query:** "What is the ACTIVITY_CODE field and what values can it have?"

**Flow:**
1. Classifier detects schema query with specific field
2. Retrieve field definition for "ACTIVITY_CODE"
3. Retrieve enumerated domain values
4. Format for LLM with field details and value codes

**Expected Response:**
```
The ACTIVITY_CODE field is a 4-digit code representing the type of activity performed.

**Definition:** Activity codes numerically categorize Forest Service activities into
groups such as Fire, Range, Timber, Wildlife, etc.

**Valid Values:**
- 1000 series: Fire/Fuels Activities
  - 1001: Fire Protection Inventory
  - 1100: Fuel Inventory
  - 1111: Broadcast Burning
  [... more codes ...]

- 2000 series: Range Activities
- 3000 series: Cultural Resources and Recreation
- 4000 series: Timber and Silviculture
- 5000 series: Soil, Air and Watershed
- 6000 series: Wildlife, Threatened/Endangered, and Fisheries
- 7000 series: Vegetation/Restoration
- 8000 series: Miscellaneous
- 9000 series: Engineering

**Source:** FACTS User Guide, Appendix B: Activity Codes
```

## Implementation Priority

### Phase 1: Core Schema Support (Tasks 1-2)
- Build XML schema parser
- Create database schema
- Test with sample datasets

### Phase 2: Integration (Tasks 3-4)
- Update embedding pipeline
- Add query classification
- Test schema retrieval

### Phase 3: API & LLM (Tasks 5-6)
- Enhance LLM prompts
- Add API endpoints
- End-to-end testing

## Testing Strategy

1. **Unit Tests:**
   - XML parsing functions
   - Database CRUD operations
   - Query classification patterns

2. **Integration Tests:**
   - Full pipeline: XML → Parse → Store → Retrieve → Embed
   - API endpoint responses
   - LLM context building

3. **Test Queries:**
   - "List all fields in Actv_BrushDisposal"
   - "What is the data lineage for brush disposal data?"
   - "Explain the REGION_CODE field"
   - "What activity codes are used for fire management?"

## Benefits

1. **Enhanced Discovery:** Users can understand dataset structure before use
2. **Data Governance:** Track data lineage and processing steps
3. **Better Search:** Schema-aware embeddings improve retrieval accuracy
4. **Transparency:** Clear field definitions and domain values
5. **Compliance:** Support data provenance requirements

## Technical Considerations

1. **Performance:**
   - Schema/lineage stored separately from embeddings
   - Indexed for fast retrieval
   - Can be cached at API layer

2. **Scalability:**
   - Schema tables normalized (one row per field)
   - JSONB for flexible domain value storage
   - Incremental updates supported

3. **Backward Compatibility:**
   - New tables don't affect existing queries
   - Schema enrichment is additive
   - Old API endpoints unchanged

4. **Data Quality:**
   - Not all XML files may have complete schema info
   - Parser should handle missing sections gracefully
   - Log parsing errors for review

## Next Steps

**Decision Points:**
1. Implement all 6 tasks or start with subset?
2. Natural language queries only, or also structured API endpoints?
3. Store lineage/schema separately or combined in document metadata?

**Recommended Start:**
- Begin with Tasks 1-2 (parser + database)
- Validate with 5-10 sample XML files
- Then proceed to integration tasks

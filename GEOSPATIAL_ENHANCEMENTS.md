# Geospatial Enhancements for Catalog Project

## Overview
This document outlines recommended geospatial enhancements for the Catalog project, which currently implements a metadata catalog with vector search and LLM-enhanced RAG capabilities for USFS (Forest Service) data.

## Current Architecture
- **Database**: PostgreSQL with pgvector extension
- **Vector Search**: Sentence Transformers (all-MiniLM-L6-v2)
- **LLM**: Llama models via CyVerse ESIIL API
- **Data**: USFS document metadata with semantic search

---

## Recommended Geospatial Enhancements

### 1. PostGIS Integration (Highest Priority)
Since you're already using PostgreSQL, add PostGIS for native geospatial support:

**Schema additions:**
```sql
CREATE EXTENSION IF NOT EXISTS postgis;

ALTER TABLE documents ADD COLUMN geom geometry(Geometry, 4326);
ALTER TABLE documents ADD COLUMN bbox geometry(Polygon, 4326);
CREATE INDEX idx_documents_geom ON documents USING GIST(geom);
```

**Benefits:**
- Query by bounding box: "datasets covering Grand Canyon"
- Spatial joins: "all datasets overlapping national forests"
- Distance queries: "datasets within 50km of coordinates"
- Works seamlessly with your existing pgvector setup

---

### 2. Enhanced Schema for Geospatial Metadata
Extend `USFSDocument` schema in `src/catalog/schema.py`:

```python
class USFSDocument(BaseModel):
    id: str
    title: str
    description: str
    keywords: Optional[List[str]] = None
    src: Optional[str] = None

    # NEW: Geospatial fields
    bbox: Optional[List[float]] = None  # [west, south, east, north]
    geometry: Optional[dict] = None  # GeoJSON
    spatial_coverage: Optional[str] = None  # "Arizona", "Coconino National Forest"
    coordinate_system: Optional[str] = None  # "EPSG:4326"
```

---

### 3. Hybrid Vector + Spatial Search
Combine semantic similarity with spatial filtering in `src/catalog/db.py`:

**Enhanced `search_docs()` function:**
```python
def search_docs(
    query_embedding: list[float],
    bbox: Optional[tuple] = None,  # (west, south, east, north)
    limit: int = 10
) -> list:
    """
    Search with both semantic similarity and spatial filter.

    Example: Find "wildfire risk" datasets in Arizona bounding box
    """

    sql_query = """
        SELECT id, title, description, keywords,
               ST_AsGeoJSON(geom) as geometry,
               1 - (embedding <=> %s::vector) AS similarity_score
        FROM documents
        WHERE embedding IS NOT NULL
    """

    params = [query_embedding, query_embedding]

    # Add spatial filter if bbox provided
    if bbox:
        sql_query += """
            AND ST_Intersects(
                geom,
                ST_MakeEnvelope(%s, %s, %s, %s, 4326)
            )
        """
        params.extend(bbox)

    sql_query += " ORDER BY embedding <=> %s::vector LIMIT %s"
    params.extend([query_embedding, limit])

    cur.execute(sql_query, params)
    # ... rest of implementation
```

---

### 4. LLM-Driven Spatial Query Understanding
Enhance `src/catalog/llm.py` to extract geospatial intent:

**New method for ChatBot class:**
```python
def extract_spatial_context(self, message: str) -> dict:
    """
    Use LLM to parse spatial references from natural language.

    Examples:
    - "datasets about Arizona" → spatial_coverage: "Arizona"
    - "data covering 34.5, -112.1" → point query
    - "Grand Canyon region" → geocode to bbox
    """

    response = self.client.chat.completions.create(
        model=self.model,
        messages=[{
            "role": "system",
            "content": (
                "Extract geospatial information from queries. Return JSON with:\n"
                "- location_names: list of place names\n"
                "- coordinates: lat/lon if mentioned\n"
                "- bbox: bounding box if inferable\n"
                "- spatial_relationship: 'within', 'near', 'intersecting'\n"
            )
        }, {
            "role": "user",
            "content": message
        }]
    )

    return json.loads(response.choices[0].message.content)
```

**Integration**: Call this method in the existing `chat()` method (around line 49) to pass spatial filters to `get_documents()`.

---

### 5. Geocoding Integration
Add location name → coordinates resolution:

**Dependencies:**
```bash
uv add geopy
```

**Implementation:**
```python
from geopy.geocoders import Nominatim

def geocode_location(location: str) -> Optional[dict]:
    """
    Convert 'Grand Canyon' → (36.1069, -112.1129, bbox)
    """
    geolocator = Nominatim(user_agent="catalog-usfs")
    result = geolocator.geocode(location)

    if result:
        return {
            'lat': result.latitude,
            'lon': result.longitude,
            'bbox': result.raw.get('boundingbox')
        }
    return None
```

---

### 6. Spatial-Aware RAG Context
Modify `src/catalog/llm.py` (around lines 51-56) to include spatial metadata:

**Enhanced context generation:**
```python
context = "\n\n".join([
    f"Title: {doc['title']}\n"
    f"Description: {doc['description']}\n"
    f"Keywords: {doc['keywords']}\n"
    f"Spatial Coverage: {doc.get('spatial_coverage', 'Not specified')}\n"
    f"Bounding Box: {doc.get('bbox', 'Not specified')}"
    for doc in documents
])
```

**Update system prompt** (lines 64-76) to include:
> "When datasets have spatial information, highlight their geographic coverage and relevance to the user's location of interest."

---

### 7. API Enhancements
Add spatial query parameters to `src/catalog/api.py`:

**Enhanced `/query` endpoint:**
```python
@api.get("/query", tags=["Query"])
async def query(
    q: str,
    bbox: Optional[str] = None,  # "west,south,east,north"
    location: Optional[str] = None,  # "Arizona" or "Grand Canyon"
    api_key: str = Depends(verify_api_key)
):
    """
    Query with optional spatial filters:
    - bbox: comma-separated coordinates
    - location: place name (will be geocoded)

    Examples:
    - /query?q=wildfire&bbox=-112.5,34.0,-111.0,35.0
    - /query?q=forest health&location=Arizona
    """

    spatial_filter = None
    if bbox:
        spatial_filter = tuple(map(float, bbox.split(',')))
    elif location:
        geocoded = geocode_location(location)
        if geocoded:
            spatial_filter = geocoded['bbox']

    bot = ChatBot()
    response = bot.chat(q, spatial_filter=spatial_filter)

    return {
        "query": q,
        "spatial_filter": spatial_filter,
        "response": response
    }
```

---

## Implementation Roadmap

### Phase 1: Core Spatial (2-3 days)
1. Install PostGIS extension in PostgreSQL
2. Add `bbox` and `geom` columns to schema
3. Update `USFSDocument` Pydantic model with spatial fields
4. Modify `search_docs()` to accept and use bbox parameter
5. Update database insertion logic to store spatial data

**Files to modify:**
- `schema.sql` - Add PostGIS columns and indexes
- `src/catalog/schema.py` - Add spatial fields to USFSDocument
- `src/catalog/db.py` - Update `save_to_vector_db()` and `search_docs()`

### Phase 2: LLM Integration (2-3 days)
6. Add spatial context extraction to `ChatBot` class
7. Update system prompt to handle spatial queries
8. Include spatial metadata in RAG context generation
9. Modify `get_documents()` to pass spatial filters

**Files to modify:**
- `src/catalog/llm.py` - Add `extract_spatial_context()` method
- `src/catalog/llm.py` - Update `chat()` and `get_documents()` methods

### Phase 3: Advanced Features (3-4 days)
10. Implement geocoding for location names
11. Add spatial query endpoints to API
12. Build spatial visualization (optional: Leaflet/Mapbox integration)
13. Add CLI commands for spatial queries
14. Create tests for spatial functionality

**Files to modify:**
- `src/catalog/api.py` - Add spatial parameters to endpoints
- `src/catalog/cli.py` - Add spatial search commands
- `tests/` - Add spatial query tests

---

## Example Use Cases

With these enhancements, users can perform queries like:

1. **"Find wildfire datasets in the Sierra Nevada"**
   - LLM extracts location name
   - Geocodes "Sierra Nevada" to bbox
   - Filters documents by spatial intersection
   - Returns semantically relevant USFS data

2. **"What data covers coordinates 34.5, -111.8?"**
   - Parses point coordinates
   - Performs point-in-polygon search
   - Ranks results by semantic relevance

3. **"Show me forest health assessments near Flagstaff within 25 miles"**
   - Geocodes "Flagstaff"
   - Performs distance-based spatial query
   - Filters by semantic relevance to "forest health"
   - Returns ranked results with RAG-enhanced descriptions

4. **"List all datasets covering Arizona national forests"**
   - Extracts state boundary
   - Filters by "national forests" keyword
   - Spatial intersection with Arizona bbox
   - LLM generates summary of available datasets

---

## Dependencies to Add

```bash
# Geospatial libraries
uv add geopy          # Geocoding
uv add shapely        # Geometry manipulation (optional)
uv add geopandas      # Geospatial data analysis (optional)
```

**PostgreSQL:**
- PostGIS extension (install via apt/yum or Docker image)

---

## Testing Strategy

1. **Unit Tests**: Test individual spatial functions (geocoding, bbox parsing)
2. **Integration Tests**: Test hybrid vector+spatial queries
3. **LLM Tests**: Verify spatial context extraction from natural language
4. **API Tests**: Test spatial parameters in query endpoints
5. **Performance Tests**: Benchmark spatial index performance

---

## Migration Strategy

**For existing data:**
1. Add new columns with `ALTER TABLE` (non-breaking change)
2. Backfill spatial data where available
3. Create spatial indexes
4. Verify query performance

**SQL migration script:**
```sql
-- Add columns
ALTER TABLE documents ADD COLUMN IF NOT EXISTS geom geometry(Geometry, 4326);
ALTER TABLE documents ADD COLUMN IF NOT EXISTS bbox geometry(Polygon, 4326);
ALTER TABLE documents ADD COLUMN IF NOT EXISTS spatial_coverage TEXT;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_documents_geom ON documents USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_documents_bbox ON documents USING GIST(bbox);

-- Backfill example (if you have lat/lon in metadata)
-- UPDATE documents SET geom = ST_SetSRID(ST_MakePoint(lon, lat), 4326)
-- WHERE lon IS NOT NULL AND lat IS NOT NULL;
```

---

## Performance Considerations

1. **Spatial Indexes**: GIST indexes are essential for spatial queries
2. **Query Planning**: Combine vector and spatial filters efficiently
3. **Data Volume**: For large datasets, consider partitioning by spatial region
4. **Caching**: Cache geocoding results to avoid repeated API calls

---

## Resources

- **PostGIS Documentation**: https://postgis.net/docs/
- **pgvector + PostGIS**: Both extensions work seamlessly together
- **GeoJSON Standard**: https://geojson.org/
- **Coordinate Systems**: EPSG:4326 (WGS84) is standard for lat/lon

---

## Questions to Consider

1. **Data Sources**: Does your USFS data already contain spatial metadata?
2. **Coordinate Systems**: Will you need to support multiple projections?
3. **Precision**: What level of spatial accuracy is required?
4. **Visualization**: Do you need map-based interfaces for users?
5. **Scale**: How many spatial queries per second do you anticipate?

---

## Next Steps

To get started, choose one of:

1. **Quick Start**: Implement Phase 1 (core spatial database features)
2. **Full Implementation**: Work through all three phases
3. **Proof of Concept**: Test with a small dataset to validate approach

Generated: 2025-10-14

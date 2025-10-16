# Geospatial Enhancement Ideas for Catalog

## Overview
This document outlines potential enhancements to leverage spatial features present in the XML and JSON metadata sources (FSGeodata, DataHub, RDA).

## 1. Database Schema Enhancements

### Add PostGIS Extension
Extend the current PostgreSQL setup to include PostGIS for spatial operations:

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
```

### Extend Documents Table
Add spatial columns to the existing `documents` table (currently defined in `schema.sql:4-17`):

```sql
ALTER TABLE documents ADD COLUMN bbox geometry(Polygon, 4326);
ALTER TABLE documents ADD COLUMN centroid geometry(Point, 4326);
CREATE INDEX idx_documents_bbox ON documents USING GIST(bbox);
```

**Spatial fields to capture:**
- Bounding box coordinates (westbc, eastbc, northbc, southbc from XML)
- Geometry column for storing spatial data
- Centroid for point-based queries
- Spatial index for query performance

## 2. Schema Model Updates

### Enhance USFSDocument Model
Update the Pydantic model in `schema.py:11-27` to include spatial fields:

```python
from typing import Optional, List
from pydantic import BaseModel

class SpatialExtent(BaseModel):
    west: float
    east: float
    north: float
    south: float

class USFSDocument(BaseModel):
    id: str
    title: str
    description: str
    keywords: Optional[List[str]] = None
    src: Optional[str] = None
    spatial_extent: Optional[SpatialExtent] = None
    centroid_lat: Optional[float] = None
    centroid_lon: Optional[float] = None
```

## 3. Parsing Enhancements

### Update Metadata Parsers
Enhance the parsing functions in `cli.py:144-239`:

- **`_parse_fsgeodata_metadata()`**: Extract `<westbc>`, `<eastbc>`, `<northbc>`, `<southbc>` from XML
- **`_parse_datahub_metadata()`**: Extract spatial/bbox fields from JSON
- **`_parse_rda_metadata()`**: Extract spatial coverage fields from JSON

Example extraction logic:
```python
# For XML (FSGeodata)
west = soup.find("westbc").get_text() if soup.find("westbc") else None
east = soup.find("eastbc").get_text() if soup.find("eastbc") else None
north = soup.find("northbc").get_text() if soup.find("northbc") else None
south = soup.find("southbc").get_text() if soup.find("southbc") else None

if all([west, east, north, south]):
    asset["spatial_extent"] = {
        "west": float(west),
        "east": float(east),
        "north": float(north),
        "south": float(south)
    }
```

## 4. New Search Capabilities

### Geospatial Query Functions
Add new functions to `db.py` for spatial operations:

**Bounding Box Search:**
```python
def search_by_bbox(west: float, south: float, east: float, north: float):
    """Find all documents within a geographic bounding box."""
    pass
```

**Radius Search:**
```python
def search_by_radius(lat: float, lon: float, radius_km: float):
    """Find documents within X km of a point."""
    pass
```

**Spatial Overlap:**
```python
def search_by_intersection(geometry):
    """Find documents that intersect with a region."""
    pass
```

**Distance-Based Ranking:**
```python
def search_with_spatial_ranking(query: str, lat: float, lon: float):
    """Combine semantic search with spatial proximity ranking."""
    pass
```

## 5. API Enhancements

### New Spatial Endpoints
Add spatial query endpoints to `api.py`:

```python
@api.get("/search/spatial")
async def search_spatial(bbox: str):
    """
    Search by bounding box.

    Query params:
        bbox: west,south,east,north (e.g., "-124,32,-72,49")
    """
    pass

@api.get("/search/nearby")
async def search_nearby(lat: float, lon: float, radius: float):
    """
    Search within radius of a point.

    Query params:
        lat: Latitude
        lon: Longitude
        radius: Radius in kilometers
    """
    pass

@api.get("/documents/{doc_id}/extent")
async def get_document_extent(doc_id: str):
    """Return the spatial extent of a specific document."""
    pass

@api.get("/search/hybrid")
async def hybrid_search(query: str, lat: float = None, lon: float = None):
    """
    Combine semantic search with optional spatial filtering.

    Query params:
        query: Natural language search query
        lat: Optional latitude for spatial ranking
        lon: Optional longitude for spatial ranking
    """
    pass
```

## 6. LLM Context Enhancement

### Include Spatial Information in Embeddings
Update `embed_and_store()` in `cli.py:280-319` to include spatial context:

```python
# Calculate human-readable spatial description
spatial_desc = ""
if doc.spatial_extent:
    spatial_desc = f"Geographic coverage: West {doc.spatial_extent.west}°, " \
                   f"East {doc.spatial_extent.east}°, " \
                   f"North {doc.spatial_extent.north}°, " \
                   f"South {doc.spatial_extent.south}°"

combined_text = f"Title: {title}\n" \
                f"Description: {description}\n" \
                f"Keywords: {keywords}\n" \
                f"{spatial_desc}\n" \
                f"Source: {src}"
```

**Benefits:**
- LLM can understand geographic context in natural language queries
- Enables queries like:
  - "Show me forest data in the Pacific Northwest"
  - "Find datasets covering Montana"
  - "What data is available for the Sierra Nevada region"
  - "Data near Yellowstone National Park"

## 7. Query Enhancement Features

### Spatial Pre-filtering
Implement a two-stage search:
1. **Stage 1**: Filter by geographic area (fast spatial index query)
2. **Stage 2**: Apply semantic vector similarity on filtered results

### Hybrid Ranking
Combine multiple ranking signals:
```python
final_score = (0.7 * semantic_similarity) + (0.3 * spatial_proximity_score)
```

### Geographic Entity Recognition
- Parse location names from natural language queries
- Convert place names to coordinates using geocoding
- Example: "data about Yosemite" → lat/lon bounds for Yosemite National Park

## 8. Visualization Opportunities

### Potential UI Enhancements
- **Map-based search interface**: Interactive map for drawing search areas
- **Spatial coverage visualization**: Show dataset footprints on a map
- **Geographic clustering**: Visualize concentration of datasets by region
- **Heatmaps**: Show data density by geographic area

### Example Libraries
- Leaflet.js for web mapping
- Folium for Python-based map generation
- Deck.gl for advanced 3D visualizations

## Implementation Priority

### Phase 1: Database Foundation
1. Add PostGIS extension to Docker setup (`Dockerfile.db`)
2. Update `schema.sql` with spatial columns
3. Add spatial indexes

### Phase 2: Data Extraction
1. Enhance metadata parsers to extract spatial data
2. Update `USFSDocument` model with spatial fields
3. Test with existing metadata sources

### Phase 3: Query Functions
1. Implement spatial query functions in `db.py`
2. Add unit tests for spatial operations
3. Benchmark query performance

### Phase 4: API Layer
1. Create spatial API endpoints in `api.py`
2. Add request validation for spatial parameters
3. Document API endpoints

### Phase 5: LLM Integration
1. Enhance embeddings with spatial context
2. Implement hybrid search (semantic + spatial)
3. Add geographic entity recognition

### Phase 6: User Experience
1. Build map-based search interface
2. Add spatial visualization components
3. Implement geographic result clustering

## Technical Considerations

### Coordinate Reference Systems
- Use EPSG:4326 (WGS84) for consistency with most web mapping
- Store coordinates as decimal degrees
- Consider reprojection for distance calculations (use EPSG:3857 or appropriate UTM zones)

### Performance Optimization
- Spatial indexes are critical (GIST indexes in PostGIS)
- Consider caching frequently searched regions
- Use spatial aggregation for large result sets

### Data Quality
- Validate bounding box coordinates (west < east, south < north)
- Handle missing spatial data gracefully
- Consider data quality flags for spatial accuracy

### Docker Compose Updates
Update `compose.yml:1-42` to use PostGIS-enabled PostgreSQL image:
```yaml
services:
  db:
    image: postgis/postgis:16-3.4
    # ... rest of configuration
```

## Example Use Cases

1. **Regional Dataset Discovery**: "Show all forest inventory data for Oregon"
2. **Proximity Search**: "Find datasets within 50km of Mount Rainier"
3. **Comparative Analysis**: "Compare datasets covering the same geographic area"
4. **Gap Analysis**: "Identify regions with sparse data coverage"
5. **Project Planning**: "Find all relevant datasets for this project boundary"

## Dependencies to Add

```toml
# Add to pyproject.toml dependencies
dependencies = [
    # ... existing dependencies
    "geoalchemy2>=0.14.0",  # SQLAlchemy spatial extensions
    "shapely>=2.0.0",        # Geometric operations
    "geopy>=2.4.0",          # Geocoding (optional)
]
```

## Resources

- **PostGIS Documentation**: https://postgis.net/documentation/
- **GeoAlchemy2 Docs**: https://geoalchemy-2.readthedocs.io/
- **Shapely Guide**: https://shapely.readthedocs.io/
- **USGS Spatial Metadata Standards**: https://www.fgdc.gov/metadata/geospatial-metadata-standards

## Notes

- This is a proof-of-concept project, so implement incrementally
- Start with simple bounding box queries before advanced spatial operations
- Consider user privacy when storing location-based search queries
- Spatial features are particularly valuable for USFS datasets which are inherently geographic

-- Migration: Add Data Librarian Enhancements
-- Date: 2025-01-05
-- Description: Extends existing tables with dataset metadata, technical field info,
--              and adds new tables for lineage and relationship tracking

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

-- Enable fuzzy text search extension
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

-- Set display names from dataset names
UPDATE entity_type
SET display_name = replace(dataset_name, '_', ' ')
WHERE display_name IS NULL AND dataset_name IS NOT NULL;

-- ============================================================================
-- ADD COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON COLUMN entity_type.dataset_name IS 'Short, unique name for dataset lookups';
COMMENT ON COLUMN entity_type.display_name IS 'Human-friendly display name';
COMMENT ON COLUMN entity_type.dataset_type IS 'Type: feature_class, table, view, raster, etc.';
COMMENT ON COLUMN entity_type.source_system IS 'Source system: USFS GIS, ArcGIS Online, etc.';

COMMENT ON COLUMN attribute.data_type IS 'Data type: Integer, String, Float, Date, Geometry, etc.';
COMMENT ON COLUMN attribute.is_primary_key IS 'Primary key indicator';
COMMENT ON COLUMN attribute.is_foreign_key IS 'Foreign key indicator';

COMMENT ON TABLE field_lineage IS 'Tracks field-level data lineage and transformations';
COMMENT ON TABLE dataset_lineage IS 'Tracks dataset-level dependencies';
COMMENT ON TABLE dataset_relationships IS 'Tracks relationships between datasets (foreign keys, references)';

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

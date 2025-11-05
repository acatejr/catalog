-- Migration: Add tables for Entity and Attribute Information (eainfo)
-- Date: 2025-11-05
-- Description: Creates normalized tables to store FGDC entity and attribute metadata

-- Create eainfo table (root level)
CREATE TABLE IF NOT EXISTS eainfo (
    id SERIAL PRIMARY KEY,
    overview TEXT,
    citation TEXT,
    parsed_at TIMESTAMP,
    source_file TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create entity_type table
CREATE TABLE IF NOT EXISTS entity_type (
    id SERIAL PRIMARY KEY,
    eainfo_id INTEGER NOT NULL REFERENCES eainfo(id) ON DELETE CASCADE,
    label TEXT NOT NULL,
    definition TEXT,
    definition_source TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create attribute table
CREATE TABLE IF NOT EXISTS attribute (
    id SERIAL PRIMARY KEY,
    entity_type_id INTEGER NOT NULL REFERENCES entity_type(id) ON DELETE CASCADE,
    label TEXT NOT NULL,
    definition TEXT NOT NULL,
    definition_source TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create attribute_domain table (stores all domain value types)
CREATE TABLE IF NOT EXISTS attribute_domain (
    id SERIAL PRIMARY KEY,
    attribute_id INTEGER NOT NULL REFERENCES attribute(id) ON DELETE CASCADE,
    domain_type VARCHAR(50) NOT NULL CHECK (domain_type IN ('unrepresentable', 'enumerated', 'codeset', 'range')),
    domain_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for foreign keys and common queries
CREATE INDEX IF NOT EXISTS idx_entity_type_eainfo_id ON entity_type(eainfo_id);
CREATE INDEX IF NOT EXISTS idx_attribute_entity_type_id ON attribute(entity_type_id);
CREATE INDEX IF NOT EXISTS idx_attribute_domain_attribute_id ON attribute_domain(attribute_id);
CREATE INDEX IF NOT EXISTS idx_attribute_domain_type ON attribute_domain(domain_type);

-- Create index on JSONB domain_data for efficient queries
CREATE INDEX IF NOT EXISTS idx_attribute_domain_data ON attribute_domain USING GIN (domain_data);

-- Add comments for documentation
COMMENT ON TABLE eainfo IS 'Root table for FGDC Entity and Attribute Information metadata';
COMMENT ON TABLE entity_type IS 'Entity type definitions (e.g., feature classes, tables)';
COMMENT ON TABLE attribute IS 'Attribute/field definitions for entities';
COMMENT ON TABLE attribute_domain IS 'Domain value specifications for attributes (enumerated, range, codeset, unrepresentable)';
COMMENT ON COLUMN attribute_domain.domain_data IS 'JSONB field storing type-specific domain information';

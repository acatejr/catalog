# Integration test based on __main__ block in schema_parser.py
import os
import pytest
from catalog.core.schema_parser import EAInfoParser


def test_parse_actv_brush_disposal_xml():
    """
    Integration test that parses the actual Actv_BrushDisposal.xml file.
    Based on the __main__ block from schema_parser.py
    """
    SOURCE_DIR = "data/catalog"
    xml_file_path = f"{SOURCE_DIR}/Actv_BrushDisposal.xml"

    # Skip test if file doesn't exist
    if not os.path.exists(xml_file_path):
        pytest.skip(f"Test file not found: {xml_file_path}")

    # Parse XML file
    parser = EAInfoParser()
    eainfo = parser.parse_xml_file(xml_file_path)

    # Verify parsing succeeded
    assert eainfo is not None
    assert eainfo.source_file == xml_file_path
    assert eainfo.parsed_at is not None

    # Access entity information
    assert eainfo.has_detailed_info, "Expected eainfo to have detailed information"
    assert eainfo.detailed is not None
    assert eainfo.detailed.entity_type is not None

    # Verify entity type label
    entity_label = eainfo.detailed.entity_type.label
    assert entity_label is not None
    assert len(entity_label) > 0
    print(f"Entity: {entity_label}")

    # Verify attributes
    assert eainfo.total_attributes > 0, "Expected at least one attribute"
    print(f"Attributes: {eainfo.total_attributes}")

    # List all attributes and verify structure
    assert len(eainfo.detailed.attributes) == eainfo.total_attributes
    for attr in eainfo.detailed.attributes:
        assert attr.label is not None
        assert attr.definition is not None
        assert len(attr.label) > 0
        assert len(attr.definition) > 0
        print(f"  - {attr.label}: {attr.definition[:50]}...")

    # Verify some expected attributes for BrushDisposal entity
    attribute_labels = eainfo.detailed.attribute_labels
    assert "OBJECTID" in attribute_labels or "objectid" in [
        a.lower() for a in attribute_labels
    ]


def test_parse_actv_brush_disposal_to_schema_dict():
    """
    Test conversion of parsed eainfo to schema dictionary
    """
    SOURCE_DIR = "data/catalog"
    xml_file_path = f"{SOURCE_DIR}/Actv_BrushDisposal.xml"

    # Skip test if file doesn't exist
    if not os.path.exists(xml_file_path):
        pytest.skip(f"Test file not found: {xml_file_path}")

    # Parse XML file
    parser = EAInfoParser()
    eainfo = parser.parse_xml_file(xml_file_path)

    # Convert to schema dict
    schema_dict = eainfo.to_schema_dict()

    # Verify schema dict structure
    assert "entity_label" in schema_dict
    assert "entity_definition" in schema_dict
    assert "attributes" in schema_dict
    assert isinstance(schema_dict["attributes"], list)
    assert len(schema_dict["attributes"]) > 0

    # Verify attribute structure
    first_attr = schema_dict["attributes"][0]
    assert "name" in first_attr
    assert "definition" in first_attr
    assert "domain_type" in first_attr

    print(
        f"Schema for {schema_dict['entity_label']} with {len(schema_dict['attributes'])} attributes"
    )

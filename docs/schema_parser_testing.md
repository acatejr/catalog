# Schema Parser Testing

## Overview

Integration tests for the FGDC Entity and Attribute Information (eainfo) parser, based on the `__main__` block in `schema_parser.py`.

## Test File

**Location:** `tests/test_eainfo.py`

## Tests Implemented

### 1. `test_parse_actv_brush_disposal_xml()`

Integration test that parses the actual `Actv_BrushDisposal.xml` file.

**Purpose:** Validate the complete parsing workflow with real-world FGDC metadata

**Test Coverage:**

- Parse XML file using `EAInfoParser.parse_xml_file()`
- Verify eainfo metadata (source_file, parsed_at timestamp)
- Validate detailed information exists
- Check entity type structure and label
- Verify attribute count > 0
- Iterate through all attributes
- Validate attribute structure (label, definition)
- Check for expected attributes (OBJECTID)

**Key Assertions:**

```python
assert eainfo.has_detailed_info
assert eainfo.total_attributes > 0
assert eainfo.detailed.entity_type.label is not None
assert "OBJECTID" in attribute_labels
```

**Features:**

- Uses `pytest.skip()` if test file doesn't exist (graceful handling)
- Includes debug print statements for manual verification
- Validates both structure and content

### 2. `test_parse_actv_brush_disposal_to_schema_dict()`

Test conversion of parsed eainfo to schema dictionary format.

**Purpose:** Validate the `to_schema_dict()` method for database storage preparation

**Test Coverage:**

- Parse XML file
- Convert eainfo to schema dictionary
- Verify schema dict structure
- Validate required fields
- Check attribute format in dictionary

**Key Assertions:**

```python
assert "entity_label" in schema_dict
assert "entity_definition" in schema_dict
assert "attributes" in schema_dict
assert "name" in first_attr
assert "definition" in first_attr
assert "domain_type" in first_attr
```

**Use Case:** Prepares data structure for database insertion

## Running the Tests

### Run Both Tests

```bash
pytest tests/test_eainfo.py -v
```

### Run Individual Test

```bash
# Test parsing
pytest tests/test_eainfo.py::test_parse_actv_brush_disposal_xml -v -s

# Test schema dict conversion
pytest tests/test_eainfo.py::test_parse_actv_brush_disposal_to_schema_dict -v -s
```

### With Debug Output

```bash
pytest tests/test_eainfo.py -v -s
```

The `-s` flag shows print statements for debugging.

## Test Data

**Required File:** `data/catalog/Actv_BrushDisposal.xml`

This is a real FGDC metadata file for the U.S. Forest Service Activity - Brush Disposal feature class.

## Expected Results

When tests pass, you should see output similar to:

```
Entity: S_USA.Activity_BrushDisposal
Attributes: 42
  - OBJECTID: Internal feature number...
  - SHAPE: Feature geometry...
  - ACTIVITY_CODE: Activity code from FACTS system...
  ...

Schema for S_USA.Activity_BrushDisposal with 42 attributes
```

## Test Design Principles

### Integration Over Unit Tests

These are integration tests rather than unit tests because:

- They test the complete parsing workflow
- They use real XML data files
- They validate the entire data pipeline from file to Python objects

### Graceful Degradation

```python
if not os.path.exists(xml_file_path):
    pytest.skip(f"Test file not found: {xml_file_path}")
```

Tests skip gracefully if data files are missing, preventing false negatives in CI/CD environments.

### Debug-Friendly

Print statements included to help diagnose issues:

```python
print(f"Entity: {entity_label}")
print(f"Attributes: {eainfo.total_attributes}")
```

## Relationship to Database Storage

These tests validate the data structures before they're saved to the database:

1. **Parse** - `test_parse_actv_brush_disposal_xml()` validates parsing
2. **Transform** - `test_parse_actv_brush_disposal_to_schema_dict()` validates transformation
3. **Save** - Future test should validate `save_eainfo()` from `db.py`

## Future Test Recommendations

### Unit Tests (Currently Commented Out)

The file contains comprehensive unit tests (lines 1-242) that are currently commented out. These should be uncommented and maintained:

- Domain value type tests (unrepresentable, enumerated, codeset, range)
- Attribute tests (enumerated values, domain filtering)
- Entity type tests
- Parser method tests (parse_domain_value, parse_attribute, etc.)

### Additional Integration Tests

1. **Test Multiple XML Files**

   ```python
   @pytest.mark.parametrize("xml_file", [
       "Actv_BrushDisposal.xml",
       "Actv_Burning.xml",
       # ... other files
   ])
   def test_parse_various_xml_files(xml_file):
       # Test parsing multiple file types
   ```

2. **Test Database Round-Trip**

   ```python
   def test_save_and_retrieve_eainfo():
       # Parse XML
       eainfo = parser.parse_xml_file(xml_file_path)

       # Save to database
       eainfo_id = save_eainfo(eainfo)

       # Retrieve from database
       saved_eainfo = get_eainfo_by_id(eainfo_id)

       # Verify data integrity
       assert saved_eainfo['entity_type']['label'] == eainfo.detailed.entity_type.label
   ```

3. **Test Error Handling**

   ```python
   def test_parse_invalid_xml():
       # Test with malformed XML

   def test_parse_missing_required_fields():
       # Test with incomplete metadata
   ```

4. **Performance Tests**

   ```python
   def test_parse_large_xml_performance():
       # Test with XML files containing many attributes
   ```

## Known Issues

### Pylance Import Warning

```
⚠ Import "catalog.core.schema_parser" could not be resolved
```

**Resolution:** Ensure PYTHONPATH includes `src/` directory when running tests:

```bash
PYTHONPATH=src pytest tests/test_eainfo.py
```

Or use the project's helper script:

```bash
./run-tests.sh
```

## Summary

The tests validate:

- ✅ XML parsing with real FGDC metadata
- ✅ Entity and attribute structure
- ✅ Data transformation to schema dictionary
- ✅ Graceful handling of missing files
- ✅ Debug-friendly output

Next steps:

1. Uncomment and update unit tests
2. Add database round-trip tests
3. Add parametrized tests for multiple XML files
4. Create CI/CD pipeline integration

"""Shared pytest fixtures for the catalog test suite."""

import pytest


@pytest.fixture
def sample_document_dict():
    """Fixture providing a sample document dictionary."""
    return {
        "id": "abc123",
        "title": "Sample Dataset",
        "abstract": "A sample abstract for testing.",
        "purpose": "Testing purposes only.",
        "keywords": ["test", "sample"],
        "src": "fsgeodata",
        "lineage": [{"description": "Created for testing", "date": "2024-01-01"}],
        "description": "A sample description.",
    }


@pytest.fixture
def sample_lineage_list():
    """Fixture providing a sample lineage list."""
    return [
        {"description": "Initial creation", "date": "2024-01-01"},
        {"description": "Updated metadata", "date": "2024-06-15"},
    ]

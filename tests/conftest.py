"""
Shared test configuration and fixtures for the catalog project.
"""

import pytest
from fastapi.testclient import TestClient
from src.catalog.api.main import app


@pytest.fixture(scope="session")
def api_client():
    """
    Create a test client for the FastAPI app that can be shared across test sessions.
    This fixture has session scope to avoid recreating the client for each test.
    """
    return TestClient(app)


@pytest.fixture
def sample_queries():
    """
    Provide sample query strings for testing the query endpoint.
    """
    return {
        "simple": "What is the weather today?",
        "complex": "Find all products with price between $10 and $50 that are in stock",
        "empty": "",
        "special_chars": "Query with special chars: @#$%^&*()!",
        "unicode": "测试查询 🚀 émojis and ñoñó",
        "long": "a" * 1000,
        "sql_injection": "'; DROP TABLE users; --",
        "xss": "<script>alert('xss')</script>",
    }

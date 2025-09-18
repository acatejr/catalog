import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import datetime
from catalog.api import api


class TestCatalogAPI:
    """Test suite for the Catalog API main module."""

    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI api."""
        return TestClient(api)

    def test_api_configuration(self):
        """Test that the FastAPI api is configured correctly."""
        assert api.title == "Catalog API"
        assert api.version == "0.0.1"

    def test_health_endpoint_success(self, client):
        """Test the health endpoint returns correct status and format."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "status" in data
        assert isinstance(data["status"], str)
        assert data["status"].startswith("ok - ")

        # Check timestamp format (YYYY-MM-DD HH:MM:SS)
        timestamp_part = data["status"].replace("ok - ", "")
        try:
            datetime.datetime.strptime(timestamp_part, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            pytest.fail(f"Timestamp format is incorrect: {timestamp_part}")

    def test_query_endpoint_success(self, client):
        """Test the query endpoint with a valid query parameter."""
        test_query = "test query string"
        response = client.get(f"/query?q={test_query}")

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "query" in data
        assert "response" in data
        assert data["query"] == test_query
        assert data["response"] is not None  # Currently returns None

#     @patch("src.catalog.api.main.datetime")
#     def test_health_endpoint_with_mocked_time(self, mock_datetime, client):
#         """Test health endpoint with a specific mocked timestamp."""
#         # Mock the datetime to return a specific time
#         mock_now = datetime.datetime(2023, 12, 25, 10, 30, 45)
#         mock_datetime.datetime.now.return_value = mock_now

#         response = client.get("/health")

#         assert response.status_code == 200
#         data = response.json()
#         expected_status = "ok - 2023-12-25 10:30:45"
#         assert data["status"] == expected_status

#     def test_query_endpoint_with_special_characters(self, client):
#         """Test the query endpoint with special characters in query."""
#         test_query = "test query with spaces & symbols!"
#         response = client.get("/query", params={"q": test_query})

#         assert response.status_code == 200
#         data = response.json()
#         assert data["query"] == test_query
#         assert data["response"] is None

#     def test_query_endpoint_with_empty_query(self, client):
#         """Test the query endpoint with an empty query parameter."""
#         response = client.get("/query?q=")

#         assert response.status_code == 200
#         data = response.json()
#         assert data["query"] == ""
#         assert data["response"] is None

#     def test_query_endpoint_missing_parameter(self, client):
#         """Test the query endpoint without the required q parameter."""
#         response = client.get("/query")

#         # FastAPI should return 422 for missing required parameter
#         assert response.status_code == 422
#         error_data = response.json()
#         assert "detail" in error_data

#         # Check that the error mentions the missing 'q' parameter
#         error_detail = error_data["detail"][0]
#         assert error_detail["loc"] == ["query", "q"]
#         assert error_detail["type"] == "missing"

#     def test_query_endpoint_with_long_query(self, client):
#         """Test the query endpoint with a very long query string."""
#         long_query = "a" * 1000  # 1000 character query
#         response = client.get("/query", params={"q": long_query})

#         assert response.status_code == 200
#         data = response.json()
#         assert data["query"] == long_query
#         assert data["response"] is None

#     def test_query_endpoint_with_unicode_characters(self, client):
#         """Test the query endpoint with unicode characters."""
#         unicode_query = "测试查询 🚀 émojis and ñoñó"
#         response = client.get("/query", params={"q": unicode_query})

#         assert response.status_code == 200
#         data = response.json()
#         assert data["query"] == unicode_query
#         assert data["response"] is None

#     def test_nonexistent_endpoint(self, client):
#         """Test that non-existent endpoints return 404."""
#         response = client.get("/nonexistent")
#         assert response.status_code == 404

#     def test_health_endpoint_method_not_allowed(self, client):
#         """Test that POST method is not allowed on health endpoint."""
#         response = client.post("/health")
#         assert response.status_code == 405

#     def test_query_endpoint_method_not_allowed(self, client):
#         """Test that POST method is not allowed on query endpoint."""
#         response = client.post("/query")
#         assert response.status_code == 405


# class TestAPIEndpointTags:
#     """Test suite for API endpoint tags and documentation."""

#     @pytest.fixture
#     def client(self):
#         """Create a test client for the FastAPI api."""
#         return TestClient(api)

#     def test_openapi_schema_includes_endpoints(self, client):
#         """Test that the OpenAPI schema includes our endpoints with correct tags."""
#         response = client.get("/openapi.json")
#         assert response.status_code == 200

#         schema = response.json()
#         paths = schema["paths"]

#         # Check health endpoint
#         assert "/health" in paths
#         assert "get" in paths["/health"]
#         assert paths["/health"]["get"]["tags"] == ["Health"]

#         # Check query endpoint
#         assert "/query" in paths
#         assert "get" in paths["/query"]
#         assert paths["/query"]["get"]["tags"] == ["Query"]

#         # Check query endpoint has parameter documentation
#         query_params = paths["/query"]["get"]["parameters"]
#         assert len(query_params) == 1
#         assert query_params[0]["name"] == "q"
#         assert query_params[0]["in"] == "query"
#         assert query_params[0]["required"] is True

#     def test_docs_endpoint_accessible(self, client):
#         """Test that the automatic docs endpoint is accessible."""
#         response = client.get("/docs")
#         assert response.status_code == 200
#         assert "text/html" in response.headers["content-type"]

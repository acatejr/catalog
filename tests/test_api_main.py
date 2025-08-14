import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone
import re

from api.main import app


class TestFastAPIApp:
    """Test suite for the FastAPI application configuration."""

    def test_app_title(self):
        """Test that the FastAPI app has the correct title."""
        assert app.title == "Data Catalog API"

    def test_app_instance(self):
        """Test that the app is a proper FastAPI instance."""
        from fastapi import FastAPI
        assert isinstance(app, FastAPI)


class TestHealthEndpoint:
    """Test suite for the /health endpoint."""

    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI app."""
        return TestClient(app)

    def test_health_endpoint_success(self, client):
        """Test that the health endpoint returns 200 status code."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_endpoint_response_structure(self, client):
        """Test that the health endpoint returns the correct response structure."""
        response = client.get("/health")
        json_response = response.json()

        # Check that required fields are present
        assert "status" in json_response
        assert "timestamp" in json_response

        # Check that there are only the expected fields
        assert len(json_response) == 2

    def test_health_endpoint_response_values(self, client):
        """Test that the health endpoint returns correct values."""
        response = client.get("/health")
        json_response = response.json()

        # Check status value
        assert json_response["status"] == "ok"

        # Check timestamp format (ISO format)
        timestamp = json_response["timestamp"]
        assert isinstance(timestamp, str)

        # Validate ISO format using regex
        iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}$'
        assert re.match(iso_pattern, timestamp), f"Timestamp '{timestamp}' is not in expected ISO format"

    def test_health_endpoint_timestamp_accuracy(self, client):
        """Test that the timestamp is recent and accurate."""
        # Record time before request
        before_request = datetime.now()

        response = client.get("/health")
        json_response = response.json()

        # Record time after request
        after_request = datetime.now()

        # Parse the timestamp from response
        response_timestamp = datetime.fromisoformat(json_response["timestamp"])

        # Verify timestamp is between before and after request times
        assert before_request <= response_timestamp <= after_request, \
            f"Timestamp {response_timestamp} is not between {before_request} and {after_request}"

    def test_health_endpoint_content_type(self, client):
        """Test that the health endpoint returns JSON content type."""
        response = client.get("/health")
        assert response.headers["content-type"] == "application/json"

    def test_health_endpoint_multiple_calls(self, client):
        """Test that multiple calls to health endpoint work correctly."""
        # Make multiple requests
        responses = [client.get("/health") for _ in range(3)]

        # All should be successful
        for response in responses:
            assert response.status_code == 200
            json_response = response.json()
            assert json_response["status"] == "ok"
            assert "timestamp" in json_response

        # Timestamps should be different (or at least not decreasing)
        timestamps = [datetime.fromisoformat(resp.json()["timestamp"]) for resp in responses]
        for i in range(1, len(timestamps)):
            assert timestamps[i] >= timestamps[i-1], "Timestamps should not decrease between calls"


class TestHealthEndpointHTTPMethods:
    """Test suite for HTTP methods on the /health endpoint."""

    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI app."""
        return TestClient(app)

    def test_health_endpoint_get_method(self, client):
        """Test that GET method works on /health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_endpoint_post_method_not_allowed(self, client):
        """Test that POST method is not allowed on /health endpoint."""
        response = client.post("/health")
        assert response.status_code == 405  # Method Not Allowed

    def test_health_endpoint_put_method_not_allowed(self, client):
        """Test that PUT method is not allowed on /health endpoint."""
        response = client.put("/health")
        assert response.status_code == 405  # Method Not Allowed

    def test_health_endpoint_delete_method_not_allowed(self, client):
        """Test that DELETE method is not allowed on /health endpoint."""
        response = client.delete("/health")
        assert response.status_code == 405  # Method Not Allowed

    def test_health_endpoint_patch_method_not_allowed(self, client):
        """Test that PATCH method is not allowed on /health endpoint."""
        response = client.patch("/health")
        assert response.status_code == 405  # Method Not Allowed


class TestAPIRouting:
    """Test suite for API routing and non-existent endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI app."""
        return TestClient(app)

    def test_nonexistent_endpoint_returns_404(self, client):
        """Test that non-existent endpoints return 404."""
        response = client.get("/nonexistent")
        assert response.status_code == 404

    def test_root_endpoint_returns_404(self, client):
        """Test that root endpoint returns 404 (no root handler defined)."""
        response = client.get("/")
        assert response.status_code == 404

    def test_health_endpoint_case_sensitive(self, client):
        """Test that the health endpoint is case sensitive."""
        # Correct case should work
        response = client.get("/health")
        assert response.status_code == 200

        # Different cases should return 404
        response = client.get("/Health")
        assert response.status_code == 404

        response = client.get("/HEALTH")
        assert response.status_code == 404

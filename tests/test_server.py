"""
Test module for torero API server functionality
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from torero_api.server import create_app, app

# Create a test client using the existing app
client = TestClient(app)

def test_create_app():
    """Test that the FastAPI app can be created."""

    test_app = create_app()
    assert test_app.title == "torero API"
    assert test_app.version == "0.1.0"
    assert "RESTful API for interacting with torero services" in test_app.description

def test_root_endpoint():
    """Test the root API endpoint."""

    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "torero API"
    assert data["version"] == "0.1.0"
    assert "endpoints" in data
    assert "services" in data["endpoints"]

def test_openapi_schema():
    """Test that OpenAPI schema is available."""

    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "torero API"
    assert schema["info"]["version"] == "0.1.0"

def test_docs_endpoint():
    """Test that docs endpoint is available."""

    response = client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

@patch("torero_api.core.torero_executor.check_torero_available")
def test_health_endpoint_healthy(mock_check_torero):
    """Test health endpoint when torero is available."""

    mock_check_torero.return_value = (True, "torero is available")
    
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["torero_available"] is True

@patch("torero_api.core.torero_executor.check_torero_available")
def test_health_endpoint_unhealthy(mock_check_torero):
    """Test health endpoint when torero is not available."""

    mock_check_torero.return_value = (False, "torero not found")
    
    response = client.get("/health")
    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "unhealthy"
    assert data["torero_available"] is False
    assert data["reason"] == "torero not found"

@patch("torero_api.core.torero_executor.check_torero_available")
def test_health_endpoint_exception(mock_check_torero):
    """Test health endpoint when an exception occurs."""

    mock_check_torero.side_effect = Exception("Something went wrong")
    
    response = client.get("/health")
    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "unhealthy"
    assert data["torero_available"] is False
    assert "Something went wrong" in data["reason"]
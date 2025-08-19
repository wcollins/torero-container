"""
Test module for torero API secrets endpoints
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime

from torero_api.server import app
from torero_api.models.secret import Secret

# Create a test client using FastAPI's TestClient
client = TestClient(app)

# Define test secrets that will be used in all tests
TEST_SECRETS = [
    Secret(
        name="test-secret-1",
        description="Test secret 1",
        type="password",
        created_at=datetime.fromisoformat("2023-01-01T00:00:00"),
        metadata={"owner": "admin", "provider": "vault"}
    ),
    Secret(
        name="test-secret-2",
        description="Test secret 2",
        type="api-key",
        created_at=datetime.fromisoformat("2023-01-02T00:00:00"),
        metadata={"owner": "admin", "provider": "vault"}
    ),
    Secret(
        name="test-secret-3",
        description="Test secret 3",
        type="token",
        created_at=datetime.fromisoformat("2023-01-03T00:00:00"),
        metadata={"owner": "admin", "provider": "vault"}
    )
]

# Direct patching for secret endpoints
@patch("torero_api.api.v1.endpoints.secrets.get_secrets")
def test_list_secrets(mock_get_secrets):
    """Test listing all secrets with direct endpoint mocking."""

    # Set up the mock to return our test secrets
    mock_get_secrets.return_value = TEST_SECRETS
    
    # Make the request
    response = client.get("/v1/secrets/")
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["name"] == "test-secret-1"
    assert data[1]["name"] == "test-secret-2"
    assert data[2]["name"] == "test-secret-3"

@patch("torero_api.api.v1.endpoints.secrets.get_secrets")
def test_list_secrets_filter_by_type(mock_get_secrets):
    """Test filtering secrets by type with direct endpoint mocking."""

    # Set up the mock to return our test secrets
    mock_get_secrets.return_value = TEST_SECRETS
    
    # Make the request
    response = client.get("/v1/secrets/?type=api-key")
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "test-secret-2"
    assert data[0]["type"] == "api-key"

@patch("torero_api.api.v1.endpoints.secrets.get_secrets")
def test_list_secret_types(mock_get_secrets):
    """Test listing secret types with direct endpoint mocking."""

    # Set up the mock to return our test secrets
    mock_get_secrets.return_value = TEST_SECRETS
    
    # Make the request
    response = client.get("/v1/secrets/types")
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert "password" in data
    assert "api-key" in data
    assert "token" in data

@patch("torero_api.api.v1.endpoints.secrets.get_secret_by_name")
def test_get_secret_by_name_found(mock_get_secret_by_name):
    """Test getting a specific secret by name with direct endpoint mocking."""

    # Set up the mock to return a specific secret
    mock_get_secret_by_name.return_value = TEST_SECRETS[1]  # test-secret-2
    
    # Make the request
    response = client.get("/v1/secrets/test-secret-2")
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "test-secret-2"
    assert data["type"] == "api-key"
    assert data["metadata"]["provider"] == "vault"

@patch("torero_api.api.v1.endpoints.secrets.get_secret_by_name")
def test_get_secret_by_name_not_found(mock_get_secret_by_name):
    """Test getting a non-existent secret with direct endpoint mocking."""

    # Set up the mock to return None (secret not found)
    mock_get_secret_by_name.return_value = None
    
    # Make the request
    response = client.get("/v1/secrets/non-existent-secret")
    
    # Assertions
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"]

@patch("torero_api.api.v1.endpoints.secrets.get_secrets")
def test_exception_handling(mock_get_secrets):
    """Test error handling with direct endpoint mocking."""

    # Set up the mock to raise an exception
    mock_get_secrets.side_effect = RuntimeError("Test error")
    
    # Make the request
    response = client.get("/v1/secrets/")
    
    # Assertions
    assert response.status_code == 500
    data = response.json()
    assert data["error_type"] == "http_error"
    assert "Test error" in data["detail"]
"""
Test module for torero API repositories endpoints
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from torero_api.server import app
from torero_api.models.repository import Repository

# Create a test client using FastAPI's TestClient
client = TestClient(app)

# Define test repositories that will be used in all tests
TEST_REPOSITORIES = [
    Repository(
        name="test-repository-1",
        description="Test repository 1",
        type="file",
        location="/etc/torero/services",
        metadata={"created": "2023-01-01T00:00:00Z", "owner": "torero"}
    ),
    Repository(
        name="test-repository-2",
        description="Test repository 2",
        type="git",
        location="https://github.com/torerodev/torero-services.git",
        metadata={"created": "2023-01-02T00:00:00Z", "owner": "torero"}
    ),
    Repository(
        name="test-repository-3",
        description="Test repository 3",
        type="s3",
        location="s3://torero-services",
        metadata={"created": "2023-01-03T00:00:00Z", "owner": "torero"}
    )
]

# Direct patching for repository endpoints
@patch("torero_api.api.v1.endpoints.repositories.get_repositories")
def test_list_repositories(mock_get_repositories):
    """Test listing all repositories with direct endpoint mocking."""

    # Set up the mock to return our test repositories
    mock_get_repositories.return_value = TEST_REPOSITORIES
    
    # Make the request
    response = client.get("/v1/repositories/")
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["name"] == "test-repository-1"
    assert data[1]["name"] == "test-repository-2"
    assert data[2]["name"] == "test-repository-3"

@patch("torero_api.api.v1.endpoints.repositories.get_repositories")
def test_list_repositories_filter_by_type(mock_get_repositories):
    """Test filtering repositories by type with direct endpoint mocking."""

    # Set up the mock to return our test repositories
    mock_get_repositories.return_value = TEST_REPOSITORIES
    
    # Make the request
    response = client.get("/v1/repositories/?type=git")
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "test-repository-2"
    assert data[0]["type"] == "git"

@patch("torero_api.api.v1.endpoints.repositories.get_repositories")
def test_list_repository_types(mock_get_repositories):
    """Test listing repository types with direct endpoint mocking."""

    # Set up the mock to return our test repositories
    mock_get_repositories.return_value = TEST_REPOSITORIES
    
    # Make the request
    response = client.get("/v1/repositories/types")
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert "file" in data
    assert "git" in data
    assert "s3" in data

@patch("torero_api.api.v1.endpoints.repositories.get_repository_by_name")
def test_get_repository_by_name_found(mock_get_repository_by_name):
    """Test getting a specific repository by name with direct endpoint mocking."""

    # Set up the mock to return a specific repository
    mock_get_repository_by_name.return_value = TEST_REPOSITORIES[1]  # test-repository-2
    
    # Make the request
    response = client.get("/v1/repositories/test-repository-2")
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "test-repository-2"
    assert data["type"] == "git"
    assert data["location"] == "https://github.com/torerodev/torero-services.git"

@patch("torero_api.api.v1.endpoints.repositories.get_repository_by_name")
def test_get_repository_by_name_not_found(mock_get_repository_by_name):
    """Test getting a non-existent repository with direct endpoint mocking."""

    # Set up the mock to return None (repository not found)
    mock_get_repository_by_name.return_value = None
    
    # Make the request
    response = client.get("/v1/repositories/non-existent-repository")
    
    # Assertions
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"]

@patch("torero_api.api.v1.endpoints.repositories.get_repositories")
def test_exception_handling(mock_get_repositories):
    """Test error handling with direct endpoint mocking."""

    # Set up the mock to raise an exception
    mock_get_repositories.side_effect = RuntimeError("Test error")
    
    # Make the request
    response = client.get("/v1/repositories/")
    
    # Assertions
    assert response.status_code == 500
    data = response.json()
    assert data["error_type"] == "http_error"
    assert "Test error" in data["detail"]
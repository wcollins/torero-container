"""
Test module for torero API decorators endpoints
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from torero_api.server import app
from torero_api.models.decorator import Decorator

# Create a test client using FastAPI's TestClient
client = TestClient(app)

# Define test decorators that will be used in all tests
TEST_DECORATORS = [
    Decorator(
        name="test-decorator-1",
        description="Test decorator 1",
        type="authentication",
        parameters={
            "username": {"type": "string", "required": True},
            "password": {"type": "string", "required": True, "secret": True}
        },
        registries={"file": {"path": "/etc/torero/decorators/test-decorator-1"}}
    ),
    Decorator(
        name="test-decorator-2",
        description="Test decorator 2",
        type="logging",
        parameters={
            "level": {"type": "string", "required": True, "default": "info"},
            "file": {"type": "string", "required": False}
        },
        registries={"file": {"path": "/etc/torero/decorators/test-decorator-2"}}
    ),
    Decorator(
        name="test-decorator-3",
        description="Test decorator 3",
        type="validation",
        parameters={
            "schema": {"type": "object", "required": True}
        },
        registries={"file": {"path": "/etc/torero/decorators/test-decorator-3"}}
    )
]

# Direct patching for decorator endpoints
@patch("torero_api.api.v1.endpoints.decorators.get_decorators")
def test_list_decorators(mock_get_decorators):
    """Test listing all decorators with direct endpoint mocking."""

    # Set up the mock to return our test decorators
    mock_get_decorators.return_value = TEST_DECORATORS
    
    # Make the request
    response = client.get("/v1/decorators/")
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["name"] == "test-decorator-1"
    assert data[1]["name"] == "test-decorator-2"
    assert data[2]["name"] == "test-decorator-3"

@patch("torero_api.api.v1.endpoints.decorators.get_decorators")
def test_list_decorators_filter_by_type(mock_get_decorators):
    """Test filtering decorators by type with direct endpoint mocking."""

    # Set up the mock to return our test decorators
    mock_get_decorators.return_value = TEST_DECORATORS
    
    # Make the request
    response = client.get("/v1/decorators/?type=authentication")
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "test-decorator-1"
    assert data[0]["type"] == "authentication"

@patch("torero_api.api.v1.endpoints.decorators.get_decorators")
def test_list_decorator_types(mock_get_decorators):
    """Test listing decorator types with direct endpoint mocking."""

    # Set up the mock to return our test decorators
    mock_get_decorators.return_value = TEST_DECORATORS
    
    # Make the request
    response = client.get("/v1/decorators/types")
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert "authentication" in data
    assert "logging" in data
    assert "validation" in data

@patch("torero_api.api.v1.endpoints.decorators.get_decorator_by_name")
def test_get_decorator_by_name_found(mock_get_decorator_by_name):
    """Test getting a specific decorator by name with direct endpoint mocking."""

    # Set up the mock to return a specific decorator
    mock_get_decorator_by_name.return_value = TEST_DECORATORS[1]  # test-decorator-2
    
    # Make the request
    response = client.get("/v1/decorators/test-decorator-2")
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "test-decorator-2"
    assert data["type"] == "logging"
    assert "level" in data["parameters"]

@patch("torero_api.api.v1.endpoints.decorators.get_decorator_by_name")
def test_get_decorator_by_name_not_found(mock_get_decorator_by_name):
    """Test getting a non-existent decorator with direct endpoint mocking."""

    # Set up the mock to return None (decorator not found)
    mock_get_decorator_by_name.return_value = None
    
    # Make the request
    response = client.get("/v1/decorators/non-existent-decorator")
    
    # Assertions
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"]

@patch("torero_api.api.v1.endpoints.decorators.get_decorators")
def test_exception_handling(mock_get_decorators):
    """Test error handling with direct endpoint mocking."""

    # Set up the mock to raise an exception
    mock_get_decorators.side_effect = RuntimeError("Test error")
    
    # Make the request
    response = client.get("/v1/decorators/")
    
    # Assertions
    assert response.status_code == 500
    data = response.json()
    assert data["error_type"] == "http_error"
    assert "Test error" in data["detail"]
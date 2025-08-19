"""
Test module for torero API services with direct mocking approach
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from torero_api.server import app
from torero_api.models.service import Service

# Create a test client using FastAPI's TestClient
client = TestClient(app)

# Define test services that will be used in all tests
TEST_SERVICES = [
    Service(
        name="test-service-1",
        description="Test service 1",
        type="ansible-playbook",
        tags=["test", "ansible", "network"],
        registries={"file": {"path": "/etc/torero/services/test-service-1"}}
    ),
    Service(
        name="test-service-2",
        description="Test service 2",
        type="opentofu-plan",
        tags=["test", "opentofu", "cloud"],
        registries={"file": {"path": "/etc/torero/services/test-service-2"}}
    ),
    Service(
        name="test-service-3",
        description="Test service 3",
        type="python-script",
        tags=["test", "python", "automation"],
        registries={"file": {"path": "/etc/torero/services/test-service-3"}}
    )
]

# Direct patching for service endpoints
@patch("torero_api.api.v1.endpoints.services.get_services")
def test_list_services(mock_get_services):
    """Test listing all services with direct endpoint mocking."""

    # Set up the mock to return our test services
    mock_get_services.return_value = TEST_SERVICES
    
    # Make the request
    response = client.get("/v1/services/")
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["name"] == "test-service-1"
    assert data[1]["name"] == "test-service-2"
    assert data[2]["name"] == "test-service-3"

@patch("torero_api.api.v1.endpoints.services.get_services")
def test_list_services_filter_by_type(mock_get_services):
    """Test filtering services by type with direct endpoint mocking."""

    # Set up the mock to return our test services
    mock_get_services.return_value = TEST_SERVICES
    
    # Make the request
    response = client.get("/v1/services/?type=ansible-playbook")
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "test-service-1"
    assert data[0]["type"] == "ansible-playbook"

@patch("torero_api.api.v1.endpoints.services.get_services")
def test_list_services_filter_by_tag(mock_get_services):
    """Test filtering services by tag with direct endpoint mocking."""

    # Set up the mock to return our test services
    mock_get_services.return_value = TEST_SERVICES
    
    # Make the request
    response = client.get("/v1/services/?tag=python")
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "test-service-3"
    assert "python" in data[0]["tags"]

@patch("torero_api.api.v1.endpoints.services.get_services")
def test_list_service_types(mock_get_services):
    """Test listing service types with direct endpoint mocking."""

    # Set up the mock to return our test services
    mock_get_services.return_value = TEST_SERVICES
    
    # Make the request
    response = client.get("/v1/services/types")
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert "ansible-playbook" in data
    assert "opentofu-plan" in data
    assert "python-script" in data

@patch("torero_api.api.v1.endpoints.services.get_services")
def test_list_service_tags(mock_get_services):
    """Test listing service tags with direct endpoint mocking."""

    # Set up the mock to return our test services
    mock_get_services.return_value = TEST_SERVICES
    
    # Make the request
    response = client.get("/v1/services/tags")
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 7
    assert "test" in data
    assert "ansible" in data
    assert "network" in data
    assert "opentofu" in data
    assert "cloud" in data
    assert "python" in data
    assert "automation" in data

@patch("torero_api.api.v1.endpoints.services.get_service_by_name")
def test_get_service_by_name_found(mock_get_service_by_name):
    """Test getting a specific service by name with direct endpoint mocking."""

    # Set up the mock to return a specific service
    mock_get_service_by_name.return_value = TEST_SERVICES[1]  # test-service-2
    
    # Make the request
    response = client.get("/v1/services/test-service-2")
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "test-service-2"
    assert data["type"] == "opentofu-plan"
    assert "cloud" in data["tags"]

@patch("torero_api.api.v1.endpoints.services.get_service_by_name")
def test_get_service_by_name_not_found(mock_get_service_by_name):
    """Test getting a non-existent service with direct endpoint mocking."""

    # Set up the mock to return None (service not found)
    mock_get_service_by_name.return_value = None
    
    # Make the request
    response = client.get("/v1/services/non-existent-service")
    
    # Assertions
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"]

@patch("torero_api.api.v1.endpoints.services.get_services")
def test_exception_handling(mock_get_services):
    """Test error handling with direct endpoint mocking."""

    # Set up the mock to raise an exception
    mock_get_services.side_effect = RuntimeError("Test error")
    
    # Make the request
    response = client.get("/v1/services/")
    
    # Assertions
    assert response.status_code == 500
    data = response.json()
    assert data["error_type"] == "http_error"
    assert "Test error" in data["detail"]

@patch("torero_api.core.torero_executor.check_torero_available")
def test_health_endpoint_success(mock_check_torero_available):
    """Test the health endpoint when torero is available."""

    # Set up the mock to return that torero is available
    mock_check_torero_available.return_value = (True, "torero is available")
    
    # Make the request
    response = client.get("/health")
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["torero_available"] is True

@patch("torero_api.core.torero_executor.check_torero_available")
def test_health_endpoint_failure(mock_check_torero_available):
    """Test the health endpoint when torero is not available."""

    # Set up the mock to return that torero is not available
    mock_check_torero_available.return_value = (False, "torero is not available")
    
    # Make the request
    response = client.get("/health")
    
    # Assertions
    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "unhealthy"
    assert data["torero_available"] is False
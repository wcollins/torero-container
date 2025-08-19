"""
Test module for torero API service description endpoint
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from torero_api.server import app
from torero_api.models.service import Service

# Create a test client using FastAPI's TestClient
client = TestClient(app)

# Define a sample service for tests
SAMPLE_SERVICE = Service(
    name="test-service",
    description="Test service",
    type="ansible-playbook",
    tags=["test", "ansible", "network"],
    registries={"file": {"path": "/etc/torero/services/test-service"}}
)

# Define a sample service description for tests - as a list to match the torero CLI output
SAMPLE_SERVICE_DESCRIPTION = [
    {
        "metadata": {
            "name": "test-service",
            "description": "Test service",
            "tags": ["test", "ansible", "network"],
            "repository": {"id": "", "type": "v1.Repository", "name": "test-repo"},
            "working_dir": "test-service",
            "credential": None,
            "id": "e9afa999-4994-40cb-83be-a1dbeffa6736",
            "created": "2025-03-11T15:30:21.264214Z",
            "decorator": None,
            "registries": []
        },
        "entity": {
            "playbook": ["test-service.yml"],
            "playbook_options": {
                "check": False,
                "diff": False,
                "extra_vars": [],
                "extra_vars_file": [],
                "forks": 0,
                "inventory": [],
                "limit": [],
                "skip_tags": "",
                "tags": "",
                "verbose_level": 0,
                "config_file": "",
                "json_encoded_arg_file": []
            }
        },
        "type": "ansible-playbook"
    }
]

@patch("torero_api.api.v1.endpoints.services.get_service_by_name")
@patch("torero_api.api.v1.endpoints.services.describe_service")
def test_describe_service_success(mock_describe_service, mock_get_service_by_name):
    """Test describing a service with success."""
    
    # Set up the mocks
    mock_get_service_by_name.return_value = SAMPLE_SERVICE
    mock_describe_service.return_value = SAMPLE_SERVICE_DESCRIPTION
    
    # Make the request
    response = client.get("/v1/services/test-service/describe")
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["metadata"]["name"] == "test-service"
    assert data[0]["type"] == "ansible-playbook"
    assert "entity" in data[0]
    mock_get_service_by_name.assert_called_once_with("test-service")
    mock_describe_service.assert_called_once_with("test-service")

@patch("torero_api.api.v1.endpoints.services.get_service_by_name")
def test_describe_service_not_found(mock_get_service_by_name):
    """Test describing a non-existent service."""
    
    # Set up the mock
    mock_get_service_by_name.return_value = None
    
    # Make the request
    response = client.get("/v1/services/non-existent-service/describe")
    
    # Assertions
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"]
    mock_get_service_by_name.assert_called_once_with("non-existent-service")

@patch("torero_api.api.v1.endpoints.services.get_service_by_name")
@patch("torero_api.api.v1.endpoints.services.describe_service")
def test_describe_service_error(mock_describe_service, mock_get_service_by_name):
    """Test error handling in describe service endpoint."""
    
    # Set up the mocks
    mock_get_service_by_name.return_value = SAMPLE_SERVICE
    mock_describe_service.side_effect = RuntimeError("Test error")
    
    # Make the request
    response = client.get("/v1/services/test-service/describe")
    
    # Assertions
    assert response.status_code == 500
    data = response.json()
    assert "error_type" in data
    assert "Test error" in data["detail"]
    mock_get_service_by_name.assert_called_once_with("test-service")
    mock_describe_service.assert_called_once_with("test-service")

@patch("torero_api.core.torero_executor.subprocess.run")
def test_describe_service_executor(mock_run):
    """Test the describe_service function in the torero_executor module."""
    
    from torero_api.core.torero_executor import describe_service
    
    # Set up the mock
    process_mock = MagicMock()
    process_mock.returncode = 0
    process_mock.stdout = '[{"metadata": {"name": "test-service", "description": "Test service"}, "entity": {}, "type": "ansible-playbook"}]'
    mock_run.return_value = process_mock
    
    # Call the function
    result = describe_service("test-service")
    
    # Assertions
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["metadata"]["name"] == "test-service"
    assert result[0]["type"] == "ansible-playbook"
    mock_run.assert_called_once_with(
        ["torero", "describe", "service", "test-service", "--raw"],
        capture_output=True,
        text=True,
        check=False,
        timeout=30
    )

@patch("torero_api.core.torero_executor.subprocess.run")
def test_describe_service_executor_error(mock_run):
    """Test error handling in the describe_service function."""
    
    from torero_api.core.torero_executor import describe_service
    
    # Set up the mock
    process_mock = MagicMock()
    process_mock.returncode = 1
    process_mock.stderr = "Error: service not found"
    mock_run.return_value = process_mock
    
    # Call the function and expect an exception
    with pytest.raises(RuntimeError) as excinfo:
        describe_service("non-existent-service")
    
    # Assertions
    assert "torero error" in str(excinfo.value)
    mock_run.assert_called_once()
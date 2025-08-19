"""
Test module for torero API core functionality

This module contains tests for the torero_api core modules, particularly
the torero_executor.py module which interfaces with the torero CLI.
"""

import pytest
from unittest.mock import patch, MagicMock
import subprocess
import json
from datetime import datetime

from torero_api.core.torero_executor import (
    check_torero_available,
    check_torero_version,
    get_services,
    get_service_by_name,
    describe_service,
    get_decorators,
    get_decorator_by_name,
    get_repositories,
    get_repository_by_name,
    get_secrets,
    get_secret_by_name
)
from torero_api.models.service import Service
from torero_api.models.decorator import Decorator
from torero_api.models.repository import Repository
from torero_api.models.secret import Secret

# Sample test data
SAMPLE_SERVICES = [
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
    )
]

@patch("shutil.which")
@patch("subprocess.run")
def test_check_torero_available_success(mock_run, mock_which):
    """Test check_torero_available when torero is available."""

    # Set up the mocks
    mock_which.return_value = "/usr/bin/torero"  # torero found in PATH
    process_mock = MagicMock()
    process_mock.returncode = 0
    process_mock.stdout = "torero version 1.3.0"
    mock_run.return_value = process_mock
    
    # Call the function
    available, message = check_torero_available()
    
    # Assertions
    assert available is True
    assert message == "torero is available"
    mock_which.assert_called_once_with("torero")
    mock_run.assert_called_once_with(
        ["torero", "version"],
        capture_output=True,
        text=True,
        check=False,
        timeout=5
    )

@patch("shutil.which")
@patch("subprocess.run")
def test_check_torero_available_failure(mock_run, mock_which):
    """Test check_torero_available when torero is not available."""

    # Set up the mocks
    mock_which.return_value = "/usr/bin/torero"  # torero found in PATH
    process_mock = MagicMock()
    process_mock.returncode = 1
    process_mock.stderr = "command not found: torero"
    mock_run.return_value = process_mock
    
    # Call the function
    available, message = check_torero_available()
    
    # Assertions
    assert available is False
    assert "torero command failed" in message
    mock_which.assert_called_once_with("torero")
    mock_run.assert_called_once()

@patch("shutil.which")
@patch("subprocess.run")
def test_check_torero_available_timeout(mock_run, mock_which):
    """Test check_torero_available when torero command times out."""

    # Set up the mocks
    mock_which.return_value = "/usr/bin/torero"  # torero found in PATH
    mock_run.side_effect = subprocess.TimeoutExpired(cmd="torero version", timeout=5)
    
    # Call the function
    available, message = check_torero_available()
    
    # Assertions
    assert available is False
    assert message == "torero command timed out"
    mock_which.assert_called_once_with("torero")
    mock_run.assert_called_once()

@patch("shutil.which")
def test_check_torero_available_not_in_path(mock_which):
    """Test check_torero_available when torero is not in PATH."""

    # Set up the mock
    mock_which.return_value = None  # torero not found in PATH
    
    # Call the function
    available, message = check_torero_available()
    
    # Assertions
    assert available is False
    assert message == "torero executable not found in PATH"
    mock_which.assert_called_once_with("torero")

@patch("subprocess.run")
def test_check_torero_version(mock_run):
    """Test check_torero_version function."""

    # Set up the mock
    process_mock = MagicMock()
    process_mock.returncode = 0
    process_mock.stdout = "torero version 1.3.0\nSome other info\n"
    mock_run.return_value = process_mock
    
    # Call the function
    version = check_torero_version()
    
    # Assertions
    assert version == "1.3.0"
    mock_run.assert_called_once()

@patch("subprocess.run")
def test_check_torero_version_error(mock_run):
    """Test check_torero_version when an error occurs."""

    # Set up the mock
    process_mock = MagicMock()
    process_mock.returncode = 1
    process_mock.stderr = "Error: torero command not found"
    mock_run.return_value = process_mock
    
    # Call the function
    version = check_torero_version()
    
    # Assertions
    assert version == "unknown"
    mock_run.assert_called_once()

@patch("subprocess.run")
def test_get_services(mock_run):
    """Test get_services function."""

    # Set up the mock
    process_mock = MagicMock()
    process_mock.returncode = 0
    process_mock.stdout = json.dumps([
        {
            "name": "test-service-1",
            "description": "Test service 1",
            "type": "ansible-playbook",
            "tags": ["test", "ansible", "network"],
            "registries": {"file": {"path": "/etc/torero/services/test-service-1"}}
        },
        {
            "name": "test-service-2",
            "description": "Test service 2",
            "type": "opentofu-plan",
            "tags": ["test", "opentofu", "cloud"],
            "registries": {"file": {"path": "/etc/torero/services/test-service-2"}}
        }
    ])
    mock_run.return_value = process_mock
    
    # Call the function
    services = get_services()
    
    # Assertions
    assert len(services) == 2
    assert services[0].name == "test-service-1"
    assert services[0].type == "ansible-playbook"
    assert "ansible" in services[0].tags
    assert services[1].name == "test-service-2"
    assert services[1].type == "opentofu-plan"
    assert "cloud" in services[1].tags
    mock_run.assert_called_once_with(
        ["torero", "get", "services", "--raw"],
        capture_output=True,
        text=True,
        check=False,
        timeout=30
    )

@patch("subprocess.run")
def test_get_services_error(mock_run):
    """Test get_services function when an error occurs."""

    # Set up the mock
    process_mock = MagicMock()
    process_mock.returncode = 1
    process_mock.stderr = "Error: torero command failed"
    mock_run.return_value = process_mock
    
    # Call the function and expect an exception
    with pytest.raises(RuntimeError) as excinfo:
        get_services()
    
    # Assertions
    assert "torero error" in str(excinfo.value)
    mock_run.assert_called_once()

@patch("subprocess.run")
def test_get_services_invalid_json(mock_run):
    """Test get_services function with invalid JSON response."""

    # Set up the mock
    process_mock = MagicMock()
    process_mock.returncode = 0
    process_mock.stdout = "Not a valid JSON"
    mock_run.return_value = process_mock
    
    # Call the function and expect an exception
    with pytest.raises(RuntimeError) as excinfo:
        get_services()
    
    # Assertions
    assert "Invalid JSON" in str(excinfo.value)
    mock_run.assert_called_once()

@patch("torero_api.core.torero_executor.get_services")
def test_get_service_by_name_found(mock_get_services):
    """Test get_service_by_name when service is found."""

    # Set up the mock
    mock_get_services.return_value = SAMPLE_SERVICES
    
    # Call the function
    service = get_service_by_name("test-service-1")
    
    # Assertions
    assert service is not None
    assert service.name == "test-service-1"
    assert service.type == "ansible-playbook"
    mock_get_services.assert_called_once()

@patch("torero_api.core.torero_executor.get_services")
def test_get_service_by_name_not_found(mock_get_services):
    """Test get_service_by_name when service is not found."""

    # Set up the mock
    mock_get_services.return_value = SAMPLE_SERVICES
    
    # Call the function
    service = get_service_by_name("non-existent-service")
    
    # Assertions
    assert service is None
    mock_get_services.assert_called_once()

@patch("subprocess.run")
def test_describe_service(mock_run):
    """Test describe_service function."""

    # Set up the mock
    process_mock = MagicMock()
    process_mock.returncode = 0
    process_mock.stdout = json.dumps([{
        "metadata": {
            "name": "test-service-1",
            "description": "Test service 1",
            "tags": ["test", "ansible", "network"],
            "repository": {"id": "", "type": "v1.Repository", "name": "test-repo"},
        },
        "entity": {
            "playbook": ["test-service-1.yml"],
            "playbook_options": {
                "check": False,
                "diff": False,
                "extra_vars": [],
                "inventory": []
            }
        },
        "type": "ansible-playbook"
    }])
    mock_run.return_value = process_mock
    
    # Call the function
    description = describe_service("test-service-1")
    
    # Assertions
    assert isinstance(description, list)
    assert description[0]["metadata"]["name"] == "test-service-1"
    assert description[0]["type"] == "ansible-playbook"
    assert "entity" in description[0]
    mock_run.assert_called_once_with(
        ["torero", "describe", "service", "test-service-1", "--raw"],
        capture_output=True,
        text=True,
        check=False,
        timeout=30
    )

@patch("subprocess.run")
def test_get_decorators(mock_run):
    """Test get_decorators function."""

    # Set up the mock
    process_mock = MagicMock()
    process_mock.returncode = 0
    process_mock.stdout = json.dumps([
        {
            "name": "test-decorator-1",
            "description": "Test decorator 1",
            "type": "authentication",
            "parameters": {
                "username": {"type": "string", "required": True},
                "password": {"type": "string", "required": True, "secret": True}
            },
            "registries": {"file": {"path": "/etc/torero/decorators/test-decorator-1"}}
        },
        {
            "name": "test-decorator-2",
            "description": "Test decorator 2",
            "type": "logging",
            "parameters": {
                "level": {"type": "string", "required": True, "default": "info"},
                "file": {"type": "string", "required": False}
            },
            "registries": {"file": {"path": "/etc/torero/decorators/test-decorator-2"}}
        }
    ])
    mock_run.return_value = process_mock
    
    # Call the function
    decorators = get_decorators()
    
    # Assertions
    assert len(decorators) == 2
    assert decorators[0].name == "test-decorator-1"
    assert decorators[0].type == "authentication"
    assert "username" in decorators[0].parameters
    assert decorators[1].name == "test-decorator-2"
    assert decorators[1].type == "logging"
    assert "level" in decorators[1].parameters
    mock_run.assert_called_once_with(
        ["torero", "get", "decorators", "--raw"],
        capture_output=True,
        text=True,
        check=False,
        timeout=30
    )

@patch("torero_api.core.torero_executor.get_decorators")
def test_get_decorator_by_name_found(mock_get_decorators):
    """Test get_decorator_by_name when decorator is found."""

    # Define test decorators
    test_decorators = [
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
        )
    ]

    # Set up the mock
    mock_get_decorators.return_value = test_decorators
    
    # Call the function
    decorator = get_decorator_by_name("test-decorator-1")
    
    # Assertions
    assert decorator is not None
    assert decorator.name == "test-decorator-1"
    assert decorator.type == "authentication"
    mock_get_decorators.assert_called_once()

@patch("torero_api.core.torero_executor.get_decorators")
def test_get_decorator_by_name_not_found(mock_get_decorators):
    """Test get_decorator_by_name when decorator is not found."""

    # Define test decorators
    test_decorators = [
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
        )
    ]

    # Set up the mock
    mock_get_decorators.return_value = test_decorators
    
    # Call the function
    decorator = get_decorator_by_name("non-existent-decorator")
    
    # Assertions
    assert decorator is None
    mock_get_decorators.assert_called_once()

@patch("subprocess.run")
def test_get_repositories(mock_run):
    """Test get_repositories function."""

    # Set up the mock
    process_mock = MagicMock()
    process_mock.returncode = 0
    process_mock.stdout = json.dumps([
        {
            "name": "test-repository-1",
            "description": "Test repository 1",
            "type": "file",
            "location": "/etc/torero/services",
            "metadata": {"created": "2023-01-01T00:00:00Z", "owner": "torero"}
        },
        {
            "name": "test-repository-2",
            "description": "Test repository 2",
            "type": "git",
            "location": "https://github.com/torerodev/torero-services.git",
            "metadata": {"created": "2023-01-02T00:00:00Z", "owner": "torero"}
        }
    ])
    mock_run.return_value = process_mock
    
    # Call the function
    repositories = get_repositories()
    
    # Assertions
    assert len(repositories) == 2
    assert repositories[0].name == "test-repository-1"
    assert repositories[0].type == "file"
    assert repositories[0].location == "/etc/torero/services"
    assert repositories[1].name == "test-repository-2"
    assert repositories[1].type == "git"
    assert repositories[1].location == "https://github.com/torerodev/torero-services.git"
    mock_run.assert_called_once_with(
        ["torero", "get", "repositories", "--raw"],
        capture_output=True,
        text=True,
        check=False,
        timeout=30
    )

@patch("torero_api.core.torero_executor.get_repositories")
def test_get_repository_by_name_found(mock_get_repositories):
    """Test get_repository_by_name when repository is found."""

    # Define test repositories
    test_repositories = [
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
        )
    ]

    # Set up the mock
    mock_get_repositories.return_value = test_repositories
    
    # Call the function
    repository = get_repository_by_name("test-repository-1")
    
    # Assertions
    assert repository is not None
    assert repository.name == "test-repository-1"
    assert repository.type == "file"
    mock_get_repositories.assert_called_once()

@patch("torero_api.core.torero_executor.get_repositories")
def test_get_repository_by_name_not_found(mock_get_repositories):
    """Test get_repository_by_name when repository is not found."""

    # Define test repositories
    test_repositories = [
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
        )
    ]

    # Set up the mock
    mock_get_repositories.return_value = test_repositories
    
    # Call the function
    repository = get_repository_by_name("non-existent-repository")
    
    # Assertions
    assert repository is None
    mock_get_repositories.assert_called_once()

@patch("subprocess.run")
def test_get_secrets(mock_run):
    """Test get_secrets function."""

    # Set up the mock
    process_mock = MagicMock()
    process_mock.returncode = 0
    process_mock.stdout = json.dumps([
        {
            "name": "test-secret-1",
            "description": "Test secret 1",
            "type": "password",
            "created_at": "2023-01-01T00:00:00Z",
            "metadata": {"owner": "admin", "provider": "vault"}
        },
        {
            "name": "test-secret-2",
            "description": "Test secret 2",
            "type": "api-key",
            "created_at": "2023-01-02T00:00:00Z",
            "metadata": {"owner": "admin", "provider": "vault"}
        }
    ])
    mock_run.return_value = process_mock
    
    # Call the function
    secrets = get_secrets()
    
    # Assertions
    assert len(secrets) == 2
    assert secrets[0].name == "test-secret-1"
    assert secrets[0].type == "password"
    assert secrets[0].created_at.isoformat() == "2023-01-01T00:00:00+00:00"
    assert secrets[1].name == "test-secret-2"
    assert secrets[1].type == "api-key"
    assert secrets[1].created_at.isoformat() == "2023-01-02T00:00:00+00:00"
    mock_run.assert_called_once_with(
        ["torero", "get", "secrets", "--raw"],
        capture_output=True,
        text=True,
        check=False,
        timeout=30
    )

@patch("torero_api.core.torero_executor.get_secrets")
def test_get_secret_by_name_found(mock_get_secrets):
    """Test get_secret_by_name when secret is found."""

    # Define test secrets
    test_secrets = [
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
        )
    ]

    # Set up the mock
    mock_get_secrets.return_value = test_secrets
    
    # Call the function
    secret = get_secret_by_name("test-secret-1")
    
    # Assertions
    assert secret is not None
    assert secret.name == "test-secret-1"
    assert secret.type == "password"
    mock_get_secrets.assert_called_once()

@patch("torero_api.core.torero_executor.get_secrets")
def test_get_secret_by_name_not_found(mock_get_secrets):
    """Test get_secret_by_name when secret is not found."""

    # Define test secrets
    test_secrets = [
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
        )
    ]

    # Set up the mock
    mock_get_secrets.return_value = test_secrets
    
    # Call the function
    secret = get_secret_by_name("non-existent-secret")
    
    # Assertions
    assert secret is None
    mock_get_secrets.assert_called_once()
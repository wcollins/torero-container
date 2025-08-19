"""
Tests for database endpoints
"""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from torero_api.server import app
from torero_api.core.torero_executor import ToreroError

client = TestClient(app)

# Test data for database export
MOCK_DB_EXPORT_YAML = """decorators:
  - name: example-decorator
    description: Example decorator
    type: decorator
    schema:
      type: object
      properties:
        param1:
          type: string
repositories:
  - name: my-repo
    type: git
    url: https://github.com/example/repo.git
    reference: main
services:
  - name: test-service
    type: ansible-playbook
    description: Test ansible service
    repository: my-repo
    decorator: example-decorator
"""

MOCK_DB_EXPORT_JSON = {
    "decorators": [{
        "name": "example-decorator",
        "description": "Example decorator",
        "type": "decorator",
        "schema": {
            "type": "object",
            "properties": {
                "param1": {"type": "string"}
            }
        }
    }],
    "repositories": [{
        "name": "my-repo",
        "type": "git",
        "url": "https://github.com/example/repo.git",
        "reference": "main"
    }],
    "services": [{
        "name": "test-service",
        "type": "ansible-playbook",
        "description": "Test ansible service",
        "repository": "my-repo",
        "decorator": "example-decorator"
    }]
}

# Test data for database import
MOCK_IMPORT_CHECK_RESULT = {
    "conflicts": [
        {
            "name": "existing-service",
            "type": "service",
            "state": "Conflict",
            "message": "Service already exists"
        }
    ],
    "additions": [
        {
            "name": "new-service",
            "type": "service",
            "state": "Add",
            "message": "Will be added"
        }
    ],
    "replacements": [],
    "summary": {
        "conflicts": 1,
        "additions": 1,
        "replacements": 0
    }
}

MOCK_IMPORT_SUCCESS_RESULT = {
    "success": True,
    "imported": {
        "services": 3,
        "repositories": 1,
        "decorators": 2
    },
    "message": "Import completed successfully"
}

class TestDatabaseExport:
    """Test database export endpoints"""
    
    @patch('torero_api.api.v1.endpoints.database.execute_db_export')
    async def test_export_database_yaml(self, mock_execute):
        """Test exporting database in YAML format"""
        # Setup mock
        mock_execute.return_value = {"data": MOCK_DB_EXPORT_YAML, "format": "yaml"}
        
        # Make request
        response = client.get("/v1/db/export?format=yaml")
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert "decorators" in data
        assert "repositories" in data
        assert "services" in data
        mock_execute.assert_called_once_with(format="yaml")
    
    @patch('torero_api.api.v1.endpoints.database.execute_db_export')
    async def test_export_database_json(self, mock_execute):
        """Test exporting database in JSON format"""
        # Setup mock
        mock_execute.return_value = MOCK_DB_EXPORT_JSON
        
        # Make request
        response = client.get("/v1/db/export?format=json")
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data == MOCK_DB_EXPORT_JSON
        mock_execute.assert_called_once_with(format="json")
    
    @patch('torero_api.api.v1.endpoints.database.execute_db_export')
    async def test_export_database_default_format(self, mock_execute):
        """Test exporting database with default format (YAML)"""
        # Setup mock
        mock_execute.return_value = {"data": MOCK_DB_EXPORT_YAML, "format": "yaml"}
        
        # Make request
        response = client.get("/v1/db/export")
        
        # Verify
        assert response.status_code == 200
        mock_execute.assert_called_once_with(format="yaml")
    
    @patch('torero_api.api.v1.endpoints.database.execute_db_export')
    async def test_export_database_error(self, mock_execute):
        """Test database export error handling"""
        # Setup mock
        mock_execute.side_effect = ToreroError("Export failed")
        
        # Make request
        response = client.get("/v1/db/export")
        
        # Verify
        assert response.status_code == 500
        assert "Export failed" in response.json()["detail"]
    
    @patch('torero_api.api.v1.endpoints.database.execute_db_export')
    async def test_download_database_export_yaml(self, mock_execute):
        """Test downloading database export as YAML file"""
        # Setup mock
        mock_execute.return_value = {"data": MOCK_DB_EXPORT_YAML, "format": "yaml"}
        
        # Make request
        response = client.get("/v1/db/export/download?format=yaml")
        
        # Verify
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/x-yaml"
        assert "attachment" in response.headers["content-disposition"]
        assert "torero-export.yaml" in response.headers["content-disposition"]
        assert response.text == MOCK_DB_EXPORT_YAML
    
    @patch('torero_api.api.v1.endpoints.database.execute_db_export')
    async def test_download_database_export_json(self, mock_execute):
        """Test downloading database export as JSON file"""
        # Setup mock
        mock_execute.return_value = MOCK_DB_EXPORT_JSON
        
        # Make request
        response = client.get("/v1/db/export/download?format=json")
        
        # Verify
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        assert "attachment" in response.headers["content-disposition"]
        assert "torero-export.json" in response.headers["content-disposition"]
        
        # Verify JSON content
        import json
        data = json.loads(response.text)
        assert data == MOCK_DB_EXPORT_JSON
    
    @patch('torero_api.api.v1.endpoints.database.execute_db_export')
    async def test_download_database_export_custom_filename(self, mock_execute):
        """Test downloading database export with custom filename"""
        # Setup mock
        mock_execute.return_value = {"data": MOCK_DB_EXPORT_YAML, "format": "yaml"}
        
        # Make request
        response = client.get("/v1/db/export/download?filename=my-backup.yaml")
        
        # Verify
        assert response.status_code == 200
        assert "my-backup.yaml" in response.headers["content-disposition"]

class TestDatabaseImport:
    """Test database import endpoints"""
    
    @patch('torero_api.api.v1.endpoints.database.execute_db_import')
    async def test_import_database_basic(self, mock_execute):
        """Test basic database import from uploaded file"""
        # Setup mock
        mock_execute.return_value = MOCK_IMPORT_SUCCESS_RESULT
        
        # Create test file
        files = {'file': ('import.yaml', MOCK_DB_EXPORT_YAML, 'application/x-yaml')}
        
        # Make request
        response = client.post("/v1/db/import", files=files)
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["imported"]["services"] == 3
        
        # Verify mock was called with correct parameters
        mock_execute.assert_called_once()
        call_args = mock_execute.call_args
        assert call_args[1]["options"].force is False
        assert call_args[1]["options"].check is False
        assert call_args[1]["options"].validate_only is False
    
    @patch('torero_api.api.v1.endpoints.database.execute_db_import')
    async def test_import_database_with_force(self, mock_execute):
        """Test database import with force option"""
        # Setup mock
        mock_execute.return_value = MOCK_IMPORT_SUCCESS_RESULT
        
        # Create test file
        files = {'file': ('import.yaml', MOCK_DB_EXPORT_YAML, 'application/x-yaml')}
        data = {'force': 'true'}
        
        # Make request
        response = client.post("/v1/db/import", files=files, data=data)
        
        # Verify
        assert response.status_code == 200
        
        # Verify force option was set
        call_args = mock_execute.call_args
        assert call_args[1]["options"].force is True
    
    @patch('torero_api.api.v1.endpoints.database.execute_db_import')
    async def test_import_database_check(self, mock_execute):
        """Test database import check (dry-run)"""
        # Setup mock
        mock_execute.return_value = MOCK_IMPORT_CHECK_RESULT
        
        # Create test file
        files = {'file': ('import.yaml', MOCK_DB_EXPORT_YAML, 'application/x-yaml')}
        data = {'check': 'true'}
        
        # Make request
        response = client.post("/v1/db/import", files=files, data=data)
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert "conflicts" in data
        assert "additions" in data
        
        # Verify check option was set
        call_args = mock_execute.call_args
        assert call_args[1]["options"].check is True
    
    @patch('torero_api.api.v1.endpoints.database.execute_db_import')
    async def test_import_database_validate_only(self, mock_execute):
        """Test database import validation only"""
        # Setup mock
        mock_execute.return_value = {"success": True, "message": "Validation successful"}
        
        # Create test file
        files = {'file': ('import.yaml', MOCK_DB_EXPORT_YAML, 'application/x-yaml')}
        data = {'validate_only': 'true'}
        
        # Make request
        response = client.post("/v1/db/import", files=files, data=data)
        
        # Verify
        assert response.status_code == 200
        
        # Verify validate option was set
        call_args = mock_execute.call_args
        assert call_args[1]["options"].validate_only is True
    
    @patch('torero_api.api.v1.endpoints.database.execute_db_import')
    async def test_import_database_error(self, mock_execute):
        """Test database import error handling"""
        # Setup mock
        mock_execute.side_effect = ToreroError("Invalid import file")
        
        # Create test file
        files = {'file': ('import.yaml', 'invalid content', 'application/x-yaml')}
        
        # Make request
        response = client.post("/v1/db/import", files=files)
        
        # Verify
        assert response.status_code == 400
        assert "Invalid import file" in response.json()["detail"]
    
    @patch('torero_api.api.v1.endpoints.database.execute_db_import')
    async def test_import_check_endpoint(self, mock_execute):
        """Test dedicated import check endpoint"""
        # Setup mock
        mock_execute.return_value = MOCK_IMPORT_CHECK_RESULT
        
        # Create test file
        files = {'file': ('import.yaml', MOCK_DB_EXPORT_YAML, 'application/x-yaml')}
        
        # Make request
        response = client.post("/v1/db/import/check", files=files)
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert len(data["conflicts"]) == 1
        assert len(data["additions"]) == 1
        assert data["summary"]["conflicts"] == 1
        
        # Verify check option was set
        call_args = mock_execute.call_args
        assert call_args[1]["options"].check is True
    
    @patch('torero_api.api.v1.endpoints.database.execute_db_import')
    async def test_import_from_repository_http(self, mock_execute):
        """Test database import from HTTP repository"""
        # Setup mock
        mock_execute.return_value = MOCK_IMPORT_SUCCESS_RESULT
        
        # Make request
        data = {
            'repository': 'https://github.com/example/configs.git',
            'file_path': 'configs/import.yaml',
            'reference': 'main'
        }
        response = client.post("/v1/db/import/repository", data=data)
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # Verify repository options were set
        call_args = mock_execute.call_args
        assert call_args[1]["file_path"] == 'configs/import.yaml'
        assert call_args[1]["options"].repository == 'https://github.com/example/configs.git'
        assert call_args[1]["options"].reference == 'main'
    
    @patch('torero_api.api.v1.endpoints.database.execute_db_import')
    async def test_import_from_repository_ssh(self, mock_execute):
        """Test database import from SSH repository with private key"""
        # Setup mock
        mock_execute.return_value = MOCK_IMPORT_SUCCESS_RESULT
        
        # Make request
        data = {
            'repository': '[email protected]:example/configs.git',
            'file_path': 'configs/import.yaml',
            'private_key_name': 'my-deploy-key',
            'force': 'true'
        }
        response = client.post("/v1/db/import/repository", data=data)
        
        # Verify
        assert response.status_code == 200
        
        # Verify SSH options were set
        call_args = mock_execute.call_args
        assert call_args[1]["options"].repository == '[email protected]:example/configs.git'
        assert call_args[1]["options"].private_key == 'my-deploy-key'
        assert call_args[1]["options"].force is True
    
    @patch('torero_api.api.v1.endpoints.database.execute_db_import')
    async def test_import_from_repository_error(self, mock_execute):
        """Test repository import error handling"""
        # Setup mock
        mock_execute.side_effect = ToreroError("Repository not found")
        
        # Make request
        data = {
            'repository': 'https://github.com/nonexistent/repo.git',
            'file_path': 'import.yaml'
        }
        response = client.post("/v1/db/import/repository", data=data)
        
        # Verify
        assert response.status_code == 400
        assert "Repository not found" in response.json()["detail"]
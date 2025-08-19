"""HTTP client for torero API."""

import json
import logging
from typing import Any, Dict, List, Optional, Union

import httpx
from pydantic import BaseModel

from .config import APIConfig, AuthConfig

logger = logging.getLogger(__name__)


class ToreroAPIError(Exception):
    """Base exception for torero API errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class ToreroClient:
    """HTTP client for torero API."""
    
    def __init__(self, config: APIConfig):
        """
        Initialize the torero client.
        
        Args:
            config: API configuration
        """
        self.config = config
        self.base_url = config.base_url.rstrip("/")
        
        # Set up authentication headers
        headers = {"Content-Type": "application/json"}
        if config.auth:
            if config.auth.type == "bearer" and config.auth.token:
                headers["Authorization"] = f"Bearer {config.auth.token}"
            elif config.auth.type == "basic" and config.auth.username and config.auth.password:
                import base64
                credentials = base64.b64encode(
                    f"{config.auth.username}:{config.auth.password}".encode()
                ).decode()
                headers["Authorization"] = f"Basic {credentials}"
        
        # Create HTTP client
        self._client = httpx.AsyncClient(
            timeout=config.timeout,
            verify=config.verify_ssl,
            headers=headers,
            follow_redirects=True,
        )
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._client.aclose()
    
    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
    
    async def _request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the torero API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint (relative to base URL)
            params: Query parameters
            json_data: JSON data for request body
            
        Returns:
            Response data as dictionary
            
        Raises:
            ToreroAPIError: If the request fails
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            logger.debug(f"Making {method} request to {url}")
            if params:
                logger.debug(f"Query parameters: {params}")
            if json_data:
                logger.debug(f"Request body: {json_data}")
            
            response = await self._client.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
            )
            
            logger.debug(f"Response status: {response.status_code}")
            
            # Handle different response types
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                raise ToreroAPIError("Resource not found", status_code=404)
            elif response.status_code >= 400:
                try:
                    error_data = response.json()
                    error_message = error_data.get("detail", f"API error: {response.status_code}")
                except Exception:
                    error_message = f"API error: {response.status_code}"
                raise ToreroAPIError(error_message, status_code=response.status_code)
            else:
                response.raise_for_status()
                return response.json()
                
        except httpx.TimeoutException:
            raise ToreroAPIError("Request timed out")
        except httpx.RequestError as e:
            raise ToreroAPIError(f"Request failed: {str(e)}")
        except Exception as e:
            if isinstance(e, ToreroAPIError):
                raise
            raise ToreroAPIError(f"Unexpected error: {str(e)}")
    
    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a GET request."""
        return await self._request("GET", endpoint, params=params)
    
    async def post(self, endpoint: str, json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a POST request."""
        return await self._request("POST", endpoint, json_data=json_data)
    
    # Health check
    async def health_check(self) -> Dict[str, Any]:
        """Check API health."""
        return await self.get("/health")
    
    # Services
    async def list_services(
        self, 
        service_type: Optional[str] = None,
        tag: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List services with optional filtering."""
        params = {"skip": skip, "limit": limit}
        if service_type:
            params["type"] = service_type
        if tag:
            params["tag"] = tag
        
        return await self.get("/v1/services/", params=params)
    
    async def get_service(self, name: str) -> Dict[str, Any]:
        """Get a specific service by name."""
        return await self.get(f"/v1/services/{name}")
    
    async def describe_service(self, name: str) -> Dict[str, Any]:
        """Get detailed description of a specific service."""
        return await self.get(f"/v1/services/{name}/describe")
    
    async def execute_service(
        self,
        service_name: str,
        parameters: Optional[Dict[str, Any]] = None,
        async_execution: bool = False,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute a service with given parameters."""
        return await self.post(
            f"/v1/services/{service_name}/execute",
            json_data={
                "parameters": parameters or {},
                "async": async_execution,
                "timeout": timeout
            }
        )
    
    async def list_service_types(self) -> List[str]:
        """List available service types."""
        return await self.get("/v1/services/types")
    
    async def list_service_tags(self) -> List[str]:
        """List all service tags."""
        return await self.get("/v1/services/tags")
    
    # Service execution
    async def execute_ansible_playbook(self, service_name: str) -> Dict[str, Any]:
        """
        Execute an ansible-playbook service.
        
        Args:
            service_name: Name of the ansible-playbook service
            
        Returns:
            Execution result with return_code, stdout, stderr, timing info
        """
        return await self.post(f"/v1/execute/ansible-playbook/{service_name}")
    
    async def execute_python_script(self, service_name: str) -> Dict[str, Any]:
        """
        Execute a python-script service.
        
        Args:
            service_name: Name of the python-script service
            
        Returns:
            Execution result with return_code, stdout, stderr, timing info
        """
        return await self.post(f"/v1/execute/python-script/{service_name}")
    
    async def execute_opentofu_plan_apply(self, service_name: str) -> Dict[str, Any]:
        """
        Execute an OpenTofu plan service to apply infrastructure changes.
        
        Args:
            service_name: Name of the OpenTofu plan service
            
        Returns:
            Execution result with return_code, stdout, stderr, timing info
        """
        return await self.post(f"/v1/execute/opentofu-plan/{service_name}/apply")
    
    async def execute_opentofu_plan_destroy(self, service_name: str) -> Dict[str, Any]:
        """
        Execute an OpenTofu plan service to destroy infrastructure resources.
        
        Args:
            service_name: Name of the OpenTofu plan service
            
        Returns:
            Execution result with return_code, stdout, stderr, timing info
        """
        return await self.post(f"/v1/execute/opentofu-plan/{service_name}/destroy")
    
    # Decorators
    async def list_decorators(
        self,
        decorator_type: Optional[str] = None,
        service_type: Optional[str] = None,
        tag: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List decorators with optional filtering."""
        params = {"skip": skip, "limit": limit}
        if decorator_type:
            params["type"] = decorator_type
        if service_type:
            params["service_type"] = service_type
        if tag:
            params["tag"] = tag
        
        return await self.get("/v1/decorators/", params=params)
    
    async def get_decorator(self, name: str) -> Dict[str, Any]:
        """Get a specific decorator by name."""
        return await self.get(f"/v1/decorators/{name}")
    
    async def list_decorator_types(self) -> List[str]:
        """List available decorator types."""
        return await self.get("/v1/decorators/types")
    
    # Repositories
    async def list_repositories(
        self,
        repo_type: Optional[str] = None,
        tag: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List repositories with optional filtering."""
        params = {"skip": skip, "limit": limit}
        if repo_type:
            params["type"] = repo_type
        if tag:
            params["tag"] = tag
        
        return await self.get("/v1/repositories/", params=params)
    
    async def get_repository(self, name: str) -> Dict[str, Any]:
        """Get a specific repository by name."""
        return await self.get(f"/v1/repositories/{name}")
    
    async def list_repository_types(self) -> List[str]:
        """List available repository types."""
        return await self.get("/v1/repositories/types")
    
    # Secrets
    async def list_secrets(
        self,
        secret_type: Optional[str] = None,
        tag: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List secrets with optional filtering."""
        params = {"skip": skip, "limit": limit}
        if secret_type:
            params["type"] = secret_type
        if tag:
            params["tag"] = tag
        
        return await self.get("/v1/secrets/", params=params)
    
    async def get_secret(self, name: str, include_value: bool = False) -> Dict[str, Any]:
        """Get a specific secret by name."""
        params = {"include_value": include_value} if include_value else {}
        return await self.get(f"/v1/secrets/{name}", params=params)
    
    async def list_secret_types(self) -> List[str]:
        """List available secret types."""
        return await self.get("/v1/secrets/types")
    
    # Executions
    async def list_executions(
        self,
        service_name: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List executions with optional filtering."""
        params = {"skip": skip, "limit": limit}
        if service_name:
            params["service_name"] = service_name
        if status:
            params["status"] = status
        
        return await self.get("/v1/executions", params=params)
    
    async def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """Get execution status."""
        return await self.get(f"/v1/executions/{execution_id}")
    
    async def cancel_execution(self, execution_id: str) -> Dict[str, Any]:
        """Cancel an execution."""
        return await self.post(f"/v1/executions/{execution_id}/cancel")
    
    async def stream_execution_logs(self, execution_id: str, follow: bool = True):
        """Stream execution logs."""
        params = {"follow": follow}
        
        async with self._client.stream(
            "GET",
            f"{self.base_url}/v1/executions/{execution_id}/logs",
            params=params
        ) as response:
            async for line in response.aiter_lines():
                if line.strip():
                    yield json.loads(line)
    
    # System info
    async def get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        return await self.get("/v1/system/info")
    
    # Service descriptions
    async def get_service_description(self, name: str) -> Dict[str, Any]:
        """Get service description."""
        return await self.get(f"/v1/services/{name}/description")
    
    # Repository management
    async def sync_repository(self, name: str, force: bool = False) -> Dict[str, Any]:
        """Sync a repository."""
        return await self.post(f"/v1/repositories/{name}/sync", json_data={"force": force})
    
    async def create_repository(self, name: str, url: str, **kwargs) -> Dict[str, Any]:
        """Create a new repository."""
        data = {"name": name, "url": url, **kwargs}
        return await self.post("/v1/repositories/", json_data=data)
    
    async def delete_repository(self, name: str) -> Dict[str, Any]:
        """Delete a repository."""
        return await self.post(f"/v1/repositories/{name}/delete")
    
    # Secret management
    async def create_secret(self, name: str, value: str, secret_type: str = "generic", **kwargs) -> Dict[str, Any]:
        """Create a new secret."""
        data = {"name": name, "value": value, "type": secret_type, **kwargs}
        return await self.post("/v1/secrets/", json_data=data)
    
    async def update_secret(self, name: str, value: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Update a secret."""
        data = {}
        if value is not None:
            data["value"] = value
        data.update(kwargs)
        return await self.post(f"/v1/secrets/{name}/update", json_data=data)
    
    async def delete_secret(self, name: str) -> Dict[str, Any]:
        """Delete a secret."""
        return await self.post(f"/v1/secrets/{name}/delete")
    
    # Database import/export
    async def export_database(self, format: str = "yaml") -> Dict[str, Any]:
        """
        Export services and resources to a file.
        
        Args:
            format: Export format (json or yaml, default: yaml)
            
        Returns:
            Exported configuration data
        """
        params = {"format": format}
        return await self.get("/v1/db/export", params=params)
    
    async def export_database_download(self, format: str = "yaml", filename: Optional[str] = None) -> bytes:
        """
        Export services and resources as a downloadable file.
        
        Args:
            format: Export format (json or yaml, default: yaml)
            filename: Optional filename for the export
            
        Returns:
            File content as bytes
        """
        params = {"format": format}
        if filename:
            params["filename"] = filename
        
        # Use raw response for file download
        response = await self._client.get(
            f"{self.base_url}/v1/db/export/download",
            params=params
        )
        response.raise_for_status()
        return response.content
    
    async def import_database(
        self,
        file_content: str,
        force: bool = False,
        check: bool = False,
        validate_only: bool = False
    ) -> Dict[str, Any]:
        """
        Import resources/services from a file.
        
        Args:
            file_content: Content of the file to import
            force: Force import even with conflicts
            check: Check for conflicts before importing
            validate_only: Only validate without importing
            
        Returns:
            Import result with status and potential conflicts
        """
        # Create multipart form data
        files = {"file": ("import.yaml", file_content, "text/yaml")}
        data = {
            "force": str(force).lower(),
            "check": str(check).lower(),
            "validate_only": str(validate_only).lower()
        }
        
        response = await self._client.post(
            f"{self.base_url}/v1/db/import",
            files=files,
            data=data
        )
        response.raise_for_status()
        return response.json()
    
    async def check_database_import(self, file_content: str) -> Dict[str, Any]:
        """
        Check what would happen during an import without actually importing.
        
        Args:
            file_content: Content of the file to check
            
        Returns:
            DatabaseImportCheckResult showing potential additions, replacements, conflicts
        """
        files = {"file": ("check.yaml", file_content, "text/yaml")}
        
        response = await self._client.post(
            f"{self.base_url}/v1/db/import/check",
            files=files
        )
        response.raise_for_status()
        return response.json()
    
    async def import_database_from_repository(
        self,
        repository_url: str,
        file_path: str,
        branch: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        private_key_name: Optional[str] = None,
        force: bool = False,
        check: bool = False,
        validate_only: bool = False
    ) -> Dict[str, Any]:
        """
        Import resources/services from a repository.
        
        Args:
            repository_url: Repository URL
            file_path: Path to the import file within the repository
            branch: Optional branch name (sent as 'reference' to API)
            username: Optional username for authentication
            password: Optional password for authentication
            private_key_name: Optional SSH private key name for authentication
            force: Force import even with conflicts
            check: Check for conflicts before importing
            validate_only: Only validate without importing
            
        Returns:
            Import result similar to standard import endpoint
        """
        # Prepare form data according to API expectations
        data = {
            "repository": repository_url,  # API expects 'repository' not 'repository_url'
            "file_path": file_path,
            "force": str(force).lower(),
            "check": str(check).lower(),
            "validate_only": str(validate_only).lower()
        }
        
        if branch:
            data["reference"] = branch  # API expects 'reference' not 'branch'
        if private_key_name:
            data["private_key_name"] = private_key_name
        if username:
            data["username"] = username
        if password:
            data["password"] = password
        
        # Use form data (application/x-www-form-urlencoded)
        response = await self._client.post(
            f"{self.base_url}/v1/db/import/repository",
            data=data,  # This will use application/x-www-form-urlencoded
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        # Better error handling for debugging
        if response.status_code >= 400:
            try:
                error_data = response.json()
                error_message = f"API error {response.status_code}: {error_data}"
            except Exception:
                error_message = f"API error {response.status_code}: {response.text}"
            raise ToreroAPIError(error_message, status_code=response.status_code)
        
        return response.json()
"""Database import/export tools for torero MCP server."""

import json
import logging
from pathlib import Path
from typing import Optional

from ..client import ToreroClient, ToreroAPIError

logger = logging.getLogger(__name__)


async def export_database(
    client: ToreroClient,
    format: str = "yaml"
) -> str:
    """Export torero database configuration.
    
    Exports all services, repositories, decorators, and secrets metadata
    to a YAML or JSON format that can be used for backup or migration.
    
    Args:
        client: ToreroClient instance
        format: Export format - either "yaml" or "json" (default: "yaml")
        
    Returns:
        JSON string containing the exported configuration data
        
    Examples:
        Export to YAML format:
        >>> export_database(format="yaml")
        
        Export to JSON format:
        >>> export_database(format="json")
    """
    try:
        if format not in ["yaml", "json"]:
            return json.dumps({
                "error": "Invalid format. Must be 'yaml' or 'json'",
                "supported_formats": ["yaml", "json"]
            }, indent=2)
        
        logger.info(f"Exporting database in {format} format")
        result = await client.export_database(format=format)
        
        return json.dumps({
            "status": "success",
            "format": format,
            "data": result
        }, indent=2)
        
    except ToreroAPIError as e:
        logger.error(f"API error exporting database: {e}")
        return json.dumps({
            "error": f"Failed to export database: {e}",
            "status_code": e.status_code
        }, indent=2)
    except Exception as e:
        logger.exception("Unexpected error exporting database")
        return json.dumps({
            "error": f"Unexpected error: {e}"
        }, indent=2)


async def export_database_to_file(
    client: ToreroClient,
    filename: str,
    format: str = "yaml"
) -> str:
    """Export torero database configuration to a file.
    
    Exports all services, repositories, decorators, and secrets metadata
    to a file in YAML or JSON format.
    
    Args:
        client: ToreroClient instance
        filename: Path where the export file will be saved
        format: Export format - either "yaml" or "json" (default: "yaml")
        
    Returns:
        JSON string with export status and file location
        
    Examples:
        Export to YAML file:
        >>> export_database_to_file(filename="backup.yaml", format="yaml")
        
        Export to JSON file:
        >>> export_database_to_file(filename="backup.json", format="json")
    """
    try:
        if format not in ["yaml", "json"]:
            return json.dumps({
                "error": "Invalid format. Must be 'yaml' or 'json'",
                "supported_formats": ["yaml", "json"]
            }, indent=2)
        
        logger.info(f"Exporting database to file: {filename}")
        content = await client.export_database_download(format=format, filename=filename)
        
        # Save to file
        output_path = Path(filename)
        output_path.write_bytes(content)
        
        return json.dumps({
            "status": "success",
            "format": format,
            "filename": str(output_path.absolute()),
            "size_bytes": len(content)
        }, indent=2)
        
    except ToreroAPIError as e:
        logger.error(f"API error exporting database to file: {e}")
        return json.dumps({
            "error": f"Failed to export database: {e}",
            "status_code": e.status_code
        }, indent=2)
    except Exception as e:
        logger.exception("Unexpected error exporting database to file")
        return json.dumps({
            "error": f"Unexpected error: {e}"
        }, indent=2)


async def import_database(
    client: ToreroClient,
    filename: str,
    force: bool = False,
    check: bool = False,
    validate_only: bool = False
) -> str:
    """Import torero database configuration from a file.
    
    Imports services, repositories, decorators, and secrets from a YAML or JSON file.
    Supports dry-run validation and conflict resolution.
    
    Args:
        client: ToreroClient instance
        filename: Path to the import file
        force: Force import even with conflicts (default: False)
        check: Check for conflicts before importing (default: False)
        validate_only: Only validate without importing (default: False)
        
    Returns:
        JSON string with import result and any conflicts
        
    Examples:
        Basic import:
        >>> import_database(filename="config.yaml")
        
        Check before import:
        >>> import_database(filename="config.yaml", check=True)
        
        Force import with conflicts:
        >>> import_database(filename="config.yaml", force=True)
        
        Validate only:
        >>> import_database(filename="config.yaml", validate_only=True)
    """
    try:
        import_path = Path(filename)
        if not import_path.exists():
            return json.dumps({
                "error": f"File not found: {filename}"
            }, indent=2)
        
        # Read file content
        file_content = import_path.read_text()
        
        logger.info(f"Importing database from file: {filename}")
        result = await client.import_database(
            file_content=file_content,
            force=force,
            check=check,
            validate_only=validate_only
        )
        
        return json.dumps({
            "status": "success",
            "filename": str(import_path.absolute()),
            "result": result,
            "options": {
                "force": force,
                "check": check,
                "validate_only": validate_only
            }
        }, indent=2)
        
    except ToreroAPIError as e:
        logger.error(f"API error importing database: {e}")
        return json.dumps({
            "error": f"Failed to import database: {e}",
            "status_code": e.status_code
        }, indent=2)
    except Exception as e:
        logger.exception("Unexpected error importing database")
        return json.dumps({
            "error": f"Unexpected error: {e}"
        }, indent=2)


async def check_database_import(
    client: ToreroClient,
    filename: str
) -> str:
    """Check what would happen during a database import.
    
    Analyzes the import file and reports what resources would be added,
    replaced, or cause conflicts, without actually performing the import.
    
    Args:
        client: ToreroClient instance
        filename: Path to the import file to check
        
    Returns:
        JSON string with analysis of potential additions, replacements, and conflicts
        
    Examples:
        Check import file:
        >>> check_database_import(filename="config.yaml")
    """
    try:
        import_path = Path(filename)
        if not import_path.exists():
            return json.dumps({
                "error": f"File not found: {filename}"
            }, indent=2)
        
        # Read file content
        file_content = import_path.read_text()
        
        logger.info(f"Checking database import from file: {filename}")
        result = await client.check_database_import(file_content=file_content)
        
        return json.dumps({
            "status": "success",
            "filename": str(import_path.absolute()),
            "check_result": result
        }, indent=2)
        
    except ToreroAPIError as e:
        logger.error(f"API error checking database import: {e}")
        return json.dumps({
            "error": f"Failed to check import: {e}",
            "status_code": e.status_code
        }, indent=2)
    except Exception as e:
        logger.exception("Unexpected error checking database import")
        return json.dumps({
            "error": f"Unexpected error: {e}"
        }, indent=2)


async def import_database_from_repository(
    client: ToreroClient,
    repository_url: str,
    file_path: str,
    branch: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    private_key_name: Optional[str] = None,
    force: bool = False,
    check: bool = False,
    validate_only: bool = False
) -> str:
    """Import torero database configuration from a git repository.
    
    Imports services, repositories, decorators, and secrets from a file
    in a git repository. Supports authentication and conflict resolution.
    
    Args:
        client: ToreroClient instance
        repository_url: Git repository URL
        file_path: Path to the import file within the repository
        branch: Optional branch name (default: repository default branch)
        username: Optional username for repository authentication
        password: Optional password for repository authentication
        private_key_name: Optional SSH private key name for authentication
        force: Force import even with conflicts (default: False)
        check: Check for conflicts before importing (default: False)
        validate_only: Only validate without importing (default: False)
        
    Returns:
        JSON string with import result and any conflicts
        
    Examples:
        Import from public repository:
        >>> import_database_from_repository(
        ...     repository_url="https://github.com/org/config",
        ...     file_path="torero/config.yaml"
        ... )
        
        Import from private repository with HTTP auth:
        >>> import_database_from_repository(
        ...     repository_url="https://github.com/org/private-config",
        ...     file_path="torero/config.yaml",
        ...     username="user",
        ...     password="token"
        ... )
        
        Import from private repository with SSH key:
        >>> import_database_from_repository(
        ...     repository_url="git@github.com:org/private-config.git",
        ...     file_path="torero/config.yaml",
        ...     private_key_name="my-ssh-key"
        ... )
        
        Import from specific branch:
        >>> import_database_from_repository(
        ...     repository_url="https://github.com/org/config",
        ...     file_path="torero/config.yaml",
        ...     branch="develop"
        ... )
    """
    try:
        logger.info(f"Importing database from repository: {repository_url}")
        result = await client.import_database_from_repository(
            repository_url=repository_url,
            file_path=file_path,
            branch=branch,
            username=username,
            password=password,
            private_key_name=private_key_name,
            force=force,
            check=check,
            validate_only=validate_only
        )
        
        return json.dumps({
            "status": "success",
            "repository_url": repository_url,
            "file_path": file_path,
            "branch": branch or "default",
            "result": result,
            "options": {
                "force": force,
                "check": check,
                "validate_only": validate_only,
                "authenticated": bool(username or private_key_name),
                "auth_type": "ssh" if private_key_name else ("http" if username else "none")
            }
        }, indent=2)
        
    except ToreroAPIError as e:
        logger.error(f"API error importing from repository: {e}")
        return json.dumps({
            "error": f"Failed to import from repository: {e}",
            "status_code": e.status_code
        }, indent=2)
    except Exception as e:
        logger.exception("Unexpected error importing from repository")
        return json.dumps({
            "error": f"Unexpected error: {e}"
        }, indent=2)
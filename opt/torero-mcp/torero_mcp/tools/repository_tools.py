"""Repository-related tools for torero MCP server."""

import json
import logging
from typing import Any, Dict, Optional

from ..client import ToreroAPIError, ToreroClient

logger = logging.getLogger(__name__)


async def list_repositories(
    client: ToreroClient,
    repo_type: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = 100
) -> str:
    """
    List torero repositories with optional filtering.
    
    Args:
        client: ToreroClient instance
        repo_type: Filter by repository type (e.g., 'file', 'git', 's3')
        tag: Filter by tag
        limit: Maximum number of repositories to return (default: 100)
        
    Returns:
        JSON string containing list of repositories
    """
    try:
        repositories = await client.list_repositories(
            repo_type=repo_type,
            tag=tag,
            limit=limit
        )
        return json.dumps(repositories, indent=2)
    except ToreroAPIError as e:
        return f"Error listing repositories: {e}"
    except Exception as e:
        logger.exception("Unexpected error in list_repositories")
        return f"Unexpected error: {e}"


async def get_repository(client: ToreroClient, name: str) -> str:
    """
    Get detailed information about a specific torero repository.
    
    Args:
        client: ToreroClient instance
        name: Name of the repository to retrieve
        
    Returns:
        JSON string containing repository details
    """
    try:
        repository = await client.get_repository(name)
        return json.dumps(repository, indent=2)
    except ToreroAPIError as e:
        return f"Error getting repository '{name}': {e}"
    except Exception as e:
        logger.exception(f"Unexpected error getting repository '{name}'")
        return f"Unexpected error: {e}"


async def list_repository_types(client: ToreroClient) -> str:
    """
    Get all available repository types.
    
    Args:
        client: ToreroClient instance
    
    Returns:
        JSON string containing list of repository types
    """
    try:
        types = await client.list_repository_types()
        return json.dumps(types, indent=2)
    except ToreroAPIError as e:
        return f"Error listing repository types: {e}"
    except Exception as e:
        logger.exception("Unexpected error in list_repository_types")
        return f"Unexpected error: {e}"


async def sync_repository(client: ToreroClient, name: str, force: bool = False) -> str:
    """
    Sync a repository with its remote source.
    
    Args:
        client: ToreroClient instance
        name: Name of the repository to sync
        force: Force sync even if there are conflicts
        
    Returns:
        JSON string containing sync result
    """
    try:
        result = await client.sync_repository(name, force=force)
        return json.dumps(result, indent=2)
    except ToreroAPIError as e:
        return f"Error syncing repository '{name}': {e}"
    except Exception as e:
        logger.exception(f"Unexpected error syncing repository '{name}'")
        return f"Unexpected error: {e}"


async def create_repository(
    client: ToreroClient, 
    name: str, 
    url: str,
    repo_type: str = "git",
    description: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Create a new repository.
    
    Args:
        client: ToreroClient instance
        name: Name of the repository
        url: URL of the repository
        repo_type: Type of repository (default: "git")
        description: Optional description of the repository
        metadata: Optional metadata dictionary
        
    Returns:
        JSON string containing creation result
    """
    try:
        kwargs = {"type": repo_type}
        if description is not None:
            kwargs["description"] = description
        if metadata is not None:
            kwargs["metadata"] = metadata
            
        result = await client.create_repository(name, url, **kwargs)
        return json.dumps(result, indent=2)
    except ToreroAPIError as e:
        return f"Error creating repository '{name}': {e}"
    except Exception as e:
        logger.exception(f"Unexpected error creating repository '{name}'")
        return f"Unexpected error: {e}"


async def delete_repository(client: ToreroClient, name: str) -> str:
    """
    Delete a repository.
    
    Args:
        client: ToreroClient instance
        name: Name of the repository to delete
        
    Returns:
        JSON string containing deletion result
    """
    try:
        result = await client.delete_repository(name)
        return json.dumps(result, indent=2)
    except ToreroAPIError as e:
        return f"Error deleting repository '{name}': {e}"
    except Exception as e:
        logger.exception(f"Unexpected error deleting repository '{name}'")
        return f"Unexpected error: {e}"
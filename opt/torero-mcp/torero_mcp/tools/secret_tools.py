"""Secret-related tools for torero MCP server."""

import json
import logging
from typing import Any, Dict, Optional

from ..client import ToreroAPIError, ToreroClient

logger = logging.getLogger(__name__)


async def list_secrets(
    client: ToreroClient,
    secret_type: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = 100
) -> str:
    """
    List torero secrets with optional filtering (metadata only).
    
    Args:
        client: ToreroClient instance
        secret_type: Filter by secret type (e.g., 'password', 'api-key', 'token')
        tag: Filter by tag
        limit: Maximum number of secrets to return (default: 100)
        
    Returns:
        JSON string containing list of secret metadata
    """
    try:
        secrets = await client.list_secrets(
            secret_type=secret_type,
            tag=tag,
            limit=limit
        )
        return json.dumps(secrets, indent=2)
    except ToreroAPIError as e:
        return f"Error listing secrets: {e}"
    except Exception as e:
        logger.exception("Unexpected error in list_secrets")
        return f"Unexpected error: {e}"


async def get_secret(client: ToreroClient, name: str, include_value: bool = False) -> str:
    """
    Get detailed information about a specific torero secret.
    
    Args:
        client: ToreroClient instance
        name: Name of the secret to retrieve
        include_value: Whether to include the secret value in the response
        
    Returns:
        JSON string containing secret metadata (and optionally value)
    """
    try:
        secret = await client.get_secret(name, include_value=include_value)
        return json.dumps(secret, indent=2)
    except ToreroAPIError as e:
        return f"Error getting secret '{name}': {e}"
    except Exception as e:
        logger.exception(f"Unexpected error getting secret '{name}'")
        return f"Unexpected error: {e}"


async def list_secret_types(client: ToreroClient) -> str:
    """
    Get all available secret types.
    
    Args:
        client: ToreroClient instance
    
    Returns:
        JSON string containing list of secret types
    """
    try:
        types = await client.list_secret_types()
        return json.dumps(types, indent=2)
    except ToreroAPIError as e:
        return f"Error listing secret types: {e}"
    except Exception as e:
        logger.exception("Unexpected error in list_secret_types")
        return f"Unexpected error: {e}"


async def create_secret(
    client: ToreroClient, 
    name: str, 
    value: str, 
    secret_type: str = "generic",
    description: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Create a new secret.
    
    Args:
        client: ToreroClient instance
        name: Name of the secret
        value: Secret value
        secret_type: Type of secret (default: "generic")
        description: Optional description of the secret
        metadata: Optional metadata dictionary
        
    Returns:
        JSON string containing creation result
    """
    try:
        kwargs = {}
        if description is not None:
            kwargs["description"] = description
        if metadata is not None:
            kwargs["metadata"] = metadata
            
        result = await client.create_secret(name, value, secret_type, **kwargs)
        return json.dumps(result, indent=2)
    except ToreroAPIError as e:
        return f"Error creating secret '{name}': {e}"
    except Exception as e:
        logger.exception(f"Unexpected error creating secret '{name}'")
        return f"Unexpected error: {e}"


async def update_secret(
    client: ToreroClient, 
    name: str, 
    value: Optional[str] = None,
    description: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Update a secret.
    
    Args:
        client: ToreroClient instance
        name: Name of the secret to update
        value: New secret value (optional)
        description: Updated description (optional)
        metadata: Updated metadata dictionary (optional)
        
    Returns:
        JSON string containing update result
    """
    try:
        kwargs = {}
        if description is not None:
            kwargs["description"] = description
        if metadata is not None:
            kwargs["metadata"] = metadata
            
        result = await client.update_secret(name, value, **kwargs)
        return json.dumps(result, indent=2)
    except ToreroAPIError as e:
        return f"Error updating secret '{name}': {e}"
    except Exception as e:
        logger.exception(f"Unexpected error updating secret '{name}'")
        return f"Unexpected error: {e}"


async def delete_secret(client: ToreroClient, name: str) -> str:
    """
    Delete a secret.
    
    Args:
        client: ToreroClient instance
        name: Name of the secret to delete
        
    Returns:
        JSON string containing deletion result
    """
    try:
        result = await client.delete_secret(name)
        return json.dumps(result, indent=2)
    except ToreroAPIError as e:
        return f"Error deleting secret '{name}': {e}"
    except Exception as e:
        logger.exception(f"Unexpected error deleting secret '{name}'")
        return f"Unexpected error: {e}"
"""Decorator-related tools for torero MCP server."""

import json
import logging
from typing import Any, Dict, Optional

from ..client import ToreroAPIError, ToreroClient

logger = logging.getLogger(__name__)


async def list_decorators(
    client: ToreroClient,
    decorator_type: Optional[str] = None,
    service_type: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = 100
) -> str:
    """
    List torero decorators with optional filtering.
    
    Args:
        client: ToreroClient instance
        decorator_type: Filter by decorator type (e.g., 'authentication', 'logging')
        service_type: Filter by applicable service type
        tag: Filter by tag
        limit: Maximum number of decorators to return (default: 100)
        
    Returns:
        JSON string containing list of decorators
    """
    try:
        decorators = await client.list_decorators(
            decorator_type=decorator_type,
            service_type=service_type,
            tag=tag,
            limit=limit
        )
        return json.dumps(decorators, indent=2)
    except ToreroAPIError as e:
        return f"Error listing decorators: {e}"
    except Exception as e:
        logger.exception("Unexpected error in list_decorators")
        return f"Unexpected error: {e}"


async def get_decorator(client: ToreroClient, name: str) -> str:
    """
    Get detailed information about a specific torero decorator.
    
    Args:
        client: ToreroClient instance
        name: Name of the decorator to retrieve
        
    Returns:
        JSON string containing decorator details
    """
    try:
        decorator = await client.get_decorator(name)
        return json.dumps(decorator, indent=2)
    except ToreroAPIError as e:
        return f"Error getting decorator '{name}': {e}"
    except Exception as e:
        logger.exception(f"Unexpected error getting decorator '{name}'")
        return f"Unexpected error: {e}"


async def list_decorator_types(client: ToreroClient) -> str:
    """
    Get all available decorator types.
    
    Args:
        client: ToreroClient instance
    
    Returns:
        JSON string containing list of decorator types
    """
    try:
        types = await client.list_decorator_types()
        return json.dumps(types, indent=2)
    except ToreroAPIError as e:
        return f"Error listing decorator types: {e}"
    except Exception as e:
        logger.exception("Unexpected error in list_decorator_types")
        return f"Unexpected error: {e}"
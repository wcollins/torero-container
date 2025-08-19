"""Service-related tools for torero MCP server."""

import json
import logging
from typing import Any, Dict, Optional

from ..client import ToreroAPIError, ToreroClient

logger = logging.getLogger(__name__)


async def list_services(
    client: ToreroClient,
    service_type: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = 100
) -> str:
    """
    List torero services with optional filtering.
    
    Args:
        client: ToreroClient instance
        service_type: Filter by service type (e.g., 'ansible-playbook', 'opentofu-plan', 'python-script')
        tag: Filter by tag (e.g., 'network', 'backup', 'automation')
        limit: Maximum number of services to return (default: 100)
        
    Returns:
        JSON string containing list of services
    """
    try:
        services = await client.list_services(
            service_type=service_type,
            tag=tag,
            limit=limit
        )
        return json.dumps(services, indent=2)
    except ToreroAPIError as e:
        return f"Error listing services: {e}"
    except Exception as e:
        logger.exception("Unexpected error in list_services")
        return f"Unexpected error: {e}"


async def get_service(client: ToreroClient, name: str) -> str:
    """
    Get detailed information about a specific torero service.
    
    Args:
        client: ToreroClient instance
        name: Name of the service to retrieve
        
    Returns:
        JSON string containing service details
    """
    try:
        service = await client.get_service(name)
        return json.dumps(service, indent=2)
    except ToreroAPIError as e:
        return f"Error getting service '{name}': {e}"
    except Exception as e:
        logger.exception(f"Unexpected error getting service '{name}'")
        return f"Unexpected error: {e}"


async def describe_service(client: ToreroClient, name: str) -> str:
    """
    Get complete and detailed description of a specific torero service.
    
    Args:
        client: ToreroClient instance
        name: Name of the service to describe
        
    Returns:
        JSON string containing detailed service description
    """
    try:
        description = await client.describe_service(name)
        return json.dumps(description, indent=2)
    except ToreroAPIError as e:
        return f"Error describing service '{name}': {e}"
    except Exception as e:
        logger.exception(f"Unexpected error describing service '{name}'")
        return f"Unexpected error: {e}"


async def list_service_types(client: ToreroClient) -> str:
    """
    Get all available service types.
    
    Args:
        client: ToreroClient instance
    
    Returns:
        JSON string containing list of service types
    """
    try:
        types = await client.list_service_types()
        return json.dumps(types, indent=2)
    except ToreroAPIError as e:
        return f"Error listing service types: {e}"
    except Exception as e:
        logger.exception("Unexpected error in list_service_types")
        return f"Unexpected error: {e}"


async def list_service_tags(client: ToreroClient) -> str:
    """
    Get all available service tags.
    
    Args:
        client: ToreroClient instance
    
    Returns:
        JSON string containing list of service tags
    """
    try:
        tags = await client.list_service_tags()
        return json.dumps(tags, indent=2)
    except ToreroAPIError as e:
        return f"Error listing service tags: {e}"
    except Exception as e:
        logger.exception("Unexpected error in list_service_tags")
        return f"Unexpected error: {e}"


async def get_service_description(client: ToreroClient, name: str) -> str:
    """
    Get detailed description of a specific torero service.
    
    Args:
        client: ToreroClient instance
        name: Name of the service to get description for
        
    Returns:
        JSON string containing service description
    """
    try:
        description = await client.get_service_description(name)
        return json.dumps(description, indent=2)
    except ToreroAPIError as e:
        return f"Error getting service description for '{name}': {e}"
    except Exception as e:
        logger.exception(f"Unexpected error getting service description for '{name}'")
        return f"Unexpected error: {e}"
"""Health check tools for torero MCP server."""

import json
import logging
from typing import Any, Dict

from ..client import ToreroAPIError, ToreroClient

logger = logging.getLogger(__name__)


async def health_check(client: ToreroClient) -> str:
    """
    Check the health of the torero API.
    
    Args:
        client: ToreroClient instance
    
    Returns:
        JSON string containing health status
    """
    try:
        health = await client.health_check()
        return json.dumps(health, indent=2)
    except ToreroAPIError as e:
        return f"Error checking health: {e}"
    except Exception as e:
        logger.exception("Unexpected error in health_check")
        return f"Unexpected error: {e}"


async def get_system_info(client: ToreroClient) -> str:
    """
    Get system information from the torero API.
    
    Args:
        client: ToreroClient instance
        
    Returns:
        JSON string containing system information
    """
    try:
        info = await client.get_system_info()
        return json.dumps(info, indent=2)
    except ToreroAPIError as e:
        return f"Error getting system info: {e}"
    except Exception as e:
        logger.exception("Unexpected error in get_system_info")
        return f"Unexpected error: {e}"
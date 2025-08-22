"""health check tools for torero mcp server."""

import json
import logging
from typing import Any, Dict

from ..executor import ToreroExecutorError, ToreroExecutor

logger = logging.getLogger(__name__)


async def health_check(executor: ToreroExecutor) -> str:
    """
    check the health of the torero cli.
    
    args:
        executor: toreroexecutor instance
    
    returns:
        json string containing health status
    """
    try:
        is_available, message = executor.check_torero_available()
        version = executor.check_torero_version()
        
        return json.dumps({
            "status": "healthy" if is_available else "unhealthy",
            "torero_available": is_available,
            "torero_version": version,
            "message": message
        }, indent=2)
    except Exception as e:
        logger.exception("unexpected error in health_check")
        return json.dumps({
            "status": "unhealthy",
            "torero_available": False,
            "error": f"unexpected error: {e}"
        }, indent=2)


async def get_torero_version(executor: ToreroExecutor) -> str:
    """
    get torero version information.
    
    args:
        executor: toreroexecutor instance
        
    returns:
        json string containing version information
    """
    try:
        version = executor.check_torero_version()
        is_available, message = executor.check_torero_available()
        
        return json.dumps({
            "version": version,
            "available": is_available,
            "message": message
        }, indent=2)
    except Exception as e:
        logger.exception("unexpected error in get_torero_version")
        return json.dumps({
            "version": "unknown",
            "available": False,
            "error": f"unexpected error: {e}"
        }, indent=2)
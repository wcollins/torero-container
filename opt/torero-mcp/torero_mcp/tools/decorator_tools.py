"""decorator-related tools for torero mcp server."""

import json
import logging
from typing import Any, Dict, Optional

from ..executor import ToreroExecutorError, ToreroExecutor

logger = logging.getLogger(__name__)


async def list_decorators(
    executor: ToreroExecutor,
    decorator_type: Optional[str] = None,
    service_type: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = 100
) -> str:
    """
    list torero decorators with optional filtering.
    
    args:
        executor: toreroexecutor instance
        decorator_type: filter by decorator type (e.g., 'authentication', 'logging')
        service_type: filter by applicable service type
        tag: filter by tag
        limit: maximum number of decorators to return (default: 100)
        
    returns:
        json string containing list of decorators
    """
    try:
        decorators = await executor.get_decorators()
        
        # apply filters
        if decorator_type:
            decorators = [d for d in decorators if d.get('type') == decorator_type]
        if service_type:
            decorators = [d for d in decorators if service_type in d.get('service_types', [])]
        if tag:
            decorators = [d for d in decorators if tag in d.get('tags', [])]
        
        # apply limit
        decorators = decorators[:limit]
        
        return json.dumps(decorators, indent=2)
    except ToreroExecutorError as e:
        return f"error listing decorators: {e}"
    except Exception as e:
        logger.exception("unexpected error in list_decorators")
        return f"unexpected error: {e}"


async def get_decorator(executor: ToreroExecutor, name: str) -> str:
    """
    get detailed information about a specific torero decorator.
    
    args:
        executor: toreroexecutor instance
        name: name of the decorator to retrieve
        
    returns:
        json string containing decorator details
    """
    try:
        decorators = await executor.get_decorators()
        decorator = next((d for d in decorators if d.get('name') == name), None)
        
        if decorator:
            return json.dumps(decorator, indent=2)
        else:
            return f"decorator '{name}' not found"
    except ToreroExecutorError as e:
        return f"error getting decorator '{name}': {e}"
    except Exception as e:
        logger.exception(f"unexpected error getting decorator '{name}'")
        return f"unexpected error: {e}"


async def list_decorator_types(executor: ToreroExecutor) -> str:
    """
    get all available decorator types.
    
    args:
        executor: toreroexecutor instance
    
    returns:
        json string containing list of decorator types
    """
    try:
        decorators = await executor.get_decorators()
        types = sorted(set(d.get('type', 'unknown') for d in decorators))
        return json.dumps(types, indent=2)
    except ToreroExecutorError as e:
        return f"error listing decorator types: {e}"
    except Exception as e:
        logger.exception("unexpected error in list_decorator_types")
        return f"unexpected error: {e}"
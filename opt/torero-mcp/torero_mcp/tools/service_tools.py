"""service-related tools for torero mcp server."""

import json
import logging
from typing import Any, Dict, Optional

from ..executor import ToreroExecutorError, ToreroExecutor

logger = logging.getLogger(__name__)


async def list_services(
    executor: ToreroExecutor,
    service_type: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = 100
) -> str:
    """
    list torero services with optional filtering.
    
    args:
        executor: toreroexecutor instance
        service_type: filter by service type (e.g., 'ansible-playbook', 'opentofu-plan', 'python-script')
        tag: filter by tag (e.g., 'network', 'backup', 'automation')
        limit: maximum number of services to return (default: 100)
        
    returns:
        json string containing list of services
    """
    try:
        services = await executor.get_services()
        
        # apply filters
        if service_type:
            services = [s for s in services if s.get('type') == service_type]
        if tag:
            services = [s for s in services if tag in s.get('tags', [])]
        
        # apply limit
        services = services[:limit]
        
        return json.dumps(services, indent=2)
    except ToreroExecutorError as e:
        return f"error listing services: {e}"
    except Exception as e:
        logger.exception("unexpected error in list_services")
        return f"unexpected error: {e}"


async def get_service(executor: ToreroExecutor, name: str) -> str:
    """
    get detailed information about a specific torero service.
    
    args:
        executor: toreroexecutor instance
        name: name of the service to retrieve
        
    returns:
        json string containing service details
    """
    try:
        service = await executor.get_service_by_name(name)
        if service:
            return json.dumps(service, indent=2)
        else:
            return f"service '{name}' not found"
    except ToreroExecutorError as e:
        return f"error getting service '{name}': {e}"
    except Exception as e:
        logger.exception(f"unexpected error getting service '{name}'")
        return f"unexpected error: {e}"


async def describe_service(executor: ToreroExecutor, name: str) -> str:
    """
    get complete and detailed description of a specific torero service.
    
    args:
        executor: toreroexecutor instance
        name: name of the service to describe
        
    returns:
        json string containing detailed service description
    """
    try:
        description = await executor.describe_service(name)
        if description:
            return json.dumps(description, indent=2)
        else:
            return f"service '{name}' description not available"
    except ToreroExecutorError as e:
        return f"error describing service '{name}': {e}"
    except Exception as e:
        logger.exception(f"unexpected error describing service '{name}'")
        return f"unexpected error: {e}"


async def list_service_types(executor: ToreroExecutor) -> str:
    """
    get all available service types.
    
    args:
        executor: toreroexecutor instance
    
    returns:
        json string containing list of service types
    """
    try:
        services = await executor.get_services()
        types = sorted(set(s.get('type', 'unknown') for s in services))
        return json.dumps(types, indent=2)
    except ToreroExecutorError as e:
        return f"error listing service types: {e}"
    except Exception as e:
        logger.exception("unexpected error in list_service_types")
        return f"unexpected error: {e}"


async def list_service_tags(executor: ToreroExecutor) -> str:
    """
    get all available service tags.
    
    args:
        executor: toreroexecutor instance
    
    returns:
        json string containing list of service tags
    """
    try:
        services = await executor.get_services()
        tags = sorted(set(tag for s in services for tag in s.get('tags', [])))
        return json.dumps(tags, indent=2)
    except ToreroExecutorError as e:
        return f"error listing service tags: {e}"
    except Exception as e:
        logger.exception("unexpected error in list_service_tags")
        return f"unexpected error: {e}"


async def get_service_description(executor: ToreroExecutor, name: str) -> str:
    """
    get detailed description of a specific torero service.
    
    args:
        executor: toreroexecutor instance
        name: name of the service to get description for
        
    returns:
        json string containing service description
    """
    try:
        description = await executor.describe_service(name)
        if description:
            return json.dumps(description, indent=2)
        else:
            return f"service '{name}' description not available"
    except ToreroExecutorError as e:
        return f"error getting service description for '{name}': {e}"
    except Exception as e:
        logger.exception(f"unexpected error getting service description for '{name}'")
        return f"unexpected error: {e}"
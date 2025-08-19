"""Service execution tools for torero MCP server."""

import json
import logging
from typing import Any, Dict, Optional

from ..client import ToreroAPIError, ToreroClient

logger = logging.getLogger(__name__)


async def execute_ansible_playbook(client: ToreroClient, service_name: str) -> str:
    """
    Execute an ansible-playbook service.
    
    Args:
        client: ToreroClient instance
        service_name: Name of the ansible-playbook service to execute
        
    Returns:
        JSON string containing execution result with return_code, stdout, stderr, and timing information
    """
    try:
        result = await client.execute_ansible_playbook(service_name=service_name)
        return json.dumps(result, indent=2)
    except ToreroAPIError as e:
        return f"Error executing ansible-playbook service '{service_name}': {e}"
    except Exception as e:
        logger.exception(f"Unexpected error executing ansible-playbook service '{service_name}'")
        return f"Unexpected error: {e}"


async def execute_python_script(client: ToreroClient, service_name: str) -> str:
    """
    Execute a python-script service.
    
    Args:
        client: ToreroClient instance
        service_name: Name of the python-script service to execute
        
    Returns:
        JSON string containing execution result with return_code, stdout, stderr, and timing information
    """
    try:
        result = await client.execute_python_script(service_name=service_name)
        return json.dumps(result, indent=2)
    except ToreroAPIError as e:
        return f"Error executing python-script service '{service_name}': {e}"
    except Exception as e:
        logger.exception(f"Unexpected error executing python-script service '{service_name}'")
        return f"Unexpected error: {e}"


async def execute_opentofu_plan_apply(client: ToreroClient, service_name: str) -> str:
    """
    Execute an OpenTofu plan service to apply infrastructure changes.
    
    Args:
        client: ToreroClient instance
        service_name: Name of the OpenTofu plan service to apply
        
    Returns:
        JSON string containing execution result with return_code, stdout, stderr, and timing information
    """
    try:
        result = await client.execute_opentofu_plan_apply(service_name=service_name)
        return json.dumps(result, indent=2)
    except ToreroAPIError as e:
        return f"Error executing OpenTofu plan apply service '{service_name}': {e}"
    except Exception as e:
        logger.exception(f"Unexpected error executing OpenTofu plan apply service '{service_name}'")
        return f"Unexpected error: {e}"


async def execute_opentofu_plan_destroy(client: ToreroClient, service_name: str) -> str:
    """
    Execute an OpenTofu plan service to destroy infrastructure resources.
    
    Args:
        client: ToreroClient instance
        service_name: Name of the OpenTofu plan service to destroy
        
    Returns:
        JSON string containing execution result with return_code, stdout, stderr, and timing information
    """
    try:
        result = await client.execute_opentofu_plan_destroy(service_name=service_name)
        return json.dumps(result, indent=2)
    except ToreroAPIError as e:
        return f"Error executing OpenTofu plan destroy service '{service_name}': {e}"
    except Exception as e:
        logger.exception(f"Unexpected error executing OpenTofu plan destroy service '{service_name}'")
        return f"Unexpected error: {e}"


async def execute_service(
    client: ToreroClient, 
    name: str, 
    parameters: Optional[Dict[str, Any]] = None,
    async_execution: bool = False,
    timeout: Optional[int] = None
) -> str:
    """
    Execute a service with given parameters.
    
    Args:
        client: ToreroClient instance
        name: Name of the service to execute
        parameters: Parameters to pass to the service
        async_execution: Whether to execute asynchronously
        timeout: Timeout in seconds
        
    Returns:
        JSON string containing execution result
    """
    try:
        result = await client.execute_service(
            name,
            parameters,
            async_execution=async_execution,
            timeout=timeout
        )
        return json.dumps(result, indent=2)
    except ToreroAPIError as e:
        return f"Error executing service '{name}': {e}"
    except Exception as e:
        logger.exception(f"Unexpected error executing service '{name}'")
        return f"Unexpected error: {e}"


async def get_execution_status(client: ToreroClient, execution_id: str) -> str:
    """
    Get the status of a service execution.
    
    Args:
        client: ToreroClient instance
        execution_id: ID of the execution to check
        
    Returns:
        JSON string containing execution status
    """
    try:
        result = await client.get_execution_status(execution_id)
        return json.dumps(result, indent=2)
    except ToreroAPIError as e:
        return f"Error getting execution status for '{execution_id}': {e}"
    except Exception as e:
        logger.exception(f"Unexpected error getting execution status for '{execution_id}'")
        return f"Unexpected error: {e}"


async def list_executions(
    client: ToreroClient,
    service_name: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100
) -> str:
    """
    List service executions with optional filtering.
    
    Args:
        client: ToreroClient instance
        service_name: Filter by service name
        status: Filter by execution status
        limit: Maximum number of executions to return
        
    Returns:
        JSON string containing list of executions
    """
    try:
        result = await client.list_executions(
            service_name=service_name,
            status=status,
            limit=limit
        )
        return json.dumps(result, indent=2)
    except ToreroAPIError as e:
        return f"Error listing executions: {e}"
    except Exception as e:
        logger.exception("Unexpected error listing executions")
        return f"Unexpected error: {e}"


async def cancel_execution(client: ToreroClient, execution_id: str) -> str:
    """
    Cancel a running service execution.
    
    Args:
        client: ToreroClient instance
        execution_id: ID of the execution to cancel
        
    Returns:
        JSON string containing cancellation result
    """
    try:
        result = await client.cancel_execution(execution_id)
        return json.dumps(result, indent=2)
    except ToreroAPIError as e:
        return f"Error cancelling execution '{execution_id}': {e}"
    except Exception as e:
        logger.exception(f"Unexpected error cancelling execution '{execution_id}'")
        return f"Unexpected error: {e}"


async def stream_execution_logs(client: ToreroClient, execution_id: str, follow: bool = True) -> str:
    """
    Stream execution logs.
    
    Args:
        client: ToreroClient instance
        execution_id: ID of the execution to stream logs for
        follow: Whether to follow the logs
        
    Returns:
        Log entries as they come
    """
    try:
        logs = []
        async for log_entry in client.stream_execution_logs(execution_id, follow=follow):
            logs.append(log_entry)
        return json.dumps(logs, indent=2)
    except ToreroAPIError as e:
        return f"Error streaming logs for execution '{execution_id}': {e}"
    except Exception as e:
        logger.exception(f"Unexpected error streaming logs for execution '{execution_id}'")
        return f"Unexpected error: {e}"
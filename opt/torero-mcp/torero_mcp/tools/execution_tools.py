"""service execution tools for torero mcp server."""

import json
import logging
from typing import Any, Dict, Optional

from ..executor import ToreroExecutorError, ToreroExecutor

logger = logging.getLogger(__name__)


async def execute_ansible_playbook(executor: ToreroExecutor, service_name: str) -> str:
    """
    execute an ansible-playbook service.
    
    args:
        executor: toreroexecutor instance
        service_name: name of the ansible-playbook service to execute
        
    returns:
        json string containing execution result with return_code, stdout, stderr, and timing information
    """
    try:
        result = await executor.run_ansible_playbook_service(service_name)
        return json.dumps(result, indent=2)
    except ToreroExecutorError as e:
        return f"error executing ansible-playbook service '{service_name}': {e}"
    except Exception as e:
        logger.exception(f"unexpected error executing ansible-playbook service '{service_name}'")
        return f"unexpected error: {e}"


async def execute_python_script(executor: ToreroExecutor, service_name: str) -> str:
    """
    execute a python-script service.
    
    args:
        executor: toreroexecutor instance
        service_name: name of the python-script service to execute
        
    returns:
        json string containing execution result with return_code, stdout, stderr, and timing information
    """
    try:
        result = await executor.run_python_script_service(service_name)
        return json.dumps(result, indent=2)
    except ToreroExecutorError as e:
        return f"error executing python-script service '{service_name}': {e}"
    except Exception as e:
        logger.exception(f"unexpected error executing python-script service '{service_name}'")
        return f"unexpected error: {e}"


async def execute_opentofu_plan_apply(executor: ToreroExecutor, service_name: str) -> str:
    """
    execute an opentofu plan service to apply infrastructure changes.
    
    args:
        executor: toreroexecutor instance
        service_name: name of the opentofu plan service to apply
        
    returns:
        json string containing execution result with return_code, stdout, stderr, and timing information
    """
    try:
        result = await executor.run_opentofu_plan_apply_service(service_name)
        return json.dumps(result, indent=2)
    except ToreroExecutorError as e:
        return f"error executing opentofu plan apply service '{service_name}': {e}"
    except Exception as e:
        logger.exception(f"unexpected error executing opentofu plan apply service '{service_name}'")
        return f"unexpected error: {e}"


async def execute_opentofu_plan_destroy(executor: ToreroExecutor, service_name: str) -> str:
    """
    execute an opentofu plan service to destroy infrastructure resources.
    
    args:
        executor: toreroexecutor instance
        service_name: name of the opentofu plan service to destroy
        
    returns:
        json string containing execution result with return_code, stdout, stderr, and timing information
    """
    try:
        result = await executor.run_opentofu_plan_destroy_service(service_name)
        return json.dumps(result, indent=2)
    except ToreroExecutorError as e:
        return f"error executing opentofu plan destroy service '{service_name}': {e}"
    except Exception as e:
        logger.exception(f"unexpected error executing opentofu plan destroy service '{service_name}'")
        return f"unexpected error: {e}"


# note: the following functions were removed as they require api-level execution tracking
# which is not available through direct cli execution:
# - execute_service (generic service execution with parameters)  
# - get_execution_status (requires execution id tracking)
# - list_executions (requires execution database)
# - cancel_execution (requires execution tracking)
# - stream_execution_logs (requires execution tracking)
#
# direct service execution is available through the specific service type functions above
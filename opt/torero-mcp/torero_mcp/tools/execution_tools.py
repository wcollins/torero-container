"""service execution tools for torero mcp server."""

import json
import logging
from typing import Any, Dict, Optional

from ..executor import ToreroExecutorError, ToreroExecutor

logger = logging.getLogger(__name__)


async def execute_ansible_playbook(
    executor: ToreroExecutor, 
    service_name: str,
    set_vars: Optional[str] = None,
    set_secrets: Optional[str] = None,
    use_decorator: bool = False
) -> str:
    """
    Execute an Ansible playbook service with comprehensive parameter support.
    
    Args:
        executor: ToreroExecutor instance
        service_name: Name of the ansible-playbook service to execute
        set_vars: JSON string of key=value pairs for --set parameters (e.g., '{"interface": "0/0/0", "environment": "production"}')
        set_secrets: Comma-separated list of secret names for --set-secret parameters (e.g., "db_password,api_key")
        use_decorator: Whether to display possible inputs via decorator (--use flag)
        
    Returns:
        JSON string containing execution result with return_code, stdout, stderr, and timing information
    """
    try:
        # parse set_vars if provided
        parsed_set_vars = None
        if set_vars:
            try:
                parsed_set_vars = json.loads(set_vars)
                if not isinstance(parsed_set_vars, dict):
                    return f"error: set_vars must be a JSON object with key-value pairs"
            except json.JSONDecodeError as e:
                return f"error: invalid JSON in set_vars: {e}"
        
        # parse set_secrets if provided
        parsed_set_secrets = None
        if set_secrets:
            parsed_set_secrets = [secret.strip() for secret in set_secrets.split(",") if secret.strip()]
        
        result = await executor.run_ansible_playbook_service(
            service_name,
            set_vars=parsed_set_vars,
            set_secrets=parsed_set_secrets,
            use_decorator=use_decorator
        )
        return json.dumps(result, indent=2)
    except ToreroExecutorError as e:
        return f"error executing ansible-playbook service '{service_name}': {e}"
    except Exception as e:
        logger.exception(f"unexpected error executing ansible-playbook service '{service_name}'")
        return f"unexpected error: {e}"


async def execute_python_script(
    executor: ToreroExecutor, 
    service_name: str,
    set_vars: Optional[str] = None,
    set_secrets: Optional[str] = None,
    use_decorator: bool = False
) -> str:
    """
    Execute a Python script service with comprehensive parameter support.
    
    Args:
        executor: ToreroExecutor instance
        service_name: Name of the python-script service to execute
        set_vars: JSON string of key=value pairs for --set parameters (e.g., '{"device": "10.0.0.1", "commands": "[\"show ver\"]"}')
        set_secrets: Comma-separated list of secret names for --set-secret parameters (e.g., "db_password,api_key")
        use_decorator: Whether to display possible inputs via decorator (--use flag)
        
    Returns:
        JSON string containing execution result with return_code, stdout, stderr, and timing information
    """
    try:
        # parse set_vars if provided
        parsed_set_vars = None
        if set_vars:
            try:
                parsed_set_vars = json.loads(set_vars)
                if not isinstance(parsed_set_vars, dict):
                    return f"error: set_vars must be a JSON object with key-value pairs"
            except json.JSONDecodeError as e:
                return f"error: invalid JSON in set_vars: {e}"
        
        # parse set_secrets if provided
        parsed_set_secrets = None
        if set_secrets:
            parsed_set_secrets = [secret.strip() for secret in set_secrets.split(",") if secret.strip()]
        
        result = await executor.run_python_script_service(
            service_name,
            set_vars=parsed_set_vars,
            set_secrets=parsed_set_secrets,
            use_decorator=use_decorator
        )
        return json.dumps(result, indent=2)
    except ToreroExecutorError as e:
        return f"error executing python-script service '{service_name}': {e}"
    except Exception as e:
        logger.exception(f"unexpected error executing python-script service '{service_name}'")
        return f"unexpected error: {e}"


async def execute_opentofu_plan_apply(
    executor: ToreroExecutor, 
    service_name: str,
    set_vars: Optional[str] = None,
    set_secrets: Optional[str] = None,
    state: Optional[str] = None,
    state_out: Optional[str] = None,
    use_decorator: bool = False
) -> str:
    """
    Execute an OpenTofu plan service to apply infrastructure changes with comprehensive parameter support.
    
    Args:
        executor: ToreroExecutor instance
        service_name: Name of the opentofu plan service to apply
        set_vars: JSON string of key=value pairs for --set parameters (e.g., '{"server_name": "web01", "region": "us-west-2"}')
        set_secrets: Comma-separated list of secret names for --set-secret parameters (e.g., "aws_secret,db_password")
        state: State file to utilize - JSON string or file path with @ prefix (e.g., "@opentofu.tfstate")
        state_out: Path to write the resulting state file (e.g., "@updated_state.tfstate")
        use_decorator: Whether to display possible inputs via decorator (--use flag)
        
    Returns:
        JSON string containing execution result with return_code, stdout, stderr, and timing information
    """
    try:
        # parse set_vars if provided
        parsed_set_vars = None
        if set_vars:
            try:
                parsed_set_vars = json.loads(set_vars)
                if not isinstance(parsed_set_vars, dict):
                    return f"error: set_vars must be a JSON object with key-value pairs"
            except json.JSONDecodeError as e:
                return f"error: invalid JSON in set_vars: {e}"
        
        # parse set_secrets if provided
        parsed_set_secrets = None
        if set_secrets:
            parsed_set_secrets = [secret.strip() for secret in set_secrets.split(",") if secret.strip()]
        
        result = await executor.run_opentofu_plan_apply_service(
            service_name,
            set_vars=parsed_set_vars,
            set_secrets=parsed_set_secrets,
            state=state,
            state_out=state_out,
            use_decorator=use_decorator
        )
        return json.dumps(result, indent=2)
    except ToreroExecutorError as e:
        return f"error executing opentofu plan apply service '{service_name}': {e}"
    except Exception as e:
        logger.exception(f"unexpected error executing opentofu plan apply service '{service_name}'")
        return f"unexpected error: {e}"


async def execute_opentofu_plan_destroy(
    executor: ToreroExecutor, 
    service_name: str,
    set_vars: Optional[str] = None,
    set_secrets: Optional[str] = None,
    state: Optional[str] = None,
    state_out: Optional[str] = None,
    use_decorator: bool = False
) -> str:
    """
    Execute an OpenTofu plan service to destroy infrastructure resources with comprehensive parameter support.
    
    Args:
        executor: ToreroExecutor instance
        service_name: Name of the opentofu plan service to destroy
        set_vars: JSON string of key=value pairs for --set parameters (e.g., '{"server_name": "web01", "region": "us-west-2"}')
        set_secrets: Comma-separated list of secret names for --set-secret parameters (e.g., "aws_secret,db_password")
        state: State file to utilize - JSON string or file path with @ prefix (e.g., "@opentofu.tfstate")
        state_out: Path to write the resulting state file (e.g., "@updated_state.tfstate")
        use_decorator: Whether to display possible inputs via decorator (--use flag)
        
    Returns:
        JSON string containing execution result with return_code, stdout, stderr, and timing information
    """
    try:
        # parse set_vars if provided
        parsed_set_vars = None
        if set_vars:
            try:
                parsed_set_vars = json.loads(set_vars)
                if not isinstance(parsed_set_vars, dict):
                    return f"error: set_vars must be a JSON object with key-value pairs"
            except json.JSONDecodeError as e:
                return f"error: invalid JSON in set_vars: {e}"
        
        # parse set_secrets if provided
        parsed_set_secrets = None
        if set_secrets:
            parsed_set_secrets = [secret.strip() for secret in set_secrets.split(",") if secret.strip()]
        
        result = await executor.run_opentofu_plan_destroy_service(
            service_name,
            set_vars=parsed_set_vars,
            set_secrets=parsed_set_secrets,
            state=state,
            state_out=state_out,
            use_decorator=use_decorator
        )
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
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
    Execute an Ansible playbook service with variable and secret injection.

    Use this function for direct execution of Ansible playbook services when you
    know the exact parameters. For more flexible input handling, consider using
    execute_service_unified() instead.

    Args:
        executor: ToreroExecutor instance for CLI interaction
        service_name: Name of the ansible-playbook service to execute (must exist in torero)
        set_vars: JSON object string containing key-value pairs for Ansible extra variables
                  Format: '{"variable_name": "value", "another_var": 123}'
                  These become --set parameters in the torero CLI
                  Example: '{"target_host": "web01", "port": 8080, "debug": true}'
        set_secrets: Comma-separated list of secret names to inject as variables
                     Format: "secret1,secret2,secret3"
                     These become --set-secret parameters in the torero CLI
                     Example: "ansible_password,vault_token,api_key"
        use_decorator: If True, displays possible inputs defined by service decorator
                       Uses the --use flag to show decorator-defined parameters

    Returns:
        JSON string containing execution result:
        {
            "return_code": 0,           # 0 for success, non-zero for failure
            "stdout": "...",            # Standard output from the playbook
            "stderr": "...",            # Standard error output
            "start_time": "...",        # ISO format timestamp
            "end_time": "...",          # ISO format timestamp
            "elapsed_time": 45.2        # Execution duration in seconds
        }

        On error, returns: "error: <description>"

    Examples:
        # Simple execution with variables
        result = await execute_ansible_playbook(
            executor,
            "configure-network",
            set_vars='{"interface": "eth0", "ip": "10.0.0.1"}'
        )

        # With secrets injection
        result = await execute_ansible_playbook(
            executor,
            "deploy-app",
            set_vars='{"version": "1.2.3", "environment": "staging"}',
            set_secrets="db_password,api_token"
        )
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
    Execute a Python script service with environment variables and secrets.

    Use this function for direct execution of Python script services when you
    know the exact parameters. For more flexible input handling, consider using
    execute_service_unified() instead.

    Args:
        executor: ToreroExecutor instance for CLI interaction
        service_name: Name of the python-script service to execute (must exist in torero)
        set_vars: JSON object string containing key-value pairs for script environment variables
                  Format: '{"variable_name": "value", "another_var": 123}'
                  These become --set parameters passed as environment variables to the script
                  Example: '{"API_URL": "https://api.example.com", "TIMEOUT": 30, "DEBUG": true}'
        set_secrets: Comma-separated list of secret names to inject as environment variables
                     Format: "secret1,secret2,secret3"
                     These become --set-secret parameters in the torero CLI
                     Example: "api_key,database_url,auth_token"
        use_decorator: If True, displays possible inputs defined by service decorator
                       Uses the --use flag to show decorator-defined parameters

    Returns:
        JSON string containing execution result:
        {
            "return_code": 0,           # Script exit code (0 for success)
            "stdout": "...",            # Script standard output
            "stderr": "...",            # Script standard error
            "start_time": "...",        # ISO format timestamp
            "end_time": "...",          # ISO format timestamp
            "elapsed_time": 12.5        # Execution duration in seconds
        }

        On error, returns: "error: <description>"

    Examples:
        # Simple script execution with environment variables
        result = await execute_python_script(
            executor,
            "data-processor",
            set_vars='{"INPUT_FILE": "/data/input.csv", "OUTPUT_FORMAT": "json"}'
        )

        # With secrets for API authentication
        result = await execute_python_script(
            executor,
            "api-sync",
            set_vars='{"ENDPOINT": "https://api.example.com", "BATCH_SIZE": 100}',
            set_secrets="api_key,api_secret"
        )
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
    Apply infrastructure changes using an OpenTofu/Terraform plan service.

    Executes the 'apply' operation for OpenTofu services, creating or updating
    infrastructure resources. For destruction, use execute_opentofu_plan_destroy().
    For more flexible input handling, consider using execute_service_unified() instead.

    Args:
        executor: ToreroExecutor instance for CLI interaction
        service_name: Name of the opentofu-plan service to apply (must exist in torero)
        set_vars: JSON object string containing Terraform/OpenTofu variables
                  Format: '{"variable_name": "value", "another_var": 123}'
                  These become --set parameters (not --var) in the torero CLI
                  Example: '{"instance_type": "t3.medium", "count": 3, "environment": "prod"}'
        set_secrets: Comma-separated list of secret names for sensitive variables
                     Format: "secret1,secret2,secret3"
                     These become --set-secret parameters in the torero CLI
                     Example: "aws_access_key,aws_secret_key,database_password"
        state: Path to existing state file to use as input
               Use @ prefix for paths relative to /home/admin/data
               Example: "@states/current.tfstate" or "/absolute/path/terraform.tfstate"
        state_out: Path where the updated state file should be written
                   Use @ prefix for paths relative to /home/admin/data
                   Example: "@states/updated.tfstate"
        use_decorator: If True, displays possible inputs defined by service decorator
                       Uses the --use flag to show decorator-defined parameters

    Returns:
        JSON string containing execution result:
        {
            "return_code": 0,           # 0 for successful apply
            "stdout": "...",            # Terraform apply output including resource changes
            "stderr": "...",            # Error messages if any
            "start_time": "...",        # ISO format timestamp
            "end_time": "...",          # ISO format timestamp
            "elapsed_time": 180.5       # Execution duration in seconds
        }

        On error, returns: "error: <description>"

    Examples:
        # Simple infrastructure deployment
        result = await execute_opentofu_plan_apply(
            executor,
            "web-infrastructure",
            set_vars='{"region": "us-east-1", "instance_count": 2}'
        )

        # With state management and secrets
        result = await execute_opentofu_plan_apply(
            executor,
            "production-deploy",
            set_vars='{"environment": "production", "vpc_cidr": "10.0.0.0/16"}',
            set_secrets="aws_access_key,aws_secret_key",
            state="@states/prod.tfstate",
            state_out="@states/prod-updated.tfstate"
        )

    Important:
        - OpenTofu commands have unique structure: 'torero run service opentofu-plan apply <name>'
        - The 'apply' operation comes BEFORE the service name in the command
        - State files should be managed carefully to avoid conflicts
        - Always backup state files before major operations
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
    Destroy infrastructure resources using an OpenTofu/Terraform plan service.

    Executes the 'destroy' operation for OpenTofu services, removing all managed
    infrastructure resources. Use with caution as this operation is destructive.
    For creating/updating resources, use execute_opentofu_plan_apply().
    For more flexible input handling, consider using execute_service_unified() instead.

    Args:
        executor: ToreroExecutor instance for CLI interaction
        service_name: Name of the opentofu-plan service to destroy (must exist in torero)
        set_vars: JSON object string containing Terraform/OpenTofu variables
                  Format: '{"variable_name": "value", "another_var": 123}'
                  These become --set parameters (not --var) in the torero CLI
                  Variables may be needed to properly identify resources to destroy
                  Example: '{"environment": "staging", "region": "us-west-2"}'
        set_secrets: Comma-separated list of secret names for sensitive variables
                     Format: "secret1,secret2,secret3"
                     Required for authenticating with cloud providers
                     Example: "aws_access_key,aws_secret_key"
        state: Path to state file containing resources to destroy
               Use @ prefix for paths relative to /home/admin/data
               This file must exist and contain the resources to be destroyed
               Example: "@states/staging.tfstate" or "/absolute/path/terraform.tfstate"
        state_out: Path where the empty state file should be written after destruction
                   Use @ prefix for paths relative to /home/admin/data
                   Example: "@states/staging-destroyed.tfstate"
        use_decorator: If True, displays possible inputs defined by service decorator
                       Uses the --use flag to show decorator-defined parameters

    Returns:
        JSON string containing execution result:
        {
            "return_code": 0,           # 0 for successful destruction
            "stdout": "...",            # Terraform destroy output showing removed resources
            "stderr": "...",            # Error messages if any
            "start_time": "...",        # ISO format timestamp
            "end_time": "...",          # ISO format timestamp
            "elapsed_time": 120.5       # Execution duration in seconds
        }

        On error, returns: "error: <description>"

    Examples:
        # Destroy staging environment
        result = await execute_opentofu_plan_destroy(
            executor,
            "staging-infrastructure",
            set_vars='{"environment": "staging"}',
            state="@states/staging.tfstate",
            state_out="@states/staging-destroyed.tfstate"
        )

        # Destroy with authentication secrets
        result = await execute_opentofu_plan_destroy(
            executor,
            "temporary-resources",
            set_vars='{"project": "temp-test", "region": "us-east-1"}',
            set_secrets="aws_access_key,aws_secret_key",
            state="@states/temp.tfstate"
        )

    Important:
        - OpenTofu commands have unique structure: 'torero run service opentofu-plan destroy <name>'
        - The 'destroy' operation comes BEFORE the service name in the command
        - This operation is DESTRUCTIVE and cannot be undone
        - Always verify the state file contains only resources you want to destroy
        - Consider backing up the state file before destruction
        - The operation will show a plan of what will be destroyed before proceeding
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


async def execute_service_unified(
    executor: ToreroExecutor,
    name: str,
    inputs: Optional[str] = None,
    input_file: Optional[str] = None,
    operation: Optional[str] = None,
    validate_only: bool = False
) -> str:
    """
    Execute any torero service with unified input handling and validation.

    This is the recommended method for executing services as it provides:
    - Automatic input discovery from service manifests
    - Input validation before execution
    - Support for input files in multiple formats
    - Consistent interface across all service types

    The function automatically determines the service type and handles the specific
    command structure required (e.g., OpenTofu requires operation before service name).

    Args:
        executor: ToreroExecutor instance for CLI interaction
        name: Name of the service to execute (must exist in torero database)
        inputs: JSON string containing service inputs with structure:
                {
                    "variables": {"key": "value", ...},  # Service variables
                    "secrets": ["secret_name", ...],     # Secret references (not values)
                    "files": {"file_key": "path", ...}   # File paths
                }
                Example: '{"variables": {"environment": "prod", "count": 3}, "secrets": ["api_key"]}'
        input_file: Path to input file containing service configuration:
                    - Supports: .yaml, .yml, .json, .toml, .tfvars formats
                    - Use @ prefix for paths relative to /home/admin/data
                    - Example: "@inputs/production.yaml" or "/absolute/path/config.json"
        operation: Specifically for OpenTofu services - either "apply" or "destroy"
                   - Required for opentofu-plan service type
                   - Ignored for other service types
                   - Defaults to manifest setting or "apply" if not specified
        validate_only: If True, validates inputs against manifest without executing
                       Returns validation result with resolved inputs for review

    Returns:
        JSON string with one of these structures:

        On successful execution:
        {
            "return_code": 0,
            "stdout": "...",
            "stderr": "...",
            "start_time": "2024-01-15T10:00:00Z",
            "end_time": "2024-01-15T10:05:00Z",
            "elapsed_time": 300.5
        }

        On validation (validate_only=True):
        {
            "valid": true,
            "resolved_inputs": {...},
            "service": "service-name",
            "service_type": "ansible-playbook"
        }

        On error:
        "error: <error message>"

    Examples:
        # Simple execution with inline variables
        result = await execute_service_unified(
            executor,
            name="web-deployment",
            inputs='{"variables": {"environment": "production", "replicas": 3}}'
        )

        # Using input file with OpenTofu destroy operation
        result = await execute_service_unified(
            executor,
            name="infrastructure",
            operation="destroy",
            input_file="@inputs/staging-teardown.yaml"
        )

        # Validate inputs before execution
        validation = await execute_service_unified(
            executor,
            name="backup-service",
            inputs='{"variables": {"target": "database"}}',
            validate_only=True
        )

        # Complex example with variables, secrets, and files
        result = await execute_service_unified(
            executor,
            name="deployment",
            inputs='''{
                "variables": {
                    "environment": "prod",
                    "region": "us-east-1",
                    "instance_type": "t3.medium"
                },
                "secrets": ["aws_access_key", "db_password"],
                "files": {
                    "config": "@configs/production.conf",
                    "state": "@states/current.tfstate"
                }
            }'''
        )

    Notes:
        - Input manifests are automatically discovered from /home/admin/data/schemas/<name>.yaml
        - Validation checks required fields, types, and constraints defined in manifests
        - Secret values are never stored; only secret names/references are used
        - File paths with @ prefix are relative to /home/admin/data
        - For OpenTofu services, the operation parameter is critical for destroy operations
    """
    try:
        from ..input_resolver import UnifiedInputResolver

        # parse user inputs if provided
        user_inputs = json.loads(inputs) if inputs else {}

        # get service details
        service_details = await executor.get_service_details(name)
        if not service_details:
            return f"error: service '{name}' not found"

        service_type = service_details.get("type")
        if not service_type:
            return f"error: unable to determine service type for '{name}'"

        # create resolver and resolve inputs
        resolver = UnifiedInputResolver(executor)
        try:
            resolved_inputs = resolver.resolve_inputs(
                name, service_type, user_inputs, input_file
            )
        except ValueError as e:
            return f"error: {e}"

        # validation only mode
        if validate_only:
            return json.dumps({
                "valid": True,
                "resolved_inputs": resolved_inputs,
                "service": name,
                "service_type": service_type
            }, indent=2)

        # convert to CLI arguments
        cli_args = resolver.to_cli_args(service_type, resolved_inputs, operation)

        # execute service based on type
        if service_type == "opentofu-plan":
            # determine operation
            if not operation:
                # use default from manifest or fallback to "apply"
                manifest = resolver.input_manager.discover_inputs(name)
                operation = manifest.get("execution", {}).get("default_operation", "apply") if manifest else "apply"

            # build command for opentofu (operation comes before service name)
            result = await executor.execute_command(
                ["run", "service", service_type, operation, name] + cli_args
            )
        else:
            # build command for other service types
            result = await executor.execute_command(
                ["run", "service", service_type, name] + cli_args
            )

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.exception(f"unexpected error in execute_service_unified for '{name}'")
        return f"unexpected error: {e}"
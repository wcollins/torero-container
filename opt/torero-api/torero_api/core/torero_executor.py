"""
torero executor module

This module provides functions to interact with the torero CLI.
It's responsible for executing torero commands and parsing their output.
"""

import json
import logging
import subprocess
import shutil
from typing import List, Tuple, Optional
from datetime import datetime

from torero_api.models.service import Service
from torero_api.models.database import DatabaseImportOptions

# Configure logging
logger = logging.getLogger(__name__)

# torero command
TORERO_COMMAND = 'torero'

def check_torero_available() -> Tuple[bool, str]:
    """
    Check if torero is available in the system PATH.
    
    Returns:
        Tuple[bool, str]: A tuple containing a boolean indicating whether torero is available
                        and a message with more details
    """

    # Check if torero executable is in PATH
    torero_path = shutil.which(TORERO_COMMAND)
    if not torero_path:
        return False, f"{TORERO_COMMAND} executable not found in PATH"
    
    # Check if torero can be executed
    try:
        result = subprocess.run(
            [TORERO_COMMAND, "version"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5
        )
        
        if result.returncode != 0:
            return False, f"{TORERO_COMMAND} command failed: {result.stderr.strip()}"
        
        return True, f"{TORERO_COMMAND} is available"
    except subprocess.TimeoutExpired:
        return False, f"{TORERO_COMMAND} command timed out"
    except Exception as e:
        return False, f"Error checking {TORERO_COMMAND}: {str(e)}"

def check_torero_version() -> str:
    """
    Get the version of torero installed.
    
    Returns:
        str: The version of torero, or "unknown" if it couldn't be determined
    """
    try:
        result = subprocess.run(
            [TORERO_COMMAND, "version"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5
        )
        
        if result.returncode != 0:
            return "unknown"
        
        # Parse the version from the output
        # Example output: "torero version 1.3.1"
        output_lines = result.stdout.strip().split("\n")
        for line in output_lines:
            if line.startswith("torero"):
                parts = line.split()
                if len(parts) >= 3:
                    return parts[2]
        
        return "unknown"
    except Exception:
        return "unknown"

def get_services() -> List[Service]:
    """
    Execute torero CLI command to get all services.
    
    Makes a system call to 'torero get services --raw' to retrieve the raw JSON
    data of all registered services, then parses and validates this data into
    Service objects.
    
    Returns:
        List[Service]: List of Service objects representing all registered torero services.
    
    Raises:
        RuntimeError: If the torero command fails or returns invalid JSON.
    """
    command = [TORERO_COMMAND, "get", "services", "--raw"]
    logger.debug(f"Executing command: {' '.join(command)}")
    
    try:
        # Run the torero command
        proc = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=30
        )

        if proc.returncode != 0:
            error_msg = f"torero error: {proc.stderr.strip()}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        try:
            # Parse the output as JSON
            raw_output = json.loads(proc.stdout)
            
            # Handle the case where services are wrapped in an "items" array
            if isinstance(raw_output, dict) and "items" in raw_output:
                services_data = raw_output["items"]
            elif isinstance(raw_output, list):
                services_data = raw_output
            else:
                raise RuntimeError(f"Unexpected JSON structure from torero: {type(raw_output)}")
            
            # Create Service objects
            services = [Service(**svc) for svc in services_data]
            logger.debug(f"Retrieved {len(services)} services from torero")
            return services
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON from torero: {e}"
            logger.error(error_msg)
            logger.debug(f"Raw output: {proc.stdout[:1000]}...")  # Log first 1000 chars
            raise RuntimeError(error_msg)
            
    except subprocess.TimeoutExpired:
        error_msg = "torero command timed out"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    except Exception as e:
        logger.exception(f"Unexpected error executing torero command: {str(e)}")
        raise RuntimeError(f"Failed to execute torero command: {str(e)}")

def get_service_by_name(name: str) -> Optional[Service]:
    """
    Get a specific service by name.
    
    Args:
        name: The name of the service to retrieve
        
    Returns:
        Optional[Service]: The service if found, None otherwise
        
    Raises:
        RuntimeError: If the torero command fails or returns invalid JSON.
    """
    services = get_services()
    
    for service in services:
        if service.name == name:
            return service
    
    return None

def describe_service(name: str) -> Optional[dict]:
    """
    Get detailed description of a specific service by name.
    
    Makes a system call to 'torero describe service <n> --raw' to retrieve
    detailed information about a specific service.
    
    Args:
        name: The name of the service to describe
        
    Returns:
        Optional[dict]: Detailed service information if found, None otherwise
        
    Raises:
        RuntimeError: If the torero command fails or returns invalid JSON.
    """
    command = [TORERO_COMMAND, "describe", "service", name, "--raw"]
    logger.debug(f"Executing command: {' '.join(command)}")
    
    try:
        # Run the torero command
        proc = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=30
        )

        if proc.returncode != 0:
            error_msg = f"torero error: {proc.stderr.strip()}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        try:
            # Parse the output as JSON
            raw_output = json.loads(proc.stdout)
            
            # The describe command returns an array, return the full response
            if isinstance(raw_output, list):
                logger.debug(f"Retrieved detailed description for service: {name}")
                return raw_output
            elif isinstance(raw_output, dict):
                logger.debug(f"Retrieved detailed description for service: {name}")
                return [raw_output]  # Wrap single dict in array for consistency
            else:
                logger.warning(f"Unexpected response format for service description: {name}")
                return None
                
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON from torero describe: {e}"
            logger.error(error_msg)
            logger.debug(f"Raw output: {proc.stdout[:1000]}...")
            raise RuntimeError(error_msg)
            
    except subprocess.TimeoutExpired:
        error_msg = "torero describe command timed out"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    except Exception as e:
        logger.exception(f"Unexpected error executing torero describe command: {str(e)}")
        raise RuntimeError(f"Failed to execute torero describe command: {str(e)}")

def get_decorators() -> List['Decorator']:
    """
    Execute torero CLI command to get all decorators.
    
    Makes a system call to 'torero get decorators --raw' to retrieve the raw JSON
    data of all registered decorators, then parses and validates this data into
    Decorator objects.
    
    Returns:
        List[Decorator]: List of Decorator objects representing all registered torero decorators.
    
    Raises:
        RuntimeError: If the torero command fails or returns invalid JSON.
    """
    command = [TORERO_COMMAND, "get", "decorators", "--raw"]
    logger.debug(f"Executing command: {' '.join(command)}")
    
    try:
        # Run the torero command
        proc = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=30
        )

        if proc.returncode != 0:
            error_msg = f"torero error: {proc.stderr.strip()}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        try:
            # Parse the output as JSON
            raw_output = json.loads(proc.stdout)
            
            # Handle the case where decorators are wrapped in a "decorators" array
            if isinstance(raw_output, dict) and "decorators" in raw_output:
                decorators_data = raw_output["decorators"]
            elif isinstance(raw_output, dict) and "items" in raw_output:
                decorators_data = raw_output["items"]
            elif isinstance(raw_output, list):
                decorators_data = raw_output
            else:
                raise RuntimeError(f"Unexpected JSON structure from torero: {type(raw_output)}")
            
            # Create Decorator objects
            from torero_api.models.decorator import Decorator
            decorators = []
            
            for decorator_data in decorators_data:
                # Map torero CLI fields to Decorator model fields
                # The CLI uses "schema" but our model expects "parameters"
                decorator_info = {
                    "name": decorator_data.get("name", "unknown"),
                    "description": decorator_data.get("description") or None,
                    "type": decorator_data.get("type", "decorator"),  # Use provided type or default to "decorator"
                    "parameters": decorator_data.get("schema") or decorator_data.get("parameters"),  # Map schema to parameters, fallback to parameters
                    "registries": {
                        "metadata": {
                            "id": decorator_data.get("id"),
                            "created": decorator_data.get("created"),
                            "tags": decorator_data.get("tags", [])
                        }
                    }
                }
                
                decorators.append(Decorator(**decorator_info))
            
            logger.debug(f"Retrieved {len(decorators)} decorators from torero")
            return decorators
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON from torero: {e}"
            logger.error(error_msg)
            logger.debug(f"Raw output: {proc.stdout[:1000]}...")
            raise RuntimeError(error_msg)
            
    except subprocess.TimeoutExpired:
        error_msg = "torero command timed out"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    except Exception as e:
        logger.exception(f"Unexpected error executing torero command: {str(e)}")
        raise RuntimeError(f"Failed to execute torero command: {str(e)}")

def get_decorator_by_name(name: str) -> Optional['Decorator']:
    """
    Get a specific decorator by name.
    
    Args:
        name: The name of the decorator to retrieve
        
    Returns:
        Optional[Decorator]: The decorator if found, None otherwise
        
    Raises:
        RuntimeError: If the torero command fails or returns invalid JSON.
    """
    decorators = get_decorators()
    
    for decorator in decorators:
        if decorator.name == name:
            return decorator
    
    return None

def get_repositories() -> List['Repository']:
    """
    Execute torero CLI command to get all repositories.
    
    Makes a system call to 'torero get repositories --raw' to retrieve the raw JSON
    data of all registered repositories, then parses and validates this data into
    Repository objects.
    
    Returns:
        List[Repository]: List of Repository objects representing all registered torero repositories.
    
    Raises:
        RuntimeError: If the torero command fails or returns invalid JSON.
    """
    command = [TORERO_COMMAND, "get", "repositories", "--raw"]
    logger.debug(f"Executing command: {' '.join(command)}")
    
    try:
        # Run the torero command
        proc = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=30
        )

        if proc.returncode != 0:
            error_msg = f"torero error: {proc.stderr.strip()}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        try:
            # Parse the output as JSON
            raw_output = json.loads(proc.stdout)
            
            # Handle the case where repositories are wrapped in an "items" array
            if isinstance(raw_output, dict) and "items" in raw_output:
                repositories_data = raw_output["items"]
            elif isinstance(raw_output, list):
                repositories_data = raw_output
            else:
                raise RuntimeError(f"Unexpected JSON structure from torero: {type(raw_output)}")
            
            # Create Repository objects
            from torero_api.models.repository import Repository
            repositories = []
            
            for repo_data in repositories_data:
                # Map torero CLI fields to Repository model fields
                repository_info = {
                    "name": repo_data.get("name", "unknown"),
                    "description": repo_data.get("description"),
                    "type": repo_data.get("type") or ("git" if repo_data.get("url", "").endswith(".git") else "unknown"),
                    "location": repo_data.get("url") or repo_data.get("location", "unknown"),
                    "metadata": {
                        "reference": repo_data.get("reference"),
                        "tags": repo_data.get("tags", []),
                        "private_key_name": repo_data.get("private_key_name", "")
                    }
                }
                
                repositories.append(Repository(**repository_info))
            
            logger.debug(f"Retrieved {len(repositories)} repositories from torero")
            return repositories
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON from torero: {e}"
            logger.error(error_msg)
            logger.debug(f"Raw output: {proc.stdout[:1000]}...")
            raise RuntimeError(error_msg)
            
    except subprocess.TimeoutExpired:
        error_msg = "torero command timed out"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    except Exception as e:
        logger.exception(f"Unexpected error executing torero command: {str(e)}")
        raise RuntimeError(f"Failed to execute torero command: {str(e)}")

def get_repository_by_name(name: str) -> Optional['Repository']:
    """
    Get a specific repository by name.
    
    Args:
        name: The name of the repository to retrieve
        
    Returns:
        Optional[Repository]: The repository if found, None otherwise
        
    Raises:
        RuntimeError: If the torero command fails.
    """
    repositories = get_repositories()
    
    for repository in repositories:
        if repository.name == name:
            return repository
    
    return None

def get_secrets() -> List['Secret']:
    """
    Execute torero CLI command to get all secrets.
    
    Makes a system call to 'torero get secrets --raw' to retrieve the raw JSON
    data of all registered secrets, then parses and validates this data into
    Secret objects.
    
    Returns:
        List[Secret]: List of Secret objects representing all registered torero secrets.
    
    Raises:
        RuntimeError: If the torero command fails or returns invalid JSON.
    """
    command = [TORERO_COMMAND, "get", "secrets", "--raw"]
    logger.debug(f"Executing command: {' '.join(command)}")
    
    try:
        # Run the torero command
        proc = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=30
        )

        if proc.returncode != 0:
            error_msg = f"torero error: {proc.stderr.strip()}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        try:
            # Parse the output as JSON
            raw_output = json.loads(proc.stdout)
            
            # Handle the case where secrets are wrapped in an "items" array
            if isinstance(raw_output, dict) and "items" in raw_output:
                secrets_data = raw_output["items"]
            elif isinstance(raw_output, list):
                secrets_data = raw_output
            else:
                raise RuntimeError(f"Unexpected JSON structure from torero: {type(raw_output)}")
            
            # Create Secret objects
            from torero_api.models.secret import Secret
            secrets = [Secret(**secret) for secret in secrets_data]
            logger.debug(f"Retrieved {len(secrets)} secrets from torero")
            return secrets
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON from torero: {e}"
            logger.error(error_msg)
            logger.debug(f"Raw output: {proc.stdout[:1000]}...")
            raise RuntimeError(error_msg)
            
    except subprocess.TimeoutExpired:
        error_msg = "torero command timed out"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    except Exception as e:
        logger.exception(f"Unexpected error executing torero command: {str(e)}")
        raise RuntimeError(f"Failed to execute torero command: {str(e)}")

def get_secret_by_name(name: str) -> Optional['Secret']:
    """
    Get a specific secret by name.
    
    Args:
        name: The name of the secret to retrieve
        
    Returns:
        Optional[Secret]: The secret if found, None otherwise
        
    Raises:
        RuntimeError: If the torero command fails or returns invalid JSON.
    """
    secrets = get_secrets()
    
    for secret in secrets:
        if secret.name == name:
            return secret
    
    return None

def run_ansible_playbook_service(name: str, **kwargs) -> dict:
    """
    Execute an Ansible playbook service using torero.
    
    Makes a system call to 'torero run service ansible-playbook <name> --raw'
    to run an Ansible playbook service and return its execution results.
    
    Args:
        name: The name of the Ansible playbook service to run
        **kwargs: Additional parameters to pass to the service
        
    Returns:
        dict: Execution results including return code, stdout, stderr, and timing information
        
    Raises:
        RuntimeError: If the torero command fails or returns invalid JSON.
    """
    command = [TORERO_COMMAND, "run", "service", "ansible-playbook", name, "--raw"]
    
    # Add any additional parameters as command arguments
    for key, value in kwargs.items():
        if value is not None:
            command.append(f"--{key}={value}")
    
    logger.debug(f"Executing command: {' '.join(command)}")
    
    try:
        # Run the torero command
        proc = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=300  # 5 minute timeout for playbook execution
        )

        try:
            # Parse the output as JSON
            result = json.loads(proc.stdout)
            logger.debug(f"Successfully executed Ansible playbook service: {name}")
            return result
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON from torero run service: {e}"
            logger.error(error_msg)
            logger.debug(f"Raw output: {proc.stdout[:1000]}...")  # Log first 1000 chars
            
            # If we can't parse JSON but have a non-zero return code, it's likely an error
            if proc.returncode != 0:
                error_msg = f"Service execution failed with code {proc.returncode}: {proc.stderr.strip()}"
            
            raise RuntimeError(error_msg)
            
    except subprocess.TimeoutExpired:
        error_msg = "Service execution timed out after 5 minutes"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    except Exception as e:
        logger.exception(f"Unexpected error executing service: {str(e)}")
        raise RuntimeError(f"Failed to execute service: {str(e)}")

def run_python_script_service(name: str, **kwargs) -> dict:
    """
    Execute a Python script service using torero.
    
    Makes a system call to 'torero run service python-script <name> --raw'
    to run a Python script service and return its execution results.
    
    Args:
        name: The name of the Python script service to run
        **kwargs: Additional parameters to pass to the service
        
    Returns:
        dict: Execution results including return code, stdout, stderr, and timing information
        
    Raises:
        RuntimeError: If the torero command fails or returns invalid JSON.
    """
    command = [TORERO_COMMAND, "run", "service", "python-script", name, "--raw"]
    
    # Add any additional parameters as command arguments
    for key, value in kwargs.items():
        if value is not None:
            command.append(f"--{key}={value}")
    
    logger.debug(f"Executing command: {' '.join(command)}")
    
    try:
        # Run the torero command
        proc = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=300  # 5 minute timeout for script execution
        )

        try:
            # Parse the output as JSON
            result = json.loads(proc.stdout)
            logger.debug(f"Successfully executed Python script service: {name}")
            return result
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON from torero run service: {e}"
            logger.error(error_msg)
            logger.debug(f"Raw output: {proc.stdout[:1000]}...")  # Log first 1000 chars
            
            # If we can't parse JSON but have a non-zero return code, it's likely an error
            if proc.returncode != 0:
                error_msg = f"Service execution failed with code {proc.returncode}: {proc.stderr.strip()}"
            
            raise RuntimeError(error_msg)
            
    except subprocess.TimeoutExpired:
        error_msg = "Service execution timed out after 5 minutes"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    except Exception as e:
        logger.exception(f"Unexpected error executing service: {str(e)}")
        raise RuntimeError(f"Failed to execute service: {str(e)}")

def run_opentofu_plan_apply_service(name: str, **kwargs) -> dict:
    """
    Execute an OpenTofu plan apply service using torero.
    
    Makes a system call to 'torero run service opentofu-plan apply <name> --raw'
    to apply an OpenTofu plan service and return its execution results.
    
    Args:
        name: The name of the OpenTofu plan service to apply
        **kwargs: Additional parameters to pass to the service
        
    Returns:
        dict: Execution results including return code, stdout, stderr, and timing information
        
    Raises:
        RuntimeError: If the torero command fails or returns invalid JSON.
    """
    command = [TORERO_COMMAND, "run", "service", "opentofu-plan", "apply", name, "--raw"]
    
    # Add any additional parameters as command arguments
    for key, value in kwargs.items():
        if value is not None:
            command.append(f"--{key}={value}")
    
    logger.debug(f"Executing command: {' '.join(command)}")
    
    try:
        # Run the torero command
        proc = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=600  # 10 minute timeout for plan apply
        )

        try:
            # Parse the output as JSON
            result = json.loads(proc.stdout)
            logger.debug(f"Successfully applied OpenTofu plan service: {name}")
            return result
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON from torero run service: {e}"
            logger.error(error_msg)
            logger.debug(f"Raw output: {proc.stdout[:1000]}...")  # Log first 1000 chars
            
            # If we can't parse JSON but have a non-zero return code, it's likely an error
            if proc.returncode != 0:
                error_msg = f"Service execution failed with code {proc.returncode}: {proc.stderr.strip()}"
            
            raise RuntimeError(error_msg)
            
    except subprocess.TimeoutExpired:
        error_msg = "Service execution timed out after 10 minutes"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    except Exception as e:
        logger.exception(f"Unexpected error executing service: {str(e)}")
        raise RuntimeError(f"Failed to execute service: {str(e)}")

def describe_repository(name: str) -> Optional[dict]:
    """
    Get detailed description of a specific repository by name.
    
    Makes a system call to 'torero describe repository <name> --raw' to retrieve
    detailed information about a specific repository.
    
    Args:
        name: The name of the repository to describe
        
    Returns:
        Optional[dict]: Detailed repository information if found, None otherwise
        
    Raises:
        RuntimeError: If the torero command fails or returns invalid JSON.
    """
    command = [TORERO_COMMAND, "describe", "repository", name, "--raw"]
    logger.debug(f"Executing command: {' '.join(command)}")
    
    try:
        # Run the torero command
        proc = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=30
        )

        if proc.returncode != 0:
            error_msg = f"torero error: {proc.stderr.strip()}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        try:
            # Parse the output as JSON
            raw_output = json.loads(proc.stdout)
            
            # The describe command returns detailed info, return the full response
            logger.debug(f"Retrieved detailed description for repository: {name}")
            return raw_output
                
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON from torero describe: {e}"
            logger.error(error_msg)
            logger.debug(f"Raw output: {proc.stdout[:1000]}...")
            raise RuntimeError(error_msg)
            
    except subprocess.TimeoutExpired:
        error_msg = "torero describe command timed out"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    except Exception as e:
        logger.exception(f"Unexpected error executing torero describe command: {str(e)}")
        raise RuntimeError(f"Failed to execute torero describe command: {str(e)}")

def describe_secret(name: str) -> Optional[dict]:
    """
    Get detailed description of a specific secret by name.
    
    Makes a system call to 'torero describe secret <name> --raw' to retrieve
    detailed information about a specific secret.
    
    Args:
        name: The name of the secret to describe
        
    Returns:
        Optional[dict]: Detailed secret information if found, None otherwise
        
    Raises:
        RuntimeError: If the torero command fails or returns invalid JSON.
    """
    command = [TORERO_COMMAND, "describe", "secret", name, "--raw"]
    logger.debug(f"Executing command: {' '.join(command)}")
    
    try:
        # Run the torero command
        proc = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=30
        )

        if proc.returncode != 0:
            error_msg = f"torero error: {proc.stderr.strip()}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        try:
            # Parse the output as JSON
            raw_output = json.loads(proc.stdout)
            
            # The describe command returns detailed info, return the full response
            logger.debug(f"Retrieved detailed description for secret: {name}")
            return raw_output
                
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON from torero describe: {e}"
            logger.error(error_msg)
            logger.debug(f"Raw output: {proc.stdout[:1000]}...")
            raise RuntimeError(error_msg)
            
    except subprocess.TimeoutExpired:
        error_msg = "torero describe command timed out"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    except Exception as e:
        logger.exception(f"Unexpected error executing torero describe command: {str(e)}")
        raise RuntimeError(f"Failed to execute torero describe command: {str(e)}")

def get_registries() -> List['Registry']:
    """
    Execute torero CLI command to get all registries.
    
    Makes a system call to 'torero get registries --raw' to retrieve the raw JSON
    data of all registered registries, then parses and validates this data into
    Registry objects.
    
    Returns:
        List[Registry]: List of Registry objects representing all registered torero registries.
    
    Raises:
        RuntimeError: If the torero command fails or returns invalid JSON.
    """
    command = [TORERO_COMMAND, "get", "registries", "--raw"]
    logger.debug(f"Executing command: {' '.join(command)}")
    
    try:
        # Run the torero command
        proc = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=30
        )

        if proc.returncode != 0:
            error_msg = f"torero error: {proc.stderr.strip()}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        try:
            # Parse the output as JSON
            raw_output = json.loads(proc.stdout)
            
            # Handle the case where registries are wrapped in an "items" array
            if isinstance(raw_output, dict) and "items" in raw_output:
                registries_data = raw_output["items"]
            elif isinstance(raw_output, list):
                registries_data = raw_output
            else:
                raise RuntimeError(f"Unexpected JSON structure from torero: {type(raw_output)}")
            
            # Create Registry objects
            from torero_api.models.registry import Registry
            registries = []
            
            for reg_data in registries_data:
                # Map torero CLI fields to Registry model fields
                registry_info = {
                    "name": reg_data.get("name", "unknown"),
                    "description": reg_data.get("description"),
                    "type": reg_data.get("type", "unknown"),
                    "url": reg_data.get("url", ""),
                    "metadata": {
                        "id": reg_data.get("id"),
                        "created": reg_data.get("created"),
                        "tags": reg_data.get("tags", []),
                        "credentials": reg_data.get("credentials")
                    }
                }
                
                registries.append(Registry(**registry_info))
            
            logger.debug(f"Retrieved {len(registries)} registries from torero")
            return registries
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON from torero: {e}"
            logger.error(error_msg)
            logger.debug(f"Raw output: {proc.stdout[:1000]}...")
            raise RuntimeError(error_msg)
            
    except subprocess.TimeoutExpired:
        error_msg = "torero command timed out"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    except Exception as e:
        logger.exception(f"Unexpected error executing torero command: {str(e)}")
        raise RuntimeError(f"Failed to execute torero command: {str(e)}")

def get_registry_by_name(name: str) -> Optional['Registry']:
    """
    Get a specific registry by name.
    
    Args:
        name: The name of the registry to retrieve
        
    Returns:
        Optional[Registry]: The registry if found, None otherwise
        
    Raises:
        RuntimeError: If the torero command fails or returns invalid JSON.
    """
    registries = get_registries()
    
    for registry in registries:
        if registry.name == name:
            return registry
    
    return None

def describe_decorator(name: str) -> Optional[dict]:
    """
    Get detailed description of a specific decorator by name.
    
    Makes a system call to 'torero describe decorator <name> --raw' to retrieve
    detailed information about a specific decorator.
    
    Args:
        name: The name of the decorator to describe
        
    Returns:
        Optional[dict]: Detailed decorator information if found, None otherwise
        
    Raises:
        RuntimeError: If the torero command fails or returns invalid JSON.
    """
    command = [TORERO_COMMAND, "describe", "decorator", name, "--raw"]
    logger.debug(f"Executing command: {' '.join(command)}")
    
    try:
        # Run the torero command
        proc = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=30
        )

        if proc.returncode != 0:
            error_msg = f"torero error: {proc.stderr.strip()}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        try:
            # Parse the output as JSON
            raw_output = json.loads(proc.stdout)
            
            # The describe command returns detailed info, return the full response
            logger.debug(f"Retrieved detailed description for decorator: {name}")
            return raw_output
                
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON from torero describe: {e}"
            logger.error(error_msg)
            logger.debug(f"Raw output: {proc.stdout[:1000]}...")
            raise RuntimeError(error_msg)
            
    except subprocess.TimeoutExpired:
        error_msg = "torero describe command timed out"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    except Exception as e:
        logger.exception(f"Unexpected error executing torero describe command: {str(e)}")
        raise RuntimeError(f"Failed to execute torero describe command: {str(e)}")

def run_opentofu_plan_destroy_service(name: str, **kwargs) -> dict:
    """
    Execute an OpenTofu plan destroy service using torero.
    
    Makes a system call to 'torero run service opentofu-plan destroy <name> --raw'
    to destroy resources managed by an OpenTofu plan service and return its execution results.
    
    Args:
        name: The name of the OpenTofu plan service to destroy
        **kwargs: Additional parameters to pass to the service
        
    Returns:
        dict: Execution results including return code, stdout, stderr, and timing information
        
    Raises:
        RuntimeError: If the torero command fails or returns invalid JSON.
    """
    command = [TORERO_COMMAND, "run", "service", "opentofu-plan", "destroy", name, "--raw"]
    
    # Add any additional parameters as command arguments
    for key, value in kwargs.items():
        if value is not None:
            command.append(f"--{key}={value}")
    
    logger.debug(f"Executing command: {' '.join(command)}")
    
    try:
        # Run the torero command
        proc = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=600
        )

        try:
            # Parse the output as JSON
            result = json.loads(proc.stdout)
            logger.debug(f"Successfully destroyed OpenTofu plan service: {name}")
            return result
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON from torero run service: {e}"
            logger.error(error_msg)
            logger.debug(f"Raw output: {proc.stdout[:1000]}...")
            
            # If we can't parse JSON but have a non-zero return code, it's likely an error
            if proc.returncode != 0:
                error_msg = f"Service execution failed with code {proc.returncode}: {proc.stderr.strip()}"
            
            raise RuntimeError(error_msg)
            
    except subprocess.TimeoutExpired:
        error_msg = "Service execution timed out after 10 minutes"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    except Exception as e:
        logger.exception(f"Unexpected error executing service: {str(e)}")
        raise RuntimeError(f"Failed to execute service: {str(e)}")

class ToreroError(Exception):
    """Custom exception for torero-related errors."""
    pass

async def execute_db_export(format: str = "yaml") -> dict:
    """
    Execute torero db export command.
    
    Makes a system call to 'torero db export --format <format> --raw' to export
    all services and resources.
    
    Args:
        format: The output format (json or yaml). Defaults to yaml.
    
    Returns:
        dict: The exported configuration data.
        
    Raises:
        ToreroError: If the export command fails.
    """
    command = [TORERO_COMMAND, "db", "export", "--format", format, "--raw"]
    logger.debug(f"Executing command: {' '.join(command)}")
    
    try:
        # Run the torero command
        proc = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=60
        )

        if proc.returncode != 0:
            error_msg = f"torero db export error: {proc.stderr.strip()}"
            logger.error(error_msg)
            raise ToreroError(error_msg)

        try:
            # For YAML format, the output might be a string
            if format == "yaml":
                # Return the raw YAML string
                return {"data": proc.stdout, "format": "yaml"}
            else:
                # Parse JSON output
                result = json.loads(proc.stdout)
                return result
        except json.JSONDecodeError as e:
            # If JSON parsing fails, return as string
            return {"data": proc.stdout, "format": format}
            
    except subprocess.TimeoutExpired:
        error_msg = "torero db export command timed out"
        logger.error(error_msg)
        raise ToreroError(error_msg)
    except Exception as e:
        logger.exception(f"Unexpected error executing db export: {str(e)}")
        raise ToreroError(f"Failed to execute db export: {str(e)}")

async def execute_db_import(file_path: str, options: DatabaseImportOptions) -> dict:
    """
    Execute torero db import command.
    
    Makes a system call to 'torero db import' with various options to import
    services and resources from a file or repository.
    
    Args:
        file_path: Path to the import file (local or within repository).
        options: Import options including repository, force, check, validate.
    
    Returns:
        dict: Import result including status and any conflicts or changes.
        
    Raises:
        ToreroError: If the import command fails.
    """
    command = [TORERO_COMMAND, "db", "import"]
    
    # Add repository options if specified
    if options.repository:
        command.extend(["--repository", options.repository])
        if options.reference:
            command.extend(["--reference", options.reference])
        if options.private_key:
            command.extend(["--private-key-name", options.private_key])
    
    # Add flags
    if options.force:
        command.append("--force")
    if options.check:
        command.append("--check")
    if options.validate_only:
        command.append("--validate")
    
    # Add file path
    command.append(file_path)
    
    # Always use raw output
    command.append("--raw")
    
    logger.debug(f"Executing command: {' '.join(command)}")
    
    try:
        # Run the torero command
        proc = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=120
        )

        # Import might return non-zero for conflicts, but still have useful output
        if proc.returncode != 0 and not proc.stdout:
            error_msg = f"torero db import error: {proc.stderr.strip()}"
            logger.error(error_msg)
            raise ToreroError(error_msg)

        try:
            # Parse the output as JSON
            if proc.stdout:
                result = json.loads(proc.stdout)
                return result
            else:
                # If no stdout but stderr has info, use that
                return {
                    "success": proc.returncode == 0,
                    "message": proc.stderr.strip() if proc.stderr else "Import completed"
                }
        except json.JSONDecodeError:
            # If not JSON, return structured response
            return {
                "success": proc.returncode == 0,
                "message": proc.stdout.strip() if proc.stdout else proc.stderr.strip()
            }
            
    except subprocess.TimeoutExpired:
        error_msg = "torero db import command timed out"
        logger.error(error_msg)
        raise ToreroError(error_msg)
    except Exception as e:
        logger.exception(f"Unexpected error executing db import: {str(e)}")
        raise ToreroError(f"Failed to execute db import: {str(e)}")
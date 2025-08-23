"""direct cli executor for torero commands."""

import json
import logging
import subprocess
import shutil
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# torero command
TORERO_COMMAND = 'torero'

class ToreroExecutorError(Exception):
    """custom exception for torero executor errors."""
    pass

class ToreroExecutor:
    """direct cli executor for torero commands."""
    
    def __init__(self, timeout: int = 30):
        """
        initialize the torero executor.
        
        args:
            timeout: default timeout for commands in seconds
        """
        self.timeout = timeout
        self.torero_command = TORERO_COMMAND
    
    def check_torero_available(self) -> Tuple[bool, str]:
        """
        check if torero is available in the system path.
        
        returns:
            tuple[bool, str]: availability status and message
        """
        torero_path = shutil.which(self.torero_command)
        if not torero_path:
            return False, f"{self.torero_command} executable not found in path"
        
        try:
            result = subprocess.run(
                [self.torero_command, "version"],
                capture_output=True,
                text=True,
                check=False,
                timeout=5
            )
            
            if result.returncode != 0:
                return False, f"{self.torero_command} command failed: {result.stderr.strip()}"
            
            return True, f"{self.torero_command} is available"
        except subprocess.TimeoutExpired:
            return False, f"{self.torero_command} command timed out"
        except Exception as e:
            return False, f"error checking {self.torero_command}: {str(e)}"
    
    def check_torero_version(self) -> str:
        """
        get the version of torero installed.
        
        returns:
            str: version of torero, or "unknown" if couldn't be determined
        """
        try:
            result = subprocess.run(
                [self.torero_command, "version"],
                capture_output=True,
                text=True,
                check=False,
                timeout=5
            )
            
            if result.returncode != 0:
                return "unknown"
            
            # parse version from output
            output_lines = result.stdout.strip().split("\n")
            for line in output_lines:
                if line.startswith("torero"):
                    parts = line.split()
                    if len(parts) >= 3:
                        return parts[2]
            
            return "unknown"
        except Exception:
            return "unknown"
    
    async def execute_command(
        self, 
        args: List[str], 
        timeout: Optional[int] = None,
        parse_json: bool = True
    ) -> Any:
        """
        execute torero command with given arguments.
        
        args:
            args: command arguments (without 'torero' prefix)
            timeout: command timeout (uses instance default if none)
            parse_json: whether to parse output as json
            
        returns:
            command output (parsed as json if parse_json=true)
            
        raises:
            toreroexecutorerror: if command fails
        """
        command = [self.torero_command] + args
        cmd_timeout = timeout or self.timeout
        
        logger.debug(f"executing command: {' '.join(command)}")
        
        try:
            proc = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                timeout=cmd_timeout
            )
            
            if proc.returncode != 0:
                error_msg = f"torero error: {proc.stderr.strip()}"
                logger.error(error_msg)
                raise ToreroExecutorError(error_msg)
            
            if parse_json:
                try:
                    return json.loads(proc.stdout)
                except json.JSONDecodeError as e:
                    error_msg = f"invalid json from torero: {e}"
                    logger.error(error_msg)
                    logger.debug(f"raw output: {proc.stdout[:1000]}...")
                    raise ToreroExecutorError(error_msg)
            else:
                return proc.stdout
                
        except subprocess.TimeoutExpired:
            error_msg = f"torero command timed out after {cmd_timeout}s"
            logger.error(error_msg)
            raise ToreroExecutorError(error_msg)
        except Exception as e:
            if isinstance(e, ToreroExecutorError):
                raise
            logger.exception(f"unexpected error executing torero command: {str(e)}")
            raise ToreroExecutorError(f"failed to execute torero command: {str(e)}")
    
    # service operations
    async def get_services(self) -> List[Dict[str, Any]]:
        """get all services."""
        raw_output = await self.execute_command(["get", "services", "--raw"])
        
        # handle different response formats
        if isinstance(raw_output, dict) and "items" in raw_output:
            return raw_output["items"]
        elif isinstance(raw_output, list):
            return raw_output
        else:
            raise ToreroExecutorError(f"unexpected json structure: {type(raw_output)}")
    
    async def get_service_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """get specific service by name."""
        services = await self.get_services()
        for service in services:
            if service.get("name") == name:
                return service
        return None
    
    async def describe_service(self, name: str) -> Optional[Dict[str, Any]]:
        """get detailed description of a service."""
        raw_output = await self.execute_command(["describe", "service", name, "--raw"])
        
        if isinstance(raw_output, list):
            return raw_output
        elif isinstance(raw_output, dict):
            return [raw_output]  # wrap for consistency
        else:
            return None
    
    # decorator operations
    async def get_decorators(self) -> List[Dict[str, Any]]:
        """get all decorators."""
        raw_output = await self.execute_command(["get", "decorators", "--raw"])
        
        if isinstance(raw_output, dict) and "decorators" in raw_output:
            return raw_output["decorators"]
        elif isinstance(raw_output, dict) and "items" in raw_output:
            return raw_output["items"]
        elif isinstance(raw_output, list):
            return raw_output
        else:
            raise ToreroExecutorError(f"unexpected json structure: {type(raw_output)}")
    
    async def describe_decorator(self, name: str) -> Optional[Dict[str, Any]]:
        """get detailed description of a decorator."""
        return await self.execute_command(["describe", "decorator", name, "--raw"])
    
    # repository operations
    async def get_repositories(self) -> List[Dict[str, Any]]:
        """get all repositories."""
        raw_output = await self.execute_command(["get", "repositories", "--raw"])
        
        if isinstance(raw_output, dict) and "items" in raw_output:
            return raw_output["items"]
        elif isinstance(raw_output, list):
            return raw_output
        else:
            raise ToreroExecutorError(f"unexpected json structure: {type(raw_output)}")
    
    async def describe_repository(self, name: str) -> Optional[Dict[str, Any]]:
        """get detailed description of a repository."""
        return await self.execute_command(["describe", "repository", name, "--raw"])
    
    # secret operations
    async def get_secrets(self) -> List[Dict[str, Any]]:
        """get all secrets."""
        raw_output = await self.execute_command(["get", "secrets", "--raw"])
        
        if isinstance(raw_output, dict) and "items" in raw_output:
            return raw_output["items"]
        elif isinstance(raw_output, list):
            return raw_output
        else:
            raise ToreroExecutorError(f"unexpected json structure: {type(raw_output)}")
    
    async def describe_secret(self, name: str) -> Optional[Dict[str, Any]]:
        """get detailed description of a secret."""
        return await self.execute_command(["describe", "secret", name, "--raw"])
    
    # registry operations
    async def get_registries(self) -> List[Dict[str, Any]]:
        """get all registries."""
        raw_output = await self.execute_command(["get", "registries", "--raw"])
        
        if isinstance(raw_output, dict) and "items" in raw_output:
            return raw_output["items"]
        elif isinstance(raw_output, list):
            return raw_output
        else:
            raise ToreroExecutorError(f"unexpected json structure: {type(raw_output)}")
    
    # service execution operations
    async def run_ansible_playbook_service(
        self, 
        name: str, 
        set_vars: Optional[Dict[str, str]] = None,
        set_secrets: Optional[List[str]] = None,
        use_decorator: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """execute ansible playbook service with full parameter support.
        
        args:
            name: service name
            set_vars: dict of key=value pairs for --set parameters
            set_secrets: list of secret names for --set-secret parameters
            use_decorator: whether to display possible inputs via decorator (--use flag)
            **kwargs: additional parameters for backward compatibility
        """
        command = ["run", "service", "ansible-playbook", name]
        
        # add --set parameters
        if set_vars:
            for key, value in set_vars.items():
                command.extend(["--set", f"{key}={value}"])
        
        # add --set-secret parameters
        if set_secrets:
            for secret in set_secrets:
                command.extend(["--set-secret", secret])
        
        # add --use flag
        if use_decorator:
            command.append("--use")
        
        # add --raw for consistent output format
        command.append("--raw")
        
        return await self.execute_command(command, timeout=300)  # 5 min timeout
    
    async def run_python_script_service(
        self,
        name: str,
        set_vars: Optional[Dict[str, str]] = None,
        set_secrets: Optional[List[str]] = None,
        use_decorator: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """execute python script service with full parameter support.
        
        args:
            name: service name
            set_vars: dict of key=value pairs for --set parameters
            set_secrets: list of secret names for --set-secret parameters
            use_decorator: whether to display possible inputs via decorator (--use flag)
            **kwargs: additional parameters for backward compatibility
        """
        command = ["run", "service", "python-script", name]
        
        # add --set parameters
        if set_vars:
            for key, value in set_vars.items():
                command.extend(["--set", f"{key}={value}"])
        
        # add --set-secret parameters
        if set_secrets:
            for secret in set_secrets:
                command.extend(["--set-secret", secret])
        
        # add --use flag
        if use_decorator:
            command.append("--use")
        
        # add --raw for consistent output format
        command.append("--raw")
        
        return await self.execute_command(command, timeout=300)
    
    async def run_opentofu_plan_apply_service(
        self,
        name: str,
        set_vars: Optional[Dict[str, str]] = None,
        set_secrets: Optional[List[str]] = None,
        state: Optional[str] = None,
        state_out: Optional[str] = None,
        use_decorator: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """execute opentofu plan apply service with full parameter support.
        
        args:
            name: service name
            set_vars: dict of key=value pairs for --set parameters
            set_secrets: list of secret names for --set-secret parameters
            state: state file to utilize (JSON or @file path)
            state_out: path to write resulting state file
            use_decorator: whether to display possible inputs via decorator (--use flag)
            **kwargs: additional parameters for backward compatibility
        """
        command = ["run", "service", "opentofu-plan", "apply", name]
        
        # add --set parameters
        if set_vars:
            for key, value in set_vars.items():
                command.extend(["--set", f"{key}={value}"])
        
        # add --set-secret parameters
        if set_secrets:
            for secret in set_secrets:
                command.extend(["--set-secret", secret])
        
        # add --state parameter
        if state:
            command.extend(["--state", state])
        
        # add --state-out parameter
        if state_out:
            command.extend(["--state-out", state_out])
        
        # add --use flag
        if use_decorator:
            command.append("--use")
        
        # add --raw for consistent output format
        command.append("--raw")
        
        return await self.execute_command(command, timeout=600)  # 10 min timeout
    
    async def run_opentofu_plan_destroy_service(
        self,
        name: str,
        set_vars: Optional[Dict[str, str]] = None,
        set_secrets: Optional[List[str]] = None,
        state: Optional[str] = None,
        state_out: Optional[str] = None,
        use_decorator: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """execute opentofu plan destroy service with full parameter support.
        
        args:
            name: service name
            set_vars: dict of key=value pairs for --set parameters
            set_secrets: list of secret names for --set-secret parameters
            state: state file to utilize (JSON or @file path)
            state_out: path to write resulting state file
            use_decorator: whether to display possible inputs via decorator (--use flag)
            **kwargs: additional parameters for backward compatibility
        """
        command = ["run", "service", "opentofu-plan", "destroy", name]
        
        # add --set parameters
        if set_vars:
            for key, value in set_vars.items():
                command.extend(["--set", f"{key}={value}"])
        
        # add --set-secret parameters
        if set_secrets:
            for secret in set_secrets:
                command.extend(["--set-secret", secret])
        
        # add --state parameter
        if state:
            command.extend(["--state", state])
        
        # add --state-out parameter
        if state_out:
            command.extend(["--state-out", state_out])
        
        # add --use flag
        if use_decorator:
            command.append("--use")
        
        # add --raw for consistent output format
        command.append("--raw")
        
        return await self.execute_command(command, timeout=600)  # 10 min timeout
    
    # database operations
    async def export_database(self, format: str = "yaml") -> Dict[str, Any]:
        """export services and resources to a file."""
        raw_output = await self.execute_command(["db", "export", "--format", format, "--raw"], timeout=60)
        
        if format == "yaml":
            # return raw yaml string
            return {"data": raw_output if isinstance(raw_output, str) else json.dumps(raw_output), "format": "yaml"}
        else:
            return raw_output
    
    async def import_database(
        self,
        file_path: str,
        repository: Optional[str] = None,
        reference: Optional[str] = None,
        private_key: Optional[str] = None,
        force: bool = False,
        check: bool = False,
        validate_only: bool = False
    ) -> Dict[str, Any]:
        """import resources/services from a file."""
        command = ["db", "import"]
        
        if repository:
            command.extend(["--repository", repository])
            if reference:
                command.extend(["--reference", reference])
            if private_key:
                command.extend(["--private-key-name", private_key])
        
        if force:
            command.append("--force")
        if check:
            command.append("--check")
        if validate_only:
            command.append("--validate")
        
        command.append(file_path)
        command.append("--raw")
        
        try:
            return await self.execute_command(command, timeout=120)
        except ToreroExecutorError as e:
            # import might return non-zero for conflicts but still have useful output
            # handle this case gracefully
            return {
                "success": False,
                "message": str(e)
            }
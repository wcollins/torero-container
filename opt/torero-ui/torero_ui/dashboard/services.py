"""services for interacting with torero cli."""

import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from dateutil import parser as date_parser
from django.conf import settings
from django.db import models, connection
from django.utils import timezone
from jsonschema import validate, ValidationError
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor

from .models import ServiceExecution, ServiceInfo, ExecutionQueue
from .input_resolver import InputResolver

# logger with fallback for initialization issues
def get_logger():
    try:
        return logging.getLogger(__name__)
    except:

        # fallback to basic logging if django logging not initialized
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__)

logger = get_logger()


class ToreroCliClient:
    """client for interacting with torero cli directly."""
    
    def __init__(self) -> None:
        self.torero_command = "torero"
        self.timeout = getattr(settings, 'TORERO_CLI_TIMEOUT', 30)
        
        # check if torero is available
        try:
            result = subprocess.run([self.torero_command, "version"], 
                                  capture_output=True, text=True, timeout=5, check=False)
            if result.returncode != 0:
                logger.warning(f"torero command may not be available: {result.stderr}")
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.error(f"torero command not found or not responding: {e}")
    
    def _execute_command(self, args: List[str]) -> Optional[Dict[str, Any]]:
        """execute torero cli command and return parsed json output."""
        command = [self.torero_command] + args + ["--raw"]
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False
            )
            
            if result.returncode == 0 and result.stdout:
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    logger.warning(f"failed to parse json from torero output: {result.stdout[:200]}")
                    logger.warning(f"command was: {' '.join(command)}")
                    return None
            else:
                logger.error(f"torero command failed: {' '.join(command)}")
                logger.error(f"return code: {result.returncode}")
                logger.error(f"stdout: {result.stdout[:500] if result.stdout else 'None'}")
                logger.error(f"stderr: {result.stderr[:500] if result.stderr else 'None'}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error(f"torero command timed out: {' '.join(command)}")
            return None
        except Exception as e:
            logger.error(f"failed to execute torero command: {e}")
            return None
    
    def get_services(self) -> List[Dict[str, Any]]:
        """get list of all services from torero cli."""

        data = self._execute_command(["get", "services"])
        if data and isinstance(data, dict) and "services" in data:
            return data["services"] if isinstance(data["services"], list) else []
        return []
    
    def get_service_details(self, service_name: str) -> Optional[Dict[str, Any]]:

        """get details for specific service from torero cli."""
        return self._execute_command(["describe", "service", service_name])
    
    def execute_service(self, service_name: str, service_type: str, **params: Any) -> Optional[Dict[str, Any]]:
        """execute a service via torero cli."""

        # extract special parameters
        operation = params.pop('operation', None)
        inputs = params.pop('inputs', None)
        input_file = params.pop('input_file', None)

        # build command based on service type
        if service_type == "ansible-playbook":
            command = ["run", "service", "ansible-playbook", service_name]
        elif service_type == "python-script":
            command = ["run", "service", "python-script", service_name]
        elif service_type == "opentofu-plan":
            # use provided operation or default to apply
            op = operation if operation in ['apply', 'destroy'] else 'apply'
            command = ["run", "service", "opentofu-plan", op, service_name]
        else:
            logger.error(f"unsupported service type: {service_type}")
            return None

        # resolve inputs and convert to CLI args
        if inputs or input_file:
            resolved_inputs = InputResolver.resolve_inputs(inputs, input_file)
            cli_args = InputResolver.to_cli_args(service_type, resolved_inputs)
            command.extend(cli_args)

        # add any remaining parameters
        for key, value in params.items():
            command.extend([f"--{key}", str(value)])
        
        logger.info(f"executing torero command: {' '.join(command)}")
        
        # quick connectivity check before executing
        try:
            version_check = subprocess.run([self.torero_command, "version"], 
                                         capture_output=True, text=True, timeout=5, check=False)
            if version_check.returncode != 0:
                logger.error(f"torero connectivity check failed before execution: {version_check.stderr}")
                return None
        except Exception as e:
            logger.error(f"torero connectivity check failed: {e}")
            return None
        
        result = self._execute_command(command)
        
        if result is None:
            logger.error(f"execution failed for service {service_name} (type: {service_type})")
        
        return result


class DataCollectionService:
    """service for collecting and storing torero execution data."""
    
    def __init__(self) -> None:
        self.cli_client = ToreroCliClient()
    
    def sync_services(self) -> None:
        """synchronize service information from torero cli."""
        services = self.cli_client.get_services()
        
        for service_data in services:
            service_name = service_data.get("name")
            if not service_name:
                continue
            
            # get detailed service info
            service_details = self.cli_client.get_service_details(service_name)
            if not service_details:
                continue
            
            # update or create service info
            service_info, created = ServiceInfo.objects.update_or_create(
                name=service_name,
                defaults={
                    "service_type": service_details.get("type", ""),
                    "description": service_details.get("description", ""),
                    "tags": service_details.get("tags", []),
                    "repository": service_details.get("repository", ""),
                    "config_data": service_details,
                }
            )
            
            if created:
                logger.info(f"created new service info: {service_name}")
            else:
                logger.debug(f"updated service info: {service_name}")
    
    def record_execution(
        self,
        service_name: str,
        service_type: str,
        execution_result: Dict[str, Any]
    ) -> ServiceExecution:
        """record service execution in database."""
        
        # parse execution data
        started_at = timezone.now()
        status = "success" if execution_result.get("return_code", 1) == 0 else "failed"
        
        # calculate duration if available
        duration_seconds = None
        if "execution_time" in execution_result:
            try:
                duration_seconds = float(execution_result["execution_time"])
            except (ValueError, TypeError):
                pass
        
        # create execution record
        execution = ServiceExecution.objects.create(
            service_name=service_name,
            service_type=service_type,
            status=status,
            started_at=started_at,
            completed_at=timezone.now(),
            duration_seconds=duration_seconds,
            stdout=execution_result.get("stdout", ""),
            stderr=execution_result.get("stderr", ""),
            return_code=execution_result.get("return_code"),
            execution_data=execution_result,
        )
        
        # update service statistics
        self._update_service_stats(service_name, status, started_at)
        
        return execution
    
    def record_api_execution(
        self,
        service_name: str,
        service_type: str,
        api_execution_result: Dict[str, Any]
    ) -> ServiceExecution:
        """record API execution result in database."""
        
        # parse execution data from API response
        start_time_str = api_execution_result.get("start_time")
        end_time_str = api_execution_result.get("end_time")
        
        if start_time_str:
            started_at = date_parser.parse(start_time_str)
        else:
            started_at = timezone.now()
            
        if end_time_str:
            completed_at = date_parser.parse(end_time_str)
        else:
            completed_at = timezone.now()
        
        status = "success" if api_execution_result.get("return_code", 1) == 0 else "failed"
        duration_seconds = api_execution_result.get("elapsed_time")
        
        # create execution record
        execution = ServiceExecution.objects.create(
            service_name=service_name,
            service_type=service_type,
            status=status,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=duration_seconds,
            stdout=api_execution_result.get("stdout", ""),
            stderr=api_execution_result.get("stderr", ""),
            return_code=api_execution_result.get("return_code"),
            execution_data=api_execution_result,
        )
        
        # update service statistics
        self._update_service_stats(service_name, status, started_at)
        
        return execution
    
    def _update_service_stats(self, service_name: str, status: str, execution_time: datetime) -> None:
        """update service execution statistics."""
        try:
            service_info = ServiceInfo.objects.get(name=service_name)
            service_info.last_execution = execution_time
            service_info.total_executions += 1
            
            if status == "success":
                service_info.success_count += 1
            else:
                service_info.failure_count += 1
            
            service_info.save()
        except ServiceInfo.DoesNotExist:
            logger.warning(f"service info not found for: {service_name}")
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """get aggregated statistics for dashboard."""
        total_services = ServiceInfo.objects.count()
        total_executions = ServiceExecution.objects.count()
        
        recent_executions = ServiceExecution.objects.filter(
            started_at__gte=timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        )
        
        success_count = recent_executions.filter(status="success").count()
        failure_count = recent_executions.filter(status="failed").count()
        
        success_rate = 0.0
        if total_executions > 0:
            total_success = ServiceExecution.objects.filter(status="success").count()
            success_rate = (total_success / total_executions) * 100
        
        avg_duration = None
        completed_executions = ServiceExecution.objects.filter(
            duration_seconds__isnull=False
        )
        if completed_executions.exists():
            from django.db.models import Avg
            avg_result = completed_executions.aggregate(avg_duration=Avg('duration_seconds'))
            avg_duration = avg_result['avg_duration']
        
        return {
            "total_services": total_services,
            "total_executions": total_executions,
            "recent_executions": recent_executions.count(),
            "success_count": success_count,
            "failure_count": failure_count,
            "success_rate": success_rate,
            "avg_duration_seconds": avg_duration,
        }


class ExecutionQueueService:
    """service for managing execution queue and progress tracking."""
    
    # class-level lock and executor to ensure single execution
    _executor = ThreadPoolExecutor(max_workers=1)  # only 1 worker for sequential execution
    _processing = False
    _lock = threading.Lock()
    
    def __init__(self):
        # don't create cli_client here - create fresh one per execution
        pass
        
    def add_to_queue(self, service_name: str, service_type: str,
                     operation: Optional[str] = None,
                     inputs: Optional[Dict] = None,
                     input_file: Optional[str] = None) -> ExecutionQueue:
        """add service to execution queue."""
        # calculate estimated duration from historical data
        avg_duration = ServiceExecution.objects.filter(
            service_name=service_name,
            status='success'
        ).aggregate(avg=models.Avg('duration_seconds'))['avg']
        
        # Try to use new fields, fall back to storing in execution_id if columns don't exist
        try:
            queue_item = ExecutionQueue.objects.create(
                service_name=service_name,
                service_type=service_type,
                operation=operation,
                inputs=inputs or {},
                input_file=input_file,
                estimated_duration=int(avg_duration) if avg_duration else None
            )
        except Exception as e:
            # Fallback: store inputs in execution_id field as JSON if new columns don't exist
            logger.warning(f"Failed to use new input fields, falling back to execution_id: {e}")
            execution_data = {}
            if inputs:
                execution_data['inputs'] = inputs
            if input_file:
                execution_data['input_file'] = input_file

            queue_item = ExecutionQueue.objects.create(
                service_name=service_name,
                service_type=service_type,
                operation=operation,
                execution_id=json.dumps(execution_data) if execution_data else None,
                estimated_duration=int(avg_duration) if avg_duration else None
            )
        
        # start processing queue if not already running
        self._ensure_queue_processor()
        return queue_item
    
    def _ensure_queue_processor(self):
        """ensure queue processor is running."""
        with self._lock:
            if not self._processing:
                self._processing = True
                self._executor.submit(self._process_queue_loop)
    
    def _process_queue_loop(self):
        """continuously process queue items one at a time."""
        try:
            while True:
                # close any stale db connections
                connection.close_if_unusable_or_obsolete()
                
                # check if there's anything to process
                next_item = ExecutionQueue.objects.filter(status=ExecutionQueue.QUEUED).first()
                if not next_item:
                    break  # no more items to process
                
                # mark as running
                next_item.status = ExecutionQueue.RUNNING
                next_item.started_at = timezone.now()
                next_item.save()
                
                # execute the service (blocking)
                self._execute_service_sync(next_item.id)
                
        finally:
            with self._lock:
                self._processing = False
            # close db connection when done
            connection.close()
    
    def _execute_service_sync(self, queue_item_id: int):
        """execute service synchronously."""
        try:
            # refresh from database to get latest state
            queue_item = ExecutionQueue.objects.get(id=queue_item_id)
            
            # create fresh CLI client for this execution
            cli_client = ToreroCliClient()
            
            # log execution start
            logger.info(f"starting execution: {queue_item.service_name} ({queue_item.service_type})")
            
            # execute via cli client with inputs
            # Extract inputs from queue item (handle both old and new schema)
            inputs = None
            input_file = None

            # Try to get from new fields first
            if hasattr(queue_item, 'inputs'):
                inputs = queue_item.inputs if queue_item.inputs else None
            if hasattr(queue_item, 'input_file'):
                input_file = queue_item.input_file if queue_item.input_file else None

            # Fallback: check execution_id field for JSON-encoded inputs
            if not inputs and not input_file and queue_item.execution_id:
                try:
                    execution_data = json.loads(queue_item.execution_id)
                    if isinstance(execution_data, dict):
                        inputs = execution_data.get('inputs')
                        input_file = execution_data.get('input_file')
                except (json.JSONDecodeError, AttributeError):
                    pass

            result = cli_client.execute_service(
                service_name=queue_item.service_name,
                service_type=queue_item.service_type,
                operation=queue_item.operation,
                inputs=inputs,
                input_file=input_file
            )
            
            # log execution result
            logger.info(f"execution result for {queue_item.service_name}: {result}")
            
            # update status based on result
            queue_item.status = ExecutionQueue.COMPLETED if result else ExecutionQueue.FAILED
            queue_item.completed_at = timezone.now()
            queue_item.save()
            
        except Exception as e:
            logger.error(f"error executing service (id={queue_item_id}): {e}")
            try:
                queue_item = ExecutionQueue.objects.get(id=queue_item_id)
                queue_item.status = ExecutionQueue.FAILED
                queue_item.completed_at = timezone.now()
                queue_item.save()
            except Exception as save_error:
                logger.error(f"failed to update queue item status: {save_error}")
    
    def cancel_execution(self, queue_id: int) -> bool:
        """cancel a queued execution (cannot cancel running due to CLI limitations)."""
        try:
            queue_item = ExecutionQueue.objects.get(id=queue_id)
            
            # can only cancel queued items - running items must complete
            if queue_item.status == ExecutionQueue.QUEUED:
                queue_item.status = ExecutionQueue.CANCELLED
                queue_item.completed_at = timezone.now()
                queue_item.save()
                return True
            return False
            
        except ExecutionQueue.DoesNotExist:
            return False
    
    def get_queue_status(self) -> Dict[str, Any]:
        """get current queue status."""
        running = ExecutionQueue.objects.filter(status=ExecutionQueue.RUNNING)
        queued = ExecutionQueue.objects.filter(status=ExecutionQueue.QUEUED)
        completed = ExecutionQueue.objects.filter(
            status__in=[ExecutionQueue.COMPLETED, ExecutionQueue.FAILED, ExecutionQueue.CANCELLED]
        ).order_by('-completed_at')[:10]
        
        return {
            'running': list(running.values()),
            'queued': list(queued.values()),
            'completed': list(completed.values()),
            'running_count': running.count(),
            'queued_count': queued.count(),
            'completed_count': completed.count()
        }


class ServiceInputManager:
    """manages service input manifests and validation."""

    def __init__(self):
        self.manifest_dir = Path("/home/admin/data/schemas")
        self.manifest_dir.mkdir(exist_ok=True, parents=True)
        self.cli_client = ToreroCliClient()

    def load_manifest(self, manifest_path: Path) -> Optional[Dict]:
        """load and parse a manifest file."""
        try:
            with open(manifest_path, 'r') as f:
                return yaml.safe_load(f)
        except (FileNotFoundError, yaml.YAMLError) as e:
            logger.error(f"failed to load manifest {manifest_path}: {e}")
            return None

    def save_manifest(self, service_name: str, manifest: Dict) -> bool:
        """save a manifest to file."""
        manifest_path = self.manifest_dir / f"{service_name}.yaml"
        try:
            with open(manifest_path, 'w') as f:
                yaml.dump(manifest, f, default_flow_style=False, sort_keys=False)
            return True
        except Exception as e:
            logger.error(f"failed to save manifest for {service_name}: {e}")
            return False

    def discover_inputs(self, service_name: str) -> Optional[Dict]:
        """discover inputs from manifest or service definition."""
        # 1. check for explicit manifest (try both .yaml and .yml extensions)
        for extension in ['.yaml', '.yml']:
            manifest_path = self.manifest_dir / f"{service_name}{extension}"
            if manifest_path.exists():
                return self.load_manifest(manifest_path)

        # 2. extract from service details
        service_details = self.cli_client.get_service_details(service_name)
        if service_details:
            # check for decorator-based inputs
            if service_details.get("decorator"):
                return self.extract_from_decorator(service_details["decorator"])

            # 3. generate from service type defaults
            service_type = service_details.get("type")
            return self.generate_default_inputs(service_name, service_type)

        return None

    def extract_from_decorator(self, decorator: Dict) -> Dict:
        """extract input definitions from service decorator."""
        # placeholder - would parse decorator metadata for input definitions
        manifest = {
            "service": {
                "decorator": decorator.get("name", "")
            },
            "inputs": {
                "variables": [],
                "secrets": [],
                "files": []
            }
        }

        # extract any parameters defined in decorator
        if decorator.get("parameters"):
            for param in decorator["parameters"]:
                manifest["inputs"]["variables"].append({
                    "name": param.get("name"),
                    "description": param.get("description", ""),
                    "type": param.get("type", "string"),
                    "required": param.get("required", False),
                    "default": param.get("default")
                })

        return manifest

    def generate_default_inputs(self, service_name: str, service_type: str) -> Dict:
        """generate default input manifest based on service type."""
        manifest = {
            "service": {
                "name": service_name,
                "type": service_type,
                "version": "1.0.0"
            },
            "inputs": {
                "variables": [],
                "secrets": [],
                "files": []
            },
            "execution": {
                "timeout": 300,
                "working_directory": "/home/admin"
            }
        }

        # add type-specific defaults
        if service_type == "ansible-playbook":
            manifest["inputs"]["variables"] = [
                {
                    "name": "inventory",
                    "description": "Ansible inventory file or host list",
                    "type": "string",
                    "required": False,
                    "default": "localhost,"
                }
            ]
        elif service_type == "opentofu-plan":
            manifest["execution"]["default_operation"] = "apply"
            manifest["inputs"]["files"] = [
                {
                    "name": "state_file",
                    "description": "Terraform state file",
                    "type": "tfstate",
                    "required": False,
                    "path": "@states/"
                }
            ]
        elif service_type == "python-script":
            manifest["inputs"]["variables"] = [
                {
                    "name": "debug",
                    "description": "Enable debug mode",
                    "type": "boolean",
                    "required": False,
                    "default": False
                }
            ]

        return manifest

    def validate_inputs(self, service_name: str, inputs: Dict) -> Tuple[bool, List[str]]:
        """validate inputs against service manifest."""
        manifest = self.discover_inputs(service_name)
        if not manifest:
            return True, []  # no manifest, skip validation

        errors = []

        # validate required variables
        for input_def in manifest.get("inputs", {}).get("variables", []):
            if input_def.get("required") and input_def["name"] not in inputs.get("variables", {}):
                errors.append(f"required input '{input_def['name']}' is missing")

            if input_def["name"] in inputs.get("variables", {}):
                value = inputs["variables"][input_def["name"]]
                validation_errors = self.validate_value(value, input_def)
                errors.extend(validation_errors)

        # validate required secrets
        for secret_def in manifest.get("inputs", {}).get("secrets", []):
            if secret_def.get("required") and secret_def["name"] not in inputs.get("secrets", []):
                errors.append(f"required secret '{secret_def['name']}' is missing")

        return len(errors) == 0, errors

    def validate_value(self, value: Any, input_def: Dict) -> List[str]:
        """validate a single value against its definition."""
        errors = []
        input_type = input_def.get("type", "string")
        input_name = input_def.get("name", "unknown")

        # type validation
        if input_type == "string":
            if not isinstance(value, str):
                errors.append(f"'{input_name}' must be a string")
            elif "validation" in input_def:
                validation = input_def["validation"]
                if "enum" in validation and value not in validation["enum"]:
                    errors.append(f"'{input_name}' must be one of: {validation['enum']}")
                if "min_length" in validation and len(value) < validation["min_length"]:
                    errors.append(f"'{input_name}' must be at least {validation['min_length']} characters")
                if "max_length" in validation and len(value) > validation["max_length"]:
                    errors.append(f"'{input_name}' must be at most {validation['max_length']} characters")

        elif input_type == "integer":
            try:
                int_value = int(value)
                if "validation" in input_def:
                    validation = input_def["validation"]
                    if "min" in validation and int_value < validation["min"]:
                        errors.append(f"'{input_name}' must be at least {validation['min']}")
                    if "max" in validation and int_value > validation["max"]:
                        errors.append(f"'{input_name}' must be at most {validation['max']}")
            except (ValueError, TypeError):
                errors.append(f"'{input_name}' must be an integer")

        elif input_type == "number":
            try:
                float_value = float(value)
                if "validation" in input_def:
                    validation = input_def["validation"]
                    if "min" in validation and float_value < validation["min"]:
                        errors.append(f"'{input_name}' must be at least {validation['min']}")
                    if "max" in validation and float_value > validation["max"]:
                        errors.append(f"'{input_name}' must be at most {validation['max']}")
            except (ValueError, TypeError):
                errors.append(f"'{input_name}' must be a number")

        elif input_type == "boolean":
            if not isinstance(value, bool):
                errors.append(f"'{input_name}' must be a boolean")

        elif input_type == "file":
            if not isinstance(value, str):
                errors.append(f"'{input_name}' must be a file path")
            elif not value.startswith("@"):
                # check if file exists (if not using @ notation)
                if not Path(value).exists():
                    errors.append(f"file '{value}' for '{input_name}' does not exist")

        return errors

    def get_input_schema(self, service_name: str) -> Dict:
        """get JSON schema for service inputs."""
        manifest = self.discover_inputs(service_name)
        if not manifest:
            return {}

        # convert manifest to JSON schema format
        schema = {
            "type": "object",
            "properties": {
                "variables": {
                    "type": "object",
                    "properties": {},
                    "required": []
                },
                "secrets": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "files": {
                    "type": "object",
                    "properties": {}
                }
            }
        }

        # add variable definitions
        for var_def in manifest.get("inputs", {}).get("variables", []):
            prop_schema = {"type": var_def.get("type", "string")}

            if "description" in var_def:
                prop_schema["description"] = var_def["description"]

            if "default" in var_def:
                prop_schema["default"] = var_def["default"]

            if "validation" in var_def:
                validation = var_def["validation"]
                if "enum" in validation:
                    prop_schema["enum"] = validation["enum"]
                if "min" in validation:
                    prop_schema["minimum"] = validation["min"]
                if "max" in validation:
                    prop_schema["maximum"] = validation["max"]

            schema["properties"]["variables"]["properties"][var_def["name"]] = prop_schema

            if var_def.get("required"):
                schema["properties"]["variables"]["required"].append(var_def["name"])

        return schema
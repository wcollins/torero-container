"""services for interacting with torero cli."""

import json
import logging
import subprocess
from datetime import datetime
from typing import Any, Dict, List, Optional

from dateutil import parser as date_parser
from django.conf import settings
from django.utils import timezone

from .models import ServiceExecution, ServiceInfo

logger = logging.getLogger(__name__)


class ToreroCliClient:
    """client for interacting with torero cli directly."""
    
    def __init__(self) -> None:
        self.torero_command = "torero"
        self.timeout = getattr(settings, 'TORERO_CLI_TIMEOUT', 30)
    
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
                    return None
            else:
                logger.error(f"torero command failed: {' '.join(command)}\nError: {result.stderr}")
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
        # build command based on service type
        if service_type == "ansible-playbook":
            command = ["run", "service", "ansible-playbook", service_name]
        elif service_type == "python-script":
            command = ["run", "service", "python-script", service_name]
        elif service_type == "opentofu-plan":
            command = ["run", "service", "opentofu-plan", service_name]
        else:
            logger.error(f"unsupported service type: {service_type}")
            return None
        
        # add any additional parameters
        for key, value in params.items():
            command.extend([f"--{key}", str(value)])
        
        return self._execute_command(command)


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
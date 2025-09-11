"""services for interacting with torero cli."""

import json
import logging
import subprocess
from datetime import datetime
from typing import Any, Dict, List, Optional

from dateutil import parser as date_parser
from django.conf import settings
from django.db import models, connection
from django.utils import timezone
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor

from .models import ServiceExecution, ServiceInfo, ExecutionQueue

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

        # extract operation parameter for opentofu
        operation = params.pop('operation', None)
        
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
        
        # add any additional parameters
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
        
    def add_to_queue(self, service_name: str, service_type: str, operation: Optional[str] = None) -> ExecutionQueue:
        """add service to execution queue."""
        # calculate estimated duration from historical data
        avg_duration = ServiceExecution.objects.filter(
            service_name=service_name,
            status='success'
        ).aggregate(avg=models.Avg('duration_seconds'))['avg']
        
        queue_item = ExecutionQueue.objects.create(
            service_name=service_name,
            service_type=service_type,
            operation=operation,
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
            
            # execute via cli client
            result = cli_client.execute_service(
                service_name=queue_item.service_name,
                service_type=queue_item.service_type,
                operation=queue_item.operation
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
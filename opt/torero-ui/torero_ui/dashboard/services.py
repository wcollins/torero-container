"""services for interacting with torero api."""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from dateutil import parser as date_parser
from django.conf import settings
from django.utils import timezone

from .models import ServiceExecution, ServiceInfo

logger = logging.getLogger(__name__)


class ToreroAPIClient:
    """client for interacting with torero api."""
    
    def __init__(self) -> None:
        self.base_url = settings.TORERO_API_BASE_URL.rstrip('/')
        self.timeout = settings.TORERO_API_TIMEOUT
        self.session = requests.Session()
    
    def _make_request(self, endpoint: str, method: str = "GET", **kwargs: Any) -> Optional[Dict[str, Any]]:
        """make http request to torero api."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"torero api request failed: {url} - {e}")
            return None
    
    def get_services(self) -> List[Dict[str, Any]]:
        """get list of all services."""
        data = self._make_request("/v1/services/")
        return data if isinstance(data, list) else []
    
    def get_service_details(self, service_name: str) -> Optional[Dict[str, Any]]:
        """get details for specific service."""
        return self._make_request(f"/v1/services/{service_name}")
    
    def execute_service(self, service_name: str, service_type: str, **params: Any) -> Optional[Dict[str, Any]]:
        """execute a service and return execution data."""
        endpoint_map = {
            "ansible-playbook": f"/v1/execution/ansible-playbook/{service_name}",
            "python-script": f"/v1/execution/python-script/{service_name}",
            "opentofu-plan": f"/v1/execution/opentofu-plan/{service_name}/apply",
        }
        
        endpoint = endpoint_map.get(service_type)
        if not endpoint:
            logger.error(f"unsupported service type: {service_type}")
            return None
        
        return self._make_request(endpoint, method="POST", json=params)


class DataCollectionService:
    """service for collecting and storing torero execution data."""
    
    def __init__(self) -> None:
        self.api_client = ToreroAPIClient()
    
    def sync_services(self) -> None:
        """synchronize service information from torero api."""
        services = self.api_client.get_services()
        
        for service_data in services:
            service_name = service_data.get("name")
            if not service_name:
                continue
            
            # get detailed service info
            service_details = self.api_client.get_service_details(service_name)
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
"""views for torero dashboard."""

import json
import logging
from typing import Any, Dict

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView

from .models import ServiceExecution, ServiceInfo
from .services import DataCollectionService, ToreroCliClient

# logger with fallback for initialization issues
def get_logger():
    try:
        return logging.getLogger(__name__)
    except:

        # fallback to basic logging if django logging not initialized
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__)

logger = get_logger()


class DashboardView(TemplateView):
    """main dashboard view."""
    
    template_name = "dashboard/index.html"
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        
        data_service = DataCollectionService()
        
        # get dashboard statistics
        stats = data_service.get_dashboard_stats()
        
        # get recent executions
        recent_executions = ServiceExecution.objects.select_related().order_by('-started_at')[:20]
        
        # get service information
        services = ServiceInfo.objects.all().order_by('name')
        
        # get latest execution per service
        latest_executions = {}
        for service in services:
            latest = ServiceExecution.objects.filter(
                service_name=service.name
            ).order_by('-started_at').first()
            if latest:
                latest_executions[service.name] = latest
        
        context.update({
            'stats': stats,
            'recent_executions': recent_executions,
            'services': services,
            'latest_executions': latest_executions,
            'refresh_interval': settings.DASHBOARD_REFRESH_INTERVAL,
        })
        
        return context


@require_http_methods(["GET"])
def api_dashboard_data(request):
    """api endpoint for dashboard data."""
    data_service = DataCollectionService()
    
    # get fresh statistics
    stats = data_service.get_dashboard_stats()
    
    # get recent executions
    recent_executions = ServiceExecution.objects.select_related().order_by('-started_at')[:20]
    executions_data = []
    
    for execution in recent_executions:
        executions_data.append({
            'id': execution.id,
            'service_name': execution.service_name,
            'service_type': execution.service_type,
            'status': execution.status,
            'started_at': execution.started_at.isoformat(),
            'duration_seconds': execution.duration_seconds,
            'execution_time_display': execution.execution_time_display,
        })
    
    # get service status
    services = ServiceInfo.objects.all().order_by('name')
    services_data = []
    
    for service in services:
        latest_execution = ServiceExecution.objects.filter(
            service_name=service.name
        ).order_by('-started_at').first()
        
        service_data = {
            'name': service.name,
            'service_type': service.service_type,
            'total_executions': service.total_executions,
            'success_count': service.success_count,
            'failure_count': service.failure_count,
            'success_rate': service.success_rate,
            'last_execution': service.last_execution.isoformat() if service.last_execution else None,
            'latest_status': latest_execution.status if latest_execution else None,
            'latest_duration': latest_execution.duration_seconds if latest_execution else None,
        }
        services_data.append(service_data)
    
    return JsonResponse({
        'stats': stats,
        'recent_executions': executions_data,
        'services': services_data,
        'timestamp': {'status': 'healthy', 'torero_available': True},
    })


@require_http_methods(["POST"])
def api_sync_services(request):
    """api endpoint to trigger service sync."""

    try:
        data_service = DataCollectionService()
        data_service.sync_services()
        return JsonResponse({'status': 'success', 'message': 'services synchronized'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@require_http_methods(["GET"])
def api_execution_details(request, execution_id):
    """api endpoint for execution details."""

    try:
        execution = ServiceExecution.objects.get(id=execution_id)
        
        data = {
            'id': execution.id,
            'service_name': execution.service_name,
            'service_type': execution.service_type,
            'status': execution.status,
            'started_at': execution.started_at.isoformat(),
            'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
            'duration_seconds': execution.duration_seconds,
            'stdout': execution.stdout,
            'stderr': execution.stderr,
            'return_code': execution.return_code,
            'execution_data': execution.execution_data,
            'service_metadata': execution.service_metadata,
        }
        
        return JsonResponse(data)
    except ServiceExecution.DoesNotExist:
        return JsonResponse({'error': 'execution not found'}, status=404)


@csrf_exempt
@require_http_methods(["POST"])
def api_record_execution(request):
    """API endpoint to record execution data from torero-api."""

    try:
        data = json.loads(request.body)
        service_name = data.get('service_name')
        service_type = data.get('service_type')
        execution_data = data.get('execution_data')
        
        if not all([service_name, service_type, execution_data]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        # Get or create service info
        service_info, created = ServiceInfo.objects.get_or_create(
            name=service_name,
            defaults={
                'service_type': service_type,
                'description': f'Auto-created service: {service_name}',
                'tags': [],
                'repository': '',
                'config_data': {}
            }
        )
        
        # Record the execution
        service = DataCollectionService()
        execution = service.record_api_execution(service_name, service_type, execution_data)
        
        return JsonResponse({
            'success': True,
            'execution_id': execution.id,
            'message': f'Recorded execution for {service_name}'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
def api_execute_service(request, service_name):
    """execute service via torero cli."""

    try:
        # get service info
        service_info = ServiceInfo.objects.get(name=service_name)
        
        # parse request body for additional parameters
        operation = None
        if request.body:
            try:
                data = json.loads(request.body)
                operation = data.get('operation')
            except json.JSONDecodeError:
                pass
        
        # execute via cli client
        cli_client = ToreroCliClient()
        result = cli_client.execute_service(
            service_name=service_name,
            service_type=service_info.service_type,
            operation=operation
        )
        
        if result:
            return JsonResponse({
                'status': 'started',
                'message': f'execution started for {service_name}'
            })
        else:
            # provide more detailed error message
            error_msg = f'failed to start execution for {service_name} (type: {service_info.service_type})'
            logger.error(error_msg)
            logger.error(f'cli client returned None for service: {service_name}')
            
            # check if it's a common issue
            if not hasattr(settings, 'TORERO_CLI_TIMEOUT'):
                logger.warning('TORERO_CLI_TIMEOUT not configured, using default')
            
            return JsonResponse({
                'status': 'error',
                'message': f'{error_msg} - check server logs for details'
            }, status=500)
            
    except ServiceInfo.DoesNotExist:
        return JsonResponse({
            'status': 'error', 
            'message': 'service not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
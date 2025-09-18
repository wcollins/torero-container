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

from .models import ServiceExecution, ServiceInfo, ExecutionQueue
from .services import DataCollectionService, ToreroCliClient, ExecutionQueueService, ServiceInputManager

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
    """add service execution to queue."""

    try:
        # get service info
        service_info = ServiceInfo.objects.get(name=service_name)

        # parse request body for additional parameters
        operation = None
        inputs = None
        input_file = None

        if request.body:
            try:
                data = json.loads(request.body)
                operation = data.get('operation')
                inputs = data.get('inputs')
                input_file = data.get('input_file')
            except json.JSONDecodeError:
                pass

        # add to execution queue with inputs
        queue_service = ExecutionQueueService()
        queue_item = queue_service.add_to_queue(
            service_name=service_name,
            service_type=service_info.service_type,
            operation=operation,
            inputs=inputs,
            input_file=input_file
        )
        
        return JsonResponse({
            'status': 'queued',
            'message': f'execution queued for {service_name}',
            'queue_id': queue_item.id,
            'position': ExecutionQueue.objects.filter(
                status=ExecutionQueue.QUEUED,
                created_at__lt=queue_item.created_at
            ).count() + 1
        })
            
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


@require_http_methods(["GET"])
def api_queue_status(request):
    """get current queue status."""

    queue_service = ExecutionQueueService()
    status = queue_service.get_queue_status()
    return JsonResponse(status)


@require_http_methods(["POST"])
def api_cancel_execution(request, queue_id):
    """cancel a queued execution."""

    queue_service = ExecutionQueueService()
    success = queue_service.cancel_execution(int(queue_id))

    if success:
        return JsonResponse({'status': 'success', 'message': 'execution cancelled'})
    else:
        return JsonResponse({'status': 'error', 'message': 'can only cancel queued executions'}, status=400)


@require_http_methods(["GET", "POST"])
def api_service_inputs(request, service_name):
    """api endpoint for service input manifests."""

    input_manager = ServiceInputManager()

    if request.method == "GET":
        # get input manifest for service
        manifest = input_manager.discover_inputs(service_name)
        if manifest:
            return JsonResponse({
                'status': 'success',
                'manifest': manifest,
                'schema': input_manager.get_input_schema(service_name)
            })
        else:
            return JsonResponse({
                'status': 'not_found',
                'message': f'no input manifest found for service {service_name}'
            }, status=404)

    elif request.method == "POST":
        # save or update input manifest
        try:
            manifest_data = json.loads(request.body)
            success = input_manager.save_manifest(service_name, manifest_data)

            if success:
                return JsonResponse({
                    'status': 'success',
                    'message': f'manifest saved for service {service_name}'
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'failed to save manifest'
                }, status=500)

        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'invalid JSON in request body'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)


@require_http_methods(["POST"])
def api_validate_inputs(request, service_name):
    """validate inputs against service manifest."""

    input_manager = ServiceInputManager()

    try:
        inputs = json.loads(request.body)
        valid, errors = input_manager.validate_inputs(service_name, inputs)

        return JsonResponse({
            'valid': valid,
            'errors': errors,
            'service': service_name
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'invalid JSON in request body'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@require_http_methods(["POST"])
def api_load_input_file(request):
    """load an input file and return its contents."""

    import yaml
    from pathlib import Path

    try:
        data = json.loads(request.body)
        file_path = data.get('file_path')
        service_name = data.get('service_name')

        if not file_path:
            return JsonResponse({
                'status': 'error',
                'message': 'file_path is required'
            }, status=400)

        # resolve path (handle @ notation)
        if file_path.startswith('@'):
            resolved_path = Path('/home/admin/data') / file_path[1:]
        else:
            resolved_path = Path(file_path)

        if not resolved_path.exists():
            return JsonResponse({
                'status': 'error',
                'message': f'file not found: {file_path}'
            }, status=404)

        # load and parse file based on extension
        try:
            suffix = resolved_path.suffix.lower()

            if suffix in ['.yaml', '.yml']:
                with open(resolved_path, 'r') as f:
                    inputs = yaml.safe_load(f)

            elif suffix == '.json':
                with open(resolved_path, 'r') as f:
                    inputs = json.load(f)

            elif suffix == '.tfvars':

                # parse terraform variables file
                inputs = {'variables': {}}
                with open(resolved_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        if '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip()

                            # basic parsing - remove quotes
                            if value.startswith('"') and value.endswith('"'):
                                value = value[1:-1]

                            # try to parse as JSON for complex types
                            try:
                                value = json.loads(value)
                            except:
                                pass
                            inputs['variables'][key] = value

            else:
                return JsonResponse({
                    'status': 'error',
                    'message': f'unsupported file format: {suffix}'
                }, status=400)

            # ensure proper structure
            if not isinstance(inputs, dict):
                inputs = {'variables': inputs}

            return JsonResponse({
                'status': 'success',
                'inputs': inputs,
                'file_path': str(resolved_path),
                'service': service_name
            })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'failed to parse file: {str(e)}'
            }, status=500)

    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'invalid JSON in request body'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
def api_list_input_files(request, service_name):
    """list available input files for a service."""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        from pathlib import Path
        import re

        # base directory for input files
        inputs_dir = Path('/home/admin/data/inputs')
        available_files = []

        if inputs_dir.exists():
            # look for files that match the service name pattern
            # e.g., for 'aws-vpc', find 'aws-vpc-dev.yaml', 'aws-vpc.tfvars', etc.
            # Note: [.-]? makes the separator optional for files like 'aws-vpc.tfvars'
            service_pattern = re.compile(f'^{re.escape(service_name)}([.-].*)?\\.(yaml|yml|json|tfvars)$', re.IGNORECASE)

            for file_path in inputs_dir.iterdir():
                if file_path.is_file() and service_pattern.match(file_path.name):
                    available_files.append({
                        'path': f"@inputs/{file_path.name}",
                        'name': file_path.name,  # Just use the filename
                        'filename': file_path.name,
                        'format': file_path.suffix[1:],  # remove the dot
                        'size': file_path.stat().st_size
                    })

            # also check for generic input files
            generic_patterns = ['config.yaml', 'config.yml', 'defaults.yaml', 'defaults.yml']
            for pattern in generic_patterns:
                file_path = inputs_dir / pattern
                if file_path.exists():
                    available_files.append({
                        'path': f"@inputs/{file_path.name}",
                        'name': 'Default Configuration',
                        'filename': file_path.name,
                        'format': file_path.suffix[1:],
                        'size': file_path.stat().st_size
                    })

        # sort by name
        available_files.sort(key=lambda x: x['name'])

        return JsonResponse({
            'status': 'success',
            'service': service_name,
            'files': available_files
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
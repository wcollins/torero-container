"""management command to create test data for dashboard."""

import json
import random
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from torero_ui.dashboard.models import ServiceExecution, ServiceInfo


class Command(BaseCommand):
    help = "Create test data for torero dashboard"
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=20,
            help='Number of test executions to create'
        )
    
    def handle(self, *args, **options):
        count = options['count']
        
        # create test services based on hello-torero example
        services = [
            {
                'name': 'hello-python',
                'service_type': 'python-script',
                'description': 'Simple python hello world script',
                'tags': ['hello', 'python', 'test'],
                'repository': 'hello-torero'
            },
            {
                'name': 'hello-ansible',
                'service_type': 'ansible-playbook',
                'description': 'Simple ansible hello world playbook',
                'tags': ['hello', 'ansible', 'test'],
                'repository': 'hello-torero'
            },
            {
                'name': 'hello-opentofu',
                'service_type': 'opentofu-plan',
                'description': 'Simple opentofu hello world plan',
                'tags': ['hello', 'opentofu', 'terraform', 'test'],
                'repository': 'hello-torero'
            },
        ]
        
        # create service info records
        for service_data in services:
            service, created = ServiceInfo.objects.get_or_create(
                name=service_data['name'],
                defaults={
                    'service_type': service_data['service_type'],
                    'description': service_data['description'],
                    'tags': service_data['tags'],
                    'repository': service_data['repository'],
                    'config_data': service_data
                }
            )
            if created:
                self.stdout.write(f"Created service: {service.name}")
        
        # create test executions
        now = timezone.now()
        
        for i in range(count):
            service = random.choice(services)
            
            # random time in last 7 days
            started_at = now - timedelta(
                days=random.randint(0, 7),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            # mostly successful executions
            status = 'success' if random.random() > 0.1 else 'failed'
            
            # random duration between 1-60 seconds
            duration = random.uniform(1.0, 60.0)
            
            # mock execution data based on service type
            if service['service_type'] == 'python-script':
                stdout = "Hello from Python!\nExecuting hello-python.py...\nScript completed successfully."
                stderr = "" if status == 'success' else "Error: mock failure for testing"
                execution_data = {
                    'script_path': 'hello-python.py',
                    'python_version': '3.11.0',
                    'virtual_env': f'/tmp/torero-venv-{random.randint(1000, 9999)}'
                }
            elif service['service_type'] == 'ansible-playbook':
                stdout = """PLAY [Hello Ansible] *********************************************************
                
TASK [Debug hello message] ****************************************************
ok: [localhost] => {
    "msg": "Hello from Ansible!"
}

PLAY RECAP ********************************************************************
localhost : ok=1 changed=0 unreachable=0 failed=0"""
                stderr = "" if status == 'success' else "TASK [failing task] FAILED!"
                execution_data = {
                    'playbook': 'hello-ansible.yml',
                    'inventory': 'localhost,',
                    'ansible_version': '8.5.0'
                }
            else:  # opentofu-plan
                stdout = """OpenTofu v1.9.0
                
Initializing the backend...
Initializing provider plugins...

Plan: 1 to add, 0 to change, 0 to destroy."""
                stderr = "" if status == 'success' else "Error: mock terraform failure"
                execution_data = {
                    'plan_file': 'hello-opentofu.tf',
                    'opentofu_version': '1.9.0',
                    'resources_to_add': 1,
                    'resources_to_change': 0,
                    'resources_to_destroy': 0
                }
            
            execution = ServiceExecution.objects.create(
                service_name=service['name'],
                service_type=service['service_type'],
                status=status,
                started_at=started_at,
                completed_at=started_at + timedelta(seconds=duration),
                duration_seconds=duration,
                stdout=stdout,
                stderr=stderr,
                return_code=0 if status == 'success' else 1,
                execution_data=execution_data,
                service_metadata=service
            )
            
            # update service statistics
            service_info = ServiceInfo.objects.get(name=service['name'])
            service_info.last_execution = started_at
            service_info.total_executions += 1
            
            if status == 'success':
                service_info.success_count += 1
            else:
                service_info.failure_count += 1
            
            service_info.save()
        
        self.stdout.write(
            self.style.SUCCESS(f"Successfully created {count} test executions")
        )
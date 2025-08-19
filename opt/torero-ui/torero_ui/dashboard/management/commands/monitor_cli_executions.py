"""Django management command to monitor CLI executions and record them in the UI."""

import json
import logging
import os
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path

import requests
from django.core.management.base import BaseCommand
from django.utils import timezone

from torero_ui.dashboard.services import DataCollectionService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Monitor torero CLI executions and record them in the UI database."""
    
    help = 'Monitor torero CLI executions and automatically record them in the UI'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--log-file',
            type=str,
            default='/home/admin/.torero.d/torero.log',
            help='Path to torero log file to monitor'
        )
        parser.add_argument(
            '--poll-interval',
            type=int,
            default=2,
            help='Polling interval in seconds'
        )
        parser.add_argument(
            '--admin-user',
            type=str,
            default='admin',
            help='Admin user to run as'
        )
    
    def handle(self, *args, **options):
        log_file = options['log_file']
        poll_interval = options['poll_interval']
        admin_user = options['admin_user']
        
        self.stdout.write(f"Starting CLI execution monitor...")
        self.stdout.write(f"Log file: {log_file}")
        self.stdout.write(f"Poll interval: {poll_interval}s")
        
        # Track last processed position
        last_position = 0
        if os.path.exists(log_file):
            last_position = os.path.getsize(log_file)
        
        while True:
            try:
                if os.path.exists(log_file):
                    current_size = os.path.getsize(log_file)
                    
                    if current_size > last_position:
                        # Read new content
                        with open(log_file, 'r') as f:
                            f.seek(last_position)
                            new_content = f.read()
                        
                        # Check for execution patterns
                        self._process_log_content(new_content, admin_user)
                        last_position = current_size
                
                time.sleep(poll_interval)
                
            except KeyboardInterrupt:
                self.stdout.write("Shutting down CLI execution monitor...")
                break
            except Exception as e:
                logger.error(f"Error in CLI execution monitor: {e}")
                time.sleep(poll_interval)
    
    def _process_log_content(self, content: str, admin_user: str):
        """Process new log content for execution patterns."""
        lines = content.split('\n')
        
        for line in lines:
            # Look for execution handlers
            if 'RunAnsiblePlaybook handler called' in line:
                self._capture_execution('ansible-playbook', admin_user)
            elif 'RunPythonScript handler called' in line:
                self._capture_execution('python-script', admin_user)  
            elif 'RunOpenTofuPlan handler called' in line:
                self._capture_execution('opentofu-plan', admin_user)
    
    def _capture_execution(self, service_type: str, admin_user: str):
        """Capture execution details by running torero with --raw flag."""
        try:
            # Get list of services of this type
            result = subprocess.run([
                'sudo', '-u', admin_user, 'torero', 'get', 'services',
                '--type', service_type, '--raw'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                logger.error(f"Failed to get services: {result.stderr}")
                return
            
            services_data = json.loads(result.stdout)
            if not services_data:
                return
            
            # For simplicity, get the first service of this type
            # In a more sophisticated implementation, we'd track which specific service was run
            service = services_data[0]
            service_name = service.get('name')
            
            if not service_name:
                return
            
            # Run the service with --raw flag to get structured output
            cmd = [
                'sudo', '-u', admin_user, 'torero', 'run', 'service',
                service_type, service_name, '--raw'
            ]
            
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            end_time = time.time()
            
            # Parse the structured output
            if result.stdout:
                try:
                    execution_data = json.loads(result.stdout)
                except json.JSONDecodeError:
                    # Fallback - create execution data from subprocess result
                    execution_data = {
                        'return_code': result.returncode,
                        'stdout': result.stdout,
                        'stderr': result.stderr,
                        'start_time': datetime.fromtimestamp(start_time).isoformat() + 'Z',
                        'end_time': datetime.fromtimestamp(end_time).isoformat() + 'Z',
                        'elapsed_time': end_time - start_time
                    }
            else:
                # Create execution data from subprocess result
                execution_data = {
                    'return_code': result.returncode,
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'start_time': datetime.fromtimestamp(start_time).isoformat() + 'Z',
                    'end_time': datetime.fromtimestamp(end_time).isoformat() + 'Z',
                    'elapsed_time': end_time - start_time
                }
            
            # Record the execution
            service_collector = DataCollectionService()
            execution = service_collector.record_api_execution(
                service_name, service_type, execution_data
            )
            
            self.stdout.write(f"Recorded CLI execution: {service_name} ({service_type}) - {execution.id}")
            
        except Exception as e:
            logger.error(f"Failed to capture {service_type} execution: {e}")
    
    def _detect_recent_execution(self, admin_user: str):
        """Detect and capture the most recent execution by monitoring the CLI."""
        try:
            # This is a simpler approach - just monitor for any recent executions
            # and capture them using the --raw flag output
            
            # Check if there are any recent executions we missed
            # This could be enhanced to parse the log timestamps and only capture very recent ones
            pass
            
        except Exception as e:
            logger.error(f"Failed to detect recent execution: {e}")
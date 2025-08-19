"""Django management command to capture CLI executions from torero command output."""

import json
import logging
import os
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand
from django.utils import timezone

from torero_ui.dashboard.services import DataCollectionService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Capture torero CLI executions by wrapping the torero command."""
    
    help = 'Capture CLI executions by monitoring torero command wrapper'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--install-wrapper',
            action='store_true',
            help='Install torero command wrapper for automatic capture'
        )
        parser.add_argument(
            '--monitor-history',
            action='store_true', 
            help='Monitor and capture from execution history'
        )
    
    def handle(self, *args, **options):
        if options['install_wrapper']:
            self._install_wrapper()
        elif options['monitor_history']:
            self._monitor_history()
        else:
            self.stdout.write("Use --install-wrapper or --monitor-history")
    
    def _install_wrapper(self):
        """Install a wrapper script to capture torero executions."""
        wrapper_script = '''#!/bin/bash
# torero execution wrapper to capture CLI runs

ORIGINAL_TORERO="/usr/local/bin/torero.orig"
CAPTURE_LOG="/tmp/torero-cli-captures.log"

# Check if this is a run command
if [[ "$1" == "run" && "$2" == "service" ]]; then
    SERVICE_TYPE="$3"
    SERVICE_NAME="$4"
    
    # Run the original command and capture output
    START_TIME=$(date -u +"%Y-%m-%dT%H:%M:%S.%6NZ")
    START_EPOCH=$(date +%s.%N)
    
    OUTPUT=$($ORIGINAL_TORERO "$@" 2>&1)
    RETURN_CODE=$?
    
    END_TIME=$(date -u +"%Y-%m-%dT%H:%M:%S.%6NZ")
    END_EPOCH=$(date +%s.%N)
    ELAPSED=$(echo "$END_EPOCH - $START_EPOCH" | bc -l)
    
    # Extract stdout and stderr
    if [[ $RETURN_CODE -eq 0 ]]; then
        STDOUT="$OUTPUT"
        STDERR=""
    else
        STDOUT=""
        STDERR="$OUTPUT"
    fi
    
    # Create execution record
    EXECUTION_DATA=$(cat <<EOF
{
    "service_name": "$SERVICE_NAME",
    "service_type": "$SERVICE_TYPE", 
    "return_code": $RETURN_CODE,
    "stdout": $(echo "$STDOUT" | jq -R -s .),
    "stderr": $(echo "$STDERR" | jq -R -s .),
    "start_time": "$START_TIME",
    "end_time": "$END_TIME",
    "elapsed_time": $ELAPSED
}
EOF
)
    
    # Log the execution
    echo "$EXECUTION_DATA" >> "$CAPTURE_LOG"
    
    # Send to UI (async)
    (curl -X POST http://localhost:8001/api/record-execution/ \\
        -H "Content-Type: application/json" \\
        -d "$EXECUTION_DATA" >/dev/null 2>&1 &)
    
    # Output the original result
    echo "$OUTPUT"
    exit $RETURN_CODE
else
    # For non-execution commands, just pass through
    exec $ORIGINAL_TORERO "$@"
fi
'''
        
        try:
            # Backup original torero binary
            subprocess.run(['sudo', 'cp', '/usr/local/bin/torero', '/usr/local/bin/torero.orig'], check=True)
            
            # Install wrapper
            with open('/tmp/torero-wrapper.sh', 'w') as f:
                f.write(wrapper_script)
            
            subprocess.run(['sudo', 'chmod', '+x', '/tmp/torero-wrapper.sh'], check=True)
            subprocess.run(['sudo', 'mv', '/tmp/torero-wrapper.sh', '/usr/local/bin/torero'], check=True)
            
            self.stdout.write("✅ Installed torero CLI wrapper for automatic execution capture")
            
        except Exception as e:
            logger.error(f"Failed to install wrapper: {e}")
            self.stdout.write(f"❌ Failed to install wrapper: {e}")
    
    def _monitor_history(self):
        """Monitor capture log for new executions."""
        capture_log = "/tmp/torero-cli-captures.log"
        self.stdout.write(f"Monitoring CLI captures from {capture_log}")
        
        # Track last processed position
        last_position = 0
        if os.path.exists(capture_log):
            last_position = os.path.getsize(capture_log)
        
        while True:
            try:
                if os.path.exists(capture_log):
                    current_size = os.path.getsize(capture_log)
                    
                    if current_size > last_position:
                        # Read new content
                        with open(capture_log, 'r') as f:
                            f.seek(last_position)
                            new_content = f.read()
                        
                        # Process new executions
                        self._process_captures(new_content)
                        last_position = current_size
                
                time.sleep(2)
                
            except KeyboardInterrupt:
                self.stdout.write("Shutting down capture monitor...")
                break
            except Exception as e:
                logger.error(f"Error in capture monitor: {e}")
                time.sleep(2)
    
    def _process_captures(self, content: str):
        """Process captured execution data."""
        lines = content.strip().split('\n')
        
        for line in lines:
            if not line.strip():
                continue
                
            try:
                execution_data = json.loads(line)
                service_name = execution_data.get('service_name')
                service_type = execution_data.get('service_type')
                
                if service_name and service_type:
                    # Record the execution
                    service_collector = DataCollectionService()
                    execution = service_collector.record_api_execution(
                        service_name, service_type, execution_data
                    )
                    
                    self.stdout.write(f"✅ Recorded CLI execution: {service_name} ({service_type}) - {execution.id}")
                    
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse capture line: {line}")
            except Exception as e:
                logger.error(f"Failed to record CLI execution: {e}")
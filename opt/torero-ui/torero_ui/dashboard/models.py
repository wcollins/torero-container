"""models for storing torero execution data."""

import json
from datetime import datetime
from typing import Any, Dict, Optional

from django.db import models


class ServiceExecution(models.Model):
    """stores execution data for torero services."""
    
    # basic execution info
    service_name = models.CharField(max_length=255)
    service_type = models.CharField(max_length=50)  # ansible-playbook, python-script, opentofu-plan
    status = models.CharField(max_length=20)  # success, failed, running
    
    # timing
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.FloatField(null=True, blank=True)
    
    # execution results stored as json
    stdout = models.TextField(blank=True)
    stderr = models.TextField(blank=True)
    return_code = models.IntegerField(null=True, blank=True)
    
    # structured execution data as json
    execution_data = models.JSONField(default=dict)
    
    # service metadata
    service_metadata = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['service_name', '-started_at']),
            models.Index(fields=['service_type', '-started_at']),
            models.Index(fields=['status', '-started_at']),
        ]
    
    def __str__(self) -> str:
        return f"{self.service_name} ({self.status}) - {self.started_at}"
    
    @property
    def is_completed(self) -> bool:
        """check if execution is completed."""
        return self.status in ['success', 'failed']
    
    @property
    def execution_time_display(self) -> str:
        """get formatted execution time."""
        if self.duration_seconds is None:
            return "N/A"
        return f"{self.duration_seconds:.2f}s"


class ExecutionQueue(models.Model):
    """manages execution queue for services."""
    
    QUEUED = 'queued'
    RUNNING = 'running'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'
    FAILED = 'failed'
    
    STATUS_CHOICES = [
        (QUEUED, 'Queued'),
        (RUNNING, 'Running'),
        (COMPLETED, 'Completed'),
        (CANCELLED, 'Cancelled'),
        (FAILED, 'Failed'),
    ]
    
    service_name = models.CharField(max_length=255)
    service_type = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=QUEUED)
    priority = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    progress_percent = models.IntegerField(default=0)
    estimated_duration = models.IntegerField(null=True, blank=True)  # seconds
    execution_id = models.CharField(max_length=255, null=True, blank=True)
    operation = models.CharField(max_length=50, null=True, blank=True)  # for opentofu apply/destroy
    inputs = models.JSONField(default=dict, blank=True, null=True)  # store input variables
    input_file = models.CharField(max_length=500, null=True, blank=True)  # optional input file path
    
    class Meta:
        ordering = ['priority', 'created_at']
        indexes = [
            models.Index(fields=['status', 'priority', 'created_at']),
            models.Index(fields=['service_name', '-created_at']),
        ]
    
    def __str__(self) -> str:
        return f"{self.service_name} ({self.status}) - {self.created_at}"


class ServiceInfo(models.Model):
    """stores service information from torero api."""
    
    name = models.CharField(max_length=255, unique=True)
    service_type = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    tags = models.JSONField(default=list)
    repository = models.CharField(max_length=255, blank=True)
    
    # service configuration as json
    config_data = models.JSONField(default=dict)
    
    # tracking
    last_execution = models.DateTimeField(null=True, blank=True)
    total_executions = models.IntegerField(default=0)
    success_count = models.IntegerField(default=0)
    failure_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self) -> str:
        return f"{self.name} ({self.service_type})"
    
    @property
    def success_rate(self) -> float:
        """calculate success rate percentage."""
        if self.total_executions == 0:
            return 0.0
        return (self.success_count / self.total_executions) * 100
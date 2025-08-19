"""admin configuration for dashboard models."""

from django.contrib import admin

from .models import ServiceExecution, ServiceInfo


@admin.register(ServiceExecution)
class ServiceExecutionAdmin(admin.ModelAdmin):
    list_display = ['service_name', 'service_type', 'status', 'started_at', 'duration_seconds']
    list_filter = ['service_type', 'status', 'started_at']
    search_fields = ['service_name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-started_at']


@admin.register(ServiceInfo)
class ServiceInfoAdmin(admin.ModelAdmin):
    list_display = ['name', 'service_type', 'total_executions', 'success_rate', 'last_execution']
    list_filter = ['service_type']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
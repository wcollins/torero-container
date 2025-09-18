"""url patterns for dashboard app."""

from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="index"),
    path("api/data/", views.api_dashboard_data, name="api_data"),
    path("api/sync/", views.api_sync_services, name="api_sync"),
    path("api/execution/<int:execution_id>/", views.api_execution_details, name="api_execution_details"),
    path("api/record-execution/", views.api_record_execution, name="api_record_execution"),
    path("api/execute/<str:service_name>/", views.api_execute_service, name="api_execute_service"),
    path("api/services/<str:service_name>/inputs/", views.api_service_inputs, name="api_service_inputs"),
    path("api/services/<str:service_name>/input-files/", views.api_list_input_files, name="api_list_input_files"),
    path("api/services/<str:service_name>/validate/", views.api_validate_inputs, name="api_validate_inputs"),
    path("api/load-input-file/", views.api_load_input_file, name="api_load_input_file"),
    path("api/queue/status/", views.api_queue_status, name="api_queue_status"),
    path("api/queue/<int:queue_id>/cancel/", views.api_cancel_execution, name="api_cancel_execution"),
]
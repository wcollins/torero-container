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
]
"""
Core functionality for the torero API

This package contains the core business logic and utility functions
for the torero API, including the interface to the torero CLI.

The core package abstracts the implementation details of interacting
with torero, allowing the API layer to focus on request handling and
response formatting.

Components:
- torero_executor: Interface for executing torero CLI commands and
  parsing their output into structured data
"""

# Re-export core components for easier imports
from torero_api.core.torero_executor import (
    check_torero_available,
    check_torero_version,
    get_services,
    get_service_by_name,
    describe_service,
    get_decorators,
    get_decorator_by_name,
    get_repositories,
    get_repository_by_name,
    get_secrets,
    get_secret_by_name,
    run_ansible_playbook_service,
    run_python_script_service
)
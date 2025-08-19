"""
Endpoint modules for the v1 torero API

This package contains endpoint modules organized by resource type.
Each module implements a FastAPI router with endpoints for a specific
resource category.

Current endpoints:
- services: Endpoints for discovering and filtering torero services
- decorators: Endpoints for discovering and filtering torero decorators
- repositories: Endpoints for discovering and filtering torero repositories
- secrets: Endpoints for discovering and filtering torero secrets
- execution: Endpoints for executing torero services

All endpoints follow RESTful principles and provide comprehensive
OpenAPI documentation for MCP compatibility.
"""
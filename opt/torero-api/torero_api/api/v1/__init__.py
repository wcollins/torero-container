"""
Version 1 of the torero API

This package contains the v1 implementation of the torero API endpoints.
It follows RESTful principles and is organized by resource type.

This version provides endpoints for:
- Service discovery and metadata
- Service filtering by type and tags
- Service type and tag enumeration

All endpoints are designed to be MCP-compatible, providing consistent
response formats and comprehensive type information.
"""

# Import and expose the endpoints for easier access
from torero_api.api.v1.endpoints import services
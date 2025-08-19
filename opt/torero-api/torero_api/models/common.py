"""
Common models for torero API

This module defines common models used throughout the API.
"""

from typing import Dict, Optional
from pydantic import BaseModel, Field

class ErrorResponse(BaseModel):
    """
    Standard error response model for API errors.
    
    Attributes:
        status_code: HTTP status code indicating the error type
        detail: Human-readable error message providing error details
        error_type: Categorization of the error for programmatic handling
        path: API endpoint where the error occurred
    """
    status_code: int = Field(..., description="HTTP status code")
    detail: str = Field(..., description="Error message")
    error_type: str = Field(..., description="Error category")
    path: str = Field(..., description="API endpoint path")
    
    # Updated Pydantic v2 configuration
    model_config = {
        "json_schema_extra": {
            "example": {
                "status_code": 400,
                "detail": "Invalid request parameters",
                "error_type": "validation_error",
                "path": "/v1/services/"
            }
        }
    }

class APIInfo(BaseModel):
    """
    Information about the API for the root endpoint response.
    
    Provides metadata about the API and navigation links to available endpoints.
    """
    name: str = Field(..., description="API name")
    version: str = Field(..., description="API version")
    description: str = Field(..., description="API description")
    documentation: str = Field(..., description="URL to API documentation")
    endpoints: Dict[str, str] = Field(..., description="Available API endpoints")
    
    # Updated Pydantic v2 configuration
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "torero API",
                "version": "0.1.0",
                "description": "API for torero services",
                "documentation": "http://localhost:8000/docs",
                "endpoints": {
                    "services": "http://localhost:8000/v1/services/",
                    "service_types": "http://localhost:8000/v1/services/types",
                    "service_tags": "http://localhost:8000/v1/services/tags"
                }
            }
        }
    }
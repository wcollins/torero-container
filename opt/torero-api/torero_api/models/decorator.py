"""
Decorator model for torero API

This module defines the Decorator model, which represents a torero decorator.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class Decorator(BaseModel):
    """
    Represents a torero decorator.
    
    Decorators modify the behavior of torero services by adding functionality
    such as authentication, logging, or parameter validation.
    
    Attributes:
        name: Unique identifier for the decorator
        description: Human-readable explanation of the decorator's purpose
        type: Category of decorator indicating its function
        parameters: Schema for parameters accepted by the decorator
        registries: Optional metadata about where the decorator is registered
    """
    name: str = Field(
        ..., 
        description="Unique identifier for the decorator"
    )
    description: Optional[str] = Field(
        None, 
        description="Human-readable explanation of the decorator's purpose"
    )
    type: str = Field(
        ..., 
        description="Category of decorator indicating its function"
    )
    parameters: Optional[Dict[str, Any]] = Field(
        None, 
        description="Schema for parameters accepted by the decorator"
    )
    registries: Optional[dict] = Field(
        None, 
        description="Metadata about where the decorator is registered"
    )
    
    # Pydantic v2 configuration
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "auth-basic",
                "description": "Adds HTTP Basic Authentication to service calls",
                "type": "authentication",
                "parameters": {
                    "username": {"type": "string", "required": True},
                    "password": {"type": "string", "required": True, "secret": True}
                },
                "registries": {
                    "file": {
                        "path": "/etc/torero/decorators/auth-basic"
                    }
                }
            }
        }
    }
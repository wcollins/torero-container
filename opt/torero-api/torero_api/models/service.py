"""
Service model for torero API

This module defines the Service model, which represents a torero service.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator

# Literal type to enforce valid service types in query parameters
ServiceType = Literal["ansible-playbook", "opentofu-plan", "python-script"]

class Service(BaseModel):
    """
    Represents a torero service.
    
    A service is a runnable unit in torero that can be executed to perform specific tasks.
    Services have different types (e.g., ansible-playbook, opentofu-plan, python-script)
    and can be tagged for organization and filtering.
    
    Attributes:
        name: Unique identifier for the service
        description: Human-readable explanation of the service's purpose
        type: Category of service indicating the underlying technology
        tags: List of labels for grouping and filtering services
        registries: Optional metadata about where the service is registered
    """
    name: str = Field(
        ..., 
        description="Unique identifier for the service"
    )
    description: Optional[str] = Field(
        None, 
        description="Human-readable explanation of the service's purpose"
    )
    type: str = Field(
        ..., 
        description="Category of service indicating the underlying technology"
    )
    tags: List[str] = Field(
        default_factory=list, 
        description="List of labels for grouping and filtering services"
    )
    registries: Optional[dict] = Field(
        None, 
        description="Metadata about where the service is registered"
    )
    
    @field_validator('tags', mode='before')
    @classmethod
    def validate_tags(cls, v):
        """
        Validate and normalize the tags field.
        
        If tags is None or not provided, return an empty list.
        If tags is already a list, return it as-is.
        """
        if v is None:
            return []
        if isinstance(v, list):
            return v
        # Handle any other edge cases
        return []
    
    # Updated Pydantic v2 configuration
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "network-backup",
                "description": "Backs up configurations from network devices",
                "type": "ansible-playbook",
                "tags": ["network", "backup", "daily"],
                "registries": {
                    "file": {
                        "path": "/etc/torero/services/network-backup"
                    }
                }
            }
        }
    }
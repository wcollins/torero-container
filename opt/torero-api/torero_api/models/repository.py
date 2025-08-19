"""
Repository model for torero API

This module defines the Repository model, which represents a torero repository.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class Repository(BaseModel):
    """
    Represents a torero repository.
    
    Repositories are storage locations for torero components such as
    services, decorators, and other resources.
    
    Attributes:
        name: Unique identifier for the repository
        description: Human-readable explanation of the repository's purpose
        type: Category of repository (e.g., 'file', 'git', 's3')
        location: Location URI for the repository
        metadata: Optional additional metadata about the repository
    """
    name: str = Field(
        ..., 
        description="Unique identifier for the repository"
    )
    description: Optional[str] = Field(
        None, 
        description="Human-readable explanation of the repository's purpose"
    )
    type: str = Field(
        ..., 
        description="Category of repository (e.g., 'file', 'git', 's3')"
    )
    location: str = Field(
        ..., 
        description="Location URI for the repository"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional metadata about the repository"
    )
    
    # Pydantic v2 configuration
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "local-services",
                "description": "Local file repository for services",
                "type": "file",
                "location": "/etc/torero/services",
                "metadata": {
                    "created": "2023-01-01T00:00:00Z",
                    "owner": "torero"
                }
            }
        }
    }
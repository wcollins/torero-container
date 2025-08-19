"""
Registry models for torero API

This module defines the data models for torero registries.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class RegistryMetadata(BaseModel):
    """Metadata information for a registry"""
    id: Optional[str] = Field(None, description="Unique identifier for the registry")
    created: Optional[datetime] = Field(None, description="Creation timestamp")
    tags: List[str] = Field(default_factory=list, description="Tags associated with the registry")
    credentials: Optional[str] = Field(None, description="Credentials reference for the registry")


class Registry(BaseModel):
    """
    Represents a torero registry.
    
    A registry is a location where packages, modules, or artifacts can be stored and retrieved.
    This could be an Ansible Galaxy registry, PyPI registry, or other package registries.
    """
    name: str = Field(..., description="The name of the registry", examples=["ansible-galaxy-main", "pypi-internal"])
    description: Optional[str] = Field(None, description="Description of the registry")
    type: str = Field(..., description="The type of registry (e.g., ansible-galaxy, pypi)", examples=["ansible-galaxy", "pypi"])
    url: str = Field(..., description="The URL of the registry", examples=["https://galaxy.ansible.com", "https://pypi.org/simple"])
    metadata: Optional[RegistryMetadata] = Field(None, description="Additional metadata for the registry")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "ansible-galaxy-main",
                "description": "Main Ansible Galaxy registry",
                "type": "ansible-galaxy",
                "url": "https://galaxy.ansible.com",
                "metadata": {
                    "id": "reg-123",
                    "created": "2024-01-01T00:00:00Z",
                    "tags": ["ansible", "production"],
                    "credentials": "galaxy-api-key"
                }
            }
        }
    }
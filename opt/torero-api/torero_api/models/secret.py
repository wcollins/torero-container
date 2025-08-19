"""
Secret model for torero API

This module defines the Secret model, which represents a torero secret.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class Secret(BaseModel):
    """
    Represents a torero secret.
    
    Secrets are sensitive values stored securely and used by torero
    services and decorators.
    
    Attributes:
        name: Unique identifier for the secret
        description: Human-readable explanation of the secret's purpose
        type: Category of secret (e.g., 'password', 'api-key', 'token')
        created_at: Timestamp when the secret was created
        metadata: Optional additional metadata about the secret
    """
    name: str = Field(
        ..., 
        description="Unique identifier for the secret"
    )
    description: Optional[str] = Field(
        None, 
        description="Human-readable explanation of the secret's purpose"
    )
    type: str = Field(
        ..., 
        description="Category of secret (e.g., 'password', 'api-key', 'token')"
    )
    created_at: Optional[datetime] = Field(
        None, 
        description="Timestamp when the secret was created"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional metadata about the secret"
    )
    
    # Pydantic v2 configuration
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "db-password",
                "description": "Database password for the application",
                "type": "password",
                "created_at": "2023-01-01T00:00:00Z",
                "metadata": {
                    "owner": "admin",
                    "provider": "vault"
                }
            }
        }
    }
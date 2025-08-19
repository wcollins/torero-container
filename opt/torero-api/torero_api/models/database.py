from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class DatabaseExportFormat(str, Enum):
    """Supported export formats for database export."""
    JSON = "json"
    YAML = "yaml"

class DatabaseImportOptions(BaseModel):
    """Options for database import operations."""
    repository: Optional[str] = Field(None, description="Repository URL for remote import")
    reference: Optional[str] = Field(None, description="Branch, tag, or commit reference")
    private_key: Optional[str] = Field(None, description="Private key name for SSH authentication")
    force: bool = Field(False, description="Override existing services")
    check: bool = Field(False, description="Perform dry-run validation")
    validate_only: bool = Field(False, description="Validate service file only")

class ImportCheckState(str, Enum):
    """States for resources during import check."""
    CONFLICT = "Conflict"
    ADD = "Add"
    REPLACEMENT = "Replacement"

class ImportCheckItem(BaseModel):
    """Individual item in import check result."""
    name: str = Field(..., description="Resource name")
    type: str = Field(..., description="Resource type")
    state: ImportCheckState = Field(..., description="Import state")
    message: Optional[str] = Field(None, description="Additional information")

class DatabaseImportCheckResult(BaseModel):
    """Result of import check operation."""
    conflicts: List[ImportCheckItem] = Field(default_factory=list, description="Resources that would conflict")
    additions: List[ImportCheckItem] = Field(default_factory=list, description="Resources that would be added")
    replacements: List[ImportCheckItem] = Field(default_factory=list, description="Resources that would be replaced")
    summary: Dict[str, int] = Field(default_factory=dict, description="Summary counts by type")

class DatabaseImportResult(BaseModel):
    """Result of database import operation."""
    success: bool = Field(..., description="Whether import was successful")
    imported: Dict[str, int] = Field(default_factory=dict, description="Count of imported resources by type")
    conflicts: Optional[List[str]] = Field(None, description="List of conflicts if any")
    message: Optional[str] = Field(None, description="Result message")

class DatabaseExportResult(BaseModel):
    """Result of database export operation."""
    decorators: Optional[List[Dict[str, Any]]] = Field(None, description="Exported decorators")
    repositories: Optional[List[Dict[str, Any]]] = Field(None, description="Exported repositories")
    services: Optional[List[Dict[str, Any]]] = Field(None, description="Exported services")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Export metadata")
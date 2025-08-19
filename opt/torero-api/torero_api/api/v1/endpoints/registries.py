"""
Registry endpoints for torero API

This module defines the API endpoints for managing torero registries.
"""

from fastapi import APIRouter, HTTPException, Query, Path
from typing import Optional, List
import logging

from torero_api.models.registry import Registry
from torero_api.core.torero_executor import get_registries, get_registry_by_name

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

@router.get(
    "/", 
    response_model=List[Registry],
    summary="List all registries",
    description="""
    Get a list of all registered torero registries.
    
    This endpoint returns all registries configured in torero, including their
    type, URL, and metadata. You can optionally filter by registry type.
    
    Registries are locations where packages, modules, or artifacts can be stored
    and retrieved, such as Ansible Galaxy or PyPI.
    """
)
def list_registries(
    type: Optional[str] = Query(
        None, 
        description="Filter registries by type (e.g., 'ansible-galaxy', 'pypi')",
        examples={
            "ansible-galaxy": {
                "summary": "Filter for Ansible Galaxy registries",
                "description": "Show only Ansible Galaxy registries",
                "value": "ansible-galaxy"
            },
            "pypi": {
                "summary": "Filter for PyPI registries",
                "description": "Show only PyPI registries",
                "value": "pypi"
            }
        }
    )
):
    """
    List all registries, optionally filtered by type.
    
    Args:
        type: Optional type filter
        
    Returns:
        List[Registry]: List of registries matching the criteria
        
    Raises:
        HTTPException: If there's an error retrieving registries
    """
    try:
        logger.info(f"Listing registries with type filter: {type}")
        
        # Get all registries from torero
        registries = get_registries()
        
        # Apply type filter if provided
        if type:
            registries = [reg for reg in registries if reg.type == type]
            logger.info(f"Filtered to {len(registries)} registries of type '{type}'")
        else:
            logger.info(f"Retrieved {len(registries)} registries")
        
        return registries
        
    except Exception as e:
        logger.error(f"Error retrieving registries: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/types",
    response_model=List[str],
    summary="List unique registry types",
    description="""
    Get a list of all unique registry types.
    
    This endpoint returns a deduplicated list of all registry types that are
    currently registered in torero, such as 'ansible-galaxy', 'pypi', etc.
    """
)
def list_registry_types():
    """
    List all unique registry types.
    
    Returns:
        List[str]: Sorted list of unique registry types
        
    Raises:
        HTTPException: If there's an error retrieving registries
    """
    try:
        logger.info("Getting unique registry types")
        
        # Get all registries
        registries = get_registries()
        
        # Extract unique types
        types = sorted(list(set(reg.type for reg in registries)))
        
        logger.info(f"Found {len(types)} unique registry types")
        return types
        
    except Exception as e:
        logger.error(f"Error retrieving registry types: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/{name}", 
    response_model=Registry,
    summary="Get registry by name",
    description="""
    Get a specific registry by its name.
    
    This endpoint returns detailed information about a single registry,
    including its type, URL, and metadata.
    
    The name is case-sensitive and must match exactly the name of a registered registry.
    
    If no registry is found with the specified name, a 404 error is returned.
    """
)
def get_registry(
    name: str = Path(
        ..., 
        description="Name of the registry to retrieve",
        examples={
            "ansible-galaxy-main": {
                "summary": "Ansible Galaxy Registry",
                "description": "Get the main Ansible Galaxy registry",
                "value": "ansible-galaxy-main"
            },
            "pypi-internal": {
                "summary": "Internal PyPI Registry",
                "description": "Get an internal PyPI registry",
                "value": "pypi-internal"
            }
        }
    )
):
    """
    Get a specific registry by name.
    
    Args:
        name: The name of the registry to retrieve
        
    Returns:
        Registry: The requested registry
        
    Raises:
        HTTPException: If the registry is not found or if there's an error
    """
    try:
        logger.info(f"Retrieving registry: {name}")
        
        # Get the specific registry
        registry = get_registry_by_name(name)
        
        if registry:
            logger.info(f"Found registry: {name}")
            return registry
                
        # If we get here, the registry was not found
        logger.warning(f"Registry not found: {name}")
        raise HTTPException(status_code=404, detail=f"Registry '{name}' not found")
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error retrieving registry: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
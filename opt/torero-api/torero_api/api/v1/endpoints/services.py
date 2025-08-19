"""
Services endpoints for torero API

This module defines the API endpoints for interacting with torero services.
"""

from fastapi import APIRouter, HTTPException, Query, Path, Depends
from typing import Optional, List
import logging

from torero_api.models.service import Service, ServiceType
from torero_api.core.torero_executor import get_services, get_service_by_name, describe_service

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Adding pagination parameters
def common_parameters(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return")
):
    """
    Common pagination parameters for endpoints that return lists.
    
    Args:
        skip: Number of items to skip
        limit: Maximum number of items to return
        
    Returns:
        dict: Dictionary containing the pagination parameters
    """
    return {"skip": skip, "limit": limit}

@router.get(
    "/", 
    response_model=List[Service], 
    summary="List services", 
    description="""
    Get all registered torero services with optional filtering.
    
    This endpoint returns a list of all services registered with torero.
    You can filter the results by service type and/or tag to narrow down
    the list to specific services of interest.
    
    Examples:
    - List all services: GET /v1/services/
    - List all ansible playbooks: GET /v1/services/?type=ansible-playbook
    - List services with "network" tag: GET /v1/services/?tag=network
    - Combine filters: GET /v1/services/?type=ansible-playbook&tag=network
    """
)
def list_services(
    commons: dict = Depends(common_parameters),
    type: Optional[ServiceType] = Query(
        None, 
        description="Filter by service type, e.g. 'ansible-playbook'",
        examples={
            "ansible-playbook": {
                "summary": "Ansible Playbook",
                "description": "Filter for only Ansible Playbook services",
                "value": "ansible-playbook"
            },
            "opentofu-plan": {
                "summary": "OpenTofu Plan",
                "description": "Filter for only OpenTofu Plan services",
                "value": "opentofu-plan"
            },
            "python-script": {
                "summary": "Python Script",
                "description": "Filter for only Python Script services",
                "value": "python-script"
            }
        }
    ),
    tag: Optional[str] = Query(
        None, 
        description="Filter by tag (e.g., 'network', 'backup')",
        examples={
            "network": {
                "summary": "Network Tag",
                "description": "Filter services with the 'network' tag",
                "value": "network"
            },
            "backup": {
                "summary": "Backup Tag",
                "description": "Filter services with the 'backup' tag",
                "value": "backup"
            },
            "automation": {
                "summary": "Automation Tag",
                "description": "Filter services with the 'automation' tag",
                "value": "automation"
            }
        }
    )
):
    """
    List all torero services, optionally filtered by type and/or tag.
    
    Args:
        commons: Common pagination parameters
        type: Optional filter to return only services of a specific type
        tag: Optional filter to return only services with a specific tag
    
    Returns:
        List[Service]: List of Service objects matching the filter criteria
    
    Raises:
        HTTPException: If an error occurs while retrieving or filtering services
    """
    try:
        logger.info(f"Getting services with filters - type: {type}, tag: {tag}")
        services = get_services()
        
        # Apply filters if provided
        if type:
            services = [s for s in services if s.type == type]
        if tag:
            services = [s for s in services if tag in s.tags]
            
        # Apply pagination
        skip = commons["skip"]
        limit = commons["limit"]
        paginated_services = services[skip:skip + limit]
        
        logger.info(f"Returning {len(paginated_services)} services after filtering")
        return paginated_services
    
    except Exception as e:
        logger.error(f"Error in list_services: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/types", 
    response_model=List[str],
    summary="List service types",
    description="""
    Return a list of unique service types used by registered services.
    
    This endpoint provides a list of all distinct service types (e.g., ansible-playbook, 
    opentofu-plan, python-script) that are currently in use across all registered services.
    
    This information is useful for:
    - Building UI dropdown filters
    - Understanding what types of services are available
    - Validating type values for new services
    """
)
def list_service_types():
    """
    Return a list of unique service types used by registered services.
    
    Retrieves all services and extracts the unique set of service types,
    returning them as a sorted list.
    
    Returns:
        List[str]: Sorted list of unique service type strings
    
    Raises:
        HTTPException: If an error occurs while retrieving services
    """
    try:
        logger.info("Getting service types")
        services = get_services()
        types = sorted(set(s.type for s in services))
        logger.info(f"Returning {len(types)} service types")
        return types
    except Exception as e:
        logger.error(f"Error in list_service_types: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/tags", 
    response_model=List[str],
    summary="List service tags",
    description="""
    Return a list of unique tags used across all registered services.
    
    This endpoint provides a list of all distinct tags that are currently 
    applied to registered services. Services can have multiple tags, and 
    this endpoint aggregates them into a single, deduplicated list.
    
    This information is useful for:
    - Building tag clouds or filter interfaces
    - Understanding how services are categorized
    - Discovering available service categories
    """
)
def list_service_tags():
    """
    Return a list of unique tags used across all registered services.
    
    Retrieves all services, extracts all tags from each service,
    and returns the unique set of tags as a sorted list.
    
    Returns:
        List[str]: Sorted list of unique tag strings
    
    Raises:
        HTTPException: If an error occurs while retrieving services
    """
    try:
        logger.info("Getting service tags")
        services = get_services()
        tags = sorted(set(tag for s in services for tag in s.tags))
        logger.info(f"Returning {len(tags)} service tags")
        return tags
    except Exception as e:
        logger.error(f"Error in list_service_tags: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/{name}", 
    response_model=Service, 
    summary="Get service details",
    description="""
    Get detailed information about a specific service by name.
    
    This endpoint retrieves detailed information about a single service
    identified by its name. The name is case-sensitive and must match
    exactly the name of a registered service.
    
    If no service is found with the specified name, a 404 error is returned.
    """
)
def get_service(
    name: str = Path(
        ..., 
        description="Name of the service to retrieve",
        examples={
            "network-backup": {
                "summary": "Network Backup Service",
                "description": "Get details for a network backup service",
                "value": "network-backup"
            },
            "app-deployment": {
                "summary": "Application Deployment Service",
                "description": "Get details for an application deployment service",
                "value": "app-deployment"
            },
            "system-monitor": {
                "summary": "System Monitoring Service",
                "description": "Get details for a system monitoring service",
                "value": "system-monitor"
            }
        }
    )
):
    """
    Get detailed information about a specific service by name.
    
    Args:
        name: The name of the service to retrieve
        
    Returns:
        Service: The service with the specified name
        
    Raises:
        HTTPException: If the service is not found or an error occurs
    """
    try:
        logger.info(f"Getting service details for: {name}")
        service = get_service_by_name(name)
        
        if service:
            logger.info(f"Found service: {name}")
            return service
                
        # If we get here, the service was not found
        logger.warning(f"Service not found: {name}")
        raise HTTPException(status_code=404, detail=f"Service '{name}' not found")
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error in get_service: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/{name}/describe", 
    summary="Get detailed service description",
    description="""
    Get comprehensive detailed description of a specific service by name.
    
    This endpoint uses 'torero describe service' to retrieve extensive
    information about a service including metadata, entity details, 
    playbook options, and configuration.
    
    If no service is found with the specified name, a 404 error is returned.
    """
)
def describe_service_endpoint(
    name: str = Path(
        ..., 
        description="Name of the service to describe",
        examples={
            "cisco-nxos-vlan-config": {
                "summary": "Cisco NXOS VLAN Config Service",
                "description": "Get detailed description for VLAN configuration service",
                "value": "cisco-nxos-vlan-config"
            }
        }
    )
):
    """
    Get comprehensive detailed description of a specific service by name.
    
    Args:
        name: The name of the service to describe
        
    Returns:
        dict: Detailed service description with metadata and entity information
        
    Raises:
        HTTPException: If the service is not found or an error occurs
    """
    try:
        logger.info(f"Getting detailed description for service: {name}")
        
        # First verify the service exists
        service = get_service_by_name(name)
        if not service:
            logger.warning(f"Service not found: {name}")
            raise HTTPException(status_code=404, detail=f"Service '{name}' not found")
        
        # Get detailed description
        description = describe_service(name)
        
        if description:
            logger.info(f"Found detailed description for service: {name}")
            return description
                
        # If we get here, the service description was not found
        logger.warning(f"Service description not found: {name}")
        raise HTTPException(status_code=404, detail=f"Service '{name}' description not available")
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except RuntimeError as e:
        # Handle specific RuntimeError from describe_service
        if "not found" in str(e).lower() or "404" in str(e):
            logger.warning(f"Service description not found: {name}")
            raise HTTPException(status_code=404, detail=f"Service '{name}' not found")
        else:
            logger.error(f"Error in describe_service_endpoint: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Error in describe_service_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
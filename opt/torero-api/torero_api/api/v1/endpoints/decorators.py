"""
Decorators endpoints for torero API

This module defines the API endpoints for interacting with torero decorators.
"""

from fastapi import APIRouter, HTTPException, Query, Path, Depends
from typing import Optional, List
import logging

from torero_api.models.decorator import Decorator
from torero_api.core.torero_executor import get_decorators, get_decorator_by_name, describe_decorator

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
    response_model=List[Decorator], 
    summary="List decorators", 
    description="""
    Get all registered torero decorators with optional filtering.
    
    This endpoint returns a list of all decorators registered with torero.
    You can filter the results by decorator type to narrow down the list.
    
    Examples:
    - List all decorators: GET /v1/decorators/
    - List all authentication decorators: GET /v1/decorators/?type=authentication
    """
)
def list_decorators(
    commons: dict = Depends(common_parameters),
    type: Optional[str] = Query(
        None, 
        description="Filter by decorator type, e.g. 'authentication'"
    )
):
    """
    List all torero decorators, optionally filtered by type.
    
    Args:
        commons: Common pagination parameters
        type: Optional filter to return only decorators of a specific type
    
    Returns:
        List[Decorator]: List of Decorator objects matching the filter criteria
    
    Raises:
        HTTPException: If an error occurs while retrieving or filtering decorators
    """
    try:
        logger.info(f"Getting decorators with filter - type: {type}")
        decorators = get_decorators()
        
        # Apply filters if provided
        if type:
            decorators = [d for d in decorators if d.type == type]
            
        # Apply pagination
        skip = commons["skip"]
        limit = commons["limit"]
        paginated_decorators = decorators[skip:skip + limit]
        
        logger.info(f"Returning {len(paginated_decorators)} decorators after filtering")
        return paginated_decorators
    
    except Exception as e:
        logger.error(f"Error in list_decorators: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/types", 
    response_model=List[str],
    summary="List decorator types",
    description="""
    Return a list of unique decorator types used by registered decorators.
    
    This endpoint provides a list of all distinct decorator types that are 
    currently in use across all registered decorators.
    
    This information is useful for:
    - Building UI dropdown filters
    - Understanding what types of decorators are available
    - Validating type values for new decorators
    """
)
def list_decorator_types():
    """
    Return a list of unique decorator types used by registered decorators.
    
    Retrieves all decorators and extracts the unique set of decorator types,
    returning them as a sorted list.
    
    Returns:
        List[str]: Sorted list of unique decorator type strings
    
    Raises:
        HTTPException: If an error occurs while retrieving decorators
    """
    try:
        logger.info("Getting decorator types")
        decorators = get_decorators()
        types = sorted(set(d.type for d in decorators))
        logger.info(f"Returning {len(types)} decorator types")
        return types
    except Exception as e:
        logger.error(f"Error in list_decorator_types: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/{name}", 
    response_model=Decorator, 
    summary="Get decorator details",
    description="""
    Get detailed information about a specific decorator by name.
    
    This endpoint retrieves detailed information about a single decorator
    identified by its name. The name is case-sensitive and must match
    exactly the name of a registered decorator.
    
    If no decorator is found with the specified name, a 404 error is returned.
    """
)
def get_decorator(
    name: str = Path(
        ..., 
        description="Name of the decorator to retrieve"
    )
):
    """
    Get detailed information about a specific decorator by name.
    
    Args:
        name: The name of the decorator to retrieve
        
    Returns:
        Decorator: The decorator with the specified name
        
    Raises:
        HTTPException: If the decorator is not found or an error occurs
    """
    try:
        logger.info(f"Getting decorator details for: {name}")
        decorator = get_decorator_by_name(name)
        
        if decorator:
            logger.info(f"Found decorator: {name}")
            return decorator
                
        # If we get here, the decorator was not found
        logger.warning(f"Decorator not found: {name}")
        raise HTTPException(status_code=404, detail=f"Decorator '{name}' not found")
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error retrieving decorator: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/{name}/describe", 
    response_model=dict,
    summary="Get detailed decorator description",
    description="""
    Get detailed description of a specific decorator by name.
    
    This endpoint returns comprehensive information about a decorator,
    including all configuration details, parameters, and metadata.
    
    The name is case-sensitive and must match exactly the name of a registered decorator.
    
    If no decorator is found with the specified name, a 404 error is returned.
    """
)
def describe_decorator_detail(
    name: str = Path(
        ..., 
        description="Name of the decorator to describe",
        examples={
            "audit-decorator": {
                "summary": "Audit Decorator",
                "description": "Get detailed description of an audit decorator",
                "value": "audit-decorator"
            },
            "logging-decorator": {
                "summary": "Logging Decorator",
                "description": "Get detailed description of a logging decorator",
                "value": "logging-decorator"
            }
        }
    )
):
    """
    Get detailed description of a specific decorator.
    
    Args:
        name: The name of the decorator to describe
        
    Returns:
        dict: Detailed decorator information
        
    Raises:
        HTTPException: If the decorator is not found or if there's an error
    """
    try:
        logger.info(f"Getting detailed description for decorator: {name}")
        
        # First verify the decorator exists
        decorator = get_decorator_by_name(name)
        if not decorator:
            logger.warning(f"Decorator not found: {name}")
            raise HTTPException(status_code=404, detail=f"Decorator '{name}' not found")
        
        # Get detailed description
        description = describe_decorator(name)
        
        if description is None:
            logger.warning(f"Could not retrieve detailed description for decorator: {name}")
            raise HTTPException(status_code=404, detail=f"Could not retrieve detailed description for decorator '{name}'")
        
        return description
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error getting detailed decorator description: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Error in get_decorator: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
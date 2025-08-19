"""
Secrets endpoints for torero API

This module defines the API endpoints for interacting with torero secrets.
"""

from fastapi import APIRouter, HTTPException, Query, Path, Depends
from typing import Optional, List
import logging

from torero_api.models.secret import Secret
from torero_api.core.torero_executor import get_secrets, get_secret_by_name, describe_secret

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
    response_model=List[Secret], 
    summary="List secrets", 
    description="""
    Get all registered torero secrets with optional filtering.
    
    This endpoint returns a list of all secrets registered with torero.
    You can filter the results by secret type to narrow down the list.
    
    Examples:
    - List all secrets: GET /v1/secrets/
    - List all password secrets: GET /v1/secrets/?type=password
    - List all API key secrets: GET /v1/secrets/?type=api-key
    """
)
def list_secrets(
    commons: dict = Depends(common_parameters),
    type: Optional[str] = Query(
        None, 
        description="Filter by secret type, e.g. 'password', 'api-key', 'token'"
    )
):
    """
    List all torero secrets, optionally filtered by type.
    
    Args:
        commons: Common pagination parameters
        type: Optional filter to return only secrets of a specific type
    
    Returns:
        List[Secret]: List of Secret objects matching the filter criteria
    
    Raises:
        HTTPException: If an error occurs while retrieving or filtering secrets
    """
    try:
        logger.info(f"Getting secrets with filter - type: {type}")
        secrets = get_secrets()
        
        # Apply filters if provided
        if type:
            secrets = [s for s in secrets if s.type == type]
            
        # Apply pagination
        skip = commons["skip"]
        limit = commons["limit"]
        paginated_secrets = secrets[skip:skip + limit]
        
        logger.info(f"Returning {len(paginated_secrets)} secrets after filtering")
        return paginated_secrets
    
    except Exception as e:
        logger.error(f"Error in list_secrets: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/types", 
    response_model=List[str],
    summary="List secret types",
    description="""
    Return a list of unique secret types used by registered secrets.
    
    This endpoint provides a list of all distinct secret types (e.g., password, api-key, token) 
    that are currently in use across all registered secrets.
    
    This information is useful for:
    - Building UI dropdown filters
    - Understanding what types of secrets are available
    - Validating type values for new secrets
    """
)
def list_secret_types():
    """
    Return a list of unique secret types used by registered secrets.
    
    Retrieves all secrets and extracts the unique set of secret types,
    returning them as a sorted list.
    
    Returns:
        List[str]: Sorted list of unique secret type strings
    
    Raises:
        HTTPException: If an error occurs while retrieving secrets
    """
    try:
        logger.info("Getting secret types")
        secrets = get_secrets()
        types = sorted(set(s.type for s in secrets))
        logger.info(f"Returning {len(types)} secret types")
        return types
    except Exception as e:
        logger.error(f"Error in list_secret_types: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/{name}", 
    response_model=Secret, 
    summary="Get secret details",
    description="""
    Get detailed information about a specific secret by name.
    
    This endpoint retrieves metadata about a single secret identified by its name.
    The name is case-sensitive and must match exactly the name of a registered secret.
    
    Note: For security reasons, this endpoint only returns metadata about the secret,
    not the actual secret value.
    
    If no secret is found with the specified name, a 404 error is returned.
    """
)
def get_secret(
    name: str = Path(
        ..., 
        description="Name of the secret to retrieve"
    )
):
    """
    Get detailed information about a specific secret by name.
    
    Args:
        name: The name of the secret to retrieve
        
    Returns:
        Secret: The secret with the specified name
        
    Raises:
        HTTPException: If the secret is not found or an error occurs
    """
    try:
        logger.info(f"Getting secret details for: {name}")
        secret = get_secret_by_name(name)
        
        if secret:
            logger.info(f"Found secret: {name}")
            return secret
                
        # If we get here, the secret was not found
        logger.warning(f"Secret not found: {name}")
        raise HTTPException(status_code=404, detail=f"Secret '{name}' not found")
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error retrieving secret: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/{name}/describe", 
    response_model=dict,
    summary="Get detailed secret description",
    description="""
    Get detailed description of a specific secret by name.
    
    This endpoint returns comprehensive information about a secret,
    including all configuration details and metadata. Note that the actual
    secret value is not returned for security reasons.
    
    The name is case-sensitive and must match exactly the name of a registered secret.
    
    If no secret is found with the specified name, a 404 error is returned.
    """
)
def describe_secret_detail(
    name: str = Path(
        ..., 
        description="Name of the secret to describe",
        examples={
            "ssh-key": {
                "summary": "SSH Key",
                "description": "Get detailed description of an SSH key secret",
                "value": "ssh-key"
            },
            "api-token": {
                "summary": "API Token",
                "description": "Get detailed description of an API token secret",
                "value": "api-token"
            }
        }
    )
):
    """
    Get detailed description of a specific secret.
    
    Args:
        name: The name of the secret to describe
        
    Returns:
        dict: Detailed secret information (without the actual secret value)
        
    Raises:
        HTTPException: If the secret is not found or if there's an error
    """
    try:
        logger.info(f"Getting detailed description for secret: {name}")
        
        # First verify the secret exists
        secret = get_secret_by_name(name)
        if not secret:
            logger.warning(f"Secret not found: {name}")
            raise HTTPException(status_code=404, detail=f"Secret '{name}' not found")
        
        # Get detailed description
        description = describe_secret(name)
        
        if description is None:
            logger.warning(f"Could not retrieve detailed description for secret: {name}")
            raise HTTPException(status_code=404, detail=f"Could not retrieve detailed description for secret '{name}'")
        
        return description
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error getting detailed secret description: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Error in get_secret: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
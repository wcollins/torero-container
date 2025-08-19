"""
Repositories endpoints for torero API

This module defines the API endpoints for interacting with torero repositories.
"""

from fastapi import APIRouter, HTTPException, Query, Path, Depends
from typing import Optional, List
import logging

from torero_api.models.repository import Repository
from torero_api.core.torero_executor import get_repositories, get_repository_by_name, describe_repository

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
    response_model=List[Repository], 
    summary="List repositories", 
    description="""
    Get all registered torero repositories with optional filtering.
    
    This endpoint returns a list of all repositories registered with torero.
    You can filter the results by repository type to narrow down the list.
    
    Examples:
    - List all repositories: GET /v1/repositories/
    - List all file repositories: GET /v1/repositories/?type=file
    - List all git repositories: GET /v1/repositories/?type=git
    """
)
def list_repositories(
    commons: dict = Depends(common_parameters),
    type: Optional[str] = Query(
        None, 
        description="Filter by repository type, e.g. 'file', 'git', 's3'"
    )
):
    """
    List all torero repositories, optionally filtered by type.
    
    Args:
        commons: Common pagination parameters
        type: Optional filter to return only repositories of a specific type
    
    Returns:
        List[Repository]: List of Repository objects matching the filter criteria
    
    Raises:
        HTTPException: If an error occurs while retrieving or filtering repositories
    """
    try:
        logger.info(f"Getting repositories with filter - type: {type}")
        repositories = get_repositories()
        
        # Apply filters if provided
        if type:
            repositories = [r for r in repositories if r.type == type]
            
        # Apply pagination
        skip = commons["skip"]
        limit = commons["limit"]
        paginated_repositories = repositories[skip:skip + limit]
        
        logger.info(f"Returning {len(paginated_repositories)} repositories after filtering")
        return paginated_repositories
    
    except Exception as e:
        logger.error(f"Error in list_repositories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/types", 
    response_model=List[str],
    summary="List repository types",
    description="""
    Return a list of unique repository types used by registered repositories.
    
    This endpoint provides a list of all distinct repository types (e.g., file, git, s3) 
    that are currently in use across all registered repositories.
    
    This information is useful for:
    - Building UI dropdown filters
    - Understanding what types of repositories are available
    - Validating type values for new repositories
    """
)
def list_repository_types():
    """
    Return a list of unique repository types used by registered repositories.
    
    Retrieves all repositories and extracts the unique set of repository types,
    returning them as a sorted list.
    
    Returns:
        List[str]: Sorted list of unique repository type strings
    
    Raises:
        HTTPException: If an error occurs while retrieving repositories
    """
    try:
        logger.info("Getting repository types")
        repositories = get_repositories()
        types = sorted(set(r.type for r in repositories))
        logger.info(f"Returning {len(types)} repository types")
        return types
    except Exception as e:
        logger.error(f"Error in list_repository_types: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/{name}", 
    response_model=Repository, 
    summary="Get repository details",
    description="""
    Get detailed information about a specific repository by name.
    
    This endpoint retrieves detailed information about a single repository
    identified by its name. The name is case-sensitive and must match
    exactly the name of a registered repository.
    
    If no repository is found with the specified name, a 404 error is returned.
    """
)
def get_repository(
    name: str = Path(
        ..., 
        description="Name of the repository to retrieve"
    )
):
    """
    Get detailed information about a specific repository by name.
    
    Args:
        name: The name of the repository to retrieve
        
    Returns:
        Repository: The repository with the specified name
        
    Raises:
        HTTPException: If the repository is not found or an error occurs
    """
    try:
        logger.info(f"Getting repository details for: {name}")
        repository = get_repository_by_name(name)
        
        if repository:
            logger.info(f"Found repository: {name}")
            return repository
                
        # If we get here, the repository was not found
        logger.warning(f"Repository not found: {name}")
        raise HTTPException(status_code=404, detail=f"Repository '{name}' not found")
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error retrieving repository: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/{name}/describe", 
    response_model=dict,
    summary="Get detailed repository description",
    description="""
    Get detailed description of a specific repository by name.
    
    This endpoint returns comprehensive information about a repository,
    including all configuration details, metadata, and additional properties
    that may not be included in the standard repository object.
    
    The name is case-sensitive and must match exactly the name of a registered repository.
    
    If no repository is found with the specified name, a 404 error is returned.
    """
)
def describe_repository_detail(
    name: str = Path(
        ..., 
        description="Name of the repository to describe",
        examples={
            "ansible-roles": {
                "summary": "Ansible Roles Repository",
                "description": "Get detailed description of an Ansible roles repository",
                "value": "ansible-roles"
            },
            "terraform-modules": {
                "summary": "Terraform Modules Repository",
                "description": "Get detailed description of a Terraform modules repository",
                "value": "terraform-modules"
            }
        }
    )
):
    """
    Get detailed description of a specific repository.
    
    Args:
        name: The name of the repository to describe
        
    Returns:
        dict: Detailed repository information
        
    Raises:
        HTTPException: If the repository is not found or if there's an error
    """
    try:
        logger.info(f"Getting detailed description for repository: {name}")
        
        # First verify the repository exists
        repository = get_repository_by_name(name)
        if not repository:
            logger.warning(f"Repository not found: {name}")
            raise HTTPException(status_code=404, detail=f"Repository '{name}' not found")
        
        # Get detailed description
        description = describe_repository(name)
        
        if description is None:
            logger.warning(f"Could not retrieve detailed description for repository: {name}")
            raise HTTPException(status_code=404, detail=f"Could not retrieve detailed description for repository '{name}'")
        
        return description
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error getting detailed repository description: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Error in get_repository: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
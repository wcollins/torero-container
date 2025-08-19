"""
Execution endpoints for torero API

This module defines the API endpoints for executing torero services.
"""

from fastapi import APIRouter, HTTPException, Path, Query
from typing import Dict, Any, Optional
import logging

from torero_api.models.execution import ServiceExecutionResult
from torero_api.core.torero_executor import (
    run_ansible_playbook_service, 
    run_python_script_service,
    run_opentofu_plan_apply_service,
    run_opentofu_plan_destroy_service, 
    get_service_by_name
)

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

@router.post(
    "/ansible-playbook/{name}", 
    response_model=ServiceExecutionResult, 
    summary="Run Ansible playbook service", 
    description="""
    Execute a registered torero Ansible playbook service by name.
    
    This endpoint runs the specified Ansible playbook service and returns
    the execution results, including standard output, standard error,
    return code, and timing information.
    
    The name is case-sensitive and must match exactly the name of a registered
    Ansible playbook service.
    
    If no service is found with the specified name, a 404 error is returned.
    """
)
def run_ansible_service(
    name: str = Path(
        ..., 
        description="Name of the Ansible playbook service to run",
        examples={
            "network-backup": {
                "summary": "Network Backup Service",
                "description": "Run a network backup service",
                "value": "network-backup"
            },
            "hello-ansible": {
                "summary": "Hello World Ansible Service",
                "description": "Run a simple hello world Ansible service",
                "value": "hello-ansible"
            }
        }
    )
):
    """
    Execute a registered torero Ansible playbook service.
    
    Args:
        name: The name of the Ansible playbook service to run
        
    Returns:
        ServiceExecutionResult: The results of the service execution
        
    Raises:
        HTTPException: If the service is not found, is not an Ansible playbook, or execution fails
    """
    try:
        logger.info(f"Running Ansible playbook service: {name}")
        
        # First, verify the service exists and is an Ansible playbook
        service = get_service_by_name(name)
        if not service:
            logger.warning(f"Service not found: {name}")
            raise HTTPException(status_code=404, detail=f"Service '{name}' not found")
            
        if service.type != "ansible-playbook":
            logger.warning(f"Service {name} is not an Ansible playbook (type: {service.type})")
            raise HTTPException(
                status_code=400, 
                detail=f"Service '{name}' is not an Ansible playbook (type: {service.type})"
            )
        
        # Execute the service
        result = run_ansible_playbook_service(name)
        
        # Convert the result to the response model
        return ServiceExecutionResult(**result)
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error running Ansible playbook service: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/python-script/{name}", 
    response_model=ServiceExecutionResult, 
    summary="Run Python script service", 
    description="""
    Execute a registered torero Python script service by name.
    
    This endpoint runs the specified Python script service and returns
    the execution results, including standard output, standard error,
    return code, and timing information.
    
    The name is case-sensitive and must match exactly the name of a registered
    Python script service.
    
    If no service is found with the specified name, a 404 error is returned.
    """
)
def run_python_script(
    name: str = Path(
        ..., 
        description="Name of the Python script service to run",
        examples={
            "hello-python": {
                "summary": "Hello World Python Script",
                "description": "Run a simple hello world Python script",
                "value": "hello-python"
            },
            "data-processor": {
                "summary": "Data Processing Script",
                "description": "Run a Python script that processes data",
                "value": "data-processor"
            }
        }
    )
):
    """
    Execute a registered torero Python script service.
    
    Args:
        name: The name of the Python script service to run
        
    Returns:
        ServiceExecutionResult: The results of the service execution
        
    Raises:
        HTTPException: If the service is not found, is not a Python script, or execution fails
    """
    try:
        logger.info(f"Running Python script service: {name}")
        
        # First, verify the service exists and is a Python script
        service = get_service_by_name(name)
        if not service:
            logger.warning(f"Service not found: {name}")
            raise HTTPException(status_code=404, detail=f"Service '{name}' not found")
            
        if service.type != "python-script":
            logger.warning(f"Service {name} is not a Python script (type: {service.type})")
            raise HTTPException(
                status_code=400, 
                detail=f"Service '{name}' is not a Python script (type: {service.type})"
            )
        
        # Execute the service
        result = run_python_script_service(name)
        
        # Convert the result to the response model
        return ServiceExecutionResult(**result)
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error running Python script service: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/opentofu-plan/{name}/apply", 
    response_model=ServiceExecutionResult, 
    summary="Apply OpenTofu plan service", 
    description="""
    Execute a registered torero OpenTofu plan service to apply infrastructure changes.
    
    This endpoint runs the specified OpenTofu plan service in apply mode and returns
    the execution results, including standard output, standard error,
    return code, and timing information.
    
    The name is case-sensitive and must match exactly the name of a registered
    OpenTofu plan service.
    
    If no service is found with the specified name, a 404 error is returned.
    """
)
def apply_opentofu_plan(
    name: str = Path(
        ..., 
        description="Name of the OpenTofu plan service to apply",
        examples={
            "infrastructure-deploy": {
                "summary": "Infrastructure Deployment",
                "description": "Apply infrastructure changes using OpenTofu",
                "value": "infrastructure-deploy"
            },
            "cloud-resources": {
                "summary": "Cloud Resources",
                "description": "Apply cloud resource configuration",
                "value": "cloud-resources"
            }
        }
    )
):
    """
    Apply a registered torero OpenTofu plan service.
    
    Args:
        name: The name of the OpenTofu plan service to apply
        
    Returns:
        ServiceExecutionResult: The results of the service execution
        
    Raises:
        HTTPException: If the service is not found, is not an OpenTofu plan, or execution fails
    """
    try:
        logger.info(f"Applying OpenTofu plan service: {name}")
        
        # First, verify the service exists and is an OpenTofu plan
        service = get_service_by_name(name)
        if not service:
            logger.warning(f"Service not found: {name}")
            raise HTTPException(status_code=404, detail=f"Service '{name}' not found")
            
        if service.type != "opentofu-plan":
            logger.warning(f"Service {name} is not an OpenTofu plan (type: {service.type})")
            raise HTTPException(
                status_code=400, 
                detail=f"Service '{name}' is not an OpenTofu plan (type: {service.type})"
            )
        
        # Execute the service
        result = run_opentofu_plan_apply_service(name)
        
        # Convert the result to the response model
        return ServiceExecutionResult(**result)
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error applying OpenTofu plan service: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/opentofu-plan/{name}/destroy", 
    response_model=ServiceExecutionResult, 
    summary="Destroy OpenTofu plan service resources", 
    description="""
    Execute a registered torero OpenTofu plan service to destroy infrastructure resources.
    
    This endpoint runs the specified OpenTofu plan service in destroy mode and returns
    the execution results, including standard output, standard error,
    return code, and timing information.
    
    The name is case-sensitive and must match exactly the name of a registered
    OpenTofu plan service.
    
    If no service is found with the specified name, a 404 error is returned.
    
    WARNING: This operation will destroy infrastructure resources and cannot be undone.
    """
)
def destroy_opentofu_plan(
    name: str = Path(
        ..., 
        description="Name of the OpenTofu plan service to destroy",
        examples={
            "infrastructure-deploy": {
                "summary": "Infrastructure Deployment",
                "description": "Destroy infrastructure managed by OpenTofu",
                "value": "infrastructure-deploy"
            },
            "cloud-resources": {
                "summary": "Cloud Resources",
                "description": "Destroy cloud resource configuration",
                "value": "cloud-resources"
            }
        }
    )
):
    """
    Destroy resources managed by a registered torero OpenTofu plan service.
    
    Args:
        name: The name of the OpenTofu plan service to destroy
        
    Returns:
        ServiceExecutionResult: The results of the service execution
        
    Raises:
        HTTPException: If the service is not found, is not an OpenTofu plan, or execution fails
    """
    try:
        logger.info(f"Destroying OpenTofu plan service: {name}")
        
        # First, verify the service exists and is an OpenTofu plan
        service = get_service_by_name(name)
        if not service:
            logger.warning(f"Service not found: {name}")
            raise HTTPException(status_code=404, detail=f"Service '{name}' not found")
            
        if service.type != "opentofu-plan":
            logger.warning(f"Service {name} is not an OpenTofu plan (type: {service.type})")
            raise HTTPException(
                status_code=400, 
                detail=f"Service '{name}' is not an OpenTofu plan (type: {service.type})"
            )
        
        # Execute the service
        result = run_opentofu_plan_destroy_service(name)
        
        # Convert the result to the response model
        return ServiceExecutionResult(**result)
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error destroying OpenTofu plan service: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
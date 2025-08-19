from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from fastapi.responses import Response
import tempfile
import os

from torero_api.core.torero_executor import (
    execute_db_export,
    execute_db_import,
    ToreroError
)
from torero_api.models.database import (
    DatabaseExportFormat,
    DatabaseImportOptions,
    DatabaseImportCheckResult
)

router = APIRouter(
    prefix="/db",
    tags=["database"],
    responses={404: {"description": "Not found"}},
)

@router.get("/export")
async def export_database(
    format: DatabaseExportFormat = DatabaseExportFormat.YAML
) -> Dict[str, Any]:
    """
    Export services and resources to a file.
    
    This endpoint exports all torero configurations including decorators, 
    repositories, and services in the specified format.
    
    Args:
        format: The output format (json or yaml). Defaults to yaml.
    
    Returns:
        The exported configuration data.
    
    Raises:
        HTTPException: If the export operation fails.
    """
    try:
        result = await execute_db_export(format=format.value)
        # If YAML format, the result contains the raw YAML data
        if format == DatabaseExportFormat.YAML and isinstance(result, dict) and "data" in result:
            # For API response, we need to parse YAML to JSON
            import yaml
            try:
                data = yaml.safe_load(result["data"])
                return data
            except yaml.YAMLError:
                # If YAML parsing fails, return the raw data
                return {"data": result["data"], "format": "yaml"}
        return result
    except ToreroError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/download")
async def download_database_export(
    format: DatabaseExportFormat = DatabaseExportFormat.YAML,
    filename: Optional[str] = None
) -> Response:
    """
    Export services and resources as a downloadable file.
    
    This endpoint exports all torero configurations and returns them as a 
    downloadable file with appropriate content type headers.
    
    Args:
        format: The output format (json or yaml). Defaults to yaml.
        filename: Optional custom filename for the export.
    
    Returns:
        A file response with the exported data.
    
    Raises:
        HTTPException: If the export operation fails.
    """
    try:
        result = await execute_db_export(format=format.value)
        
        # Determine content type and default filename based on format
        if format == DatabaseExportFormat.JSON:
            content_type = "application/json"
            default_filename = "torero-export.json"
            # Convert dict to JSON string if needed
            if isinstance(result, dict):
                import json
                content = json.dumps(result, indent=2)
            else:
                content = result
        else:
            content_type = "application/x-yaml"
            default_filename = "torero-export.yaml"
            # Get the raw YAML data if it's wrapped
            if isinstance(result, dict) and "data" in result:
                content = result["data"]
            else:
                # Convert dict to YAML if needed
                import yaml
                content = yaml.dump(result, default_flow_style=False)
        
        filename = filename or default_filename
        
        return Response(
            content=content if isinstance(content, (str, bytes)) else str(content),
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except ToreroError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import")
async def import_database(
    file: UploadFile = File(...),
    force: bool = Form(False),
    check: bool = Form(False),
    validate_only: bool = Form(False)
) -> Dict[str, Any]:
    """
    Import resources/services from a service file.
    
    This endpoint imports services and resources from an uploaded file to move
    configurations between torero instances.
    
    Args:
        file: The service configuration file to import.
        force: Override existing services.
        check: Perform validation and dry-run of import.
        validate_only: Validate service file only.
    
    Returns:
        Import result including status and any conflicts or changes.
    
    Raises:
        HTTPException: If the import operation fails.
    """
    try:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Execute import with options
            options = DatabaseImportOptions(
                force=force,
                check=check,
                validate_only=validate_only
            )
            result = await execute_db_import(file_path=tmp_file_path, options=options)
            return result
        finally:
            # Clean up temporary file
            os.unlink(tmp_file_path)
            
    except ToreroError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

@router.post("/import/check")
async def check_import(
    file: UploadFile = File(...)
) -> DatabaseImportCheckResult:
    """
    Check what would happen during an import without actually importing.
    
    This endpoint performs a dry-run of the import operation to show what
    resources would be added, replaced, or conflict.
    
    Args:
        file: The service configuration file to check.
    
    Returns:
        Check results showing conflicts, additions, and potential replacements.
    
    Raises:
        HTTPException: If the check operation fails.
    """
    try:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Execute import check
            options = DatabaseImportOptions(check=True)
            result = await execute_db_import(file_path=tmp_file_path, options=options)
            return DatabaseImportCheckResult(**result)
        finally:
            # Clean up temporary file
            os.unlink(tmp_file_path)
            
    except ToreroError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Check failed: {str(e)}")

@router.post("/import/repository")
async def import_from_repository(
    repository: str = Form(...),
    file_path: str = Form(...),
    reference: Optional[str] = Form(None),
    private_key_name: Optional[str] = Form(None),
    force: bool = Form(False),
    check: bool = Form(False),
    validate_only: bool = Form(False)
) -> Dict[str, Any]:
    """
    Import resources/services from a repository.
    
    This endpoint imports services and resources from a file in a git repository.
    Supports both HTTP and SSH repositories with optional private key authentication.
    
    Args:
        repository: Repository URL (HTTP or SSH).
        file_path: Path to the import file within the repository.
        reference: Optional branch/tag/commit reference.
        private_key_name: Optional private key name for SSH authentication.
        force: Override existing services.
        check: Perform validation and dry-run of import.
        validate_only: Validate service file only.
    
    Returns:
        Import result including status and any conflicts or changes.
    
    Raises:
        HTTPException: If the import operation fails.
    """
    try:
        options = DatabaseImportOptions(
            repository=repository,
            reference=reference,
            private_key=private_key_name,
            force=force,
            check=check,
            validate_only=validate_only
        )
        result = await execute_db_import(file_path=file_path, options=options)
        return result
    except ToreroError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Repository import failed: {str(e)}")
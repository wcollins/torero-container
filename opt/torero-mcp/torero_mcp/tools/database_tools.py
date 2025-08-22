"""database import/export tools for torero mcp server."""

import json
import logging
from typing import Optional

from ..executor import ToreroExecutor, ToreroExecutorError

logger = logging.getLogger(__name__)


async def export_database(
    executor: ToreroExecutor,
    format: str = "yaml"
) -> str:
    """export torero database configuration.
    
    exports all services, repositories, decorators, and secrets metadata
    to a yaml or json format that can be used for backup or migration.
    
    args:
        executor: toreroexecutor instance
        format: export format - either "yaml" or "json" (default: "yaml")
        
    returns:
        json string containing the exported configuration data
        
    examples:
        export to yaml format:
        >>> export_database(format="yaml")
        
        export to json format:
        >>> export_database(format="json")
    """
    try:
        if format not in ["yaml", "json"]:
            return json.dumps({
                "error": "invalid format. must be 'yaml' or 'json'",
                "supported_formats": ["yaml", "json"]
            }, indent=2)
        
        logger.info(f"exporting database in {format} format")
        result = await executor.export_database(format=format)
        
        return json.dumps({
            "status": "success",
            "format": format,
            "data": result
        }, indent=2)
        
    except ToreroExecutorError as e:
        logger.error(f"executor error exporting database: {e}")
        return json.dumps({
            "error": f"failed to export database: {e}"
        }, indent=2)
    except Exception as e:
        logger.exception("unexpected error exporting database")
        return json.dumps({
            "error": f"unexpected error: {e}"
        }, indent=2)


async def import_database(
    executor: ToreroExecutor,
    file_path: str,
    repository: Optional[str] = None,
    reference: Optional[str] = None,
    private_key: Optional[str] = None,
    force: bool = False,
    check: bool = False,
    validate_only: bool = False
) -> str:
    """import torero database configuration from a file or repository.
    
    args:
        executor: toreroexecutor instance
        file_path: path to the import file
        repository: optional repository url
        reference: optional branch/reference
        private_key: optional ssh private key name
        force: force import even with conflicts
        check: check for conflicts before importing
        validate_only: only validate without importing
        
    returns:
        json string with import result
    """
    try:
        logger.info(f"importing database from: {file_path}")
        result = await executor.import_database(
            file_path=file_path,
            repository=repository,
            reference=reference,
            private_key=private_key,
            force=force,
            check=check,
            validate_only=validate_only
        )
        
        return json.dumps({
            "status": "success",
            "file_path": file_path,
            "result": result,
            "options": {
                "force": force,
                "check": check,
                "validate_only": validate_only
            }
        }, indent=2)
        
    except ToreroExecutorError as e:
        logger.error(f"executor error importing database: {e}")
        return json.dumps({
            "error": f"failed to import database: {e}"
        }, indent=2)
    except Exception as e:
        logger.exception("unexpected error importing database")
        return json.dumps({
            "error": f"unexpected error: {e}"
        }, indent=2)
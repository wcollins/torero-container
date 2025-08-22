"""secret-related tools for torero mcp server."""

import json
import logging
from typing import Any, Dict, Optional

from ..executor import ToreroExecutorError, ToreroExecutor

logger = logging.getLogger(__name__)


async def list_secrets(
    executor: ToreroExecutor,
    secret_type: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = 100
) -> str:
    """
    list torero secrets with optional filtering (metadata only).
    
    args:
        executor: toreroexecutor instance
        secret_type: filter by secret type (e.g., 'password', 'api-key', 'token')
        tag: filter by tag
        limit: maximum number of secrets to return (default: 100)
        
    returns:
        json string containing list of secret metadata
    """
    try:
        secrets = await executor.get_secrets()
        
        # apply filters
        if secret_type:
            secrets = [s for s in secrets if s.get('type') == secret_type]
        if tag:
            secrets = [s for s in secrets if tag in s.get('tags', [])]
        
        # apply limit
        secrets = secrets[:limit]
        
        return json.dumps(secrets, indent=2)
    except ToreroExecutorError as e:
        return f"error listing secrets: {e}"
    except Exception as e:
        logger.exception("unexpected error in list_secrets")
        return f"unexpected error: {e}"


async def get_secret(executor: ToreroExecutor, name: str, include_value: bool = False) -> str:
    """
    get detailed information about a specific torero secret.
    
    args:
        executor: toreroexecutor instance
        name: name of the secret to retrieve
        include_value: whether to include the secret value (note: not supported via cli)
        
    returns:
        json string containing secret metadata
    """
    try:
        secrets = await executor.get_secrets()
        secret = next((s for s in secrets if s.get('name') == name), None)
        
        if secret:
            if include_value:
                # note: cli doesn't expose secret values for security
                secret['note'] = 'secret values not exposed via cli for security'
            return json.dumps(secret, indent=2)
        else:
            return f"secret '{name}' not found"
    except ToreroExecutorError as e:
        return f"error getting secret '{name}': {e}"
    except Exception as e:
        logger.exception(f"unexpected error getting secret '{name}'")
        return f"unexpected error: {e}"


async def list_secret_types(executor: ToreroExecutor) -> str:
    """
    get all available secret types.
    
    args:
        executor: toreroexecutor instance
    
    returns:
        json string containing list of secret types
    """
    try:
        secrets = await executor.get_secrets()
        types = sorted(set(s.get('type', 'unknown') for s in secrets))
        return json.dumps(types, indent=2)
    except ToreroExecutorError as e:
        return f"error listing secret types: {e}"
    except Exception as e:
        logger.exception("unexpected error in list_secret_types")
        return f"unexpected error: {e}"


# note: the following functions require api-level secret management
# which is not available through direct cli operations:
# - create_secret (requires api-level creation)
# - update_secret (requires api-level updates)
# - delete_secret (requires api-level deletion)
#
# secret information access is available through the functions above
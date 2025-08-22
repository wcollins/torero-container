"""repository-related tools for torero mcp server."""

import json
import logging
from typing import Any, Dict, Optional

from ..executor import ToreroExecutorError, ToreroExecutor

logger = logging.getLogger(__name__)


async def list_repositories(
    executor: ToreroExecutor,
    repo_type: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = 100
) -> str:
    """
    list torero repositories with optional filtering.
    
    args:
        executor: toreroexecutor instance
        repo_type: filter by repository type (e.g., 'file', 'git', 's3')
        tag: filter by tag
        limit: maximum number of repositories to return (default: 100)
        
    returns:
        json string containing list of repositories
    """
    try:
        repositories = await executor.get_repositories()
        
        # apply filters
        if repo_type:
            repositories = [r for r in repositories if r.get('type') == repo_type]
        if tag:
            repositories = [r for r in repositories if tag in r.get('tags', [])]
        
        # apply limit
        repositories = repositories[:limit]
        
        return json.dumps(repositories, indent=2)
    except ToreroExecutorError as e:
        return f"error listing repositories: {e}"
    except Exception as e:
        logger.exception("unexpected error in list_repositories")
        return f"unexpected error: {e}"


async def get_repository(executor: ToreroExecutor, name: str) -> str:
    """
    get detailed information about a specific torero repository.
    
    args:
        executor: toreroexecutor instance
        name: name of the repository to retrieve
        
    returns:
        json string containing repository details
    """
    try:
        repositories = await executor.get_repositories()
        repository = next((r for r in repositories if r.get('name') == name), None)
        
        if repository:
            return json.dumps(repository, indent=2)
        else:
            return f"repository '{name}' not found"
    except ToreroExecutorError as e:
        return f"error getting repository '{name}': {e}"
    except Exception as e:
        logger.exception(f"unexpected error getting repository '{name}'")
        return f"unexpected error: {e}"


async def list_repository_types(executor: ToreroExecutor) -> str:
    """
    get all available repository types.
    
    args:
        executor: toreroexecutor instance
    
    returns:
        json string containing list of repository types
    """
    try:
        repositories = await executor.get_repositories()
        types = sorted(set(r.get('type', 'unknown') for r in repositories))
        return json.dumps(types, indent=2)
    except ToreroExecutorError as e:
        return f"error listing repository types: {e}"
    except Exception as e:
        logger.exception("unexpected error in list_repository_types")
        return f"unexpected error: {e}"


# note: the following functions require api-level repository management
# which is not available through direct cli operations:
# - sync_repository (requires api-level sync operations)
# - create_repository (requires api-level creation)
# - delete_repository (requires api-level deletion)
#
# repository information access is available through the functions above
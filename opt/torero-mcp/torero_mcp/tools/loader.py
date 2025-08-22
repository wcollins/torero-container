"""dynamic tool loader for torero mcp server."""

import importlib
import inspect
import logging
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List

from ..executor import ToreroExecutor

logger = logging.getLogger(__name__)


class ToolLoader:
    """dynamically loads and registers mcp tools."""
    
    def __init__(self, executor: ToreroExecutor):
        """
        initialize the tool loader.
        
        args:
            executor: toreroexecutor instance to pass to tools
        """
        self.executor = executor
        self.tools: Dict[str, Callable] = {}
    
    def discover_tools(self) -> List[str]:
        """
        discover all tool modules in the tools directory.
        
        returns:
            list of module names containing tools
        """
        tools_dir = Path(__file__).parent
        tool_modules = []
        
        for file_path in tools_dir.glob("*_tools.py"):
            module_name = file_path.stem
            tool_modules.append(f"torero_mcp.tools.{module_name}")
            
        logger.info(f"discovered tool modules: {tool_modules}")
        return tool_modules
    
    def load_tools_from_module(self, module_name: str) -> Dict[str, Callable]:
        """
        load all async functions from a module as tools.
        
        args:
            module_name: name of the module to load tools from
            
        returns:
            dictionary mapping tool names to functions
        """
        try:
            module = importlib.import_module(module_name)
            tools = {}
            
            for name, obj in inspect.getmembers(module):
                if (inspect.iscoroutinefunction(obj) and 
                    not name.startswith('_') and
                    name != 'executor'):  # exclude private functions and executor
                    
                    # store the original function with its executor parameter
                    tools[name] = obj
                    logger.debug(f"loaded tool: {name} from {module_name}")
            
            return tools
            
        except Exception as e:
            logger.error(f"failed to load tools from {module_name}: {e}")
            return {}
    
    def load_all_tools(self) -> Dict[str, Callable]:
        """
        load all tools from all discovered modules.
        
        returns:
            dictionary mapping tool names to functions
        """
        all_tools = {}
        
        for module_name in self.discover_tools():
            module_tools = self.load_tools_from_module(module_name)
            
            # check for name conflicts
            for tool_name, tool_func in module_tools.items():
                if tool_name in all_tools:
                    logger.warning(f"tool name conflict: {tool_name} found in multiple modules")
                all_tools[tool_name] = tool_func
        
        self.tools = all_tools
        logger.info(f"loaded {len(all_tools)} tools: {list(all_tools.keys())}")
        return all_tools
    
    def get_tool(self, name: str) -> Callable:
        """
        get a specific tool by name.
        
        args:
            name: name of the tool to retrieve
            
        returns:
            tool function
            
        raises:
            keyerror: if tool is not found
        """
        if name not in self.tools:
            raise KeyError(f"tool '{name}' not found. available tools: {list(self.tools.keys())}")
        
        return self.tools[name]
"""Dynamic tool loader for torero MCP server."""

import importlib
import inspect
import logging
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List

from ..client import ToreroClient

logger = logging.getLogger(__name__)


class ToolLoader:
    """Dynamically loads and registers MCP tools."""
    
    def __init__(self, client: ToreroClient):
        """
        Initialize the tool loader.
        
        Args:
            client: ToreroClient instance to pass to tools
        """
        self.client = client
        self.tools: Dict[str, Callable] = {}
    
    def discover_tools(self) -> List[str]:
        """
        Discover all tool modules in the tools directory.
        
        Returns:
            List of module names containing tools
        """
        tools_dir = Path(__file__).parent
        tool_modules = []
        
        for file_path in tools_dir.glob("*_tools.py"):
            module_name = file_path.stem
            tool_modules.append(f"torero_mcp.tools.{module_name}")
            
        logger.info(f"Discovered tool modules: {tool_modules}")
        return tool_modules
    
    def load_tools_from_module(self, module_name: str) -> Dict[str, Callable]:
        """
        Load all async functions from a module as tools.
        
        Args:
            module_name: Name of the module to load tools from
            
        Returns:
            Dictionary mapping tool names to functions
        """
        try:
            module = importlib.import_module(module_name)
            tools = {}
            
            for name, obj in inspect.getmembers(module):
                if (inspect.iscoroutinefunction(obj) and 
                    not name.startswith('_') and
                    name != 'client'):  # Exclude private functions and client
                    
                    # Store the original function with its client parameter
                    tools[name] = obj
                    logger.debug(f"Loaded tool: {name} from {module_name}")
            
            return tools
            
        except Exception as e:
            logger.error(f"Failed to load tools from {module_name}: {e}")
            return {}
    
    def load_all_tools(self) -> Dict[str, Callable]:
        """
        Load all tools from all discovered modules.
        
        Returns:
            Dictionary mapping tool names to functions
        """
        all_tools = {}
        
        for module_name in self.discover_tools():
            module_tools = self.load_tools_from_module(module_name)
            
            # Check for name conflicts
            for tool_name, tool_func in module_tools.items():
                if tool_name in all_tools:
                    logger.warning(f"Tool name conflict: {tool_name} found in multiple modules")
                all_tools[tool_name] = tool_func
        
        self.tools = all_tools
        logger.info(f"Loaded {len(all_tools)} tools: {list(all_tools.keys())}")
        return all_tools
    
    def get_tool(self, name: str) -> Callable:
        """
        Get a specific tool by name.
        
        Args:
            name: Name of the tool to retrieve
            
        Returns:
            Tool function
            
        Raises:
            KeyError: If tool is not found
        """
        if name not in self.tools:
            raise KeyError(f"Tool '{name}' not found. Available tools: {list(self.tools.keys())}")
        
        return self.tools[name]
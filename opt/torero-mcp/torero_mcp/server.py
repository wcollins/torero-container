"""MCP server implementation for torero."""

import logging
from typing import Any, Dict, List, Optional, Sequence

from fastmcp import FastMCP
from pydantic import BaseModel, Field

from .client import ToreroClient, ToreroAPIError
from .config import Config
from .tools.loader import ToolLoader

logger = logging.getLogger(__name__)


class ToreroMCPServer:
    """MCP server for torero API integration."""
    
    def __init__(self, config: Config):
        """
        Initialize the torero MCP server.
        
        Args:
            config: Server configuration
        """
        self.config = config
        self.client = ToreroClient(config.api)
        self.mcp = FastMCP(config.mcp.name)
        self.tool_loader = ToolLoader(self.client)
        self._setup_tools()
    
    def _setup_tools(self) -> None:
        """Set up MCP tools dynamically."""
        import inspect
        from functools import wraps
        
        # Load all tools from the tools directory
        tools = self.tool_loader.load_all_tools()
        
        # Register each tool with FastMCP
        registered_count = 0
        for tool_name, tool_func in tools.items():
            try:
                # Get the function signature
                sig = inspect.signature(tool_func)
                params = list(sig.parameters.values())
                
                # Skip the client parameter
                if params and params[0].name == 'client':
                    params = params[1:]
                
                # For functions with no parameters (except client), create a simple wrapper
                if len(params) == 0:
                    # Create a factory function that returns a wrapper
                    def make_wrapper(func, client):
                        async def wrapper():
                            return await func(client)
                        wrapper.__name__ = func.__name__
                        wrapper.__doc__ = func.__doc__
                        return wrapper
                    
                    wrapper = make_wrapper(tool_func, self.client)
                else:
                    # For functions with parameters, use the existing wrapper creation
                    wrapper = self._create_tool_wrapper(tool_func)
                
                # Register the wrapper with FastMCP
                decorated_tool = self.mcp.tool()(wrapper)
                logger.debug(f"Registered tool: {tool_name}")
                registered_count += 1
            except Exception as e:
                logger.error(f"Failed to register tool {tool_name}: {e}")
        
        logger.info(f"Successfully registered {registered_count} tools")
    
    def _create_tool_wrapper(self, tool_func):
        """Create a wrapper function that injects the client parameter."""
        import inspect
        from functools import wraps
        
        # Get function signature and parameters
        sig = inspect.signature(tool_func)
        params = list(sig.parameters.values())
        
        # Skip the client parameter
        if params and params[0].name == 'client':
            params = params[1:]
        
        # Create a dynamic wrapper that preserves parameter names
        def create_wrapper():
            # Build parameter names and defaults
            param_names = [p.name for p in params]
            param_defaults = {}
            
            for p in params:
                if p.default != inspect.Parameter.empty:
                    param_defaults[p.name] = p.default
            
            # Create wrapper function dynamically
            @wraps(tool_func)
            async def wrapper(**kwargs):
                # Fill missing parameters with defaults
                for name in param_names:
                    if name not in kwargs and name in param_defaults:
                        kwargs[name] = param_defaults[name]
                
                # Call original function with client and provided kwargs
                return await tool_func(self.client, **kwargs)
            
            # Preserve original signature (without client parameter)
            wrapper.__signature__ = inspect.Signature(params)
            wrapper.__name__ = tool_func.__name__
            wrapper.__doc__ = tool_func.__doc__
            
            return wrapper
        
        return create_wrapper()
    
    async def test_connection(self) -> None:
        """Test API connection."""
        try:
            await self.client.health_check()
            logger.info("Successfully connected to torero API")
        except Exception as e:
            logger.warning(f"Could not connect to torero API: {e}")
            logger.info("Server will start anyway, but tools may fail")

    def run(self) -> None:
        """Run the MCP server."""
        logger.info(f"Starting torero MCP server '{self.config.mcp.name}'")
        logger.info(f"Connecting to torero API at: {self.config.api.base_url}")
        
        transport_config = self.config.mcp.transport
        logger.info(f"Using {transport_config.type} transport")
        
        # Add ready signal for AnythingLLM
        logger.info("🚀 torero MCP server is ready for connections")
        # Only print to stdout for non-stdio transports to avoid interfering with JSON-RPC protocol
        if transport_config.type != "stdio":
            print("🚀 torero MCP server is ready for connections", flush=True)
        
        # Let FastMCP handle the event loop with appropriate transport
        if transport_config.type == "stdio":
            self.mcp.run()
        elif transport_config.type == "sse":
            logger.info(f"Starting SSE server on {transport_config.host}:{transport_config.port}")
            logger.info(f"SSE endpoint: {transport_config.path}")
            self.mcp.run(
                transport="sse",
                host=transport_config.host,
                port=transport_config.port,
                path=transport_config.path
            )
        elif transport_config.type == "streamable_http":
            logger.info(f"Starting Streamable HTTP server on {transport_config.host}:{transport_config.port}")
            self.mcp.run(
                transport="streamable_http",
                host=transport_config.host,
                port=transport_config.port
            )
        else:
            raise ValueError(f"Unknown transport type: {transport_config.type}")
    
    async def close(self) -> None:
        """Close the server and cleanup resources."""
        await self.client.close()
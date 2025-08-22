"""mcp server implementation for torero."""

import logging
from typing import Any, Dict, List, Optional, Sequence

from fastmcp import FastMCP
from pydantic import BaseModel, Field

from .executor import ToreroExecutor, ToreroExecutorError
from .config import Config
from .tools.loader import ToolLoader

logger = logging.getLogger(__name__)


class ToreroMCPServer:
    """mcp server for torero direct cli integration."""
    
    def __init__(self, config: Config):
        """
        initialize the torero mcp server.
        
        args:
            config: server configuration
        """
        self.config = config
        self.executor = ToreroExecutor(timeout=config.executor.timeout)
        self.mcp = FastMCP(config.mcp.name)
        self.tool_loader = ToolLoader(self.executor)
        self._setup_tools()
    
    def _setup_tools(self) -> None:
        """set up mcp tools dynamically."""
        import inspect
        from functools import wraps
        
        # load all tools from the tools directory
        tools = self.tool_loader.load_all_tools()
        
        # register each tool with fastmcp
        registered_count = 0
        for tool_name, tool_func in tools.items():
            try:
                # get the function signature
                sig = inspect.signature(tool_func)
                params = list(sig.parameters.values())
                
                # skip the executor parameter
                if params and params[0].name == 'executor':
                    params = params[1:]
                
                # for functions with no parameters (except executor), create a simple wrapper
                if len(params) == 0:
                    # create a factory function that returns a wrapper
                    def make_wrapper(func, executor):
                        async def wrapper():
                            return await func(executor)
                        wrapper.__name__ = func.__name__
                        wrapper.__doc__ = func.__doc__
                        return wrapper
                    
                    wrapper = make_wrapper(tool_func, self.executor)
                else:
                    # for functions with parameters, use the existing wrapper creation
                    wrapper = self._create_tool_wrapper(tool_func)
                
                # register the wrapper with fastmcp
                decorated_tool = self.mcp.tool()(wrapper)
                logger.debug(f"registered tool: {tool_name}")
                registered_count += 1
            except Exception as e:
                logger.error(f"failed to register tool {tool_name}: {e}")
        
        logger.info(f"successfully registered {registered_count} tools")
    
    def _create_tool_wrapper(self, tool_func):
        """create a wrapper function that injects the executor parameter."""
        import inspect
        from functools import wraps
        
        # get function signature and parameters
        sig = inspect.signature(tool_func)
        params = list(sig.parameters.values())
        
        # skip the executor parameter
        if params and params[0].name == 'executor':
            params = params[1:]
        
        # create a dynamic wrapper that preserves parameter names
        def create_wrapper():
            # build parameter names and defaults
            param_names = [p.name for p in params]
            param_defaults = {}
            
            for p in params:
                if p.default != inspect.Parameter.empty:
                    param_defaults[p.name] = p.default
            
            # create wrapper function dynamically
            @wraps(tool_func)
            async def wrapper(**kwargs):
                # fill missing parameters with defaults
                for name in param_names:
                    if name not in kwargs and name in param_defaults:
                        kwargs[name] = param_defaults[name]
                
                # call original function with executor and provided kwargs
                return await tool_func(self.executor, **kwargs)
            
            # preserve original signature (without executor parameter)
            wrapper.__signature__ = inspect.Signature(params)
            wrapper.__name__ = tool_func.__name__
            wrapper.__doc__ = tool_func.__doc__
            
            return wrapper
        
        return create_wrapper()
    
    async def test_connection(self) -> None:
        """test torero cli connection."""
        try:
            is_available, message = self.executor.check_torero_available()
            if is_available:
                logger.info("successfully connected to torero cli")
            else:
                logger.warning(f"torero cli not available: {message}")
                logger.info("server will start anyway, but tools may fail")
        except Exception as e:
            logger.warning(f"could not test torero cli: {e}")
            logger.info("server will start anyway, but tools may fail")

    def run(self) -> None:
        """run the mcp server."""
        logger.info(f"starting torero mcp server '{self.config.mcp.name}'")
        logger.info("using direct torero cli integration")
        
        transport_config = self.config.mcp.transport
        logger.info(f"using {transport_config.type} transport")
        
        # add ready signal for anythingllm
        logger.info("🚀 torero mcp server is ready for connections")
        # only print to stdout for non-stdio transports to avoid interfering with json-rpc protocol
        if transport_config.type != "stdio":
            print("🚀 torero mcp server is ready for connections", flush=True)
        
        # let fastmcp handle the event loop with appropriate transport
        if transport_config.type == "stdio":
            self.mcp.run()
        elif transport_config.type == "sse":
            logger.info(f"starting sse server on {transport_config.host}:{transport_config.port}")
            logger.info(f"sse endpoint: {transport_config.path}")
            self.mcp.run(
                transport="sse",
                host=transport_config.host,
                port=transport_config.port,
                path=transport_config.path
            )
        elif transport_config.type == "streamable_http":
            logger.info(f"starting streamable http server on {transport_config.host}:{transport_config.port}")
            self.mcp.run(
                transport="streamable_http",
                host=transport_config.host,
                port=transport_config.port
            )
        else:
            raise ValueError(f"unknown transport type: {transport_config.type}")
    
    async def close(self) -> None:
        """Close the server and cleanup resources.
        
        Performs cleanup operations when shutting down the MCP server.
        This method is primarily used for resource cleanup and graceful shutdown.
        """
        # no cleanup needed for direct cli integration
        logger.info("mcp server shutdown complete")
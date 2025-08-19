"""
Server module for torero-api

This module provides functionality to start and configure the FastAPI server
that serves the torero API.
"""

import logging
import os
import sys
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi

from torero_api.api.v1.endpoints import services, decorators, repositories, secrets, execution, registries, database
from torero_api.models.common import APIInfo, ErrorResponse
from torero_api.middleware.execution_tracker import ExecutionTrackerMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger("torero-api")

def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application instance.
    
    Returns:
        FastAPI: Configured FastAPI application
    """

    # Create FastAPI application
    app = FastAPI(
        title="torero API", 
        version="0.1.0",
        description="""
        RESTful API for interacting with torero services.
        
        This API provides endpoints for discovering and managing torero services,
        allowing you to list services, filter by type or tag, and get metadata
        about available service types and tags.
        
        Model Context Protocol (MCP) Integration:
        This API follows OpenAPI standards and provides comprehensive type
        information for seamless integration with MCP-enabled applications.
        """
    )
    
    # Add execution tracking middleware
    ui_base_url = os.environ.get("TORERO_UI_BASE_URL", "http://localhost:8001")
    app.add_middleware(ExecutionTrackerMiddleware, ui_base_url=ui_base_url)
    
    # Include the routers
    app.include_router(services.router, prefix="/v1/services", tags=["services"])
    app.include_router(decorators.router, prefix="/v1/decorators", tags=["decorators"])
    app.include_router(repositories.router, prefix="/v1/repositories", tags=["repositories"])
    app.include_router(secrets.router, prefix="/v1/secrets", tags=["secrets"])
    app.include_router(registries.router, prefix="/v1/registries", tags=["registries"])
    app.include_router(execution.router, prefix="/v1/execute", tags=["execution"])
    app.include_router(database.router, prefix="/v1", tags=["database"])
    
    # Root endpoint
    @app.get("/", response_model=APIInfo, tags=["root"], 
             summary="API information",
             description="Returns basic information about the API and available endpoints.")
    async def root():
        """
        Return basic information about the API and available endpoints.
        
        This endpoint serves as an entry point to the API, providing metadata
        about the API itself and links to the main endpoints following the
        HATEOAS (Hypermedia as the Engine of Application State) principle.
        """
        logger.debug("Root endpoint called")
        api_port = os.environ.get("TORERO_API_PORT", "8000")
        api_host = os.environ.get("TORERO_API_HOST", "localhost")
        
        return APIInfo(
            name="torero API",
            version="0.1.0",
            description="API for torero services",
            documentation=f"http://{api_host}:{api_port}/docs",
            endpoints={
                "services": f"http://{api_host}:{api_port}/v1/services/",
                "service_types": f"http://{api_host}:{api_port}/v1/services/types",
                "service_tags": f"http://{api_host}:{api_port}/v1/services/tags",
                "decorators": f"http://{api_host}:{api_port}/v1/decorators/",
                "decorator_types": f"http://{api_host}:{api_port}/v1/decorators/types",
                "repositories": f"http://{api_host}:{api_port}/v1/repositories/",
                "repository_types": f"http://{api_host}:{api_port}/v1/repositories/types",
                "secrets": f"http://{api_host}:{api_port}/v1/secrets/",
                "secret_types": f"http://{api_host}:{api_port}/v1/secrets/types",
                "registries": f"http://{api_host}:{api_port}/v1/registries/",
                "registry_types": f"http://{api_host}:{api_port}/v1/registries/types",
                "execute": f"http://{api_host}:{api_port}/v1/execute/",
                "database_export": f"http://{api_host}:{api_port}/v1/db/export",
                "database_import": f"http://{api_host}:{api_port}/v1/db/import",
            }
        )
    
    # Health check endpoint
    @app.get("/health", tags=["system"], 
             summary="API health check",
             description="Check if the API is operational and can connect to torero.")
    async def health_check():
        """
        Check if the API is operational and can connect to torero.
        
        This endpoint attempts to execute a simple torero command to verify
        that the API can communicate with the torero CLI.
        """
        from torero_api.core.torero_executor import check_torero_available
        
        try:
            is_available, message = check_torero_available()
            
            if is_available:
                return {"status": "healthy", "torero_available": True}
            else:
                logger.warning(f"torero health check failed: {message}")
                return JSONResponse(
                    status_code=503,
                    content={
                        "status": "unhealthy", 
                        "torero_available": False, 
                        "reason": message
                    }
                )
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy", 
                    "torero_available": False, 
                    "reason": f"Error checking torero: {str(e)}"
                }
            )
    
    # Custom exception handler for consistent error responses
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """
        Custom exception handler for HTTPExceptions.
        
        Transforms HTTPExceptions into a consistent error response format.
        """
        error = ErrorResponse(
            status_code=exc.status_code,
            detail=str(exc.detail),
            error_type="http_error",
            path=request.url.path
        )
        return JSONResponse(status_code=exc.status_code, content=error.model_dump())
    
    # Exception handler for unexpected errors
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        """
        Generic exception handler for unexpected errors.
        
        Catches any unhandled exceptions and returns a formatted error response.
        """
        import traceback
        logger.error(f"Unhandled exception: {str(exc)}")
        logger.error(traceback.format_exc())
        
        error = ErrorResponse(
            status_code=500,
            detail=f"Internal server error: {str(exc)}",
            error_type="server_error",
            path=request.url.path
        )
        return JSONResponse(status_code=500, content=error.model_dump())
    
    # Custom OpenAPI schema with enhanced metadata for MCP
    def custom_openapi():
        """
        Generate a custom OpenAPI schema with enhanced metadata for MCP compatibility.
        
        This function extends the default OpenAPI schema with additional information
        that helps MCP systems better understand the API structure and capabilities.
        """
        if app.openapi_schema:
            return app.openapi_schema
        
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        
        # Add custom MCP-related metadata
        openapi_schema["info"]["x-mcp-compatible"] = True
        openapi_schema["info"]["x-mcp-version"] = "1.0"
        openapi_schema["info"]["x-mcp-description"] = "This API is optimized for Model Context Protocol integration."
        
        # Add contact information
        openapi_schema["info"]["contact"] = {
            "name": "torero Development Team",
            "url": "https://torero.dev/contact",
            "email": "opensource@itential.com"
        }
        
        # Add license information
        openapi_schema["info"]["license"] = {
            "name": "Apache License 2.0",
            "url": "https://www.apache.org/licenses/LICENSE-2.0"
        }
        
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    
    # Set custom OpenAPI schema generator
    app.openapi = custom_openapi
    
    return app

def start_server(host: str = "0.0.0.0", port: int = 8000, log_level: str = "info", reload: bool = False):
    """
    Start the FastAPI server using Uvicorn.
    
    Args:
        host: The host to bind the server to
        port: The port to bind the server to
        log_level: The log level to use
        reload: Whether to enable auto-reload
    """
    logger.info(f"Starting torero API server on {host}:{port} with log level {log_level}")
    
    # Set environment variables for the API to use
    os.environ["TORERO_API_PORT"] = str(port)
    os.environ["TORERO_API_HOST"] = host
    
    try:
        # Start the server
        uvicorn.run(
            "torero_api.server:app",
            host=host,
            port=port,
            log_level=log_level,
            reload=reload
        )
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        raise

# Create the app instance
app = create_app()

# Make sure these are exported at module level
__all__ = ["app", "create_app", "start_server"]
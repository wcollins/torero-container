"""Middleware for automatic execution tracking to torero-ui database."""

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

import httpx
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from dateutil import parser as date_parser

logger = logging.getLogger(__name__)


class ExecutionTrackerMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically track all service executions to the UI database."""
    
    def __init__(self, app, ui_base_url: str = "http://localhost:8001"):
        super().__init__(app)
        self.ui_base_url = ui_base_url
        self.execution_endpoints = [
            "/v1/execute/python-script/",
            "/v1/execute/ansible-playbook/", 
            "/v1/execute/opentofu-plan/"
        ]
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process the request and track executions."""
        
        # Check if this is an execution endpoint
        path = request.url.path
        is_execution_request = any(path.startswith(endpoint) for endpoint in self.execution_endpoints)
        
        if not is_execution_request:
            return await call_next(request)
        
        # Get service name and type from path
        service_name, service_type = self._extract_service_info(path)
        
        if not service_name or not service_type:
            return await call_next(request)
        
        # Execute the original request
        response = await call_next(request)
        
        # Track execution if successful
        if response.status_code == 200:
            # Create a new response that captures the body
            from starlette.responses import JSONResponse
            import io
            
            try:
                # Read the response body
                body = b""
                async for chunk in response.body_iterator:
                    body += chunk
                
                # Parse and track the execution
                execution_data = json.loads(body.decode())
                await self._track_execution_with_data(service_name, service_type, execution_data)
                
                # Return a new response with the same body
                return JSONResponse(content=execution_data, status_code=response.status_code, headers=dict(response.headers))
                
            except Exception as e:
                logger.error(f"Failed to intercept response for tracking: {e}")
                # Return original response if tracking fails
                return response
        
        return response
    
    def _extract_service_info(self, path: str) -> tuple[Optional[str], Optional[str]]:
        """Extract service name and type from request path."""
        try:
            if "/v1/execute/python-script/" in path:
                service_name = path.split("/v1/execute/python-script/")[1].split("/")[0]
                return service_name, "python-script"
            elif "/v1/execute/ansible-playbook/" in path:
                service_name = path.split("/v1/execute/ansible-playbook/")[1].split("/")[0]
                return service_name, "ansible-playbook"
            elif "/v1/execute/opentofu-plan/" in path and "/apply" in path:
                service_name = path.split("/v1/execute/opentofu-plan/")[1].split("/apply")[0]
                return service_name, "opentofu-plan"
            elif "/v1/execute/opentofu-plan/" in path and "/destroy" in path:
                service_name = path.split("/v1/execute/opentofu-plan/")[1].split("/destroy")[0]
                return service_name, "opentofu-plan"
        except Exception:
            logger.warning(f"Failed to extract service info from path: {path}")
        
        return None, None
    
    async def _track_execution_with_data(
        self, 
        service_name: str, 
        service_type: str,
        execution_data: Dict[str, Any]
    ):
        """Track execution asynchronously without blocking the response."""
        asyncio.create_task(
            self._record_execution_data(service_name, service_type, execution_data)
        )
    
    async def _record_execution_data(
        self, 
        service_name: str, 
        service_type: str,
        execution_data: Dict[str, Any]
    ):
        """Record execution to the UI database."""
        try:
            # Prepare data for UI recording
            api_execution_data = {
                "return_code": execution_data.get("return_code", 1),
                "stdout": execution_data.get("stdout", ""),
                "stderr": execution_data.get("stderr", ""),
                "start_time": execution_data.get("start_time"),
                "end_time": execution_data.get("end_time"),
                "elapsed_time": execution_data.get("elapsed_time", 0.0)
            }
            
            # Send to UI for recording
            await self._send_to_ui(service_name, service_type, api_execution_data)
            
            logger.info(f"Successfully tracked execution: {service_name} ({service_type})")
            
        except Exception as e:
            logger.error(f"Failed to track execution for {service_name}: {e}")
    
    async def _send_to_ui(self, service_name: str, service_type: str, execution_data: Dict[str, Any]):
        """Send execution data to the UI for recording."""
        try:
            url = f"{self.ui_base_url}/api/record-execution/"
            payload = {
                "service_name": service_name,
                "service_type": service_type,
                "execution_data": execution_data
            }
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                
        except Exception as e:
            logger.error(f"Failed to send execution data to UI: {e}")
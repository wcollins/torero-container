"""Configuration management for torero MCP server."""

import os
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml
from pydantic import BaseModel, Field, field_validator


class AuthConfig(BaseModel):
    """Authentication configuration."""
    
    type: str = Field(..., description="Authentication type (bearer, basic)")
    token: Optional[str] = Field(None, description="Bearer token")
    username: Optional[str] = Field(None, description="Basic auth username")
    password: Optional[str] = Field(None, description="Basic auth password")
    
    @field_validator("type")
    @classmethod
    def validate_auth_type(cls, v: str) -> str:
        """Validate authentication type."""
        if v not in ["bearer", "basic"]:
            raise ValueError("Auth type must be 'bearer' or 'basic'")
        return v


class APIConfig(BaseModel):
    """API configuration."""
    
    base_url: str = Field(
        default="http://localhost:8000",
        description="Base URL for the torero API"
    )
    timeout: int = Field(default=30, description="Request timeout in seconds")
    verify_ssl: bool = Field(default=True, description="Verify SSL certificates")
    auth: Optional[AuthConfig] = Field(None, description="Authentication config")


class LoggingConfig(BaseModel):
    """Logging configuration."""
    
    level: str = Field(default="INFO", description="Logging level")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format"
    )
    file: Optional[str] = Field(None, description="Log file path")
    
    @field_validator("level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate logging level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()


class TransportConfig(BaseModel):
    """Transport configuration for MCP server."""
    
    type: str = Field(default="stdio", description="Transport type: stdio, sse, or streamable_http")
    host: str = Field(default="127.0.0.1", description="Host for SSE/HTTP transport")
    port: int = Field(default=8000, description="Port for SSE/HTTP transport")
    path: str = Field(default="/sse", description="SSE endpoint path")
    
    @field_validator("type")
    @classmethod
    def validate_transport_type(cls, v: str) -> str:
        """Validate transport type."""
        if v not in ["stdio", "sse", "streamable_http"]:
            raise ValueError("Transport type must be 'stdio', 'sse', or 'streamable_http'")
        return v


class MCPConfig(BaseModel):
    """MCP server configuration."""
    
    name: str = Field(default="torero", description="Server name")
    version: str = Field(default="0.1.0", description="Server version")
    transport: TransportConfig = Field(default_factory=TransportConfig, description="Transport configuration")


class Config(BaseModel):
    """Main configuration."""
    
    api: APIConfig = Field(default_factory=APIConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    mcp: MCPConfig = Field(default_factory=MCPConfig)


def load_config(config_path: Optional[Union[str, Path]] = None) -> Config:
    """
    Load configuration from file and environment variables.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Config: Loaded configuration
    """
    config_data: Dict[str, Any] = {}
    
    # Load from file if provided
    if config_path:
        config_file = Path(config_path)
        if config_file.exists():
            with open(config_file, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f) or {}
    
    # Override with environment variables
    env_overrides = {
        "api": {
            "base_url": os.getenv("TORERO_API_BASE_URL"),
            "timeout": os.getenv("TORERO_API_TIMEOUT"),
            "verify_ssl": os.getenv("TORERO_API_VERIFY_SSL"),
        },
        "logging": {
            "level": os.getenv("TORERO_LOG_LEVEL"),
            "file": os.getenv("TORERO_LOG_FILE"),
        },
        "mcp": {
            "transport": {
                "type": os.getenv("TORERO_MCP_TRANSPORT_TYPE"),
                "host": os.getenv("TORERO_MCP_TRANSPORT_HOST"),
                "port": os.getenv("TORERO_MCP_TRANSPORT_PORT"),
                "path": os.getenv("TORERO_MCP_TRANSPORT_PATH"),
            }
        }
    }
    
    # Merge environment overrides
    for section, values in env_overrides.items():
        if section not in config_data:
            config_data[section] = {}
        
        if isinstance(values, dict):
            for key, value in values.items():
                if isinstance(value, dict):
                    # Handle nested config like transport
                    if key not in config_data[section]:
                        config_data[section][key] = {}
                    for sub_key, sub_value in value.items():
                        if sub_value is not None:
                            # Convert string values to appropriate types
                            if sub_key == "port":
                                sub_value = int(sub_value)
                            config_data[section][key][sub_key] = sub_value
                elif value is not None:
                    # Convert string values to appropriate types
                    if key == "timeout":
                        value = int(value)
                    elif key == "verify_ssl":
                        value = value.lower() in ("true", "1", "yes", "on")
                    config_data[section][key] = value
    
    return Config(**config_data)


def setup_logging(config: LoggingConfig) -> None:
    """
    Set up logging based on configuration.
    
    Args:
        config: Logging configuration
    """
    # Configure logging
    log_config = {
        "level": getattr(logging, config.level),
        "format": config.format,
    }
    
    if config.file:
        log_config["filename"] = config.file
        log_config["filemode"] = "a"
    
    logging.basicConfig(**log_config)
    
    # Set httpx logging to WARNING to reduce noise
    logging.getLogger("httpx").setLevel(logging.WARNING)
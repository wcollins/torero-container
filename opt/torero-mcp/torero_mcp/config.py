"""configuration management for torero mcp server."""

import os
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml
from pydantic import BaseModel, Field, field_validator


class LoggingConfig(BaseModel):
    """Logging configuration for the MCP server."""
    
    level: str = Field(default="INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Python logging format string"
    )
    file: Optional[str] = Field(None, description="Optional log file path for file-based logging")
    
    @field_validator("level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate that the logging level is supported by Python's logging module."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()


class TransportConfig(BaseModel):
    """Transport configuration for the MCP server communication layer."""
    
    type: str = Field(
        default="stdio", 
        description="Transport protocol: stdio for direct process communication, sse for Server-Sent Events, or streamable_http for HTTP streaming"
    )
    host: str = Field(default="127.0.0.1", description="Host address for network-based transports (sse, streamable_http)")
    port: int = Field(default=8000, description="Network port for network-based transports (sse, streamable_http)")
    path: str = Field(default="/sse", description="URL path for Server-Sent Events endpoint")
    
    @field_validator("type")
    @classmethod
    def validate_transport_type(cls, v: str) -> str:
        """Validate that the transport type is one of the supported MCP transport protocols."""
        if v not in ["stdio", "sse", "streamable_http"]:
            raise ValueError("Transport type must be 'stdio', 'sse', or 'streamable_http'")
        return v


class ExecutorConfig(BaseModel):
    """Configuration for the torero CLI executor."""
    
    timeout: int = Field(default=30, description="Default timeout in seconds for torero CLI commands")
    torero_command: str = Field(default="torero", description="Path or name of the torero CLI executable")


class MCPConfig(BaseModel):
    """Core MCP server configuration."""
    
    name: str = Field(default="torero", description="Name identifier for this MCP server instance")
    version: str = Field(default="0.1.0", description="Version of this MCP server implementation")
    transport: TransportConfig = Field(default_factory=TransportConfig, description="Transport layer configuration")


class Config(BaseModel):
    """Main configuration object containing all server settings."""
    
    logging: LoggingConfig = Field(default_factory=LoggingConfig, description="Logging configuration")
    mcp: MCPConfig = Field(default_factory=MCPConfig, description="MCP server configuration")
    executor: ExecutorConfig = Field(default_factory=ExecutorConfig, description="torero CLI executor configuration")


def load_config(config_path: Optional[Union[str, Path]] = None) -> Config:
    """
    Load configuration from YAML file and environment variables.
    
    Environment variables take precedence over file configuration.
    The configuration supports nested structures for organizing related settings.
    
    Args:
        config_path: Optional path to a YAML configuration file. If None, only environment variables are used.
        
    Returns:
        Config: A validated configuration object with all settings loaded and validated.
        
    Environment Variables:
        - TORERO_LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        - TORERO_LOG_FILE: Path to log file (optional)
        - TORERO_MCP_TRANSPORT_TYPE: Transport type (stdio, sse, streamable_http)
        - TORERO_MCP_TRANSPORT_HOST: Host for network transports
        - TORERO_MCP_TRANSPORT_PORT: Port for network transports
        - TORERO_MCP_TRANSPORT_PATH: Path for SSE endpoint
        - TORERO_CLI_TIMEOUT: Timeout for torero CLI commands in seconds
    """
    config_data: Dict[str, Any] = {}
    
    # load from yaml file if provided
    if config_path:
        config_file = Path(config_path)
        if config_file.exists():
            with open(config_file, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f) or {}
    
    # override with environment variables
    env_overrides = {
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
        },
        "executor": {
            "timeout": os.getenv("TORERO_CLI_TIMEOUT"),
            "torero_command": os.getenv("TORERO_CLI_COMMAND"),
        }
    }
    
    # merge environment overrides into config data
    for section, values in env_overrides.items():
        if section not in config_data:
            config_data[section] = {}
        
        if isinstance(values, dict):
            for key, value in values.items():
                if isinstance(value, dict):
                    # handle nested config like transport
                    if key not in config_data[section]:
                        config_data[section][key] = {}
                    for sub_key, sub_value in value.items():
                        if sub_value is not None:
                            # convert string values to appropriate types
                            if sub_key == "port" or sub_key == "timeout":
                                sub_value = int(sub_value)
                            config_data[section][key][sub_key] = sub_value
                elif value is not None:
                    # convert string values to appropriate types
                    if key == "timeout":
                        value = int(value)
                    config_data[section][key] = value
    
    return Config(**config_data)


def setup_logging(config: LoggingConfig) -> None:
    """
    Configure Python logging based on the provided logging configuration.
    
    Sets up console and/or file logging with the specified format and level.
    Also configures third-party library logging to reduce noise.
    
    Args:
        config: LoggingConfig object containing logging preferences including level, format, and optional file output.
    """
    # configure main logging
    log_config = {
        "level": getattr(logging, config.level),
        "format": config.format,
    }
    
    if config.file:
        log_config["filename"] = config.file
        log_config["filemode"] = "a"
    
    logging.basicConfig(**log_config)
    
    # reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
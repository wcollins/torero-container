# torero Container Docs
This directory contains documentation for the torero Container project.

## Documentation Structure
- **[tests.md](./tests.md)** - Step-by-step guide for running local tests
- **[global-context.md](../config/global-context.md)** - Comprehensive architecture documentation

## Components

### torero MCP
Model Context Protocol server for integration with AI assistants. Located in `opt/torero-mcp/`.
- Direct CLI integration for optimal performance
- FastMCP-based implementation
- Support for SSE, stdio, and streamable HTTP transports

### torero UI
Web-based user interface for managing torero operations. Located in `opt/torero-ui/`.
- Django-based dashboard with auto-refresh
- Automatic service synchronization
- Direct CLI integration via ToreroCliClient

## Architecture Highlights

The torero-container has been optimized for performance and simplicity:
- **Direct CLI Integration**: Both MCP and UI services interact directly with the torero CLI
- **Automatic Synchronization**: UI automatically detects service changes from any source
- **Universal CLI Wrapper**: Captures all executions for comprehensive tracking
- **Supervisor Management**: All services managed through a single supervisor configuration

## Quick Links
- [Running Tests](./tests.md)
- [Architecture Documentation](../config/global-context.md)
- [Main README](../README.md)
- [MCP Service Documentation](../opt/torero-mcp/README.md)
- [UI Service Documentation](../opt/torero-ui/README.md)
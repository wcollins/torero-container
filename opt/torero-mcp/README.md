# torero MCP Service

Model Context Protocol (MCP) server providing AI assistants with direct access to torero automation capabilities through CLI integration.

## Features
- **Direct CLI Integration**: Execute torero commands directly without API overhead
- **Service Management**: List, search, and inspect torero services
- **Service Execution**: Execute Ansible playbooks, Python scripts, and OpenTofu plans
- **Decorator Operations**: Access and manage service decorators
- **Repository Integration**: Browse and interact with torero repositories
- **Secret Management**: List and inspect secret metadata (values not exposed for security)
- **Database Import/Export**: Backup and migrate configurations between environments
- **Health Monitoring**: Check torero CLI availability and version

## Architecture
The MCP server has been redesigned to use direct CLI integration for optimal performance:

- **Before**: MCP Tools → HTTP Client → torero-api → subprocess → torero CLI
- **Now**: MCP Tools → Direct subprocess → torero CLI

This eliminates the HTTP API layer, reducing latency and complexity while maintaining full functionality.

## Configuration

The MCP service is configured via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_MCP`                | `false`                 | Enable the MCP service          |
| `TORERO_MCP_TRANSPORT_TYPE` | `sse`                   | MCP transport type              |
| `TORERO_MCP_TRANSPORT_HOST` | `0.0.0.0`               | MCP server host                 |
| `TORERO_MCP_TRANSPORT_PORT` | `8080`                  | MCP server port                 |
| `TORERO_MCP_TRANSPORT_PATH` | `/sse`                  | SSE endpoint path               |
| `TORERO_CLI_TIMEOUT`        | `30`                    | CLI command timeout in seconds  |
| `TORERO_LOG_LEVEL`          | `INFO`                  | Logging level                   |

## Available MCP Tools

### Service Tools
- `list_services` - List all available torero services with filtering
- `get_service` - Get detailed information about a specific service
- `describe_service` - Get complete description of a service
- `list_service_types` - Get all available service types
- `list_service_tags` - Get all available service tags

### Service Execution Tools
- `execute_ansible_playbook` - Execute an Ansible playbook service
- `execute_python_script` - Execute a Python script service
- `execute_opentofu_plan_apply` - Apply OpenTofu infrastructure changes
- `execute_opentofu_plan_destroy` - Destroy OpenTofu infrastructure resources

### Decorator Tools
- `list_decorators` - List all available decorators with filtering
- `get_decorator` - Get details about a specific decorator
- `list_decorator_types` - Get all available decorator types

### Repository Tools
- `list_repositories` - List all configured repositories with filtering
- `get_repository` - Get details about a specific repository
- `list_repository_types` - Get all available repository types

### Secret Tools
- `list_secrets` - List all configured secrets (metadata only)
- `get_secret` - Get details about a specific secret (metadata only, values not exposed)
- `list_secret_types` - Get all available secret types

### Database Tools
- `export_database` - Export torero database to YAML or JSON format
- `import_database` - Import torero database from a file or repository

### Health Tools
- `health_check` - Check the health status of torero CLI
- `get_torero_version` - Get torero version information

## Usage Examples

### Testing Connection
```bash
# from the container
torero-mcp test-connection
```

### Running the MCP Server

#### SSE Transport (Default)
```bash
# start with SSE transport
torero-mcp run --transport sse --host 0.0.0.0 --port 8080
```

#### Stdio Transport
```bash
# start with stdio transport (for direct integration)
torero-mcp run --transport stdio
```

#### Streamable HTTP Transport
```bash
# start with streamable HTTP transport
torero-mcp run --transport streamable_http --host 0.0.0.0 --port 8080
```

### Daemon Mode
```bash
# start as daemon
torero-mcp run --daemon --transport sse --port 8080

# check status
torero-mcp status

# stop daemon
torero-mcp stop

# view logs
torero-mcp logs
```

## Integration with AI Assistants

### Claude Desktop Configuration
Add to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "torero": {
      "url": "http://localhost:8080/sse"
    }
  }
}
```

### AnythingLLM Configuration
```json
{
  "name": "torero",
  "url": "http://localhost:8080/sse",
  "description": "torero automation integration"
}
```

### Custom Integration
```python
import httpx
from sseclient import SSEClient

# connect to MCP server
url = "http://localhost:8080/sse"
client = SSEClient(url)

# send tool request
for event in client:
    print(event.data)
```

## Development

### Running Locally
```bash
# from the container root
cd opt/torero-mcp
uv run python -m torero_mcp run

# with specific transport
uv run python -m torero_mcp run --transport sse --port 8080
```

### Testing Tools
```bash
# test CLI connection
uv run python -m torero_mcp test-connection

# list available tools
uv run python -m torero_mcp list-tools
```

### Installing for Development
```bash
cd opt/torero-mcp
uv pip install -e .
```

## Tool Response Format

All tools return structured JSON responses:

```json
{
  "success": true,
  "data": {
    // tool-specific response data
  },
  "error": null
}
```

Error responses:
```json
{
  "success": false,
  "data": null,
  "error": "Error description"
}
```

## Performance Benefits

The direct CLI integration provides several performance benefits:

1. **Reduced Latency**: Eliminates HTTP request/response overhead
2. **Lower Resource Usage**: No HTTP client or API server overhead
3. **Simplified Error Handling**: Direct access to subprocess errors
4. **Better Reliability**: Fewer failure points in the execution chain
5. **Improved Security**: No network traffic for internal operations

## Security Considerations

- Secret values are never exposed through MCP tools for security
- All CLI commands are executed with proper timeout limits
- No external network access required for core functionality
- CLI wrapper still captures execution data for UI dashboard when enabled
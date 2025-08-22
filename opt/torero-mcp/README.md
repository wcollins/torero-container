# torero MCP Service

Model Context Protocol (MCP) server providing AI assistants with access to torero automation capabilities.

## Features
- **Service Management**: List, search, and inspect torero services
- **Decorator Operations**: Access and manage service decorators
- **Repository Integration**: Browse and interact with torero repositories
- **Health Monitoring**: Check torero API connectivity and status
- **Service Execution**: Execute Ansible playbooks, Python scripts, and OpenTofu plans
- **Database Import/Export**: Backup and migrate configurations between environments

## Configuration

The MCP service is configured via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_MCP`                | `false`                 | Enable the MCP service          |
| `TORERO_MCP_TRANSPORT_TYPE` | `sse`                   | MCP transport type              |
| `TORERO_MCP_TRANSPORT_HOST` | `0.0.0.0`               | MCP server host                 |
| `TORERO_MCP_TRANSPORT_PORT` | `8080`                  | MCP server port                 |
| `TORERO_MCP_TRANSPORT_PATH` | `/sse`                  | SSE endpoint path               |
| `TORERO_API_BASE_URL`       | `http://localhost:8000` | torero API base URL             |
| `TORERO_API_TIMEOUT`        | `30`                    | API request timeout in seconds  |
| `TORERO_LOG_LEVEL`          | `INFO`                  | Logging level                   |

## Available MCP Tools

### Service Tools
- `list_services` - List all available torero services with filtering
- `describe_service` - Get detailed information about a specific service
- `execute_service` - Execute a torero service with parameters

### Decorator Tools
- `list_decorators` - List all available decorators
- `get_decorator` - Get details about a specific decorator

### Repository Tools
- `list_repositories` - List all configured repositories
- `get_repository` - Get details about a specific repository

### Registry Tools
- `list_registries` - List all configured registries
- `list_registry_packages` - List packages in a specific registry

### Database Tools
- `export_database` - Export torero database to a backup file
- `import_database` - Import torero database from a backup file

### Secret Tools
- `list_secrets` - List all configured secrets
- `get_secret` - Get details about a specific secret (metadata only)
- `create_secret` - Create a new secret
- `update_secret` - Update an existing secret
- `delete_secret` - Delete a secret

### System Tools
- `check_health` - Check the health status of torero API

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
python -m torero_mcp run

# with specific transport
python -m torero_mcp run --transport sse --port 8080
```

### Testing Tools
```bash
# test connection to API
python -m torero_mcp test-connection

# list available tools
python -m torero_mcp list-tools
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
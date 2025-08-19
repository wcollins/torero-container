# 🔌 torero MCP Server
A [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that provides AI assistants with access to [torero](https://torero.dev). Built with [FastMCP](https://github.com/jlowin/fastmcp) for high-performance AI integrations.

## ✨ Features
🔧 **Service Management**: List, search, and inspect torero services  
🎨 **Decorator Operations**: Access and manage service decorators  
📦 **Repository Integration**: Browse and interact with torero repositories  
🏥 **Health Monitoring**: Check torero API connectivity and status  
⚡ **Service Execution**: Execute Ansible playbooks, Python scripts, and OpenTofu plans  
💾 **Database Import/Export**: Backup and migrate configurations between environments  
📖 **Comprehensive Logging**: Detailed logging for debugging and monitoring  
🤖 **AI Ready**: Native MCP support to tackle the _agentic_ automation landscape  

## 🚦 Quick Start

### Prerequisites
To run this MCP Server with torero, you first need _torero_ and _torero-api_ running and reachable. You can accomplish this by either:
- Running [torero-container](https://github.com/torerodev/torero-container)  
- Installing and running [torero](https://docs.torero.dev/en/latest/installation/) and [torero-api](https://github.com/torerodev/torero-api) independently
- `Python 3.10` or higher is required when not using the _torero-container_

> [!NOTE]
> See the following [docker compose](https://github.com/torerodev/torero-container?tab=readme-ov-file#docker-compose-with-latest-opentofu-version
) for setting the appropriate environment variables.

### Installation

#### Using uv (Recommended)
```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the project
git clone https://github.com/torerodev/torero-mcp.git
cd torero-mcp

# Create virtual environment and install
uv venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install with uv
uv pip install -e .

# Or install with development dependencies
uv pip install -e . --all-extras
```

#### Using pip
```bash
# Clone the repository
git clone https://github.com/torerodev/torero-mcp.git
cd torero-mcp

# Install with pip
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### Basic Usage
1. **Generate a configuration file:**
   ```bash
   torero-mcp init-config
   ```

2. **Edit the configuration:**
   ```yaml
   # config.yaml
   api:
     base_url: "http://localhost:8000"
     timeout: 30

   mcp:
     transport:
       type: "stdio"      # or "sse" or "streamable_http"
       host: "127.0.0.1"  # for SSE/HTTP
       port: 8000         # for SSE/HTTP
   ```

3. **Test the connection:**
   ```bash
   torero-mcp test-connection --config config.yaml
   ```

4. **Run the MCP server:**
   ```bash
   # Default stdio transport
   torero-mcp run --config config.yaml

   # Or with SSE transport
   torero-mcp run --config config.yaml --transport sse

   # Or specify host/port
   torero-mcp run --transport sse --host 0.0.0.0 --port 8080
   ```

## 🔧 Daemon Mode
The torero MCP server can run as a background daemon.

### Running as Daemon
```bash
# Start daemon with default settings
torero-mcp run --daemon

# Start daemon with custom settings
torero-mcp run --daemon \
  --host 0.0.0.0 \
  --port 8080 \
  --pid-file /var/run/torero-mcp.pid \
  --log-file /var/log/torero-mcp.log \
  --config /etc/torero-mcp/config.yaml

# Start daemon with SSE transport
torero-mcp run --daemon --transport sse --host 0.0.0.0 --port 8080
```

### Daemon Control
```bash
# Check daemon status
torero-mcp status

# Stop daemon
torero-mcp stop

# Restart daemon (preserves configuration)
torero-mcp restart

# View recent logs
torero-mcp logs

# Follow logs in real-time
torero-mcp follow-logs
```

### Control Script
Keep things easy and breezy! Manage the _daemon_ with the following script:

```bash
# Using the control script
./scripts/torero_mcp_ctl.sh start
./scripts/torero_mcp_ctl.sh stop
./scripts/torero_mcp_ctl.sh restart
./scripts/torero_mcp_ctl.sh status
./scripts/torero_mcp_ctl.sh logs
./scripts/torero_mcp_ctl.sh follow-logs
```

### Environment Variables for Daemon Mode

```bash
# Daemon configuration
export TORERO_MCP_PID_FILE="/var/run/torero-mcp.pid"
export TORERO_MCP_LOG_FILE="/var/log/torero-mcp.log"
export TORERO_MCP_HOST="0.0.0.0"
export TORERO_MCP_PORT="8080"
export TORERO_MCP_CONFIG="/etc/torero-mcp/config.yaml"

# Start daemon using environment variables
torero-mcp run --daemon
```

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TORERO_API_BASE_URL` | `http://localhost:8000` | torero API base URL |
| `TORERO_API_TIMEOUT` | `30` | API request timeout in seconds |
| `TORERO_LOG_LEVEL` | `INFO` | Logging level |
| `TORERO_LOG_FILE` | - | Log file path |
| `TORERO_MCP_TRANSPORT_TYPE` | `stdio` | Transport type (stdio, sse, streamable_http) |
| `TORERO_MCP_TRANSPORT_HOST` | `127.0.0.1` | Host for SSE/HTTP transport |
| `TORERO_MCP_TRANSPORT_PORT` | `8080` | Port for SSE/HTTP transport |
| `TORERO_MCP_TRANSPORT_PATH` | `/sse` | SSE endpoint path |
| `TORERO_MCP_PID_FILE` | `/tmp/torero-mcp.pid` | PID file location for daemon mode |
| `TORERO_MCP_LOG_FILE` | - | Log file path for daemon mode |

### CLI Commands

```bash
# Run the MCP server
torero-mcp run [OPTIONS]

# Test API connection
torero-mcp test-connection [OPTIONS]

# Generate sample configuration
torero-mcp init-config [OPTIONS]

# Show version information
torero-mcp version

# Daemon control commands
torero-mcp stop [OPTIONS]          # Stop daemon
torero-mcp status [OPTIONS]        # Check daemon status
torero-mcp restart [OPTIONS]       # Restart daemon
torero-mcp logs [OPTIONS]          # View daemon logs
torero-mcp follow-logs [OPTIONS]   # Follow daemon logs

# Show help
torero-mcp --help
```

### Command Options

```bash
# Common options for run and test-connection
--config, -c PATH       Path to configuration file
--api-url TEXT          torero API base URL (overrides config)
--log-level LEVEL       Override logging level

# Transport options for run command
--transport TYPE        Transport type: stdio, sse, streamable_http (overrides config)
--host TEXT            Host for SSE/HTTP transport (overrides config)
--port INT             Port for SSE/HTTP transport (overrides config)
--sse-path TEXT        SSE endpoint path (overrides config)

# Daemon options for run command
--daemon               Run as daemon in background
--pid-file PATH        PID file location for daemon mode (default: /tmp/torero-mcp.pid)
--log-file PATH        Log file location for daemon mode

# Options for daemon control commands
--pid-file PATH        PID file location (for stop, status, restart)
--log-file PATH        Log file location (for logs, follow-logs, restart)
--lines, -n INT        Number of lines to show (for logs command, default: 50)

# Options for init-config
--output, -o PATH       Output configuration file path (default: config.yaml)
```

## 🤖 Integration with AI Assistants

### Claude Desktop
To use with Claude Desktop, add to your `claude_desktop_config.json`:

**For stdio transport (default):**
```json
{
  "mcpServers": {
    "torero": {
      "command": "/path/to/torero-mcp/.venv/bin/python",
      "args": [
        "-m",
        "torero_mcp.cli",
        "run",
        "--transport",
        "stdio",
        "--config",
        "/path/to/torero-mcp/config.yaml"
      ],
      "env": {
        "TORERO_CONFIG_PATH": "/path/to/torero-mcp/config.yaml"
      }
    }
  }
}
```

> **Note**: For stdio transport, make sure `torero-mcp` is in your PATH after installation, or use the full path to the executable. For SSE transport, ensure the server is running before connecting.

### Other AI Assistants
The server supports standard MCP protocols and can be integrated with any MCP-compatible AI assistant. Check the `docs/` directory as more examples get added in over time.

## 📲 Available MCP Tools
Once connected to an AI assistant, you can use these tools:

| Tool | Description |
|------|-------------|
| `list_services` | List all torero services with optional filtering |
| `get_service` | Get detailed information about a specific service |
| `describe_service` | Get comprehensive description of a service |
| `execute_ansible_playbook` | Execute Ansible playbook services |
| `execute_python_script` | Execute Python script services |
| `execute_opentofu_plan_apply` | Apply OpenTofu plan services |
| `execute_opentofu_plan_destroy` | Destroy OpenTofu plan services |
| `list_decorators` | List all available decorators |
| `get_decorator` | Get detailed decorator information |
| `list_repositories` | List all torero repositories |
| `get_repository` | Get detailed repository information |
| `list_secrets` | List secret metadata (secure) |
| `get_secret` | Get secret metadata (secure) |
| `health_check` | Check torero API health and connectivity |
| `export_database` | Export database configuration to JSON/YAML format |
| `export_database_to_file` | Export database configuration to a file |
| `import_database` | Import database configuration from a file |
| `check_database_import` | Check what would happen during import without executing |
| `import_database_from_repository` | Import database configuration from a git repository |
# 📦 torero container
Container image for [torero](https://torero.dev), built using vendor-neutral Containerfile specifications and packaged in a _ready-to-use_ container with optional [OpenTofu](https://opentofu.org) installation. The image is hosted on GitHub Container Registry (GHCR). For more details about _torero_, visit the [official docs](https://docs.torero.dev/en/latest/).

> [!NOTE]
> For questions or _real-time_ feedback, you can connect with us directly in the [Network Automation Forum (NAF) Slack Workspace](https://networkautomationfrm.slack.com/?redir=%2Farchives%2FC075L2LR3HU%3Fname%3DC075L2LR3HU) in the **#tools-torero** channel.

## ✨ Features
- Built with vendor-neutral Containerfile for maximum compatibility
- Multi-architecture support _(AMD64 and ARM64)_
- Based on [debian-slim](https://github.com/lxc/lxc-ci/tree/main/images/debian) for minimal footprint
- Hosted on GitHub Container Registry (GHCR) for reliable distribution
- Includes _torero_ installed and ready to go
- Optional [OpenTofu](https://opentofu.org/) installation at runtime
- Optional SSH administration for testing convenience + labs
- Integrated torero-mcp service for Model Context Protocol server with direct CLI integration
- Optional torero-ui service for web-based dashboard

## Inspiration
Managing and automating a hybrid, _multi-vendor_ infrastrcuture that encompasses _on-premises systems, private and public clouds, edge computing, and colocation environments_ poses significant challenges. How can you experiment to _learn_ without breaking things? How can you test new and innovative products like _torero_ on the test bench without friction to help in your evaluation? How do you test the behavior of changes in lower level environments before making changes to production? I use [containerlab](https://containerlab.dev/) for all of the above! This project makes it easy to insert _torero_ in your _containerlab_ topology file, connect to the container, and run your experiments -- the sky is the limit!

## Getting Started
To get started you can use any OCI-compatible container runtime (Docker, Podman, etc.) with CLI or compose.

### docker cli
```bash
docker run -d -p 2222:22 ghcr.io/torerodev/torero-container:latest
```

![docker cli](./img/docker-cli.gif)

### docker compose _(with MCP server enabled)_
```yaml
---
services:
  torero:
    image: ghcr.io/torerodev/torero-container:latest
    container_name: torero
    ports:
      - "22:22"                  # use when ENABLE_SSH_ADMIN=true
      - "8080:8080"              # use when ENABLE_MCP=true
      - "8001:8001"              # use when ENABLE_UI=true
    volumes:
      - ./data:/home/admin/data
    environment:
      - ENABLE_MCP=true          # enable torero-mcp server
      - ENABLE_UI=true           # enable torero web dashboard
      - ENABLE_SSH_ADMIN=true    # enable ssh admin at runtime
      - OPENTOFU_VERSION=1.9.0   # override OpenTofu version at runtime (optional)
      - PYTHON_VERSION=3.13.0
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "torero", "version"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s
...
```

![docker compose](./img/docker-compose.gif)

### Connecting to the container
You can connect to the container with 'admin' when _ENABLE_SSH_ADMIN=true_ is set during runtime.

```bash
ssh admin@localhost -p 2222  # default password: admin
```

### Environment Variables
The following environment variables can be set at runtime:

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_UI`        | `false`  | Enable torero web dashboard    |
| `UI_PORT`          | `8001`   | Set UI port                    |
| `ENABLE_MCP`       | `false`  | Enable torero MCP server       |
| `ENABLE_SSH_ADMIN` | `false`  | Enable SSH admin user          |
| `OPENTOFU_VERSION` | `1.10.5` | Override OpenTofu version      |
| `PYTHON_VERSION`   | `3.13.0` | Set Python version             |

#### MCP Server Environment Variables
When `ENABLE_MCP=true`, the following additional environment variables are available:

| Variable | Default | Description |
|----------|---------|-------------|
| `TORERO_MCP_TRANSPORT_TYPE` | `sse`                         | MCP transport type (stdio, sse, streamable_http) |
| `TORERO_MCP_TRANSPORT_HOST` | `0.0.0.0`                     | MCP server host                 |
| `TORERO_MCP_TRANSPORT_PORT` | `8080`                        | MCP server port                 |
| `TORERO_MCP_TRANSPORT_PATH` | `/sse`                        | SSE endpoint path               |
| `TORERO_CLI_TIMEOUT`        | `30`                          | CLI command timeout in seconds  |
| `TORERO_LOG_LEVEL`          | `INFO`                        | Logging level                   |
| `TORERO_MCP_LOG_FILE`       | `/home/admin/.torero-mcp.log` | Log file path                   |

### OpenTofu Version Management
The container comes with OpenTofu 1.10.5 (latest stable) pre-installed at build time. You can override this at runtime using the `OPENTOFU_VERSION` environment variable:

```bash
# Use a different OpenTofu version
docker run -e OPENTOFU_VERSION=1.8.5 ghcr.io/torerodev/torero-container:latest

# Or with docker-compose
services:
  torero:
    image: ghcr.io/torerodev/torero-container:latest
    environment:
      - OPENTOFU_VERSION=1.9.0  # Will download and install 1.9.0 at startup
```

The container will automatically download and install the requested version at startup if it differs from the pre-installed version. If no `OPENTOFU_VERSION` is specified, it uses the pre-installed version (1.10.5).

## MCP Server Integration

The torero-mcp service provides Model Context Protocol integration with direct CLI access for optimal performance. This allows AI assistants and other MCP clients to interact with torero services without the overhead of an intermediate REST API.

### Key Features:
- **Direct CLI Integration**: MCP tools execute torero commands directly for optimal performance
- **Comprehensive Tool Coverage**: Full access to torero services, repositories, decorators, secrets, and execution capabilities
- **Multiple Transport Options**: Support for stdio, Server-Sent Events (SSE), and streamable HTTP
- **Automatic Tool Discovery**: Dynamic loading of MCP tools with proper parameter mapping

### Connecting MCP Clients:
```bash
# For stdio transport (direct process communication)
torero-mcp run --transport stdio

# For SSE transport (web-based clients)
torero-mcp run --transport sse --host 0.0.0.0 --port 8080

# For streamable HTTP transport
torero-mcp run --transport streamable_http --host 0.0.0.0 --port 8080
```

## Local Development

### Using docker-compose for local testing

```bash
# start all services with development configuration
docker compose -f docker-compose.dev.yml up -d

# stop services
docker compose -f docker-compose.dev.yml down

# rebuild and start
docker compose -f docker-compose.dev.yml up --build -d

# view logs
docker compose -f docker-compose.dev.yml logs -f

# clean up everything
docker compose -f docker-compose.dev.yml down -v
```

### Using tools.sh for development tasks

```bash
# setup development environment
./tools.sh --setup

# run tests with coverage
./tools.sh --test

# generate openapi schema
./tools.sh --schema
```

## Container Architecture
This project uses vendor-neutral Containerfile specifications for maximum compatibility across container runtimes. The image is built and distributed through GitHub Container Registry (GHCR) for reliable access and version management.

The architecture has been simplified to use direct CLI integration for optimal performance:
- **torero CLI**: Core torero functionality accessed directly
- **torero-mcp**: MCP server providing direct CLI integration for AI assistants
- **torero-ui**: Optional web dashboard for execution monitoring (uses CLI wrapper data)

### Multi-Architecture Support
The container images support both AMD64 and ARM64 architectures. The appropriate architecture will be selected automatically based on your host system when pulling the image.

For building multi-architecture images locally:
```bash
# build for multiple platforms
make build-multi PLATFORMS=linux/amd64,linux/arm64

# build for local platform only
make build
```

## Software Licenses
This project incorporates the following software with their respective licenses:

- torero: refer to the [torero license](https://torero.dev/licenses/eula)
- opentofu: [mozilla public license 2.0](https://github.com/opentofu/opentofu/blob/main/LICENSE) 
- debian: [multiple licenses](https://www.debian.org/legal/licenses/)

All modifications and original code in this project are licensed under the apache license 2.0.
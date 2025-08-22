# torero-ui

Web dashboard for the torero automation platform. Provides visibility into service executions, statistics, and operational health with automatic service synchronization.

## Features

- Real-time dashboard with auto-refresh
- Automatic service synchronization from torero CLI
- Service execution history and statistics
- Responsive design with torero branding
- SQLite database with JSON columns for execution data
- RESTful API for data access
- Direct CLI integration for real-time data

## Architecture

The UI service uses direct CLI integration for optimal performance:
- **ToreroCliClient**: Executes torero commands directly via subprocess
- **Sync Service**: Automatically detects and syncs service changes
- **CLI Wrapper**: Captures all executions for display in dashboard

## Quick Start

### Container Deployment (Recommended)

1. Build the OCI-compliant container:
```bash
docker build -f Containerfile -t torero-ui:latest .
```

2. Run the container:
```bash
docker run -d -p 8001:8001 torero-ui:latest
```

3. Access dashboard at http://localhost:8001

### Development Setup

1. Install dependencies:
```bash
uv pip install -e .
```

2. Set up database:
```bash
uv run python torero_ui/manage.py migrate
```

3. Create superuser (optional):
```bash
uv run python torero_ui/manage.py createsuperuser
```

4. Run development server:
```bash
uv run python torero_ui/manage.py runserver 8001
```

5. Run sync service (in another terminal):
```bash
uv run python torero_ui/manage.py sync_services
```

6. Access dashboard at http://localhost:8001

## Configuration

Environment variables:
- `TORERO_CLI_TIMEOUT`: CLI command timeout in seconds (default: 30)
- `UI_REFRESH_INTERVAL`: Dashboard auto-refresh interval in seconds (default: 30)
- `DEBUG`: Enable debug mode (default: False)
- `SECRET_KEY`: Django secret key
- `CONTAINER_BUILD_MODE`: Set to true during container build only

## Service Synchronization

The UI includes an automatic sync service that:
- Polls torero CLI for service changes
- Updates the database with new/modified services
- Runs at the interval specified by `UI_REFRESH_INTERVAL`
- Detects services added via CLI, database import, or MCP operations

To run the sync service manually:
```bash
# Sync once
uv run python torero_ui/manage.py sync_services --once

# Continuous sync (default)
uv run python torero_ui/manage.py sync_services --interval 30
```

## Integration with torero-container

Add to your docker-compose:

```yaml
services:
  torero-ui:
    build:
      context: .
      dockerfile: Containerfile
    ports:
      - "8001:8001"
    environment:
      - ENABLE_UI=true
      - UI_REFRESH_INTERVAL=30
      - TORERO_CLI_TIMEOUT=30
      - DEBUG=False
    volumes:
      - ./data:/home/admin/data  # Persistent database
```

## API Endpoints

- `GET /`: Main dashboard view
- `GET /api/services/`: List all services
- `GET /api/executions/`: List recent executions
- `POST /api/record-execution/`: Record new execution
- `GET /api/execution/<id>/`: Execution details
- `POST /api/sync/`: Trigger manual service sync

## Database

The UI uses SQLite with persistent storage in `/home/admin/data/torero_ui.db`. The database schema includes:

- **ServiceInfo**: Stores service metadata and statistics
- **ServiceExecution**: Stores execution history with full details

## CLI Integration

The UI directly integrates with the torero CLI through the `ToreroCliClient` class:

```python
from torero_ui.dashboard.services import ToreroCliClient

client = ToreroCliClient()
services = client.get_services()  # Direct CLI call
```

This eliminates the need for an intermediate API layer and ensures data is always current.

## License
Apache-2.0
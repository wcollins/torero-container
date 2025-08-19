# torero-ui

Web dashboard for the torero automation platform. Provides visibility into service executions, statistics, and operational health.

## Features

- Real-time dashboard with auto-refresh
- Service execution history and statistics
- Responsive design with torero branding
- SQLite database with JSON columns for execution data
- RESTful API for data access
- Integration with torero-api

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
pip install -e .
```

2. Set up database:
```bash
python torero_ui/manage.py migrate
```

3. Create superuser (optional):
```bash
python torero_ui/manage.py createsuperuser
```

4. Run development server:
```bash
python torero_ui/manage.py runserver 8001
```

5. Access dashboard at http://localhost:8001

## Configuration

Environment variables:
- `TORERO_API_BASE_URL`: Base URL for torero-api (default: http://localhost:8000)
- `TORERO_API_TIMEOUT`: API request timeout in seconds (default: 30)
- `DASHBOARD_REFRESH_INTERVAL`: Auto-refresh interval in seconds (default: 30)
- `DEBUG`: Enable debug mode (default: True)
- `SECRET_KEY`: Django secret key

## Integration with torero-container

Add to your containerlab topology or docker-compose:

```yaml
services:
  torero-ui:
    build:
      context: .
      dockerfile: Containerfile
    ports:
      - "8001:8001"
    environment:
      - TORERO_API_BASE_URL=http://torero-container:8000
      - DEBUG=False
    depends_on:
      - torero-container
```

## API Endpoints

- `GET /api/data/`: Dashboard data (stats, services, executions)
- `POST /api/sync/`: Sync services from torero-api
- `GET /api/execution/<id>/`: Execution details

## License

Apache-2.0
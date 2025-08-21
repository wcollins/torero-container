# torero API Service

RESTful API service providing programmatic access to torero automation capabilities.

## Features
- **Service Discovery**: List, filter, and search torero services
- **Service Execution**: Execute Ansible playbooks, Python scripts, and OpenTofu plans
- **Registry Management**: Manage package registries (Ansible Galaxy, PyPI, etc.)
- **Database Operations**: Export and import configurations between torero instances
- **Auto Documentation**: Interactive API docs with OpenAPI/Swagger

## Configuration

The API service is configured via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_API` | `false`   | Enable the API service    |
| `API_PORT`   | `8000`    | Port for the API service  |
| `API_HOST`   | `0.0.0.0` | Host binding for the API  |

## API Endpoints

### Core Endpoints
- `GET /health` - Health check endpoint
- `GET /api/v1/services` - List all available services
- `POST /api/v1/services/{service_name}/execute` - Execute a service
- `GET /api/v1/services/{service_name}/describe` - Get service details

### Decorator Endpoints
- `GET /api/v1/decorators` - List all decorators
- `GET /api/v1/decorators/{name}` - Get decorator details

### Repository Endpoints
- `GET /api/v1/repositories` - List all repositories
- `GET /api/v1/repositories/{name}` - Get repository details

### Registry Endpoints
- `GET /api/v1/registries` - List all registries
- `POST /api/v1/registries/{name}/packages` - List packages in registry

### Database Operations
- `POST /api/v1/database/export` - Export torero database
- `POST /api/v1/database/import` - Import torero database

### Secret Management
- `GET /api/v1/secrets` - List all secrets
- `GET /api/v1/secrets/{name}` - Get secret details
- `POST /api/v1/secrets` - Create a new secret
- `PUT /api/v1/secrets/{name}` - Update a secret
- `DELETE /api/v1/secrets/{name}` - Delete a secret

## Usage Examples

### List Services
```bash
curl http://localhost:8000/api/v1/services
```

### Execute a Service
```bash
curl -X POST http://localhost:8000/api/v1/services/my-playbook/execute \
  -H "Content-Type: application/json" \
  -d '{"parameters": {"target": "localhost"}}'
```

### Filter Services by Type
```bash
curl "http://localhost:8000/api/v1/services?service_type=ansible-playbook"
```

### Export Database
```bash
curl -X POST http://localhost:8000/api/v1/database/export \
  -H "Content-Type: application/json" \
  -d '{"output_file": "/tmp/torero-backup.tar.gz"}'
```

## Interactive Documentation

When the API is running, access the interactive documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI Schema: `http://localhost:8000/openapi.json`

## Development

### Running Locally
```bash
# from the container root
cd opt/torero-api
python -m torero_api

# with auto-reload for development
python -m torero_api --reload
```

### Running Tests
```bash
# from the container root
./tools.sh --test
```

### Generating OpenAPI Schema
```bash
# from the container root
./tools.sh --schema
```
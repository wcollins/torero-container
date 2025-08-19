# torero-container Integration Changes

This document outlines the changes needed to integrate torero-ui into the torero-container project.

## Files Modified

### 1. Containerfile
**Location**: `/torero-container/Containerfile`

**Changes**: Add environment variables for UI configuration
```dockerfile
# UI server is disabled by default
ENV ENABLE_UI=false
ENV UI_PORT=8001
ENV DASHBOARD_REFRESH_INTERVAL=30
ENV TORERO_UI_LOG_FILE=/home/admin/.torero-ui.log
ENV TORERO_UI_PID_FILE=/tmp/torero-ui.pid

# expose UI port (only used if UI is enabled)
EXPOSE 8001
```

### 2. entrypoint.sh
**Location**: `/torero-container/entrypoint.sh`

**Changes**: Add `setup_torero_ui()` function and call it in the main execution sequence.

**New Function Added**:
```bash
setup_torero_ui() {
    if [[ "${ENABLE_UI}" != "true" ]]; then
        echo "skipping torero-ui setup as ENABLE_UI is not set to true"
        return 0
    fi

    # Wait for torero-api to be ready
    # Install uv package manager if needed
    # Clone and install torero-ui from GitHub
    # Set up Django database
    # Create sample data if none exists
    # Start Django development server
    # Update service manifest
}
```

**Execution Order Update**:
```bash
configure_dns
setup_ssh_runtime
handle_torero_eula
verify_opentofu || echo "OpenTofu verification failed, continuing without it"
setup_torero_api || echo "torero-api setup failed, continuing without it"
setup_torero_mcp || echo "torero-mcp setup failed, continuing without it"
setup_torero_ui || echo "torero-ui setup failed, continuing without it"  # NEW
exec "$@"
```

### 3. docker-compose.yml
**Location**: `/torero-container/docker-compose.yml`

**Changes**: Update to build locally and include UI environment variables
```yaml
services:
  torero:
    build:                    # Changed from image
      context: .
      dockerfile: Containerfile
    ports:
      - "8001:8001"          # Added UI port
    environment:
      - ENABLE_UI=true       # Added
      - UI_PORT=8001         # Added
      - DASHBOARD_REFRESH_INTERVAL=15  # Added
```

## Environment Variables

### New Variables for torero-container

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_UI` | `false` | Enable torero-ui dashboard |
| `UI_PORT` | `8001` | Dashboard HTTP port |
| `DASHBOARD_REFRESH_INTERVAL` | `30` | Auto-refresh interval in seconds |
| `TORERO_UI_LOG_FILE` | `/home/admin/.torero-ui.log` | Dashboard log file path |
| `TORERO_UI_PID_FILE` | `/tmp/torero-ui.pid` | Dashboard PID file path |

## Setup Process

When `ENABLE_UI=true`, the container will:

1. **Wait for torero-api** (if enabled) to be ready
2. **Install uv** package manager if not present
3. **Clone torero-ui** from GitHub repository
4. **Install dependencies** using uv
5. **Setup database** with Django migrations
6. **Create sample data** if no executions exist
7. **Start Django server** on configured port
8. **Update manifest** with service information

## Dependencies

The UI setup function requires:
- `curl` (for downloading uv and API health checks)
- `git` (for cloning torero-ui repository)
- `python3` (for Django application)
- `torero-api` running (for data integration)

## Port Exposure

The container now exposes:
- Port 22: SSH (if `ENABLE_SSH_ADMIN=true`)
- Port 8000: torero-api (if `ENABLE_API=true`)
- Port 8001: torero-ui (if `ENABLE_UI=true`)
- Port 8080: torero-mcp (if `ENABLE_MCP=true`)

## Integration Testing

To test the integration:

1. **Build container** (using OCI-compliant Containerfile):
   ```bash
   cd torero-container
   docker build -f Containerfile -t torero-with-ui:test .
   ```

2. **Run with UI enabled**:
   ```bash
   docker run -d \
     -p 8000:8000 \
     -p 8001:8001 \
     -e ENABLE_API=true \
     -e ENABLE_UI=true \
     torero-with-ui:test
   ```

3. **Verify services**:
   ```bash
   curl http://localhost:8000/health  # API health
   curl http://localhost:8001/        # Dashboard
   ```

## Troubleshooting

### UI fails to start
- Check that `ENABLE_API=true` and API is healthy
- Verify network connectivity within container
- Check logs: `docker logs <container> | grep torero-ui`

### Database issues
- Django migration failures usually indicate Python environment issues
- Check that required packages are installed
- Verify file permissions for SQLite database

### Performance considerations
- UI startup adds ~30-60 seconds to container initialization
- Memory usage increases by ~100MB for Django process
- Consider disabling auto-refresh in production environments

## Future Enhancements

Potential improvements for production deployment:
- Use production WSGI server instead of Django development server
- Add health checks for UI service
- Implement graceful shutdown handling
- Add configuration validation
- Support for custom UI themes/branding
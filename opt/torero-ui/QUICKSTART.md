# torero-ui Quickstart Guide

This guide shows you how to deploy and run the torero dashboard in conjunction with torero-container for a complete automation platform experience.

## Overview

The torero-ui dashboard provides real-time visibility into your automation executions when deployed alongside:
- **torero-container**: Core automation platform
- **torero-api**: RESTful API for automation services  
- **torero-mcp**: Model Context Protocol server (optional)

## Quick Start with Containerlab

### 1. Basic Setup

Create a simple containerlab topology with dashboard enabled:

```yaml
# demo-topology.yml
---
name: torero-demo

mgmt:
  network: torero-demo
  ipv4-subnet: 198.18.1.0/24

topology:
  nodes:
    automation-host:
      kind: linux
      image: ghcr.io/torerodev/torero-container:latest
      mgmt-ipv4: 198.18.1.10
      ports:
        - "8000:8000"  # torero-api
        - "8001:8001"  # torero-ui dashboard
        - "8080:8080"  # torero-mcp (optional)
      env:
        ENABLE_SSH_ADMIN: "true"
        ENABLE_API: "true"
        ENABLE_UI: "true"           # Enable dashboard
        UI_PORT: "8001"             # Dashboard port
        DASHBOARD_REFRESH_INTERVAL: "30"  # Refresh every 30 seconds
      binds:
        - $PWD/data:/home/admin/data
      exec:
        # Import sample services for testing
        - "runuser -u admin -- torero db import --repository https://github.com/torerodev/hello-torero.git import.yml"
```

### 2. Deploy the Lab

```bash
# Deploy the topology
sudo containerlab deploy -t demo-topology.yml

# Wait for services to start (about 30-60 seconds)
sleep 60

# Check service status
curl http://198.18.1.10:8000/health  # torero-api health
curl http://198.18.1.10:8001/        # dashboard home page
```

### 3. Access the Dashboard

Open your browser and navigate to:
- **Dashboard**: http://198.18.1.10:8001
- **API**: http://198.18.1.10:8000/docs (Swagger UI)

### 4. Run Some Automations

Generate dashboard data by running the sample services:

```bash
# SSH into the container
ssh admin@198.18.1.10
# Password: admin

# Run sample automations
torero service run hello-python
torero service run hello-ansible  
torero service run hello-opentofu

# Or run them all
torero service run hello-python hello-ansible hello-opentofu
```

The dashboard will automatically update to show execution results!

## Docker Compose Deployment

For a simpler setup without containerlab, you'll need to build the torero-container locally with UI support:

### Option 1: Using Updated torero-container

**Note**: The UI functionality requires changes to torero-container that are not yet in the official image.

1. **Clone and update torero-container**:
```bash
git clone https://github.com/torerodev/torero-container.git
cd torero-container
# Apply the UI integration changes from this repository
```

2. **Use the provided docker-compose.yml**:
```yaml
# docker-compose.yml (included in torero-container)
version: '3.8'

services:
  torero:
    build:
      context: .
      dockerfile: Containerfile
    ports:
      - "8000:8000"  # torero-api
      - "8001:8001"  # torero-ui
      - "8080:8080"  # torero-mcp
      - "22:22"      # SSH access
    environment:
      - ENABLE_SSH_ADMIN=true
      - ENABLE_API=true
      - ENABLE_UI=true          # Enable dashboard
      - UI_PORT=8001
      - DASHBOARD_REFRESH_INTERVAL=15
    volumes:
      - ./data:/home/admin/data
```

3. **Deploy**:
```bash
docker compose up -d
```

### Option 2: Standalone Dashboard + Existing Container

If you want to use the current torero-container without modifications:

```yaml
# docker-compose.yml
version: '3.8'

services:
  torero-platform:
    image: ghcr.io/torerodev/torero-container:latest
    ports:
      - "8000:8000"
      - "8080:8080"
      - "22:22"
    environment:
      - ENABLE_SSH_ADMIN=true
      - ENABLE_API=true
      - ENABLE_MCP=true
    volumes:
      - ./data:/home/admin/data

  torero-dashboard:
    build:
      context: ./torero-ui
      dockerfile: Containerfile
    ports:
      - "8001:8001"
    environment:
      - TORERO_API_BASE_URL=http://torero-platform:8000
      - DASHBOARD_REFRESH_INTERVAL=15
    depends_on:
      - torero-platform
```

## Standalone Dashboard

To run just the dashboard (requires separate torero-api):

```bash
# Clone and setup
git clone https://github.com/torerodev/torero-ui.git
cd torero-ui

# Install dependencies
pip install -e .

# Configure environment
export TORERO_API_BASE_URL=http://localhost:8000
export DASHBOARD_REFRESH_INTERVAL=30

# Setup database and create sample data
python torero_ui/manage.py migrate
python torero_ui/manage.py create_test_data --count 20

# Run the dashboard
python torero_ui/manage.py runserver 0.0.0.0:8001
```

## Environment Variables

### torero-container Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_UI` | `false` | Enable torero-ui dashboard |
| `UI_PORT` | `8001` | Dashboard HTTP port |
| `DASHBOARD_REFRESH_INTERVAL` | `30` | Auto-refresh interval (seconds) |
| `TORERO_API_BASE_URL` | `http://localhost:8000` | torero-api endpoint |

### Dashboard-Only Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `TORERO_API_BASE_URL` | `http://localhost:8000` | torero-api endpoint |
| `TORERO_API_TIMEOUT` | `30` | API request timeout |
| `DASHBOARD_REFRESH_INTERVAL` | `30` | Auto-refresh interval |
| `DEBUG` | `False` | Django debug mode |

## Dashboard Features

### Real-Time Monitoring
- **Auto-refresh**: Configurable polling interval
- **Live statistics**: Success rates, execution counts, timing
- **Service status**: Per-service health and metrics

### Execution History
- **Recent executions**: Last 20 automation runs
- **Filtered views**: Success/failure tabs
- **Detailed output**: stdout, stderr, timing, metadata

### Interactive Elements
- **Execution details**: Click any execution for full output
- **Service sync**: Manual refresh from torero-api
- **Keyboard shortcuts**: `Ctrl+R` refresh, `Ctrl+S` sync

## Integration with Existing Infrastructure

### Network Automation Lab

```yaml
# network-lab.yml
---
name: network-automation

mgmt:
  network: automation-lab
  ipv4-subnet: 172.16.1.0/24

topology:
  nodes:
    # Automation platform
    controller:
      kind: linux
      image: ghcr.io/torerodev/torero-container:latest
      mgmt-ipv4: 172.16.1.100
      ports:
        - "8000:8000"
        - "8001:8001"
      env:
        ENABLE_API: "true"
        ENABLE_UI: "true"
        ENABLE_SSH_ADMIN: "true"
      exec:
        - "runuser -u admin -- torero db import --repository https://github.com/your-org/network-automations.git imports/all.yml"
    
    # Network devices
    router1:
      kind: arista_ceos
      image: ceos:4.34.1F
      mgmt-ipv4: 172.16.1.11
    
    router2:
      kind: arista_ceos  
      image: ceos:4.34.1F
      mgmt-ipv4: 172.16.1.12

  links:
    - endpoints: ["router1:eth1", "router2:eth1"]
```

### Cloud Infrastructure Automation

```yaml
# cloud-automation.yml
version: '3.8'

services:
  torero:
    image: ghcr.io/torerodev/torero-container:latest
    ports:
      - "8000:8000"
      - "8001:8001"
    environment:
      - ENABLE_API=true
      - ENABLE_UI=true
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      - ARM_CLIENT_ID=${ARM_CLIENT_ID}
      - ARM_CLIENT_SECRET=${ARM_CLIENT_SECRET}
    volumes:
      - ./terraform:/home/admin/data/terraform
      - ./ansible:/home/admin/data/ansible
    command: >
      bash -c "
        runuser -u admin -- torero db import --repository https://github.com/your-org/cloud-automations.git imports/
        tail -f /dev/null
      "
```

## Troubleshooting

### Dashboard Not Loading

1. **Check container logs**:
   ```bash
   docker logs <container-name> | grep torero-ui
   ```

2. **Verify API connectivity**:
   ```bash
   curl http://localhost:8000/health
   ```

3. **Check environment variables**:
   ```bash
   docker exec <container> env | grep -E "(ENABLE_UI|UI_PORT|TORERO_API)"
   ```

### API Connection Issues

1. **Test API directly**:
   ```bash
   curl http://localhost:8000/v1/services/
   ```

2. **Check network connectivity**:
   ```bash
   docker exec <container> wget -qO- http://localhost:8000/health
   ```

### No Execution Data

1. **Import services**:
   ```bash
   docker exec <container> runuser -u admin -- torero db import --repository https://github.com/torerodev/hello-torero.git import.yml
   ```

2. **Run test automations**:
   ```bash
   docker exec <container> runuser -u admin -- torero service run hello-python
   ```

3. **Create sample data**:
   ```bash
   docker exec <container> python /opt/torero-ui/torero_ui/manage.py create_test_data --count 10
   ```

## Performance Tuning

### High-Frequency Environments

For environments with many executions:

```yaml
environment:
  - DASHBOARD_REFRESH_INTERVAL=10  # Faster updates
  - TORERO_API_TIMEOUT=60         # Longer timeout
```

### Large Datasets

Configure pagination for large execution histories:

```bash
# Limit dashboard to recent executions only
export DASHBOARD_MAX_EXECUTIONS=100
```

## Security Considerations

### Production Deployment

- Change default SSH password: `admin:admin`
- Use HTTPS with proper certificates
- Configure firewall rules for required ports only
- Use secrets management for API keys

### Network Isolation

```yaml
# Example with custom network
networks:
  automation:
    driver: bridge
    ipam:
      config:
        - subnet: 10.1.0.0/16

services:
  torero:
    networks:
      - automation
    # ... other config
```

## Next Steps

1. **Custom Automations**: Import your own automation repositories
2. **CI/CD Integration**: Trigger automations from pipelines
3. **Monitoring**: Set up alerts for failed executions
4. **Scaling**: Deploy multiple torero instances for larger environments

For more advanced configurations, see the [full documentation](README.md) and [torero-container documentation](https://github.com/torerodev/torero-container).
# 📦 torero container
Container image for [torero](https://torero.dev), built using vendor-neutral Containerfile specifications and packaged in a _ready-to-use_ container with optional [OpenTofu](https://opentofu.org) installation. The image is hosted on GitHub Container Registry (GHCR). For more details about _torero_, visit the [official docs](https://docs.torero.dev/en/latest/).

> [!NOTE]
> For questions or _real-time_ feedback, you can connect with us directly in the [Network Automation Forum (NAF) Slack Workspace](https://networkautomationfrm.slack.com/?redir=%2Farchives%2FC075L2LR3HU%3Fname%3DC075L2LR3HU) in the **#tools-torero** channel.

## Features
- Built with vendor-neutral Containerfile for maximum compatibility
- Based on [debian-slim](https://github.com/lxc/lxc-ci/tree/main/images/debian) for minimal footprint
- Hosted on GitHub Container Registry (GHCR) for reliable distribution
- Includes _torero_ installed and ready to go
- Optional [OpenTofu](https://opentofu.org/) installation at runtime
- Optional SSH administration for testing convenience + labs
- Health Check to verify functionality

## Inspiration
Managing and automating a hybrid, _multi-vendor_ infrastrcuture that encompasses _on-premises systems, private and public clouds, edge computing, and colocation environments_ poses significant challenges. How can you experiment to _learn_ without breaking things? How can you test new and innovative products like _torero_ on the test bench without friction to help in your evaluation? How do you test the behavior of changes in lower level environments before making changes to production? I use [containerlab](https://containerlab.dev/) for all of the above! This project makes it easy to insert _torero_ in your _containerlab_ topology file, connect to the container, and run your experiments -- the sky is the limit!

## Getting Started
To get started you can use any OCI-compatible container runtime (Docker, Podman, etc.) with CLI or compose.

### docker cli
```bash
docker run -d -p 2222:22 ghcr.io/torerodev/torero-container:latest
```

![docker cli](./img/docker-cli.gif)

### docker compose _(with latest OpenTofu version)_
```yaml
---
services:
  torero:
    image: ghcr.io/torerodev/torero-container:latest
    container_name: torero
    ports:
      - "2222:22"              # use when ENABLE_SSH_ADMIN=true
    volumes:
      - ./data:/home/admin/data
    environment:
      - ENABLE_SSH_ADMIN=true  # enable ssh admin at runtime
      - INSTALL_OPENTOFU=true  # enable OpenTofu installation at runtime
      - OPENTOFU_VERSION=1.9.0
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
| `ENABLE_SSH_ADMIN` | `false`  | Enable SSH admin user  |
| `INSTALL_OPENTOFU` | `true`   | Install OpenTofu       |
| `OPENTOFU_VERSION` | `1.9.0`  | Set OpenTofu version   |
| `PYTHON_VERSION`   | `3.13.0` | Set Python version     |

## CLI runner script
The _cli-runner.sh_ script provides a convenient way to run, test, and do house cleaning locally when running on your workstation. I use it for quick and dirty testing 🚀

```bash
# build + run
./cli-runner.sh --build --run

# run and immediately ssh into container
./cli-runner.sh --run --ssh

# check status
./cli-runner.sh --status

# stop container
./cli-runner.sh --stop

# start a stopped container
./cli-runner.sh --start

# view logs
./cli-runner.sh --logs

# clean up everything (will prompt before deleting local data)
./cli-runner.sh --clean
```

## Container Architecture
This project uses vendor-neutral Containerfile specifications for maximum compatibility across container runtimes. The image is built and distributed through GitHub Container Registry (GHCR) for reliable access and version management.

## Software Licenses
This project incorporates the following software with their respective licenses:

- torero: refer to the [torero license](https://torero.dev/licenses/eula)
- opentofu: [mozilla public license 2.0](https://github.com/opentofu/opentofu/blob/main/LICENSE) 
- debian: [multiple licenses](https://www.debian.org/legal/licenses/)

All modifications and original code in this project are licensed under the apache license 2.0.

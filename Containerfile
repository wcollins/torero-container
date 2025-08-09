# Use official Python slim image as base
ARG PYTHON_VERSION=3.13.0
ARG TOFU_VERSION=1.10.5

FROM python:${PYTHON_VERSION}-slim-bookworm

LABEL maintainer="torerodev <opensource@itential.com>"
LABEL org.opencontainers.image.source="https://github.com/torerodev/torero-container"
LABEL org.opencontainers.image.description="torero container image"
LABEL org.opencontainers.image.licenses="Apache-2.0"

# default locale
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

# default version
ARG TORERO_VERSION=1.4.0
ENV TORERO_VERSION=${TORERO_VERSION}

# OpenTofu is now installed at build time
ARG TOFU_VERSION
ENV TOFU_VERSION=${TOFU_VERSION:-1.10.5}

# ssh access is disabled by default
ENV ENABLE_SSH_ADMIN=false

# torero eula auto-acceptance is enabled by default
ENV TORERO_APPLICATION_AUTO_ACCEPT_EULA=true

# MCP server is disabled by default
ENV ENABLE_MCP=false

# MCP server default configuration
ENV TORERO_MCP_TRANSPORT_TYPE=sse
ENV TORERO_MCP_TRANSPORT_HOST=0.0.0.0
ENV TORERO_MCP_TRANSPORT_PORT=8080
ENV TORERO_MCP_TRANSPORT_PATH=/sse
ENV TORERO_API_BASE_URL=http://localhost:8000
ENV TORERO_API_TIMEOUT=30
ENV TORERO_LOG_LEVEL=INFO
ENV TORERO_MCP_PID_FILE=/tmp/torero-mcp.pid
ENV TORERO_MCP_LOG_FILE=/home/admin/.torero-mcp.log

# reduce docker image size
ENV DEBIAN_FRONTEND=noninteractive

# copy scripts to image
COPY configure.sh /configure.sh
COPY entrypoint.sh /entrypoint.sh

# Install OpenTofu at build time
RUN apt-get update && apt-get install -y curl unzip && \
    ARCH=$(dpkg --print-architecture) && \
    if [ "$ARCH" = "amd64" ]; then TOFU_ARCH="amd64"; \
    elif [ "$ARCH" = "arm64" ]; then TOFU_ARCH="arm64"; \
    else echo "Unsupported architecture: $ARCH" && exit 1; fi && \
    curl -L -o /tmp/tofu.zip \
    "https://github.com/opentofu/opentofu/releases/download/v${TOFU_VERSION}/tofu_${TOFU_VERSION}_linux_${TOFU_ARCH}.zip" && \
    unzip /tmp/tofu.zip -d /tmp && \
    mv /tmp/tofu /usr/local/bin/tofu && \
    chmod +x /usr/local/bin/tofu && \
    rm /tmp/tofu.zip && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# make executable, run configuration script
RUN chmod +x /configure.sh && /configure.sh && \
    chmod +x /entrypoint.sh

# expose ssh port (only used if SSH is enabled)
EXPOSE 22

# expose MCP port (only used if MCP is enabled)
EXPOSE 8080

# create volume for persistent data
VOLUME ["/home/admin/data"]

# healthcheck - is torero functional?
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD torero version || exit 1

# set entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# default command depends on SSH being enabled
CMD ["/bin/bash", "-c", "if [ \"$ENABLE_SSH_ADMIN\" = \"true\" ]; then /usr/sbin/sshd -D; else tail -f /dev/null; fi"]
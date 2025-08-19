#!/bin/bash
#
# Copyright 2025 torerodev
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
set -euo pipefail

# cleanup function for temporary files
cleanup() {
    rm -f /tmp/tofu.zip /tmp/*.exp /tmp/manifest.json /tmp/tofu /tmp/CHANGELOG.md /tmp/LICENSE /tmp/README.md
}
trap cleanup EXIT

# function to update manifest file
update_manifest() {
    local json_update="$1"
    if [ -f "/etc/torero-image-manifest.json" ] && command -v jq &> /dev/null; then
        jq "$json_update" /etc/torero-image-manifest.json > /tmp/manifest.json
        mv /tmp/manifest.json /etc/torero-image-manifest.json
    fi
}

# function to wait for API to be ready
wait_for_api() {
    local api_port="${1:-8000}"
    local max_attempts="${2:-30}"
    local attempt=0
    
    echo "waiting for torero-api to be ready on port ${api_port}..."
    while [ $attempt -lt $max_attempts ]; do
        if curl -s -o /dev/null -w "%{http_code}" "http://localhost:${api_port}/health" | grep -q "200"; then
            echo "torero-api is ready"
            return 0
        fi
        echo "waiting for torero-api... (attempt $((attempt+1))/${max_attempts})"
        sleep 2
        attempt=$((attempt+1))
    done
    
    echo "warning: torero-api not reachable after ${max_attempts} attempts" >&2
    return 1
}

install_opentofu_version() {
    local target_version="$1"
    local arch=$(dpkg --print-architecture)
    local tofu_arch=""
    
    if [ "$arch" = "amd64" ]; then
        tofu_arch="amd64"
    elif [ "$arch" = "arm64" ]; then
        tofu_arch="arm64"
    else
        echo "error: unsupported architecture: $arch" >&2
        return 1
    fi
    
    echo "installing OpenTofu ${target_version}..."
    
    # download and install the specified version
    if ! curl -L -o /tmp/tofu.zip "https://github.com/opentofu/opentofu/releases/download/v${target_version}/tofu_${target_version}_linux_${tofu_arch}.zip"; then
        echo "error: failed to download OpenTofu ${target_version}" >&2
        return 1
    fi
    
    if ! unzip -o /tmp/tofu.zip -d /tmp; then
        echo "error: failed to extract OpenTofu ${target_version}" >&2
        rm -f /tmp/tofu.zip
        return 1
    fi
    
    if ! mv /tmp/tofu /usr/local/bin/tofu; then
        echo "error: failed to install OpenTofu ${target_version}" >&2
        rm -f /tmp/tofu.zip /tmp/tofu
        return 1
    fi
    
    chmod +x /usr/local/bin/tofu
    
    echo "OpenTofu ${target_version} installed successfully"
    return 0
}

verify_opentofu() {
    local runtime_version="${OPENTOFU_VERSION:-}"
    local build_version="${TOFU_BUILD_VERSION:-1.10.5}"
    
    # check if OpenTofu is installed
    if command -v tofu &> /dev/null; then
        local installed_version=$(tofu version | grep -oP "v\K[0-9]+\.[0-9]+\.[0-9]+" | head -1 || echo "unknown")
        
        # if runtime version is specified and different from installed, install new version
        if [ -n "$runtime_version" ] && [ "$runtime_version" != "$installed_version" ]; then
            echo "OpenTofu ${installed_version} is pre-installed, but OPENTOFU_VERSION=${runtime_version} requested"
            if install_opentofu_version "$runtime_version"; then
                installed_version="$runtime_version"
                echo "OpenTofu switched to version ${runtime_version}"
            else
                echo "warning: failed to install requested version ${runtime_version}, using pre-installed ${installed_version}" >&2
            fi
        else
            if [ -n "$runtime_version" ]; then
                echo "OpenTofu ${installed_version} matches requested version ${runtime_version}"
            else
                echo "OpenTofu ${installed_version} is pre-installed (use OPENTOFU_VERSION env var to override)"
            fi
        fi
        
        # update manifest
        update_manifest ".tools.opentofu = \"${installed_version}\""
        return 0
    else
        # if no OpenTofu found, install the requested or default version
        local target_version="${runtime_version:-$build_version}"
        echo "OpenTofu binary not found, installing version ${target_version}"
        if install_opentofu_version "$target_version"; then
            return 0
        else
            echo "error: failed to install OpenTofu ${target_version}" >&2
            return 1
        fi
    fi
}

configure_dns() {
    echo "configuring DNS at runtime..."
    echo -e "nameserver 8.8.8.8\nnameserver 8.8.4.4" > /etc/resolv.conf
}

handle_torero_eula() {
    local auto_accept_eula="${TORERO_APPLICATION_AUTO_ACCEPT_EULA:-true}"
    if [ "$auto_accept_eula" = "true" ]; then
        echo "handling torero EULA acceptance (TORERO_APPLICATION_AUTO_ACCEPT_EULA=${auto_accept_eula})..."
        
        # create eula acceptance marker for admin user if it doesn't exist
        if [ -d "/home/admin" ] && [ ! -f "/home/admin/.torero.d/.license-accepted" ]; then
            mkdir -p /home/admin/.torero.d
            touch /home/admin/.torero.d/.license-accepted
            chmod -R 755 /home/admin/.torero.d
            chown -R admin:admin /home/admin/.torero.d
            echo "EULA pre-accepted for admin user"
        fi
        
        # try interactive EULA acceptance if expect is available
        if command -v expect &> /dev/null; then
            cat > /tmp/accept-eula.exp << 'EOF'
#!/usr/bin/expect -f
set timeout 10
spawn /usr/local/bin/torero version
expect {
    "Do you agree to the EULA? (yes/no):" {
        send "yes\r"
        expect eof
        exit 0
    }
    timeout {
        exit 0
    }
    eof {
        exit 0
    }
}
EOF
            chmod +x /tmp/accept-eula.exp
            /tmp/accept-eula.exp 2>/dev/null || echo "EULA prompt not found or already accepted"
            rm -f /tmp/accept-eula.exp
        fi
    else
        echo "EULA auto-acceptance disabled (TORERO_APPLICATION_AUTO_ACCEPT_EULA=${auto_accept_eula})"
        echo "user will need to manually accept EULA on first run"
    fi
}

setup_cli_capture() {
    echo "setting up CLI execution capture wrapper..."
    
    # only set up if UI is enabled (since the wrapper sends data to UI)
    if [[ "${ENABLE_UI:-false}" != "true" ]]; then
        echo "skipping CLI capture setup as ENABLE_UI is not set to true"
        return 0
    fi
    
    # backup original torero binary if not already done
    if [ ! -f "/usr/local/bin/torero.real" ]; then
        cp /usr/local/bin/torero /usr/local/bin/torero.real
    fi
    
    # create wrapper script to capture CLI executions and send to UI database
    cat > /usr/local/bin/torero-capture-wrapper.sh << 'EOF'
#!/bin/bash
# Wrapper script to capture torero CLI executions and send to UI database

ORIGINAL_TORERO="/usr/local/bin/torero.real"

# Check if this is a 'run service' command  
if [[ "$1" == "run" && "$2" == "service" && "$#" -ge 4 ]]; then
    SERVICE_TYPE="$3"
    
    # Handle different command structures
    if [[ "$SERVICE_TYPE" == "opentofu-plan" && "$#" -ge 5 ]]; then
        # OpenTofu commands: run service opentofu-plan apply/destroy service-name
        SERVICE_NAME="$5"
    else
        # Regular commands: run service type service-name
        SERVICE_NAME="$4"
    fi
    
    # Debug logging to see what we captured
    echo "DEBUG: All args: $@" >> /tmp/torero-wrapper-debug.log
    echo "DEBUG: SERVICE_TYPE='$SERVICE_TYPE', SERVICE_NAME='$SERVICE_NAME'" >> /tmp/torero-wrapper-debug.log
    
    # Capture execution with timing
    START_TIME=$(date -u +"%Y-%m-%dT%H:%M:%S.%6NZ")
    START_EPOCH=$(date +%s.%N)
    
    # Run the original command and capture all output
    OUTPUT_FILE=$(mktemp)
    ERROR_FILE=$(mktemp)
    
    # Run command and capture stdout/stderr separately
    $ORIGINAL_TORERO "$@" > "$OUTPUT_FILE" 2> "$ERROR_FILE"
    RETURN_CODE=$?
    
    END_TIME=$(date -u +"%Y-%m-%dT%H:%M:%S.%6NZ")
    END_EPOCH=$(date +%s.%N)
    ELAPSED=$(echo "scale=6; $END_EPOCH - $START_EPOCH" | bc -l)
    
    STDOUT_CONTENT=$(cat "$OUTPUT_FILE")
    STDERR_CONTENT=$(cat "$ERROR_FILE")
    
    # Send execution data to UI database (async, non-blocking)
    (
        curl -X POST http://localhost:8001/api/record-execution/ \
            -H "Content-Type: application/json" \
            -d "{
                \"service_name\": \"$SERVICE_NAME\",
                \"service_type\": \"$SERVICE_TYPE\",
                \"execution_data\": {
                    \"return_code\": $RETURN_CODE,
                    \"stdout\": $(echo "$STDOUT_CONTENT" | jq -R -s .),
                    \"stderr\": $(echo "$STDERR_CONTENT" | jq -R -s .),
                    \"start_time\": \"$START_TIME\",
                    \"end_time\": \"$END_TIME\",
                    \"elapsed_time\": $ELAPSED
                }
            }" >/dev/null 2>&1
    ) &
    
    # Clean up temp files
    rm -f "$OUTPUT_FILE" "$ERROR_FILE"
    
    # Display original output to user (exactly as torero would)
    echo "$STDOUT_CONTENT"
    if [[ -n "$STDERR_CONTENT" ]]; then
        echo "$STDERR_CONTENT" >&2
    fi
    
    exit $RETURN_CODE
else
    # For non-execution commands, just pass through
    exec $ORIGINAL_TORERO "$@"
fi
EOF

    # make wrapper script executable
    chmod +x /usr/local/bin/torero-capture-wrapper.sh
    
    # replace torero with wrapper
    cp /usr/local/bin/torero-capture-wrapper.sh /usr/local/bin/torero
    
    echo "CLI execution capture wrapper installed successfully"
}

setup_supervisor() {
    echo "installing and configuring supervisor..."
    
    # install supervisor
    apt-get update -y
    apt-get install -y supervisor
    
    # create supervisor configuration directory
    mkdir -p /etc/supervisor/conf.d
    
    # create supervisor configuration for enabled services
    cat > /etc/supervisor/conf.d/torero-services.conf << 'EOF'
[unix_http_server]
file=/tmp/supervisor.sock

[supervisord]
logfile=/tmp/supervisord.log
logfile_maxbytes=50MB
logfile_backups=10
loglevel=info
pidfile=/tmp/supervisord.pid
nodaemon=true
silent=false

[rpcinterface:supervisor]
supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface

[supervisorctl]
serverurl=unix:///tmp/supervisor.sock

EOF

    # add torero-api service if enabled
    if [[ "${ENABLE_API:-false}" == "true" ]]; then
        local api_port="${API_PORT:-8000}"
        cat >> /etc/supervisor/conf.d/torero-services.conf << EOF
[program:torero-api]
command=/usr/local/bin/torero-api --host 0.0.0.0 --port ${api_port} --log-file /home/admin/.torero-api.log
directory=/home/admin
user=admin
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/admin/.torero-api.log
stderr_logfile=/home/admin/.torero-api.log
environment=HOME="/home/admin",USER="admin"

EOF
    fi
    
    # add torero-mcp service if enabled
    if [[ "${ENABLE_MCP:-false}" == "true" ]]; then
        local mcp_transport="${TORERO_MCP_TRANSPORT_TYPE:-sse}"
        local mcp_host="${TORERO_MCP_TRANSPORT_HOST:-0.0.0.0}"
        local mcp_port="${TORERO_MCP_TRANSPORT_PORT:-8080}"
        local mcp_path="${TORERO_MCP_TRANSPORT_PATH:-/sse}"
        local api_base_url="${TORERO_API_BASE_URL:-http://localhost:${API_PORT:-8000}}"
        local api_timeout="${TORERO_API_TIMEOUT:-30}"
        local log_level="${TORERO_LOG_LEVEL:-INFO}"
        local mcp_log_file="${TORERO_MCP_LOG_FILE:-/home/admin/.torero-mcp.log}"
        
        cat >> /etc/supervisor/conf.d/torero-services.conf << EOF
[program:torero-mcp]
command=/usr/local/bin/torero-mcp run --transport ${mcp_transport} --host ${mcp_host} --port ${mcp_port}
directory=/home/admin
user=admin
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=${mcp_log_file}
stderr_logfile=${mcp_log_file}
environment=HOME="/home/admin",USER="admin",TORERO_MCP_TRANSPORT_TYPE="${mcp_transport}",TORERO_MCP_TRANSPORT_HOST="${mcp_host}",TORERO_MCP_TRANSPORT_PORT="${mcp_port}",TORERO_MCP_TRANSPORT_PATH="${mcp_path}",TORERO_API_BASE_URL="${api_base_url}",TORERO_API_TIMEOUT="${api_timeout}",TORERO_LOG_LEVEL="${log_level}"

EOF
    fi
    
    # add torero-ui service if enabled
    if [[ "${ENABLE_UI:-false}" == "true" ]]; then
        local ui_port="${UI_PORT:-8001}"
        local api_base_url="${TORERO_API_BASE_URL:-http://localhost:${API_PORT:-8000}}"
        local refresh_interval="${UI_REFRESH_INTERVAL:-30}"
        local ui_log_file="${TORERO_UI_LOG_FILE:-/home/admin/.torero-ui.log}"
        
        cat >> /etc/supervisor/conf.d/torero-services.conf << EOF
[program:torero-ui]
command=python torero_ui/manage.py runserver 0.0.0.0:${ui_port} --noreload
directory=/opt/torero-ui
user=admin
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=${ui_log_file}
stderr_logfile=${ui_log_file}
environment=HOME="/home/admin",USER="admin",DJANGO_SETTINGS_MODULE="torero_ui.settings",TORERO_API_BASE_URL="${api_base_url}",UI_REFRESH_INTERVAL="${refresh_interval}",DEBUG="False"

EOF
    fi
    
    echo "supervisor configuration created successfully"
    return 0
}

setup_torero_api() {
    if [[ "${ENABLE_API:-false}" != "true" ]]; then
        echo "skipping torero-api setup as ENABLE_API is not set to true"
        return 0
    fi

    local api_port="${API_PORT:-8000}"
    echo "setting up torero-api runtime configuration..."

    # ensure db maps to admin user
    if [ ! -d "/home/admin/.torero.d" ]; then
        echo "creating torero database directory for admin user..."
        mkdir -p /home/admin/.torero.d
        chown -R admin:admin /home/admin/.torero.d
        chmod 755 /home/admin/.torero.d
    fi

    # create log file
    touch /home/admin/.torero-api.log
    chown admin:admin /home/admin/.torero-api.log

    echo "torero-api runtime setup completed (will be managed by supervisor)"
    return 0
}

setup_torero_mcp() {
    if [[ "${ENABLE_MCP:-false}" != "true" ]]; then
        echo "skipping torero-mcp setup as ENABLE_MCP is not set to true"
        return 0
    fi

    local mcp_log_file="${TORERO_MCP_LOG_FILE:-/home/admin/.torero-mcp.log}"
    echo "setting up torero-mcp runtime configuration..."

    # create log file
    touch "${mcp_log_file}"
    chown admin:admin "${mcp_log_file}"

    echo "torero-mcp runtime setup completed (will be managed by supervisor)"
    return 0
}

# Setup SSH at runtime (SSH is no longer configured at build time)
setup_ssh_runtime() {
    if [ "${ENABLE_SSH_ADMIN}" = "true" ]; then
        echo "Setting up SSH admin access at runtime..."
        
        # Install SSH packages if not present
        if ! command -v sshd &> /dev/null; then
            echo "Installing SSH packages..."
            apt-get update -y
            apt-get install -y --no-install-recommends openssh-server sudo
        fi
        
        # Always ensure /var/run/sshd exists (required for sshd to start)
        mkdir -p /var/run/sshd
        
        # set up admin user if doesn't exist
        if ! id admin &>/dev/null; then
            useradd -m -s /bin/bash admin
        fi
        
        # Always set/reset the password
        echo "admin:admin" | chpasswd
        
        # Ensure sudo permissions
        if [ ! -f "/etc/sudoers.d/admin" ]; then
            echo "admin ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/admin
            chmod 0440 /etc/sudoers.d/admin
        fi
        
        # Configure SSH if not already configured
        if [ ! -f "/etc/ssh/sshd_config" ] || ! grep -q "PermitRootLogin" /etc/ssh/sshd_config; then
            echo "Configuring SSH settings..."
            echo "PermitRootLogin no" >> /etc/ssh/sshd_config
            echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config
            echo "PubkeyAuthentication yes" >> /etc/ssh/sshd_config
            echo "PermitEmptyPasswords no" >> /etc/ssh/sshd_config
            echo "LoginGraceTime 120" >> /etc/ssh/sshd_config
        fi
        
        # Set up SSH keys directory
        mkdir -p /home/admin/.ssh
        chmod 700 /home/admin/.ssh
        touch /home/admin/.ssh/authorized_keys
        chmod 600 /home/admin/.ssh/authorized_keys
        chown -R admin:admin /home/admin/.ssh
        
        # Generate SSH host keys if they don't exist
        if [ ! -f "/etc/ssh/ssh_host_rsa_key" ]; then
            ssh-keygen -A
        fi
        
        # Start SSH daemon
        echo "Starting SSH daemon..."
        /usr/sbin/sshd
        
        # Verify SSH is running
        if pgrep -x sshd > /dev/null; then
            echo "SSH daemon started successfully"
            # update manifest
            update_manifest '.config.ssh_enabled = "true"'
        else
            echo "WARNING: Failed to start SSH daemon" >&2
        fi
    fi
}

setup_torero_ui() {
    if [[ "${ENABLE_UI:-false}" != "true" ]]; then
        echo "skipping torero-ui setup as ENABLE_UI is not set to true"
        return 0
    fi

    local api_base_url="${TORERO_API_BASE_URL:-http://localhost:${API_PORT:-8000}}"
    local refresh_interval="${UI_REFRESH_INTERVAL:-30}"
    local ui_log_file="${TORERO_UI_LOG_FILE:-/home/admin/.torero-ui.log}"

    echo "setting up torero-ui runtime configuration..."

    # create log file
    touch "${ui_log_file}"
    chown admin:admin "${ui_log_file}"

    # ensure data directory exists and run migrations for persistent database
    mkdir -p /home/admin/data
    chown -R admin:admin /home/admin/data
    
    # run database migrations for runtime (static files collected at build time)
    echo "running database migrations for persistent storage..."
    su - admin -c "export DJANGO_SETTINGS_MODULE='torero_ui.settings' && \
                   export TORERO_API_BASE_URL='${api_base_url}' && \
                   export UI_REFRESH_INTERVAL='${refresh_interval}' && \
                   export DEBUG='False' && \
                   cd /opt/torero-ui && \
                   python torero_ui/manage.py migrate"
    
    echo "torero-ui runtime setup completed (will be managed by supervisor)"
    return 0
}


# unset build mode for runtime
unset CONTAINER_BUILD_MODE

configure_dns
setup_ssh_runtime
handle_torero_eula
verify_opentofu || echo "OpenTofu verification failed, continuing without it"
setup_torero_api || echo "torero-api setup failed, continuing without it"
setup_torero_mcp || echo "torero-mcp setup failed, continuing without it"
setup_torero_ui || echo "torero-ui setup failed, continuing without it"
setup_cli_capture || echo "CLI capture setup failed, continuing without it"
setup_supervisor || echo "supervisor setup failed, continuing without it"

# Check if any services are enabled that need supervisor
if [[ "${ENABLE_API:-false}" == "true" || "${ENABLE_MCP:-false}" == "true" || "${ENABLE_UI:-false}" == "true" ]]; then
    echo "starting services with supervisor..."
    # Wait a moment for services to be ready
    sleep 2
    # Start supervisor in foreground mode with our configuration
    exec /usr/bin/supervisord -c /etc/supervisor/conf.d/torero-services.conf
else
    echo "no services enabled, continuing with original command..."
    exec "$@"
fi
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
set -eo pipefail

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
    rm -f /tmp/tofu.zip /tmp/CHANGELOG.md /tmp/LICENSE /tmp/README.md
    
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
        
        # update manifest if present
        if [ -f "/etc/torero-image-manifest.json" ]; then
            if command -v jq &> /dev/null; then
                jq ".tools.opentofu = \"${installed_version}\"" /etc/torero-image-manifest.json > /tmp/manifest.json
                mv /tmp/manifest.json /etc/torero-image-manifest.json
            else
                echo "jq not found, skipping manifest update"
            fi
        fi
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

setup_torero_api() {
    if [[ "${ENABLE_API}" != "true" ]]; then
        echo "skipping torero-api setup as ENABLE_API is not set to true"
        return 0
    fi

    local api_port="${API_PORT:-8000}"
    echo "setting up torero-api on port ${api_port}..."

    # install uv
    if ! command -v uv &> /dev/null; then
        echo "installing uv package manager..."
        curl -LsSf https://astral.sh/uv/install.sh | sh || {
            echo "error: failed to install uv" >&2
            return 1
        }
        # add uv to PATH
        export PATH="$HOME/.local/bin:$PATH"
    fi

    # clone and install torero-api
    if [ ! -d "/opt/torero-api" ]; then
        echo "cloning torero-api repository..."
        git clone https://github.com/torerodev/torero-api.git /opt/torero-api || {
            echo "error: failed to clone torero-api repository" >&2
            return 1
        }
    fi

    cd /opt/torero-api
    echo "installing torero-api with uv..."
    PATH="$HOME/.local/bin:$PATH" uv pip install --system -e . || {
        echo "error: failed to install torero-api" >&2
        return 1
    }

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

    # start torero-api daemon
    echo "starting torero-api daemon on port ${api_port}..."

    # run as admin user
    su - admin -c "nohup /usr/local/bin/torero-api --daemon --host 0.0.0.0 --port ${api_port} --log-file /home/admin/.torero-api.log > /dev/null 2>&1 &"
    
    # success?
    sleep 2
    if pgrep -f "torero-api" > /dev/null; then
        echo "torero-api daemon started successfully on port ${api_port}"
        
        # update manifest if available
        if [ -f "/etc/torero-image-manifest.json" ] && command -v jq &> /dev/null; then
            jq ".services.torero_api = {\"enabled\": true, \"port\": ${api_port}}" /etc/torero-image-manifest.json > /tmp/manifest.json
            mv /tmp/manifest.json /etc/torero-image-manifest.json
        fi
    else
        echo "warning: torero-api daemon failed to start" >&2
        return 1
    fi

    return 0
}

setup_torero_mcp() {
    if [[ "${ENABLE_MCP}" != "true" ]]; then
        echo "skipping torero-mcp setup as ENABLE_MCP is not set to true"
        return 0
    fi

    # ensure torero-api is running first
    if [[ "${ENABLE_API}" == "true" ]]; then
        local api_port="${API_PORT:-8000}"
        local max_attempts=30
        local attempt=0
        
        echo "waiting for torero-api to be ready on port ${api_port}..."
        while [ $attempt -lt $max_attempts ]; do
            if curl -s -o /dev/null -w "%{http_code}" "http://localhost:${api_port}/health" | grep -q "200"; then
                echo "torero-api is ready"
                break
            fi
            echo "waiting for torero-api... (attempt $((attempt+1))/${max_attempts})"
            sleep 2
            attempt=$((attempt+1))
        done
        
        if [ $attempt -eq $max_attempts ]; then
            echo "warning: torero-api not reachable after ${max_attempts} attempts" >&2
            return 1
        fi
    fi

    # set default MCP configuration
    local mcp_transport="${TORERO_MCP_TRANSPORT_TYPE:-sse}"
    local mcp_host="${TORERO_MCP_TRANSPORT_HOST:-0.0.0.0}"
    local mcp_port="${TORERO_MCP_TRANSPORT_PORT:-8080}"
    local mcp_path="${TORERO_MCP_TRANSPORT_PATH:-/sse}"
    local api_base_url="${TORERO_API_BASE_URL:-http://localhost:${API_PORT:-8000}}"
    local api_timeout="${TORERO_API_TIMEOUT:-30}"
    local log_level="${TORERO_LOG_LEVEL:-INFO}"
    local mcp_pid_file="${TORERO_MCP_PID_FILE:-/tmp/torero-mcp.pid}"
    local mcp_log_file="${TORERO_MCP_LOG_FILE:-/home/admin/.torero-mcp.log}"

    echo "setting up torero-mcp with transport ${mcp_transport} on ${mcp_host}:${mcp_port}..."

    # ensure uv is available
    if ! command -v uv &> /dev/null; then
        echo "installing uv package manager..."
        curl -LsSf https://astral.sh/uv/install.sh | sh || {
            echo "error: failed to install uv" >&2
            return 1
        }
        export PATH="$HOME/.local/bin:$PATH"
    fi

    # clone and install torero-mcp
    if [ ! -d "/opt/torero-mcp" ]; then
        echo "cloning torero-mcp repository..."
        git clone https://github.com/torerodev/torero-mcp.git /opt/torero-mcp || {
            echo "error: failed to clone torero-mcp repository" >&2
            return 1
        }
    fi

    cd /opt/torero-mcp
    echo "installing torero-mcp with uv..."
    PATH="$HOME/.local/bin:$PATH" uv pip install --system -e . || {
        echo "error: failed to install torero-mcp" >&2
        return 1
    }

    # create log file
    touch "${mcp_log_file}"
    chown admin:admin "${mcp_log_file}"

    # export environment variables for torero-mcp
    export TORERO_MCP_TRANSPORT_TYPE="${mcp_transport}"
    export TORERO_MCP_TRANSPORT_HOST="${mcp_host}"
    export TORERO_MCP_TRANSPORT_PORT="${mcp_port}"
    export TORERO_MCP_TRANSPORT_PATH="${mcp_path}"
    export TORERO_API_BASE_URL="${api_base_url}"
    export TORERO_API_TIMEOUT="${api_timeout}"
    export TORERO_LOG_LEVEL="${log_level}"
    export TORERO_MCP_PID_FILE="${mcp_pid_file}"
    export TORERO_MCP_LOG_FILE="${mcp_log_file}"

    # start torero-mcp daemon
    echo "starting torero-mcp daemon with transport ${mcp_transport} on ${mcp_host}:${mcp_port}..."
    
    # run as admin user with environment variables
    su - admin -c "export TORERO_MCP_TRANSPORT_TYPE='${mcp_transport}' && \
                   export TORERO_MCP_TRANSPORT_HOST='${mcp_host}' && \
                   export TORERO_MCP_TRANSPORT_PORT='${mcp_port}' && \
                   export TORERO_MCP_TRANSPORT_PATH='${mcp_path}' && \
                   export TORERO_API_BASE_URL='${api_base_url}' && \
                   export TORERO_API_TIMEOUT='${api_timeout}' && \
                   export TORERO_LOG_LEVEL='${log_level}' && \
                   export TORERO_MCP_PID_FILE='${mcp_pid_file}' && \
                   export TORERO_MCP_LOG_FILE='${mcp_log_file}' && \
                   nohup /usr/local/bin/torero-mcp run --transport ${mcp_transport} --host ${mcp_host} --port ${mcp_port} > /dev/null 2>&1 &"
    
    # verify startup
    sleep 3
    if [ -f "${mcp_pid_file}" ] && kill -0 $(cat "${mcp_pid_file}") 2>/dev/null; then
        echo "torero-mcp daemon started successfully on ${mcp_host}:${mcp_port}"
        
        # update manifest if available
        if [ -f "/etc/torero-image-manifest.json" ] && command -v jq &> /dev/null; then
            jq ".services.torero_mcp = {\"enabled\": true, \"transport\": \"${mcp_transport}\", \"host\": \"${mcp_host}\", \"port\": ${mcp_port}}" /etc/torero-image-manifest.json > /tmp/manifest.json
            mv /tmp/manifest.json /etc/torero-image-manifest.json
        fi
    else
        echo "warning: torero-mcp daemon failed to start" >&2
        return 1
    fi

    return 0
}

# check if ssh access is needed but not configured at build time
setup_ssh_runtime() {
    if [ "${ENABLE_SSH_ADMIN}" = "true" ]; then

        # check if ssh is already set up
        if [ ! -f "/etc/ssh/sshd_config" ] || ! grep -q "PermitRootLogin" /etc/ssh/sshd_config; then
            echo "SSH was not enabled at build time but requested at runtime. Installing SSH..."
            apt-get update -y
            apt-get install -y --no-install-recommends openssh-server sudo
            
            # set up admin user
            if ! id admin &>/dev/null; then
                useradd -m -s /bin/bash admin
            fi
            echo "admin:admin" | chpasswd
            echo "admin ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/admin
            chmod 0440 /etc/sudoers.d/admin
            
            # configure ssh
            mkdir -p /var/run/sshd
            echo "PermitRootLogin no" >> /etc/ssh/sshd_config
            echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config
            echo "PubkeyAuthentication yes" >> /etc/ssh/sshd_config
            echo "PermitEmptyPasswords no" >> /etc/ssh/sshd_config
            echo "LoginGraceTime 120" >> /etc/ssh/sshd_config
            
            mkdir -p /home/admin/.ssh
            chmod 700 /home/admin/.ssh
            touch /home/admin/.ssh/authorized_keys
            chmod 600 /home/admin/.ssh/authorized_keys
            chown -R admin:admin /home/admin/.ssh
            
            ssh-keygen -A
            
            # update manifest
            if [ -f "/etc/torero-image-manifest.json" ] && command -v jq &> /dev/null; then
                jq '.config.ssh_enabled = "true"' /etc/torero-image-manifest.json > /tmp/manifest.json
                mv /tmp/manifest.json /etc/torero-image-manifest.json
            fi
            
            echo "SSH access enabled at runtime"
        fi
    fi
}

configure_dns
setup_ssh_runtime
handle_torero_eula
verify_opentofu || echo "OpenTofu verification failed, continuing without it"
setup_torero_api || echo "torero-api setup failed, continuing without it"
setup_torero_mcp || echo "torero-mcp setup failed, continuing without it"
exec "$@"
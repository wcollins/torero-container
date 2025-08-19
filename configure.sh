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

# debugging for ci
if [ "${CI:-false}" = "true" ]; then
    set -x
fi

# purpose: build-phase script for torero container
check_version() {
    if [ -z "${TORERO_VERSION:-}" ]; then
        echo "error: torero_version must be set" >&2
        exit 1
    fi
}

install_packages() {
    echo "installing dependencies..."
    echo "Architecture: $(uname -m)"
    echo "Python version: $(python3 --version 2>&1 || echo 'Python not found')"
    apt-get update -y || { echo "failed to update package list" >&2; exit 1; }
    
    # install all core packages including curl and unzip for OpenTofu
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        git \
        tzdata \
        gnupg \
        dirmngr \
        expect \
        jq \
        iputils-ping \
        iproute2 \
        net-tools \
        procps \
        unzip \
        file \
        locales \
        vim \
        bc \
        || { echo "failed to install core packages" >&2; exit 1; }
}

setup_admin_user() {
    echo "setting up admin user..."
    useradd -m -s /bin/bash admin || { echo "failed to create admin user" >&2; exit 1; }
    
    mkdir -p /home/admin/data
    chown admin:admin /home/admin/data
}


configure_locale() {
    echo "configuring locale..."
    
    # set up locale
    sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen
    locale-gen
    update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8
    
    # add to environment
    echo "export LANG=en_US.UTF-8" >> /etc/profile.d/locale.sh
    echo "export LC_ALL=en_US.UTF-8" >> /etc/profile.d/locale.sh
}

install_opentofu() {
    local version="${OPENTOFU_BUILD_VERSION:-1.10.5}"
    local arch=""
    
    # detect architecture
    case "$(uname -m)" in
        x86_64|amd64)
            arch="amd64"
            ;;
        aarch64|arm64)
            arch="arm64"
            ;;
        *)
            echo "unsupported architecture for OpenTofu: $(uname -m)" >&2
            return 1
            ;;
    esac
    
    echo "installing OpenTofu ${version} for ${arch} architecture..."
    
    local tofu_url="https://github.com/opentofu/opentofu/releases/download/v${version}/tofu_${version}_linux_${arch}.zip"
    local tofu_zip="/tmp/tofu.zip"
    
    # download with retry logic
    local max_attempts=3
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        echo "Download attempt $attempt of $max_attempts"
        
        if curl -fL --connect-timeout 30 --max-time 300 "$tofu_url" -o "$tofu_zip" 2>&1; then
            echo "Download successful"
            break
        else
            echo "Download attempt $attempt failed" >&2
            if [ $attempt -eq $max_attempts ]; then
                echo "failed to download OpenTofu after $max_attempts attempts" >&2
                return 1
            fi
            echo "Retrying in 5 seconds..." >&2
            sleep 5
            attempt=$((attempt + 1))
        fi
    done
    
    # extract and install
    if ! unzip -o "$tofu_zip" -d /tmp; then
        echo "failed to extract OpenTofu" >&2
        rm -f "$tofu_zip"
        return 1
    fi
    
    if ! mv /tmp/tofu /usr/local/bin/tofu; then
        echo "failed to install OpenTofu" >&2
        rm -f "$tofu_zip" /tmp/tofu
        return 1
    fi
    
    chmod +x /usr/local/bin/tofu
    rm -f "$tofu_zip" /tmp/CHANGELOG.md /tmp/LICENSE /tmp/README.md
    
    # verify installation
    if /usr/local/bin/tofu version; then
        echo "OpenTofu ${version} installed successfully"
    else
        echo "OpenTofu installation verification failed" >&2
        return 1
    fi
}

install_torero() {

    # detect architecture
    local arch=""
    case "$(uname -m)" in
        x86_64|amd64)
            arch="amd64"
            ;;
        aarch64|arm64)
            arch="arm64"
            ;;
        *)
            echo "unsupported architecture: $(uname -m)" >&2
            exit 1
            ;;
    esac
    
    local torero_url="https://download.torero.dev/torero-v${TORERO_VERSION}-linux-${arch}.tar.gz"
    local torero_tar="/tmp/torero.tar.gz"

    echo "installing torero version ${TORERO_VERSION} for ${arch} architecture..."
    echo "downloading from: $torero_url"
    
    # download with retry logic
    local max_attempts=3
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        echo "Download attempt $attempt of $max_attempts"
        
        # use curl with verbose error reporting
        if curl -fL --connect-timeout 30 --max-time 300 "$torero_url" -o "$torero_tar" 2>&1; then
            echo "Download successful"
            echo "File size: $(stat -c%s "$torero_tar" 2>/dev/null || stat -f%z "$torero_tar" 2>/dev/null || echo 'unknown')"
            break
        else
            echo "Download attempt $attempt failed" >&2
            if [ $attempt -eq $max_attempts ]; then
                echo "failed to download torero after $max_attempts attempts" >&2
                echo "URL: $torero_url" >&2
                echo "HTTP response:" >&2
                curl -I "$torero_url" >&2 || true
                exit 1
            fi
            echo "Retrying in 5 seconds..." >&2
            sleep 5
            attempt=$((attempt + 1))
        fi
    done
    
    # is file actually gzipped?
    if command -v file >/dev/null 2>&1; then
        if ! file "$torero_tar" | grep -q "gzip compressed"; then
            echo "Downloaded file is not a gzip archive" >&2
            echo "File type: $(file "$torero_tar")" >&2
            echo "First 100 bytes:" >&2
            head -c 100 "$torero_tar" >&2
            exit 1
        fi
    else
        echo "Warning: 'file' command not available, skipping file type check"
    fi
    
    # try to extract
    if ! tar -xzf "$torero_tar" -C /tmp 2>&1; then
        echo "failed to extract torero" >&2
        echo "Tar file details:" >&2
        ls -la "$torero_tar" >&2
        echo "File type:" >&2
        file "$torero_tar" >&2 || echo "file command not available" >&2
        echo "First 200 characters of file:" >&2
        head -c 200 "$torero_tar" >&2 || true
        echo "" >&2
        exit 1
    fi
    
    mv /tmp/torero /usr/local/bin/torero || { echo "failed to move torero" >&2; exit 1; }
    chmod +x /usr/local/bin/torero || { echo "failed to set torero permissions" >&2; exit 1; }
    
    # clean up
    rm -f "$torero_tar"
    
    # verify install
    /usr/local/bin/torero version || { echo "torero installation verification failed" >&2; exit 1; }
}

# set up CLI execution capture wrapper
setup_cli_capture() {
    echo "setting up CLI execution capture wrapper..."
    
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

    # install the wrapper if torero exists
    if [[ -f "/usr/local/bin/torero" ]]; then
        # Backup original if not already done
        if [[ ! -f "/usr/local/bin/torero.real" ]]; then
            cp /usr/local/bin/torero /usr/local/bin/torero.real
        fi
        
        # install wrapper
        chmod +x /usr/local/bin/torero-capture-wrapper.sh
        cp /usr/local/bin/torero-capture-wrapper.sh /usr/local/bin/torero
        
        echo "CLI execution capture wrapper installed - all CLI runs will be recorded in UI database"
    else
        echo "torero binary not found, skipping CLI capture setup"
    fi
}

# set up python environment
setup_python() {
    echo "setting up python environment..."
    
    # upgrade pip and install essential packages
    python3 -m pip install --no-cache-dir --upgrade pip setuptools wheel virtualenv || {
        echo "Failed to install Python packages. Python version:" >&2
        python3 --version >&2
        echo "pip version:" >&2
        pip3 --version >&2 || echo "pip3 not found" >&2
        return 1
    }
    
    # create a virtual environment for admin user
    if [ -d "/home/admin" ]; then
        mkdir -p /home/admin/.venvs
        python3 -m venv /home/admin/.venvs/default
        chown -R admin:admin /home/admin/.venvs
        
        # add activation to .bashrc
        echo 'export PATH="/home/admin/.venvs/default/bin:$PATH"' >> /home/admin/.bashrc
    fi
    
    # verify installation
    python3 --version || { echo "Python verification failed" >&2; return 1; }
    pip3 --version || { echo "pip verification failed" >&2; return 1; }
}

cleanup() {
    echo "cleaning up..."
    apt-get clean
    apt-get autoremove -y
    rm -rf /var/lib/apt/lists/*
    rm -rf /tmp/*
}

create_manifest() {
    echo "creating version manifest..."
    mkdir -p /etc
    
    local opentofu_version="not_installed"
    if command -v tofu &> /dev/null; then
        opentofu_version=$(tofu version | grep -oP "v\K[0-9]+\.[0-9]+\.[0-9]+" | head -1 || echo "unknown")
    fi
    
    cat > /etc/torero-image-manifest.json << EOF
{
  "build_date": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "architecture": "$(uname -m)",
  "tools": {
    "torero": "${TORERO_VERSION}",
    "opentofu": "${opentofu_version}",
    "python": "$(python3 --version 2>&1)"
  },
  "config": {
    "ssh_enabled": "runtime_only"
  }
}
EOF
}

main() {
    check_version
    
    # verify Python is available from base image
    if ! command -v python3 >/dev/null 2>&1; then
        echo "ERROR: Python3 not found in base image" >&2
        echo "Current PATH: $PATH" >&2
        echo "Available commands in /usr/local/bin:" >&2
        ls -la /usr/local/bin/ 2>&1 || echo "Cannot list /usr/local/bin" >&2
        exit 1
    fi
    
    install_packages
    configure_locale
    setup_admin_user
    setup_python
    install_torero
    setup_cli_capture
    install_opentofu || echo "WARNING: OpenTofu installation failed, will retry at runtime"
    create_manifest
    cleanup
    echo "configuration complete!"
}

main
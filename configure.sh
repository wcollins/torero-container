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
    
    # always install core packages
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
        unzip \
        locales \
        vim \
        || { echo "failed to install core packages" >&2; exit 1; }
        
    # only install ssh-related packages if ssh is enabled
    if [ "${ENABLE_SSH_ADMIN:-false}" = "true" ]; then
        apt-get install -y --no-install-recommends \
            openssh-server \
            sudo || { echo "failed to install SSH packages" >&2; exit 1; }
    fi
}

setup_admin_user() {
    echo "setting up admin user..."
    useradd -m -s /bin/bash admin || { echo "failed to create admin user" >&2; exit 1; }
    
    # only set password if ssh is enabled
    if [ "${ENABLE_SSH_ADMIN:-false}" = "true" ]; then
        echo "admin:admin" | chpasswd || { echo "failed to set admin password" >&2; exit 1; }
        echo "admin ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/admin
        chmod 0440 /etc/sudoers.d/admin || { echo "failed to set sudoers permissions" >&2; exit 1; }
    fi
    
    mkdir -p /home/admin/data
    chown admin:admin /home/admin/data
}

configure_ssh() {
    echo "configuring ssh..."
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
    curl -L "$torero_url" -o "$torero_tar" || { echo "failed to download torero" >&2; exit 1; }
    tar -xzf "$torero_tar" -C /tmp || { echo "failed to extract torero" >&2; exit 1; }
    
    mv /tmp/torero /usr/local/bin/torero || { echo "failed to move torero" >&2; exit 1; }
    chmod +x /usr/local/bin/torero || { echo "failed to set torero permissions" >&2; exit 1; }
    
    # clean up
    rm -f "$torero_tar"
    
    # verify install
    /usr/local/bin/torero version || { echo "torero installation verification failed" >&2; exit 1; }
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
    cat > /etc/torero-image-manifest.json << EOF
{
  "build_date": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "architecture": "$(uname -m)",
  "tools": {
    "torero": "${TORERO_VERSION}",
    "python": "$(python3 --version 2>&1)"
  },
  "config": {
    "ssh_enabled": "${ENABLE_SSH_ADMIN:-false}"
  }
}
EOF
}

main() {
    check_version
    
    # Verify Python is available from base image
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
    
    # only configure ssh if enabled
    if [ "${ENABLE_SSH_ADMIN:-false}" = "true" ]; then
        configure_ssh
        echo "SSH admin access enabled"
    else
        echo "SSH admin access disabled"
    fi
    
    install_torero
    create_manifest
    cleanup
    echo "configuration complete!"
}

main
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

install_opentofu() {
    if [[ "${INSTALL_OPENTOFU}" == "false" ]]; then
        echo "skipping opentofu installation as INSTALL_OPENTOFU=false"
        return 0
    fi

    if command -v tofu &> /dev/null; then
        INSTALLED_VERSION=$(tofu version | grep -oP "v\K[0-9]+\.[0-9]+\.[0-9]+" | head -1)
        if [[ "${INSTALLED_VERSION}" == "${OPENTOFU_VERSION}" ]]; then
            echo "opentofu ${OPENTOFU_VERSION} is already installed"
            return 0
        else
            echo "replacing opentofu ${INSTALLED_VERSION} with ${OPENTOFU_VERSION}"
        fi
    else
        echo "installing opentofu version ${OPENTOFU_VERSION}..."
    fi

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
            echo "warning: unsupported architecture $(uname -m) for opentofu" >&2
            return 1
            ;;
    esac
    
    local os="linux"
    local opentofu_url="https://github.com/opentofu/opentofu/releases/download/v${OPENTOFU_VERSION}/tofu_${OPENTOFU_VERSION}_${os}_${arch}.zip"
    local opentofu_zip="/tmp/opentofu.zip"

    curl -L "$opentofu_url" -o "$opentofu_zip" || { 
        echo "warning: failed to download opentofu v${OPENTOFU_VERSION}" >&2 
        return 1
    }
    
    mkdir -p /tmp/opentofu
    unzip -q "$opentofu_zip" -d /tmp/opentofu || { 
        echo "warning: failed to extract opentofu" >&2 
        return 1
    }
    
    mv /tmp/opentofu/tofu /usr/local/bin/tofu || { 
        echo "warning: failed to move opentofu" >&2 
        return 1
    }
    
    rm -f "$opentofu_zip"
    rm -rf /tmp/opentofu
    
    chmod +x /usr/local/bin/tofu || { 
        echo "warning: failed to set opentofu permissions" >&2 
        return 1
    }
    
    /usr/local/bin/tofu version || { 
        echo "warning: opentofu installation verification failed" >&2 
        return 1
    }

    if [ -f "/etc/torero-image-manifest.json" ]; then
        if command -v jq &> /dev/null; then
            jq ".tools.opentofu = \"${OPENTOFU_VERSION}\"" /etc/torero-image-manifest.json > /tmp/manifest.json
            mv /tmp/manifest.json /etc/torero-image-manifest.json
        else
            echo "jq not found, skipping manifest update"
        fi
    fi

    echo "opentofu ${OPENTOFU_VERSION} installation complete for ${arch} architecture"
    return 0
}

configure_dns() {
    echo "configuring DNS at runtime..."
    echo -e "nameserver 8.8.8.8\nnameserver 8.8.4.4" > /etc/resolv.conf
}

handle_torero_eula() {
    local auto_accept_eula="${TORERO_APPLICATION_AUTO_ACCEPT_EULA:-true}"
    if [ "$auto_accept_eula" = "true" ]; then
        echo "handling torero EULA acceptance (TORERO_APPLICATION_AUTO_ACCEPT_EULA=${auto_accept_eula})..."
        
        # Create EULA acceptance marker for admin user if it doesn't exist
        if [ -d "/home/admin" ] && [ ! -f "/home/admin/.torero.d/.license-accepted" ]; then
            mkdir -p /home/admin/.torero.d
            touch /home/admin/.torero.d/.license-accepted
            chmod -R 755 /home/admin/.torero.d
            chown -R admin:admin /home/admin/.torero.d
            echo "EULA pre-accepted for admin user"
        fi
        
        # Try interactive EULA acceptance if expect is available
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
install_opentofu || echo "opentofu installation failed, continuing without it"
exec "$@"
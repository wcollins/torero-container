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
# Manual build and push to GHCR

# display usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  -v, --version VERSION          Container version (default: 1.4.0)"
    echo "  -t, --torero-version VERSION   Torero version (default: 1.4.0)"
    echo "  -p, --python-version VERSION   Python version (default: 3.13.0)"
    echo "  -u, --username USERNAME        GitHub username"
    echo "  -h, --help                     Show this help message"
}

# prompt for a value if not provided
prompt_for_value() {
    local var_name="$1"
    local prompt_text="$2"
    local default_value="$3"
    
    if [ -z "${!var_name}" ]; then
        if [ -n "$default_value" ]; then
            read -p "$prompt_text [$default_value]: " input
            eval "$var_name=\"${input:-$default_value}\""
        else
            while [ -z "${!var_name}" ]; do
                read -p "$prompt_text: " input
                eval "$var_name=\"$input\""
                if [ -z "${!var_name}" ]; then
                    echo "This value is required."
                fi
            done
        fi
    fi
}

# set hard-coded variables
REGISTRY="ghcr.io"
IMAGE_NAME="torerodev/torero-container"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--version)
            VERSION="$2"
            shift 2
            ;;
        -t|--torero-version)
            TORERO_VERSION="$2"
            shift 2
            ;;
        -p|--python-version)
            PYTHON_VERSION="$2"
            shift 2
            ;;
        -u|--username)
            GITHUB_USERNAME="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# prompt for missing values
prompt_for_value "VERSION" "Enter container version" "1.4.0"
prompt_for_value "TORERO_VERSION" "Enter Torero version" "1.4.0"
prompt_for_value "PYTHON_VERSION" "Enter Python version" "3.13.0"
prompt_for_value "GITHUB_USERNAME" "Enter GitHub username"

# login to GHCR
echo "Logging into GHCR..."
echo "You'll need a GitHub Personal Access Token with 'write:packages' permission"
docker login ghcr.io -u "$GITHUB_USERNAME"

# build for current platform
echo "Building image..."
docker build -t ${REGISTRY}/${IMAGE_NAME}:${VERSION} \
  --build-arg TORERO_VERSION=${TORERO_VERSION} \
  --build-arg PYTHON_VERSION=${PYTHON_VERSION} \
  -f Containerfile .

# test the image
echo "Testing image..."
docker run --rm ${REGISTRY}/${IMAGE_NAME}:${VERSION} torero version
docker run --rm ${REGISTRY}/${IMAGE_NAME}:${VERSION} python3 --version

# build and push multi-arch using buildx
echo "Building and pushing multi-arch image..."
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag ${REGISTRY}/${IMAGE_NAME}:${VERSION} \
  --tag ${REGISTRY}/${IMAGE_NAME}:latest \
  --build-arg TORERO_VERSION=${TORERO_VERSION} \
  --build-arg PYTHON_VERSION=${PYTHON_VERSION} \
  --push \
  -f Containerfile .

echo "Done! Pushed to:"
echo "  ${REGISTRY}/${IMAGE_NAME}:${VERSION}"
echo "  ${REGISTRY}/${IMAGE_NAME}:latest"
#!/bin/bash
# development tools for tests, schema generation, and setup

set -e

# colors for output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# display usage
usage() {
    echo -e "${BLUE}Usage:${NC} $0 [OPTIONS]"
    echo
    echo -e "${BLUE}Options:${NC}"
    echo "  --test          Run tests with coverage"
    echo "  --schema        Generate OpenAPI schema"
    echo "  --setup         Setup development environment"
    echo "  --help          Display this help message"
    echo
    echo -e "${BLUE}Examples:${NC}"
    echo "  $0 --setup      # setup venv and dependencies"
    echo "  $0 --test       # run all tests"
    echo "  $0 --schema     # generate api schema"
    echo
}

# setup virtual environment
setup_venv() {
    if [ -z "$VIRTUAL_ENV" ]; then
        if [ -f ".venv/bin/activate" ]; then
            source .venv/bin/activate
        else
            echo -e "${YELLOW}virtual environment not found. creating...${NC}"
            uv venv
            source .venv/bin/activate
        fi
    fi
}

# install dependencies
install_deps() {
    echo -e "${BLUE}installing dependencies...${NC}"
    uv pip install pytest pytest-asyncio pytest-cov httpx fastapi uvicorn[standard] pydantic python-multipart python-dateutil PyYAML
    echo -e "${GREEN}dependencies installed${NC}"
}

# run tests
run_tests() {
    setup_venv
    # ensure dependencies are installed
    if ! python -c "import pytest" 2>/dev/null; then
        echo -e "${YELLOW}dependencies missing. installing...${NC}"
        install_deps
    fi
    echo -e "${BLUE}running tests with coverage...${NC}"
    pytest tests/ "$@"
}

# generate openapi schema
generate_schema() {
    setup_venv
    # ensure dependencies are installed
    if ! python -c "import uvicorn" 2>/dev/null; then
        echo -e "${YELLOW}dependencies missing. installing...${NC}"
        install_deps
    fi
    echo -e "${BLUE}generating openapi schema...${NC}"
    python scripts/generate_openapi.py "$@"
}

# setup development environment
setup_dev() {
    echo -e "${BLUE}setting up development environment...${NC}"
    setup_venv
    install_deps
    echo -e "${GREEN}development environment ready${NC}"
}

# parse arguments
if [ $# -eq 0 ]; then
    usage
    exit 0
fi

while [[ $# -gt 0 ]]; do
    case "$1" in
        --test)
            shift
            run_tests "$@"
            exit $?
            ;;
        --schema)
            shift
            generate_schema "$@"
            exit $?
            ;;
        --setup)
            setup_dev
            exit $?
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            echo -e "${RED}unknown option: $1${NC}"
            usage
            exit 1
            ;;
    esac
done
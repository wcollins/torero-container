#!/bin/bash
# generate OpenAPI schema for torero-api

# activate venv
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
    else
        echo "Virtual environment not found. Creating one..."
        uv venv
        source .venv/bin/activate
        echo "Installing dependencies..."
        uv pip install fastapi uvicorn[standard] pydantic python-multipart python-dateutil PyYAML httpx
    fi
fi

# generate OpenAPI schema
echo "Generating OpenAPI schema..."
python scripts/generate_openapi.py "$@"
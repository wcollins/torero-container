#!/bin/bash
# setup dependencies and run torero-api tests

# activate venv
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
    else
        echo "Virtual environment not found. Creating one..."
        uv venv
        source .venv/bin/activate
        echo "Installing dependencies..."
        uv pip install pytest pytest-asyncio pytest-cov httpx fastapi uvicorn[standard] pydantic python-multipart python-dateutil PyYAML
    fi
fi

# run tests with coverage
echo "Running tests with coverage..."
pytest tests/ "$@"
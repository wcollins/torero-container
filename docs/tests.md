# Guide for local testing
This guide provides step-by-step instructions for running tests across the torero Container components.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Running All Tests](#running-all-tests)
- [Testing torero API](#testing-torero-api)
- [Test Coverage](#test-coverage)
- [Common Issues](#common-issues)

## Prerequisites
Before running tests, ensure you have the following installed:
- Python 3.10 or higher
- `uv` package manager
- Git (for version control)

## Running All Tests

### Quick Start

The easiest way to run tests for torero API is using the provided script from the root directory:

```bash
# from the torero-container root directory
./tools.sh --test
```

This script will:
1. Check for and activate the virtual environment
2. Install dependencies if needed
3. Run all tests with coverage reporting

## Testing torero API

### Step-by-Step Setup

1. **Navigate to the project root:**
   ```bash
   cd /path/to/torero-container
   ```

2. **Install development dependencies:**
   ```bash
   cd opt/torero-api
   uv pip install -e ".[dev]"
   ```

   This installs:
   - pytest (test framework)
   - pytest-asyncio (async test support)
   - pytest-cov (coverage reporting)
   - httpx (HTTP client for testing)
   - Other development tools (black, flake8, isort)

3. **Run tests from the root directory:**
   ```bash
   cd ../..  # back to project root
   ./tools.sh --test
   ```

### Alternative Methods

#### Method 1: Direct pytest execution
```bash
# from torero-container root
pytest tests/ -v
```

#### Method 2: With specific options
```bash
# run with coverage report
pytest tests/ --cov=opt/torero-api/torero_api --cov-report=term-missing

# stop on first failure
pytest tests/ -x

# run specific test file
pytest tests/test_server.py

# run tests matching a pattern
pytest tests/ -k "test_health"

# run with maximum verbosity
pytest tests/ -vv
```

#### Method 3: From the torero-api directory
```bash
cd opt/torero-api
pytest ../../tests/ -v
```

## Test Coverage

The test suite generates three types of coverage reports:

1. **Terminal Report**: Displayed immediately after test execution
2. **HTML Report**: Generated in `htmlcov/` directory
   ```bash
   # View HTML coverage report
   open htmlcov/index.html  # macOS
   xdg-open htmlcov/index.html  # Linux
   ```
3. **XML Report**: Generated as `coverage.xml` for CI/CD integration

### Current Test Coverage

As of the latest run:
- **Total Coverage**: ~53%
- **Test Count**: 77 tests
- **Components Tested**:
  - Core functionality (torero executor)
  - Database operations (import/export)
  - API endpoints (services, decorators, repositories, secrets)
  - Server health checks
  - Service descriptions

### Coverage by Module

| Module | Coverage | Key Areas |
|--------|----------|-----------|
| API Endpoints | 65-82% | Services, database, decorators |
| Models | 89-100% | Data models and schemas |
| Server | 82% | Application setup and routing |
| Core Executor | 32% | Command execution logic |

## Common Issues

### Issue 1: pytest command not found

**Solution**: Install development dependencies
```bash
cd opt/torero-api
uv pip install -e ".[dev]"
```

### Issue 2: Virtual environment not activated

**Solution**: The `tools.sh` script handles this automatically. For manual testing:
```bash
source .venv/bin/activate
```

### Issue 3: Import errors

**Solution**: Ensure you're running tests from the correct directory
```bash
# always run from the torero-container root
cd /path/to/torero-container
./tools.sh --test
```

### Issue 4: Permission denied on tools.sh

**Solution**: Make the script executable
```bash
chmod +x tools.sh
```

## Advanced Testing

### Running with different Python versions

```bash
# using uv to test with specific Python version
uv run --python 3.11 pytest tests/
```

### Parallel test execution

```bash
# install pytest-xdist
uv pip install pytest-xdist

# run tests in parallel
pytest tests/ -n auto
```

### Debugging failed tests

```bash
# drop into debugger on failures
pytest tests/ --pdb

# show local variables for failed tests
pytest tests/ -l
```

## Continuous Integration

For CI/CD pipelines, use the XML coverage report:

```bash
pytest tests/ --cov=opt/torero-api/torero_api --cov-report=xml
```

The `coverage.xml` file can be uploaded to services like Codecov or Coveralls.

## Writing New Tests

Tests are located in the `tests/` directory at the root level. Follow these conventions:

1. **File naming**: `test_<module_name>.py`
2. **Test function naming**: `test_<functionality_description>`
3. **Test classes**: `Test<ComponentName>`
4. **Use fixtures**: Define reusable test fixtures in `tests/conftest.py`

Example test structure:
```python
import pytest
from fastapi.testclient import TestClient

def test_endpoint_success(client):
    response = client.get("/api/v1/endpoint")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
```

## Some `TODO` items
- Review test failures and improve coverage
- Add integration tests for complex workflows
- Set up continuous integration with GitHub Actions
- Configure code quality tools (black, flake8, mypy)
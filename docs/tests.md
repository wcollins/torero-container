# Guide for local testing
This guide provides step-by-step instructions for running tests across the torero Container components.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Running All Tests](#running-all-tests)
- [Testing torero MCP](#testing-torero-mcp)
- [Testing torero UI](#testing-torero-ui)
- [Test Coverage](#test-coverage)
- [Common Issues](#common-issues)

## Prerequisites
Before running tests, ensure you have the following installed:
- Python 3.10 or higher
- `uv` package manager
- Git (for version control)

## Running All Tests

### Quick Start

The easiest way to run tests is using the provided script from the root directory:

```bash
# from the torero-container root directory
./tools.sh --test
```

This script will:
1. Check for and activate the virtual environment
2. Install dependencies if needed
3. Run all tests with coverage reporting

## Testing torero MCP

### Step-by-Step Setup

1. **Navigate to the project root:**
   ```bash
   cd /path/to/torero-container
   ```

2. **Install development dependencies:**
   ```bash
   cd opt/torero-mcp
   uv pip install -e ".[dev]"
   ```

   This installs:
   - pytest (test framework)
   - pytest-asyncio (async test support)
   - pytest-cov (coverage reporting)
   - Other development tools (black, flake8, isort)

3. **Run tests:**
   ```bash
   uv run pytest tests/ -v
   ```

### Alternative Methods

#### Method 1: Direct pytest execution
```bash
# from torero-container root
uv run pytest opt/torero-mcp/tests/ -v
```

#### Method 2: With specific options
```bash
# run with coverage report
uv run pytest opt/torero-mcp/tests/ --cov=opt/torero-mcp/torero_mcp --cov-report=term-missing

# stop on first failure
uv run pytest opt/torero-mcp/tests/ -x

# run specific test file
uv run pytest opt/torero-mcp/tests/test_executor.py

# run tests matching a pattern
uv run pytest opt/torero-mcp/tests/ -k "test_health"

# run with maximum verbosity
uv run pytest opt/torero-mcp/tests/ -vv
```

## Testing torero UI

### Step-by-Step Setup

1. **Navigate to the UI directory:**
   ```bash
   cd opt/torero-ui
   ```

2. **Install development dependencies:**
   ```bash
   uv pip install -e ".[dev]"
   ```

3. **Run Django tests:**
   ```bash
   uv run python torero_ui/manage.py test
   ```

### Alternative Methods

#### Method 1: Using pytest with Django
```bash
# from torero-ui directory
uv run pytest --ds=torero_ui.settings
```

#### Method 2: Test specific apps
```bash
uv run python torero_ui/manage.py test dashboard
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

Test coverage varies by component:
- **torero-mcp**: Direct CLI executor and MCP tools
- **torero-ui**: Django views, models, and service sync

### Coverage by Module

| Module | Component | Key Areas |
|--------|-----------|-----------|
| MCP Executor | torero-mcp | CLI command execution, parsing |
| MCP Tools | torero-mcp | Service, database, health tools |
| UI Models | torero-ui | ServiceInfo, ServiceExecution |
| UI Services | torero-ui | ToreroCliClient, sync services |
| UI Views | torero-ui | Dashboard, API endpoints |

## Common Issues

### Issue 1: pytest command not found

**Solution**: Install pytest using uv
```bash
uv pip install pytest pytest-asyncio pytest-cov
```

### Issue 2: Virtual environment not activated

**Solution**: With uv, virtual environments are handled automatically. For manual activation:
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

### Issue 5: torero CLI not found

**Solution**: Tests that use ToreroExecutor or ToreroCliClient require torero to be installed
```bash
# Install torero or run tests in container
docker compose -f docker-compose.dev.yml exec torero uv run pytest
```

## Advanced Testing

### Running with different Python versions

```bash
# using specific Python version with uv
uv run --python 3.11 pytest opt/torero-mcp/tests/
```

### Parallel test execution

```bash
# install pytest-xdist
uv pip install pytest-xdist

# run tests in parallel
uv run pytest opt/torero-mcp/tests/ -n auto
```

### Debugging failed tests

```bash
# drop into debugger on failures
uv run pytest opt/torero-mcp/tests/ --pdb

# show local variables for failed tests
uv run pytest opt/torero-mcp/tests/ -l
```

## Continuous Integration

For CI/CD pipelines, use the XML coverage report:

```bash
uv run pytest opt/torero-mcp/tests/ --cov=opt/torero-mcp/torero_mcp --cov-report=xml
```

The `coverage.xml` file can be uploaded to services like Codecov or Coveralls.

## Writing New Tests

Tests are organized by component:
- **MCP Tests**: `opt/torero-mcp/tests/`
- **UI Tests**: `opt/torero-ui/tests/` or `opt/torero-ui/torero_ui/dashboard/tests.py`

Follow these conventions:

1. **File naming**: `test_<module_name>.py`
2. **Test function naming**: `test_<functionality_description>`
3. **Test classes**: `Test<ComponentName>`
4. **Use fixtures**: Define reusable test fixtures in `conftest.py`

Example test structure for MCP:
```python
import pytest
from torero_mcp.executor import ToreroExecutor

@pytest.mark.asyncio
async def test_executor_get_services():
    executor = ToreroExecutor(timeout=30)
    services = await executor.get_services()
    assert isinstance(services, list)
```

Example test structure for UI:
```python
from django.test import TestCase
from torero_ui.dashboard.services import ToreroCliClient

class TestCliClient(TestCase):
    def test_get_services(self):
        client = ToreroCliClient()
        services = client.get_services()
        self.assertIsInstance(services, list)
```

## TODO items
- Add integration tests for MCP-CLI interaction
- Add tests for UI sync service
- Improve test coverage for subprocess handling
- Set up continuous integration with GitHub Actions
- Configure code quality tools (black, flake8, mypy)
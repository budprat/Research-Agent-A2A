# A2A MCP Framework - Testing Guide

This directory contains the comprehensive test suite for the A2A MCP Framework. Our testing strategy follows industry best practices with unit, integration, and end-to-end tests.

## Quick Start

```bash
# Run all tests (excluding slow tests)
./run_tests.sh

# Run with coverage report
./run_tests.sh -c

# Run only unit tests
./run_tests.sh -u

# Run specific test file
./run_tests.sh tests/unit/test_a2a_protocol_client.py

# Get help with all options
./run_tests.sh --help
```

## Test Structure

```
tests/
├── conftest.py                 # Shared fixtures and test configuration
├── unit/                       # Unit tests (test individual components)
│   ├── test_a2a_protocol_client.py
│   ├── test_config_manager.py
│   ├── test_quality_threshold_framework.py
│   └── ...
├── integration/                # Integration tests (test component interactions)
│   ├── test_agent_orchestration.py
│   ├── test_mcp_integration.py
│   └── ...
├── e2e/                        # End-to-end tests (test complete workflows)
│   ├── test_full_workflow.py
│   └── ...
└── fixtures/                   # Test data and fixtures
    ├── sample_configs/
    ├── sample_requests/
    └── ...
```

## Test Categories

### Unit Tests (`@pytest.mark.unit`)
Test individual components in isolation with mocked dependencies.

**Characteristics:**
- Fast execution (< 100ms per test)
- No external dependencies
- Extensive use of mocks
- High coverage of edge cases

**Example:**
```python
@pytest.mark.unit
def test_create_a2a_request_with_minimal_params():
    request = create_a2a_request("test_method", "test message")
    assert request["jsonrpc"] == "2.0"
    assert request["method"] == "test_method"
```

### Integration Tests (`@pytest.mark.integration`)
Test interactions between multiple components.

**Characteristics:**
- Moderate execution time (< 5s per test)
- Real component interactions
- Minimal external service mocking
- Focus on interfaces and protocols

**Example:**
```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_master_orchestrator_delegates_to_specialist():
    orchestrator = MasterOracleAgent()
    specialist = ResearchSpecialistAgent()
    # Test actual delegation flow
    result = await orchestrator.delegate_to_specialist(specialist, task)
    assert result["status"] == "success"
```

### End-to-End Tests (`@pytest.mark.e2e`)
Test complete user workflows from start to finish.

**Characteristics:**
- Slow execution (> 5s per test)
- Real service integration
- Complete workflow validation
- Production-like scenarios

**Example:**
```python
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_complete_research_workflow():
    # Start MCP server, agents, and execute full workflow
    result = await execute_research_query("What is quantum computing?")
    assert result["quality_score"] > 0.8
    assert "quantum" in result["content"].lower()
```

## Test Markers

Our test suite uses pytest markers to categorize and filter tests:

- `@pytest.mark.unit` - Unit tests (fast, isolated)
- `@pytest.mark.integration` - Integration tests (moderate speed)
- `@pytest.mark.e2e` - End-to-end tests (slow, comprehensive)
- `@pytest.mark.slow` - Slow tests (excluded by default)
- `@pytest.mark.asyncio` - Async tests requiring event loop

### Running Tests by Marker

```bash
# Only unit tests
./run_tests.sh -u

# Only integration tests
./run_tests.sh -i

# Only end-to-end tests
./run_tests.sh -e

# Include slow tests
./run_tests.sh -s

# Unit tests with coverage
./run_tests.sh -u -c
```

## Coverage Goals

We maintain the following coverage targets:

| Phase | Target | Description |
|-------|--------|-------------|
| Phase 1 (Current) | 30% | Core components covered |
| Phase 2 | 60% | Major features covered |
| Phase 3 | 80% | Production ready |

### Checking Coverage

```bash
# Run tests with coverage report
./run_tests.sh -c

# Generate HTML coverage report
./run_tests.sh -c
# Open htmlcov/index.html in your browser

# Set minimum coverage threshold
./run_tests.sh -c --min-coverage 30  # Fails if < 30%
```

## Writing Tests

### Test File Naming

- Unit tests: `test_<component_name>.py`
- Integration tests: `test_<integration_area>.py`
- E2E tests: `test_<workflow_name>.py`

### Test Function Naming

Use descriptive names that explain what is being tested:

```python
# Good
def test_config_manager_loads_yaml_file_successfully():
    ...

def test_a2a_client_retries_on_connection_failure():
    ...

# Bad
def test_config():
    ...

def test_retry():
    ...
```

### Test Structure (AAA Pattern)

Follow the Arrange-Act-Assert pattern:

```python
def test_quality_framework_validates_metrics():
    # Arrange - Set up test data and mocks
    framework = QualityThresholdFramework()
    response = {"metrics": {"accuracy": 0.95}}

    # Act - Execute the code being tested
    result = framework.validate(response)

    # Assert - Verify the expected outcome
    assert result.passed is True
    assert result.score >= 0.9
```

### Using Fixtures

We provide comprehensive fixtures in `conftest.py`:

```python
def test_with_mock_agent(mock_agent_config):
    """Use fixture for test setup."""
    agent = create_agent(mock_agent_config)
    assert agent.name == "Test Agent"

@pytest.mark.asyncio
async def test_with_mock_session(mock_aiohttp_session):
    """Use async fixture."""
    response = await mock_aiohttp_session.post("/test")
    assert response.status == 200
```

### Async Tests

For async code, use `@pytest.mark.asyncio`:

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

### Parametrized Tests

Test multiple scenarios with `@pytest.mark.parametrize`:

```python
@pytest.mark.parametrize("domain,expected_metrics", [
    ("BUSINESS", ["confidence_score", "technical_feasibility"]),
    ("ACADEMIC", ["research_confidence", "evidence_quality"]),
    ("SERVICE", ["uptime", "reliability"]),
])
def test_domain_specific_metrics(domain, expected_metrics):
    framework = QualityThresholdFramework()
    framework.configure_domain(domain)
    # Test domain-specific behavior
```

## Mocking Best Practices

### When to Mock

- External API calls
- Database connections
- File system operations
- Time-dependent behavior
- Expensive computations

### When NOT to Mock

- Simple data structures
- Pure functions
- Internal component interactions (in integration tests)

### Mock Examples

```python
from unittest.mock import Mock, AsyncMock, patch

# Mock synchronous function
def test_with_mock():
    mock_service = Mock()
    mock_service.get_data.return_value = {"key": "value"}

    result = process_data(mock_service)
    mock_service.get_data.assert_called_once()

# Mock async function
@pytest.mark.asyncio
async def test_with_async_mock():
    mock_client = AsyncMock()
    mock_client.fetch.return_value = {"data": "test"}

    result = await fetch_and_process(mock_client)
    assert result["data"] == "test"

# Patch environment variable
def test_with_env_patch(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test_key")
    config = load_config()
    assert config.api_key == "test_key"
```

## Test Data

### Using Fixtures Directory

Store sample data in `tests/fixtures/`:

```python
def load_sample_config():
    with open("tests/fixtures/sample_configs/valid.yaml") as f:
        return yaml.safe_load(f)
```

### Generating Test Data

Use factory functions for consistent test data:

```python
def create_test_agent_config(**overrides):
    """Create test agent config with optional overrides."""
    config = {
        "agent_id": "test_agent",
        "name": "Test Agent",
        "port": 10000,
        "tier": 2,
    }
    config.update(overrides)
    return config
```

## Debugging Tests

### Verbose Output

```bash
# Show detailed test output
./run_tests.sh -v

# Show print statements
./run_tests.sh -s  # pytest -s flag (note: conflicts with --slow flag)
```

### Running Single Test

```bash
# Run specific test file
./run_tests.sh tests/unit/test_a2a_protocol_client.py

# Run specific test function
./run_tests.sh -k "test_create_request"

# Run tests matching pattern
./run_tests.sh -k "config and yaml"
```

### Using pdb Debugger

Add breakpoint in test:

```python
def test_something():
    data = prepare_data()
    breakpoint()  # Execution will pause here
    result = process(data)
    assert result is not None
```

## Continuous Integration

Tests run automatically on every commit via GitHub Actions (see `.github/workflows/ci.yml`).

### CI Test Workflow

1. **Lint & Format** - Code style checks
2. **Unit Tests** - Fast validation
3. **Integration Tests** - Component interaction
4. **E2E Tests** - Full workflow validation (on main branch only)
5. **Coverage Report** - Ensure coverage targets met

### Pre-commit Hooks

Install pre-commit hooks to run tests before committing:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## Common Issues

### Import Errors

If you encounter import errors:

```bash
# Ensure dependencies are installed
pip install -e .
pip install pytest pytest-asyncio pytest-cov pytest-mock

# Check PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

### Async Test Failures

Ensure async tests use `@pytest.mark.asyncio`:

```python
# Correct
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()

# Wrong - will fail
async def test_async_function():  # Missing decorator!
    result = await some_async_function()
```

### Fixture Not Found

Ensure fixtures are defined in `conftest.py` or imported correctly:

```python
# In conftest.py
@pytest.fixture
def my_fixture():
    return "test_data"

# In test file - fixture automatically available
def test_something(my_fixture):
    assert my_fixture == "test_data"
```

## Performance Testing

Mark slow tests appropriately:

```python
@pytest.mark.slow
@pytest.mark.unit
def test_performance_heavy_operation():
    # This test takes > 1 second
    result = perform_heavy_computation()
    assert result is not None
```

Run performance tests separately:

```bash
# Exclude slow tests (default)
./run_tests.sh

# Include slow tests
./run_tests.sh -s
```

## Test Metrics

Track these metrics for test health:

- **Coverage**: Aim for 80%+ for critical paths
- **Execution Time**: Unit tests < 100ms, Integration < 5s
- **Flakiness**: Zero flaky tests tolerated
- **Maintenance**: Tests should be easy to understand and update

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)

## Contributing

When adding new features:

1. Write tests FIRST (TDD approach)
2. Ensure tests cover happy path and edge cases
3. Add appropriate markers (`@pytest.mark.unit`, etc.)
4. Update this README if adding new test patterns
5. Verify coverage doesn't decrease

## Questions?

For questions about testing:
- Check existing tests for examples
- Review `conftest.py` for available fixtures
- Consult this README
- Ask in team chat or create an issue

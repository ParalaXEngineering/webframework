# ParalaX Web Framework Tests

This directory contains the pytest test suite for the ParalaX Web Framework.

## Test Structure

- **`conftest.py`**: Test configuration and fixtures
- **`test_startup.py`**: Tests for framework initialization and startup
- **`test_imports.py`**: Tests for import structure and dependencies
- **`test_core_modules.py`**: Tests for core module functionality

## Running Tests

### Install pytest

```bash
pip install pytest pytest-cov
```

### Run all tests

```bash
cd /path/to/webframework
pytest tests/
```

### Run with verbose output

```bash
pytest tests/ -v
```

### Run specific test file

```bash
pytest tests/test_startup.py -v
```

### Run with coverage

```bash
pytest tests/ --cov=src --cov-report=html
```

## Test Execution Order

Tests are executed in a specific order to ensure proper validation:

1. **test_startup.py** - Validates basic framework startup
2. **test_imports.py** - Validates import structure
3. **test_core_modules.py** - Validates core functionality

This order is enforced in `conftest.py` using `pytest_collection_modifyitems`.

## Test Fixtures

### Session Fixtures (run once per test session)

- **`setup_environment`**: Configures paths and environment
- **`setup_log`**: Cleans up log files before tests

### Function Fixtures (run for each test that uses them)

- **`flask_app`**: Provides a configured Flask app instance
- **`client`**: Provides a Flask test client
- **`runner`**: Provides a Flask CLI test runner

## Writing New Tests

When adding new tests:

1. Create a new `test_*.py` file in this directory
2. Import pytest: `import pytest`
3. Add test order to `conftest.py` if execution order matters
4. Use fixtures as needed
5. Follow the naming convention: `test_<description>`

Example:

```python
"""
Test description here.
"""
import pytest

def test_my_feature():
    """Test that my feature works."""
    import my_module
    
    result = my_module.my_function()
    assert result is not None
```

## Test Coverage

The test suite covers:

- ✅ Framework initialization
- ✅ Import structure (relative/absolute imports)
- ✅ Core module availability
- ✅ Circular dependency resolution
- ✅ Optional dependency handling
- ✅ Path management
- ✅ Basic object creation

## Dependencies

Tests can run with minimal dependencies:

- **Required**: pytest
- **Optional**: pytest-cov (for coverage reports)
- **Framework dependencies**: Tests gracefully skip if Flask/other deps not installed

## Continuous Integration

These tests are designed to work in CI/CD environments:

```yaml
# Example GitHub Actions
- name: Run tests
  run: |
    pip install pytest pytest-cov
    pytest tests/ --cov=src --cov-report=xml
```

## Troubleshooting

### Import errors

If you see import errors, ensure:
- You're running pytest from the framework root directory
- The `src/` directory exists
- `conftest.py` is setting up paths correctly

### Skipped tests

Some tests may skip if dependencies are not installed. This is expected behavior.
To run all tests, install full dependencies:

```bash
pip install -r requirements.txt
```
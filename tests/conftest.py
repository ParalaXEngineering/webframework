"""
Conftest for the ParalaX Web Framework testing.

This configuration sets up the test environment, manages paths,
and provides fixtures for testing the framework.
"""
from pathlib import Path
import sys
import os
import pytest

# Configure test execution order
def pytest_collection_modifyitems(config, items):
    """Modify test collection to enforce execution order."""
    # Define the desired execution order
    order_map = {
        'test_startup.py': 0,
        'test_imports.py': 1,
        'test_core_modules.py': 2,
    }
    
    def get_order_key(item):
        # Get the filename from the test item
        filename = item.fspath.basename
        # Get order priority (default to 999 for unknown files)
        file_priority = order_map.get(filename, 999)
        
        # Within each file, maintain original order by using item's line number
        line_number = item.location[1] if item.location else 0
        
        return (file_priority, line_number)
    
    # Sort items by the order key
    items.sort(key=get_order_key)

@pytest.fixture(scope="session", autouse=True)
def setup_environment():
    """Setup the test environment once for all tests in this session."""
    # Get paths
    test_dir = Path(__file__).parent
    framework_dir = test_dir.parent
    src_dir = framework_dir / 'src'
    
    # Add src to Python path
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    
    # Change to framework directory for relative paths
    original_cwd = os.getcwd()
    os.chdir(framework_dir)
    
    yield
    
    # Cleanup: restore original directory
    os.chdir(original_cwd)

@pytest.fixture(scope="session", autouse=True)
def setup_log():
    """Reset logs once for all tests in this session."""
    log_dir = Path("logs")
    if log_dir.exists() and log_dir.is_dir():
        for log_file in log_dir.glob("*.log"):
            try:
                log_file.unlink()
            except Exception:
                pass  # Ignore errors during cleanup

@pytest.fixture(scope="function")
def flask_app():
    """Create and configure a test Flask app for tests that need it."""
    try:
        from main import app, setup_app, FLASK_AVAILABLE
        
        if not FLASK_AVAILABLE:
            pytest.skip("Flask not available for this test")
        
        # Configure for testing
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        
        # Setup the app
        setup_app(app)
        
        return app
    except ImportError as e:
        pytest.skip(f"Cannot import Flask app: {e}")

@pytest.fixture
def client(flask_app):
    """Create a test client."""
    return flask_app.test_client()

@pytest.fixture
def runner(flask_app):
    """Create a test CLI runner."""
    return flask_app.test_cli_runner()
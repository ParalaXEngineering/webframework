"""
Unit Test Configuration

This conftest.py provides fixtures for unit tests that don't require Flask.
These tests verify core logic, business rules, and isolated components.
"""
from pathlib import Path
import sys
import os
import pytest
import tempfile

# Setup paths
@pytest.fixture(scope="session", autouse=True)
def setup_unit_environment():
    """Setup the test environment for unit tests."""
    test_dir = Path(__file__).parent.parent
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


@pytest.fixture
def temp_config():
    """Provide a temporary config file for settings tests."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config_path = f.name
    yield config_path
    # Cleanup
    if os.path.exists(config_path):
        os.unlink(config_path)


@pytest.fixture
def temp_auth_dir():
    """Create a temporary auth directory for testing."""
    import tempfile
    import shutil
    temp_dir = tempfile.mkdtemp()
    auth_dir = Path(temp_dir) / "auth"
    auth_dir.mkdir()
    yield str(auth_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def auth_manager_instance(temp_auth_dir):
    """Create a standalone AuthManager instance for unit tests."""
    from src.modules.auth.auth_manager import AuthManager
    manager = AuthManager(auth_dir=temp_auth_dir)
    return manager


@pytest.fixture(autouse=True)
def reset_thread_manager():
    """Reset thread manager before each test."""
    from src.modules.threaded import threaded_manager
    threaded_manager.thread_manager_obj = threaded_manager.Threaded_manager()
    yield
    # Cleanup threads after test
    if threaded_manager.thread_manager_obj:
        for thread in threaded_manager.thread_manager_obj.get_all_threads():
            try:
                thread.delete()
            except Exception:
                pass


@pytest.fixture(autouse=True)
def reset_logs():
    """Reset logs before each test."""
    log_dir = Path("logs")
    if log_dir.exists() and log_dir.is_dir():
        for log_file in log_dir.glob("*.log"):
            try:
                log_file.unlink()
            except Exception:
                pass

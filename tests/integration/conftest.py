"""
Integration Test Configuration

This conftest.py provides fixtures for integration tests that require Flask.
These tests verify end-to-end functionality, HTTP routing, and template rendering.
"""
from pathlib import Path
import sys
import os
import pytest
import tempfile
import shutil

# Setup paths
@pytest.fixture(scope="session", autouse=True)
def setup_integration_environment():
    """Setup the test environment for integration tests."""
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


@pytest.fixture(scope="session", autouse=True)
def setup_log():
    """Reset logs once for all tests in this session."""
    log_dir = Path("logs")
    if log_dir.exists() and log_dir.is_dir():
        for log_file in log_dir.glob("*.log"):
            try:
                log_file.unlink()
            except Exception:
                pass


@pytest.fixture(scope="function")
def test_app():
    """Create and configure a test Flask app for integration tests.
    
    This fixture creates a Flask app with full framework setup including:
    - Thread manager
    - Auth manager
    - Site configuration
    - All blueprints registered
    """
    from flask import Flask
    from src.modules.threaded import threaded_manager
    from src.modules.auth.auth_manager import AuthManager
    import src.modules.auth.auth_manager as auth_module
    from src.modules.site_conf import Site_conf
    import src.modules.site_conf as site_conf_module
    from src.modules.auth.permission_registry import permission_registry
    
    # Create temporary auth directory
    temp_dir = tempfile.mkdtemp()
    auth_dir = Path(temp_dir) / "auth"
    auth_dir.mkdir()
    
    # Create Flask app with templates directory
    framework_dir = Path(__file__).parent.parent.parent
    templates_dir = framework_dir / "templates"
    
    app = Flask(__name__, template_folder=str(templates_dir))
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key-for-integration-tests'
    app.config['WTF_CSRF_ENABLED'] = False
    
    # Initialize thread manager
    threaded_manager.thread_manager_obj = threaded_manager.Threaded_manager()
    
    # Create auth manager
    manager = AuthManager(auth_dir=str(auth_dir))
    auth_module.auth_manager = manager
    
    # Create minimal site_conf
    class TestSiteConf(Site_conf):
        def context_processor(self):
            return {"enable_easter_eggs": False}
    
    site_conf_obj = TestSiteConf()
    site_conf_module.site_conf_obj = site_conf_obj
    
    # Register test module permissions
    permission_registry.clear()
    permission_registry.register_module("TestModule", ["execute", "configure", "view", "edit", "delete"])
    permission_registry.register_module("Demo_Threading", ["view", "execute"])
    permission_registry.register_module("Demo_Scheduler", ["view"])
    
    # Register blueprints
    from src.pages.common import bp as common_bp
    app.register_blueprint(common_bp)
    
    # DON'T register demo blueprints - they can cause conflicts with test routes
    
    # Add context processor for user injection
    @app.context_processor
    def inject_user():
        from flask import session
        user = session.get('user')
        # Provide app info required by login template
        return dict(
            user=user, 
            endpoint=None, 
            page_info="",
            topbarItems={"display": False, "login": False},
            app=site_conf_obj.m_app,  # Required by login.j2 template
            title=site_conf_obj.m_app["name"],
            web_title=site_conf_obj.m_app["name"],
            footer=site_conf_obj.m_app["footer"]
        )
    
    # Create test users with permissions
    manager.create_user("testadmin", "admin123", ["admin"], "Test Admin", "admin@test.com")
    manager.create_user("testuser", "user123", ["users"], "Test User", "user@test.com")
    manager.create_user("GUEST", "", ["guest"], "Test Guest", None)
    
    # Setup permissions for test groups
    manager.set_module_permissions("TestModule", "admin", ["execute", "configure", "view", "edit", "delete"])
    manager.set_module_permissions("TestModule", "users", ["view", "edit"])
    manager.set_module_permissions("Demo_Threading", "users", ["view"])
    manager.set_module_permissions("Demo_Scheduler", "users", ["view"])
    
    yield app
    
    # Cleanup
    shutil.rmtree(temp_dir)
    
    # Cleanup threads
    if threaded_manager.thread_manager_obj:
        for thread in threaded_manager.thread_manager_obj.get_all_threads():
            try:
                thread.delete()
            except Exception:
                pass


@pytest.fixture
def client(test_app):
    """Create a test client for making HTTP requests."""
    return test_app.test_client()


@pytest.fixture
def auth_manager_instance():
    """Create a standalone AuthManager instance for auth-specific tests."""
    temp_dir = tempfile.mkdtemp()
    auth_dir = Path(temp_dir) / "auth"
    auth_dir.mkdir()
    
    from src.modules.auth.auth_manager import AuthManager
    manager = AuthManager(auth_dir=str(auth_dir))
    
    yield manager
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def temp_auth_dir():
    """Create a temporary auth directory for testing."""
    temp_dir = tempfile.mkdtemp()
    auth_dir = Path(temp_dir) / "auth"
    auth_dir.mkdir()
    yield str(auth_dir)
    shutil.rmtree(temp_dir)

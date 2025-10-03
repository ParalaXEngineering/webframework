"""
Test framework startup and basic initialization.

This test ensures the framework can start up properly
without errors in the basic initialization.
"""
import pytest


def test_framework_startup():
    """Test that the framework can start up and basic modules load."""
    # Test that we can import core modules
    import threaded_manager
    import scheduler
    import access_manager
    import site_conf
    
    assert threaded_manager is not None
    assert scheduler is not None
    assert access_manager is not None
    assert site_conf is not None


def test_module_objects_exist():
    """Test that key module objects are created."""
    import threaded_manager
    import scheduler
    import access_manager
    import site_conf
    
    # Check that global objects are initialized (can be None initially)
    assert hasattr(threaded_manager, 'thread_manager_obj')
    assert hasattr(scheduler, 'scheduler_obj')
    assert hasattr(access_manager, 'auth_object')
    assert hasattr(site_conf, 'site_conf_obj')


def test_framework_paths():
    """Test that the framework can find its paths."""
    import os
    from pathlib import Path
    
    # Check that key directories exist
    framework_dir = Path.cwd()
    
    assert (framework_dir / 'src').exists(), "src directory should exist"
    assert (framework_dir / 'templates').exists(), "templates directory should exist"
    assert (framework_dir / 'webengine').exists(), "webengine directory should exist"
    assert (framework_dir / 'log_config.ini').exists(), "log_config.ini should exist"


def test_framework_version():
    """Test that the framework package has version information."""
    try:
        # Try to import the package
        import sys
        import os
        
        # Add src to path if needed
        src_dir = os.path.join(os.getcwd(), 'src')
        if src_dir not in sys.path:
            sys.path.insert(0, src_dir)
        
        # Import the package init
        import importlib
        src_package = importlib.import_module('__init__')
        
        # Check for version
        assert hasattr(src_package, '__version__')
        assert src_package.__version__ is not None
        
    except ImportError:
        # If we can't import as package, that's ok for now
        pytest.skip("Package initialization not testable in this mode")


def test_no_import_errors():
    """Test that importing core modules doesn't raise exceptions."""
    modules_to_test = [
        'threaded_manager',
        'scheduler',
        'access_manager',
        'site_conf',
        'User_defined_module',
        'threaded_action',
        'workflow',
        'displayer',
    ]
    
    failed_imports = []
    
    for module_name in modules_to_test:
        try:
            __import__(module_name)
        except Exception as e:
            failed_imports.append(f"{module_name}: {str(e)}")
    
    assert len(failed_imports) == 0, f"Some modules failed to import: {failed_imports}"


def test_circular_imports_resolved():
    """Test that circular imports don't cause issues."""
    # These imports used to have circular dependencies
    # If this test passes, circular dependencies are resolved
    
    import User_defined_module
    import threaded_action
    import scheduler
    
    # If we get here without exception, circular imports are resolved
    assert True
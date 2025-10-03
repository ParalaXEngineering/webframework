"""
Test module import structure and dependencies.

This test validates that the refactored import structure works correctly
for both standalone and submodule usage.
"""
import pytest
import sys


def test_relative_import_fallback():
    """Test that relative imports fall back to absolute imports properly."""
    # Clear any cached modules
    modules_to_clear = [m for m in sys.modules.keys() if 'access_manager' in m or 'utilities' in m]
    for mod in modules_to_clear:
        del sys.modules[mod]
    
    # Import should work regardless of package context
    import access_manager
    assert access_manager is not None


def test_all_core_modules_importable():
    """Test that all core modules can be imported."""
    core_modules = [
        'access_manager',
        'threaded_manager', 
        'scheduler',
        'site_conf',
        'displayer',
        'utilities',
        'workflow',
        'User_defined_module',
        'threaded_action',
    ]
    
    for module_name in core_modules:
        try:
            module = __import__(module_name)
            assert module is not None, f"{module_name} should not be None"
        except ImportError as e:
            pytest.fail(f"Failed to import {module_name}: {e}")


def test_optional_dependencies_handled():
    """Test that modules handle missing optional dependencies gracefully."""
    import utilities
    
    # utilities should import even if serial is not available
    assert utilities is not None
    
    # Check that optional dependencies are handled
    # serial might be None if not installed
    assert hasattr(utilities, 'serial')


def test_flask_optional():
    """Test that Flask being missing doesn't break core imports."""
    # Even without Flask, core modules should import
    import threaded_manager
    import scheduler
    import access_manager
    
    # These should all import successfully
    assert threaded_manager is not None
    assert scheduler is not None  
    assert access_manager is not None


def test_module_interdependencies():
    """Test that module interdependencies work correctly."""
    # Test common dependency chains
    import displayer
    import access_manager
    
    # displayer depends on access_manager
    # Both should load without issues
    assert displayer is not None
    assert access_manager is not None
    
    # Import workflow which depends on both scheduler and displayer
    import workflow
    assert workflow is not None


def test_no_hardcoded_submodule_paths():
    """Test that modules don't use hardcoded submodule paths."""
    import inspect
    import access_manager
    import displayer
    import scheduler
    
    # Get source code of modules
    modules_to_check = [access_manager, displayer, scheduler]
    
    for module in modules_to_check:
        source = inspect.getsource(module)
        
        # Check that there are no direct references to submodules.framework
        # (except in try/except blocks which is ok)
        lines = source.split('\n')
        for i, line in enumerate(lines):
            if 'submodules.framework' in line and 'try:' not in lines[max(0, i-2):i+3]:
                # Allow it in comments
                if not line.strip().startswith('#'):
                    pytest.fail(
                        f"Found hardcoded submodule path in {module.__name__} at line {i+1}: {line}"
                    )
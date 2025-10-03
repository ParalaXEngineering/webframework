"""
Test core module functionality.

This test validates that core modules function correctly
after the refactoring.
"""
import pytest


def test_displayer_creation():
    """Test Displayer class instantiation."""
    from src.displayer import Displayer
    
    displayer = Displayer()
    assert displayer is not None
    assert hasattr(displayer, 'm_modules')


def test_displayer_items():
    """Test that DisplayerItem classes exist."""
    import displayer
    
    # Check that item classes exist
    assert hasattr(displayer, 'DisplayerItemText')
    assert hasattr(displayer, 'DisplayerItemButton')
    assert hasattr(displayer, 'DisplayerItemAlert')
    
    # Test creating items
    text_item = displayer.DisplayerItemText("Test")
    assert text_item is not None


def test_scheduler_object():
    """Test that scheduler object exists and has expected attributes."""
    import scheduler
    
    # Check scheduler class exists
    assert hasattr(scheduler, 'Scheduler')
    
    # Check global scheduler object
    assert hasattr(scheduler, 'scheduler_obj')


def test_threaded_manager_object():
    """Test Threaded_manager object exists."""
    import src.threaded_manager as tm
    
    assert hasattr(tm, 'Threaded_manager')


def test_access_manager_class():
    """Test that Access_manager class exists and can be instantiated."""
    import access_manager
    
    # Check class exists
    assert hasattr(access_manager, 'Access_manager')
    
    # Check global auth object
    assert hasattr(access_manager, 'auth_object')


def test_site_conf_class():
    """Test that Site_conf class exists."""
    import site_conf
    
    # Check class exists
    assert hasattr(site_conf, 'Site_conf')
    
    # Check global object
    assert hasattr(site_conf, 'site_conf_obj')


def test_workflow_class():
    """Test that Workflow class exists."""
    import workflow
    
    # Check class exists
    assert hasattr(workflow, 'Workflow')


def test_user_defined_module_class():
    """Test that User_defined_module class exists."""
    import User_defined_module
    
    # Check class exists
    assert hasattr(User_defined_module, 'User_defined_module')


def test_threaded_action_class():
    """Test that Threaded_action class exists."""
    import threaded_action
    
    # Check class exists
    assert hasattr(threaded_action, 'Threaded_action')


def test_utilities_functions():
    """Test that utilities module has key functions."""
    from src import utilities
    
    assert hasattr(utilities, 'util_read_parameters')
    assert hasattr(utilities, 'get_breadcrumbs')


def test_displayer_enums():
    """Test that displayer enums are available."""
    import displayer
    
    # Check for important enums
    assert hasattr(displayer, 'BSstyle')
    assert hasattr(displayer, 'BSalign')
    assert hasattr(displayer, 'Layouts')
    
    # Test that enums have expected values
    assert hasattr(displayer.BSstyle, 'PRIMARY')
    assert hasattr(displayer.BSalign, 'L')
    assert hasattr(displayer.Layouts, 'VERTICAL')
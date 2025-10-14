"""
Test the new automatic authorization system.
"""

import pytest
from src.modules.threaded import Threaded_action
from src.modules.action import Action
from src.modules.displayer import Displayer
from src.modules.auth.auth_manager import AuthManager
from flask import Flask, session


class TestAuthorizationModule(Threaded_action):
    """Test module with required permissions."""
    m_default_name = "Test Auth Module"
    m_required_permission = "TestModule"
    m_required_action = "view"
    
    def action(self):
        pass


class TestSimpleAction(Action):
    """Test action with required permissions."""
    m_default_name = "Test Action"
    m_required_permission = "TestAction"
    m_required_action = "execute"


def test_module_user_context_injection():
    """Test that user context is injected into modules."""
    # Create a Flask app with session
    app = Flask(__name__)
    app.secret_key = 'test'
    
    # Initialize thread manager
    from src.modules.threaded import threaded_manager
    threaded_manager.thread_manager_obj = threaded_manager.Threaded_manager()
    
    with app.app_context():
        with app.test_request_context():
            # Setup auth manager
            auth_manager = AuthManager(auth_dir="tests/test_auth_data")
            
            # Create test users
            auth_manager.create_user("testuser", "password", ["users"])
            auth_manager.create_user("GUEST", "", ["guest"])
            
            # Set permissions
            auth_manager.set_module_permissions("TestModule", "users", ["view", "edit"])
            auth_manager.set_module_permissions("TestModule", "guest", [])  # No access
            
            # Test 1: Regular user with permissions
            session['username'] = 'testuser'
            
            module1 = TestAuthorizationModule()
            disp1 = Displayer()
            
            # Inject auth_manager into auth_manager module (not displayer module)
            import src.modules.auth.auth_manager as auth_manager_module
            auth_manager_module.auth_manager = auth_manager
            
            disp1.add_module(module1)
            
            # Check injected values
            assert module1.get_current_user() == 'testuser'
            assert 'view' in module1.get_user_permissions()
            assert 'edit' in module1.get_user_permissions()
            assert not module1.is_guest_user()
            assert not module1.is_readonly_mode()  # Has edit permission
            assert module1.has_permission('view')
            assert module1.has_permission('edit')
            assert not module1.has_permission('delete')
            
            # Check module wasn't marked as access denied
            result1 = disp1.display()
            assert 'Test Auth Module' in result1
            assert not result1['Test Auth Module'].get('access_denied', False)
            
            # Test 2: GUEST user without permissions
            session['username'] = 'GUEST'
            
            module2 = TestAuthorizationModule()
            disp2 = Displayer()
            disp2.add_module(module2)
            
            # Check injected values
            assert module2.get_current_user() == 'GUEST'
            assert module2.is_guest_user()
            assert module2.is_readonly_mode()
            assert len(module2.get_user_permissions()) == 0
            
            # Check module WAS marked as access denied
            result2 = disp2.display()
            assert 'Test Auth Module' in result2
            assert result2['Test Auth Module'].get('access_denied', False)
            # GUEST is treated like any other user - no special message
            assert "permission" in result2['Test Auth Module'].get('denied_reason', '').lower()


def test_action_user_context():
    """Test that Action class also gets user context."""
    app = Flask(__name__)
    app.secret_key = 'test'
    
    # Initialize thread manager
    from src.modules.threaded import threaded_manager
    if not threaded_manager.thread_manager_obj:
        threaded_manager.thread_manager_obj = threaded_manager.Threaded_manager()
    
    with app.app_context():
        with app.test_request_context():
            auth_manager = AuthManager(auth_dir="tests/test_auth_data")
            auth_manager.create_user("actionuser", "pass", ["executors"])
            auth_manager.set_module_permissions("TestAction", "executors", ["execute", "view"])
            
            session['username'] = 'actionuser'
            
            action = TestSimpleAction()
            disp = Displayer()
            
            import src.modules.auth.auth_manager as auth_manager_module
            auth_manager_module.auth_manager = auth_manager
            
            disp.add_module(action)
            
            # Check API works on Action class too
            assert action.get_current_user() == 'actionuser'
            assert action.has_permission('execute')
            assert not action.has_permission('write')
            # Note: "execute" is in the list, so is_readonly will be False
            # because execute is checked along with write/edit
            assert not action.is_readonly_mode()  # Has execute permission


def test_module_without_permission_requirement():
    """Test that modules without m_required_permission still check authorization."""
    
    class NoAuthModule(Threaded_action):
        m_default_name = "No Auth Module"
        # No m_required_permission set - should use module name as permission
        
        def action(self):
            pass
    
    app = Flask(__name__)
    app.secret_key = 'test'
    
    # Initialize thread manager
    from src.modules.threaded import threaded_manager
    if not threaded_manager.thread_manager_obj:
        threaded_manager.thread_manager_obj = threaded_manager.Threaded_manager()
    
    with app.app_context():
        with app.test_request_context():
            auth_manager = AuthManager(auth_dir="tests/test_auth_data")
            
            # Create GUEST user with no permissions
            auth_manager.create_user("GUEST", "", ["guest"])
            auth_manager.create_user("normaluser", "pass", ["users"])
            
            # Give normaluser access to the module (using module name as permission)
            auth_manager.set_module_permissions("No Auth Module", "users", ["view"])
            # GUEST has no permissions for this module
            
            import src.modules.auth.auth_manager as auth_manager_module
            auth_manager_module.auth_manager = auth_manager
            
            # Test 1: GUEST user should be DENIED
            session['username'] = 'GUEST'
            
            module1 = NoAuthModule()
            disp1 = Displayer()
            disp1.add_module(module1)
            
            result1 = disp1.display()
            assert 'No Auth Module' in result1
            # GUEST should be denied even though module has no explicit m_required_permission
            assert result1['No Auth Module'].get('access_denied', False), "GUEST should be denied access"
            
            # Test 2: Normal user with permission should have access
            session['username'] = 'normaluser'
            
            module2 = NoAuthModule()
            disp2 = Displayer()
            disp2.add_module(module2)
            
            result2 = disp2.display()
            assert 'No Auth Module' in result2
            assert not result2['No Auth Module'].get('access_denied', False), "Normal user should have access"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

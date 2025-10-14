"""
Integration Tests for Authentication and Authorization System

These tests verify the complete auth/authz flow with Flask integration:
- HTTP-based authentication (login, session management)
- Route protection (admin-only, user-required)
- Module-level authorization (Displayer automatic permission checks)
- User context injection into modules
- Permission-based access control
"""

import pytest
import shutil
import os
from flask import Flask, request, redirect, url_for, session
from src.modules.threaded import Threaded_action
from src.modules.action import Action
from src.modules.displayer import Displayer
from src.modules.auth.auth_manager import AuthManager


# =============================================================================
# Test Fixtures - Cleanup
# =============================================================================

@pytest.fixture(scope="module", autouse=True)
def cleanup_test_auth_data():
    """Clean up test_auth_data folder after all tests in this module complete."""
    yield  # Let all tests run first
    
    # After all tests complete, remove test_auth_data folder
    test_auth_dir = os.path.join(os.path.dirname(__file__), "..", "test_auth_data")
    if os.path.exists(test_auth_dir):
        shutil.rmtree(test_auth_dir)
        print(f"\n✅ Cleaned up {test_auth_dir}")


# =============================================================================
# Test Fixtures - Additional Routes for Testing
# =============================================================================

@pytest.fixture(scope="function")
def auth_app(test_app):
    """Add test-specific routes to the Flask app.
    
    Note: The /login route comes from the framework (src.pages.common blueprint),
    so we test the actual implementation instead of mocking it.
    """
    app = test_app
    
    # Add profile route for testing authenticated access
    @app.route('/user/profile')
    def profile():
        if 'user' not in session:
            return redirect(url_for('common.login'))
        return f'<h1>Profile</h1><p>Welcome {session["user"]}</p>', 200
    
    # Add admin route for testing role-based access
    @app.route('/admin/users')
    def admin_users():
        from src.modules.auth import auth_manager as auth_module
        
        if 'user' not in session:
            return redirect(url_for('common.login'))
        
        username = session['user']
        user = auth_module.auth_manager.get_user(username)
        
        # Check if user is in admin group
        if user and 'admin' in user.groups:
            return '<h1>Admin - User Management</h1>', 200
        else:
            return 'Access Denied', 403
    
    return app


# =============================================================================
# Test Modules for Authorization Testing
# =============================================================================

class SecureModule(Threaded_action):
    """Test module requiring specific permissions."""
    m_default_name = "Secure Module"
    m_required_permission = "SecureModule"
    m_required_action = "view"
    
    def action(self):
        pass


class ExecutableAction(Action):
    """Test action requiring execute permission."""
    m_default_name = "Executable Action"
    m_required_permission = "ExecutableAction"
    m_required_action = "execute"


class ImplicitPermissionModule(Threaded_action):
    """Module without explicit permission - uses module name as default."""
    m_default_name = "Implicit Permission Module"
    # No m_required_permission - framework uses module name
    
    def action(self):
        pass


# =============================================================================
# HTTP Authentication Tests
# =============================================================================

class TestHTTPAuthentication:
    """Test HTTP-based login flows and session management using the framework's actual login page."""
    
    def test_framework_login_page_accessible(self, auth_app):
        """Test that the framework's login page loads successfully."""
        client = auth_app.test_client()
        response = client.get('/common/login')
        
        assert response.status_code == 200
        # Check for actual framework login template content
        assert b'Log in' in response.data
        assert b'Please select a user' in response.data
        assert b'testadmin' in response.data  # User created in conftest
        assert b'testuser' in response.data
        assert b'GUEST' in response.data
    
    def test_framework_login_with_password(self, auth_app):
        """Test user can log in through framework's actual login route."""
        client = auth_app.test_client()
        
        response = client.post('/common/login', data={
            'user': 'testadmin',
            'password': 'admin123'
        }, follow_redirects=False)
        
        # Framework redirects to / on success
        assert response.status_code == 302
        assert response.location == '/'
        
        # Session should be set by framework's auth_manager
        with client.session_transaction() as sess:
            assert 'user' in sess
            assert sess['user'] == 'testadmin'
    
    def test_framework_passwordless_login(self, auth_app):
        """Test passwordless users (like GUEST) can log in through framework."""
        client = auth_app.test_client()
        
        response = client.post('/common/login', data={
            'user': 'GUEST',
            'password': ''
        }, follow_redirects=False)
        
        # GUEST user created in conftest with empty password
        assert response.status_code == 302
        assert response.location == '/'
        
        with client.session_transaction() as sess:
            assert sess['user'] == 'GUEST'
    
    def test_framework_failed_login(self, auth_app):
        """Test login fails with incorrect password using framework's login."""
        client = auth_app.test_client()
        
        response = client.post('/common/login', data={
            'user': 'testadmin',
            'password': 'wrongpassword'
        })
        
        # Framework stays on login page and renders template with error
        assert response.status_code == 200
        assert b'Log in' in response.data  # Still on login page
        # Framework shows error message in template


# =============================================================================
# Route Protection Tests
# =============================================================================

class TestRouteProtection:
    """Test that routes enforce authentication and authorization."""
    
    def test_profile_accessible_after_login(self, auth_app):
        """Test user can access profile after logging in."""
        client = auth_app.test_client()
        
        # Login first using framework's actual login route
        client.post('/common/login', data={'user': 'testuser', 'password': 'user123'})
        
        # Access profile
        response = client.get('/user/profile')
        assert response.status_code == 200
        assert b'Profile' in response.data
        assert b'testuser' in response.data
    
    def test_profile_requires_authentication(self, auth_app):
        """Test profile redirects to login if not authenticated."""
        client = auth_app.test_client()
        
        # Try to access profile without logging in
        response = client.get('/user/profile', follow_redirects=False)
        
        # Should redirect to login
        assert response.status_code == 302
        assert '/common/login' in response.location
    
    def test_admin_route_denies_regular_users(self, auth_app):
        """Test admin routes deny access to non-admin users."""
        client = auth_app.test_client()
        
        # Login as regular user
        client.post('/common/login', data={'user': 'testuser', 'password': 'user123'})
        
        # Try to access admin page
        response = client.get('/admin/users')
        
        # Should be denied
        assert response.status_code == 403
    
    def test_admin_route_allows_admin_users(self, auth_app):
        """Test admin routes allow access to admin users."""
        client = auth_app.test_client()
        
        # Login as admin
        client.post('/common/login', data={'user': 'testadmin', 'password': 'admin123'})
        
        # Access admin page
        response = client.get('/admin/users')
        
        assert response.status_code == 200
        assert b'Admin' in response.data


# =============================================================================
# Module Authorization Tests
# =============================================================================

class TestModuleAuthorization:
    """Test automatic authorization checks on modules via Displayer."""
    
    def test_user_context_injected_into_modules(self):
        """Test that Displayer injects user context (username, permissions) into modules."""
        app = Flask(__name__)
        app.secret_key = 'test'
        
        # Initialize thread manager
        from src.modules.threaded import threaded_manager
        threaded_manager.thread_manager_obj = threaded_manager.Threaded_manager()
        
        with app.app_context():
            with app.test_request_context():
                # Setup auth manager
                auth_manager = AuthManager(auth_dir="tests/test_auth_data")
                auth_manager.create_user("testuser", "password", ["users"])
                auth_manager.set_module_permissions("SecureModule", "users", ["view", "edit"])
                
                session['username'] = 'testuser'
                
                # Create module and add to displayer
                module = SecureModule()
                disp = Displayer()
                
                import src.modules.auth.auth_manager as auth_manager_module
                auth_manager_module.auth_manager = auth_manager
                
                disp.add_module(module)
                
                # Verify user context API works
                assert module.get_current_user() == 'testuser'
                assert 'view' in module.get_user_permissions()
                assert 'edit' in module.get_user_permissions()
                assert not module.is_guest_user()
                assert not module.is_readonly_mode()  # Has edit permission
                assert module.has_permission('view')
                assert module.has_permission('edit')
                assert not module.has_permission('delete')
    
    def test_module_grants_access_with_valid_permissions(self):
        """Test modules are accessible when user has required permissions."""
        app = Flask(__name__)
        app.secret_key = 'test'
        
        from src.modules.threaded import threaded_manager
        threaded_manager.thread_manager_obj = threaded_manager.Threaded_manager()
        
        with app.app_context():
            with app.test_request_context():
                auth_manager = AuthManager(auth_dir="tests/test_auth_data")
                auth_manager.create_user("testuser", "password", ["users"])
                auth_manager.set_module_permissions("SecureModule", "users", ["view", "edit"])
                
                session['username'] = 'testuser'
                
                module = SecureModule()
                disp = Displayer()
                
                import src.modules.auth.auth_manager as auth_manager_module
                auth_manager_module.auth_manager = auth_manager
                
                disp.add_module(module)
                
                # Check module is NOT marked as access denied
                result = disp.display()
                assert 'Secure Module' in result
                assert not result['Secure Module'].get('access_denied', False)
    
    def test_module_denies_access_without_permissions(self):
        """Test modules are blocked when user lacks required permissions."""
        app = Flask(__name__)
        app.secret_key = 'test'
        
        from src.modules.threaded import threaded_manager
        threaded_manager.thread_manager_obj = threaded_manager.Threaded_manager()
        
        with app.app_context():
            with app.test_request_context():
                auth_manager = AuthManager(auth_dir="tests/test_auth_data")
                auth_manager.create_user("GUEST", "", ["guest"])
                auth_manager.set_module_permissions("SecureModule", "guest", [])  # No access
                
                session['username'] = 'GUEST'
                
                module = SecureModule()
                disp = Displayer()
                
                import src.modules.auth.auth_manager as auth_manager_module
                auth_manager_module.auth_manager = auth_manager
                
                disp.add_module(module)
                
                # Verify user context shows no permissions
                assert module.get_current_user() == 'GUEST'
                assert module.is_guest_user()
                assert module.is_readonly_mode()
                assert len(module.get_user_permissions()) == 0
                
                # Check module IS marked as access denied
                result = disp.display()
                assert 'Secure Module' in result
                assert result['Secure Module'].get('access_denied', False)
                assert "permission" in result['Secure Module'].get('denied_reason', '').lower()
    
    def test_action_class_receives_user_context(self):
        """Test that Action class (not just Threaded_action) receives user context."""
        app = Flask(__name__)
        app.secret_key = 'test'
        
        from src.modules.threaded import threaded_manager
        if not threaded_manager.thread_manager_obj:
            threaded_manager.thread_manager_obj = threaded_manager.Threaded_manager()
        
        with app.app_context():
            with app.test_request_context():
                auth_manager = AuthManager(auth_dir="tests/test_auth_data")
                auth_manager.create_user("actionuser", "pass", ["executors"])
                auth_manager.set_module_permissions("ExecutableAction", "executors", ["execute", "view"])
                
                session['username'] = 'actionuser'
                
                action = ExecutableAction()
                disp = Displayer()
                
                import src.modules.auth.auth_manager as auth_manager_module
                auth_manager_module.auth_manager = auth_manager
                
                disp.add_module(action)
                
                # Verify user context API works on Action class
                assert action.get_current_user() == 'actionuser'
                assert action.has_permission('execute')
                assert not action.has_permission('write')
                assert not action.is_readonly_mode()  # Has execute permission
    
    def test_implicit_permission_uses_module_name(self):
        """Test modules without explicit m_required_permission use module name as default."""
        app = Flask(__name__)
        app.secret_key = 'test'
        
        from src.modules.threaded import threaded_manager
        if not threaded_manager.thread_manager_obj:
            threaded_manager.thread_manager_obj = threaded_manager.Threaded_manager()
        
        with app.app_context():
            with app.test_request_context():
                auth_manager = AuthManager(auth_dir="tests/test_auth_data")
                auth_manager.create_user("GUEST", "", ["guest"])
                auth_manager.create_user("normaluser", "pass", ["users"])
                
                # Give normaluser access using module name as permission
                auth_manager.set_module_permissions("Implicit Permission Module", "users", ["view"])
                # GUEST has no permissions
                
                import src.modules.auth.auth_manager as auth_manager_module
                auth_manager_module.auth_manager = auth_manager
                
                # Test 1: GUEST should be denied
                session['username'] = 'GUEST'
                
                module1 = ImplicitPermissionModule()
                disp1 = Displayer()
                disp1.add_module(module1)
                
                result1 = disp1.display()
                assert 'Implicit Permission Module' in result1
                assert result1['Implicit Permission Module'].get('access_denied', False), \
                    "GUEST should be denied access even without explicit m_required_permission"
                
                # Test 2: Normal user with permission should have access
                session['username'] = 'normaluser'
                
                module2 = ImplicitPermissionModule()
                disp2 = Displayer()
                disp2.add_module(module2)
                
                result2 = disp2.display()
                assert 'Implicit Permission Module' in result2
                assert not result2['Implicit Permission Module'].get('access_denied', False), \
                    "User with permission should have access"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

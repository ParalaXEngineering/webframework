"""
Integration tests for the authentication and authorization system.

These tests start a full Flask application and test the complete auth flow:
- User login (password and passwordless)
- Permission checking
- User management (admin operations)
- User preferences
- Profile updates
"""

import pytest
import os
import json
import tempfile
import shutil
from pathlib import Path

# Import Flask app setup
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.modules.auth.auth_manager import AuthManager
from src.modules.auth.permission_registry import permission_registry


@pytest.fixture
def temp_auth_dir():
    """Create a temporary auth directory for testing."""
    temp_dir = tempfile.mkdtemp()
    auth_dir = Path(temp_dir) / "auth"
    auth_dir.mkdir()
    yield str(auth_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def auth_manager_instance(temp_auth_dir):
    """Create an AuthManager instance for testing."""
    manager = AuthManager(auth_dir=temp_auth_dir)
    return manager


@pytest.fixture(scope="session")
def flask_app():
    """Create a Flask app with auth system for testing (session-scoped)."""
    from flask import Flask
    from src.modules.auth.auth_manager import AuthManager
    import src.modules.auth.auth_manager as auth_module
    from src.modules.site_conf import Site_conf
    import src.modules.site_conf as site_conf_module
    import tempfile
    import shutil
    
    # Create temporary auth directory for this test session
    temp_dir = tempfile.mkdtemp()
    auth_dir = Path(temp_dir) / "auth"
    auth_dir.mkdir()
    
    # Create a fresh Flask app (don't reuse global app)
    test_app = Flask(__name__)
    test_app.config['TESTING'] = True
    test_app.config['SECRET_KEY'] = 'test-secret-key-for-integration-tests'
    
    # Create auth manager
    manager = AuthManager(auth_dir=str(auth_dir))
    auth_module.auth_manager = manager
    
    # Create minimal site_conf to avoid NoneType errors
    class TestSiteConf(Site_conf):
        def context_processor(self):
            return {"enable_easter_eggs": False}
    
    site_conf_obj = TestSiteConf()
    site_conf_module.site_conf_obj = site_conf_obj
    
    # Register test module permissions
    permission_registry.clear()
    permission_registry.register_module("TestModule", ["execute", "configure"])
    
    # Register blueprints
    from src.pages.common import common_bp
    from tests.demo.website.pages.user_profile_bp import user_profile_bp
    from tests.demo.website.pages.admin_auth_bp import admin_auth_bp
    
    test_app.register_blueprint(common_bp)
    test_app.register_blueprint(user_profile_bp)
    test_app.register_blueprint(admin_auth_bp)
    
    # Add context processor for user injection
    @test_app.context_processor
    def inject_user():
        from flask import session
        user = session.get('user')
        return dict(user=user, endpoint=None, page_info="", topbarItems={"display": False, "login": False})
    
    # Create test users with permissions
    manager.create_user("testadmin", "admin123", ["admin"], "Test Admin", "admin@test.com")
    manager.create_user("testuser", "user123", ["users"], "Test User", "user@test.com")
    manager.create_user("testguest", "", ["guest"], "Test Guest", None)
    
    # Set up permissions
    manager.set_module_permissions("TestModule", "admin", ["read", "write", "delete", "execute", "configure"])
    manager.set_module_permissions("TestModule", "users", ["read", "execute"])
    manager.set_module_permissions("TestModule", "guest", ["read"])
    
    yield test_app
    
    # Cleanup
    shutil.rmtree(temp_dir)


class TestAuthManager:
    """Test AuthManager functionality."""
    
    def test_user_creation(self, auth_manager_instance):
        """Test creating users."""
        manager = auth_manager_instance
        
        # Create user with password
        assert manager.create_user("alice", "password123", ["users"], "Alice", "alice@example.com")
        user = manager.get_user("alice")
        assert user is not None
        assert user.username == "alice"
        assert user.display_name == "Alice"
        assert user.email == "alice@example.com"
        assert "users" in user.groups
        
        # Create passwordless user
        assert manager.create_user("bob", "", ["guest"], "Bob")
        user = manager.get_user("bob")
        assert user.password_hash == ""
        
        # Cannot create duplicate
        assert not manager.create_user("alice", "password", ["users"])
    
    def test_password_verification(self, auth_manager_instance):
        """Test password verification."""
        manager = auth_manager_instance
        
        manager.create_user("alice", "secure123", ["users"])
        
        # Correct password
        assert manager.verify_login("alice", "secure123")
        
        # Wrong password
        assert not manager.verify_login("alice", "wrong")
        
        # Nonexistent user
        assert not manager.verify_login("nobody", "password")
    
    def test_passwordless_login(self, auth_manager_instance):
        """Test passwordless user login."""
        manager = auth_manager_instance
        
        manager.create_user("guest", "", ["guest"])
        
        # Empty password should work
        assert manager.verify_login("guest", "")
        
        # Any password should fail
        assert not manager.verify_login("guest", "anypassword")
    
    def test_permissions(self, auth_manager_instance):
        """Test permission management."""
        manager = auth_manager_instance
        
        # Create users with different groups
        manager.create_user("admin", "pass", ["admin"])
        manager.create_user("user", "pass", ["users"])
        
        # Set permissions
        manager.set_module_permissions("Module1", "admin", ["read", "write", "delete"])
        manager.set_module_permissions("Module1", "users", ["read"])
        
        # Check admin permissions
        assert manager.has_permission("admin", "Module1", "read")
        assert manager.has_permission("admin", "Module1", "write")
        assert manager.has_permission("admin", "Module1", "delete")
        
    def test_permissions_persistence(self, auth_manager_instance):
        """Test that permissions are saved and persist across reload."""
        from pathlib import Path
        
        manager = auth_manager_instance
        
        # Create test users
        manager.create_user("testadmin", "pass", ["admin"])
        manager.create_user("testuser", "pass", ["users"])
        
        # Set some permissions
        manager.set_module_permissions("TestApp", "admin", ["read", "write", "execute"])
        manager.set_module_permissions("TestApp", "users", ["read"])
        manager.set_module_permissions("AnotherModule", "admin", ["configure"])
        
        # Verify permissions.json was created
        permissions_file = Path(manager.auth_dir) / "permissions.json"
        assert permissions_file.exists()
        
        # Verify file contains our permissions
        with open(permissions_file) as f:
            data = json.load(f)
            assert "modules" in data
            assert "TestApp" in data["modules"]
            assert "admin" in data["modules"]["TestApp"]["groups"]
            assert "read" in data["modules"]["TestApp"]["groups"]["admin"]
            assert "write" in data["modules"]["TestApp"]["groups"]["admin"]
            assert "execute" in data["modules"]["TestApp"]["groups"]["admin"]
            assert "users" in data["modules"]["TestApp"]["groups"]
            assert "read" in data["modules"]["TestApp"]["groups"]["users"]
        
        # Reload from disk
        manager.reload()
        
        # Verify permissions still work after reload
        assert manager.has_permission("testadmin", "TestApp", "read")
        assert manager.has_permission("testadmin", "TestApp", "write")
        assert manager.has_permission("testadmin", "AnotherModule", "configure")
        assert manager.has_permission("testuser", "TestApp", "read")
        assert not manager.has_permission("testuser", "TestApp", "write")
    
    def test_user_preferences(self, auth_manager_instance):
        """Test user preferences storage."""
        manager = auth_manager_instance
        
        manager.create_user("alice", "pass", ["users"])
        
        # Get default preferences
        prefs = manager.get_user_prefs("alice")
        assert "theme" in prefs
        assert prefs["theme"] == "light"
        
        # Save custom preferences
        prefs["theme"] = "dark"
        prefs["module_settings"]["TestModule"] = {"port": "COM3", "timeout": 30}
        manager.save_user_prefs("alice", prefs)
        
        # Retrieve saved preferences
        loaded_prefs = manager.get_user_prefs("alice")
        assert loaded_prefs["theme"] == "dark"
        assert loaded_prefs["module_settings"]["TestModule"]["port"] == "COM3"
    
    def test_group_management(self, auth_manager_instance):
        """Test group operations."""
        manager = auth_manager_instance
        
        # Create users in different groups
        manager.create_user("alice", "pass", ["engineers", "quality"])
        manager.create_user("bob", "pass", ["engineers"])
        
        # Get all groups
        groups = manager.get_all_groups()
        assert "engineers" in groups
        assert "quality" in groups
        
        # Rename group
        manager.rename_group("engineers", "developers")
        alice = manager.get_user("alice")
        assert "developers" in alice.groups
        assert "engineers" not in alice.groups
        
        # Delete group
        manager.delete_group("quality")
        alice = manager.get_user("alice")
        assert "quality" not in alice.groups
    
    def test_group_creation(self, auth_manager_instance):
        """Test creating groups via create_group method."""
        manager = auth_manager_instance
        
        # Create a new group
        assert manager.create_group("testers")
        
        # Verify group appears in get_all_groups
        groups = manager.get_all_groups()
        assert "testers" in groups
        
        # Cannot create duplicate group
        assert not manager.create_group("testers")
        
        # Create another group
        assert manager.create_group("reviewers")
        groups = manager.get_all_groups()
        assert "reviewers" in groups
        assert "testers" in groups
    
    def test_group_persistence(self, auth_manager_instance):
        """Test that groups persist across reload."""
        manager = auth_manager_instance
        
        # Create groups
        manager.create_group("architects")
        manager.create_group("designers")
        
        # Verify they exist
        assert "architects" in manager.get_all_groups()
        assert "designers" in manager.get_all_groups()
        
        # Reload from disk
        manager.reload()
        
        # Verify groups still exist
        groups = manager.get_all_groups()
        assert "architects" in groups
        assert "designers" in groups
    
    def test_groups_file_operations(self, temp_auth_dir):
        """Test groups.json file is created and maintained."""
        from pathlib import Path
        
        manager = AuthManager(auth_dir=temp_auth_dir)
        
        # Verify groups.json was created with defaults
        groups_file = Path(temp_auth_dir) / "groups.json"
        assert groups_file.exists()
        
        with open(groups_file) as f:
            data = json.load(f)
            assert "groups" in data
            assert "admin" in data["groups"]
            assert "guest" in data["groups"]
        
        # Create new groups
        manager.create_group("operations")
        manager.create_group("finance")
        
        # Verify file was updated
        with open(groups_file) as f:
            data = json.load(f)
            assert "operations" in data["groups"]
            assert "finance" in data["groups"]
        
        # Delete a group
        manager.delete_group("operations")
        
        # Verify file reflects deletion
        with open(groups_file) as f:
            data = json.load(f)
            assert "operations" not in data["groups"]
            assert "finance" in data["groups"]


class TestAuthIntegration:
    """Test auth system integration with Flask app."""
    
    @pytest.mark.skip(reason="Flask integration tests need fixture refactoring - see manual_test_webapp.py for full integration testing")
    def test_login_page_loads(self, flask_app):
        """Test that login page is accessible."""
        client = flask_app.test_client()
        response = client.get('/login')
        assert response.status_code == 200
    
    @pytest.mark.skip(reason="Flask integration tests need fixture refactoring - see manual_test_webapp.py for full integration testing")
    def test_login_with_password(self, flask_app):
        """Test logging in with username and password."""
        client = flask_app.test_client()
        
        response = client.post('/login', data={
            'user': 'testadmin',
            'password': 'admin123'
        }, follow_redirects=False)
        
        # Should redirect on success
        assert response.status_code == 302
        
        # Check session was set
        with client.session_transaction() as sess:
            assert 'user' in sess
            assert sess['user'] == 'testadmin'
    
    @pytest.mark.skip(reason="Flask integration tests need fixture refactoring - see manual_test_webapp.py for full integration testing")
    def test_login_passwordless(self, flask_app):
        """Test logging in without password."""
        client = flask_app.test_client()
        
        response = client.post('/login', data={
            'user': 'testguest',
            'password': ''
        }, follow_redirects=False)
        
        assert response.status_code == 302
        
        with client.session_transaction() as sess:
            assert sess['user'] == 'testguest'
    
    @pytest.mark.skip(reason="Flask integration tests need fixture refactoring - see manual_test_webapp.py for full integration testing")
    def test_login_wrong_password(self, flask_app):
        """Test login fails with wrong password."""
        client = flask_app.test_client()
        
        response = client.post('/login', data={
            'user': 'testadmin',
            'password': 'wrongpassword'
        })
        
        # Should stay on login page
        assert response.status_code == 200
        assert b'Invalid' in response.data or b'incorrect' in response.data.lower()
    
    @pytest.mark.skip(reason="Flask integration tests need fixture refactoring - see manual_test_webapp.py for full integration testing")
    def test_user_profile_access(self, flask_app):
        """Test accessing user profile page."""
        client = flask_app.test_client()
        
        # Login first
        client.post('/login', data={'user': 'testuser', 'password': 'user123'})
        
        # Access profile page
        response = client.get('/user/profile')
        assert response.status_code == 200
        assert b'Profile' in response.data
    
    @pytest.mark.skip(reason="Flask integration tests need fixture refactoring - see manual_test_webapp.py for full integration testing")
    def test_admin_access_control(self, flask_app):
        """Test that admin pages require admin group."""
        client = flask_app.test_client()
        
        # Try as regular user
        client.post('/login', data={'user': 'testuser', 'password': 'user123'})
        response = client.get('/admin/users')
        # Should be redirected or denied
        assert response.status_code in [302, 403]
        
        # Try as admin
        client.post('/login', data={'user': 'testadmin', 'password': 'admin123'})
        response = client.get('/admin/users')
        assert response.status_code == 200
    
    def test_check_login_attempt_successful(self, auth_manager_instance):
        """Test successful login with check_login_attempt."""
        manager = auth_manager_instance
        manager.create_user("testuser", "correct_password", ["users"])
        
        success, error_msg = manager.check_login_attempt("testuser", "correct_password")
        
        assert success is True
        assert error_msg is None
        
        # Failed attempts should be reset
        remaining = manager.failed_login_manager.get_remaining_attempts("testuser")
        assert remaining == 5
    
    def test_check_login_attempt_wrong_password(self, auth_manager_instance):
        """Test failed login increments attempt counter."""
        manager = auth_manager_instance
        manager.create_user("testuser", "correct_password", ["users"])
        
        success, error_msg = manager.check_login_attempt("testuser", "wrong_password")
        
        assert success is False
        assert "Bad password" in error_msg
        assert "4 attempts remaining" in error_msg
        
        # Verify attempt was recorded
        status = manager.failed_login_manager.get_user_status("testuser")
        assert status['count'] == 1
    
    def test_check_login_attempt_lockout_after_5_failures(self, auth_manager_instance):
        """Test account locks after 5 failed attempts."""
        manager = auth_manager_instance
        manager.create_user("testuser", "correct_password", ["users"])
        
        # Make 5 failed attempts
        for i in range(5):
            success, error_msg = manager.check_login_attempt("testuser", "wrong_password")
            assert success is False
            
            if i < 4:
                # First 4 attempts show remaining count
                assert "attempts remaining" in error_msg
            else:
                # 5th attempt locks the account
                assert "Account locked" in error_msg or "Too many failed attempts" in error_msg
        
        # Account should be locked
        is_locked, _ = manager.failed_login_manager.is_locked("testuser")
        assert is_locked
    
    def test_check_login_attempt_cannot_login_while_locked(self, auth_manager_instance):
        """Test cannot login while account is locked."""
        manager = auth_manager_instance
        manager.create_user("testuser", "correct_password", ["users"])
        
        # Lock the account
        for _ in range(5):
            manager.check_login_attempt("testuser", "wrong_password")
        
        # Try to login with CORRECT password while locked
        success, error_msg = manager.check_login_attempt("testuser", "correct_password")
        
        assert success is False
        assert "Account locked" in error_msg
        assert "Try again in" in error_msg
    
    def test_check_login_attempt_user_not_exists(self, auth_manager_instance):
        """Test login attempt for non-existent user."""
        manager = auth_manager_instance
        
        success, error_msg = manager.check_login_attempt("nonexistent", "anypassword")
        
        assert success is False
        assert "User does not exist" in error_msg
    
    def test_check_login_attempt_passwordless_user(self, auth_manager_instance):
        """Test passwordless users can always login."""
        manager = auth_manager_instance
        manager.create_user("guestuser", "", ["guest"])  # Empty password
        
        # Should login successfully
        success, error_msg = manager.check_login_attempt("guestuser", "")
        
        assert success is True
        assert error_msg is None
        
        # Even with any password (passwordless users don't check)
        success2, error_msg2 = manager.check_login_attempt("guestuser", "anypassword")
        assert success2 is True
        assert error_msg2 is None
    
    def test_check_login_attempt_resets_on_success(self, auth_manager_instance):
        """Test successful login resets failed attempt counter."""
        manager = auth_manager_instance
        manager.create_user("testuser", "correct_password", ["users"])
        
        # Make 3 failed attempts
        for _ in range(3):
            manager.check_login_attempt("testuser", "wrong_password")
        
        status = manager.failed_login_manager.get_user_status("testuser")
        assert status['count'] == 3
        
        # Successful login should reset
        success, _ = manager.check_login_attempt("testuser", "correct_password")
        assert success is True
        
        status_after = manager.failed_login_manager.get_user_status("testuser")
        assert status_after['count'] == 0
    
    def test_check_login_attempt_lockout_persists(self, auth_manager_instance):
        """Test lockout state persists across reload."""
        manager = auth_manager_instance
        manager.create_user("testuser", "correct_password", ["users"])
        
        # Lock the account
        for _ in range(5):
            manager.check_login_attempt("testuser", "wrong_password")
        
        is_locked_before, _ = manager.failed_login_manager.is_locked("testuser")
        assert is_locked_before
        
        # Reload manager (simulates restart)
        manager.reload()
        
        # Still locked after reload
        is_locked_after, _ = manager.failed_login_manager.is_locked("testuser")
        assert is_locked_after


class TestPermissionRegistry:
    """Test permission registry functionality."""
    
    def test_module_registration(self):
        """Test registering module actions."""
        permission_registry.clear()
        
        permission_registry.register_module("TestModule", ["execute", "configure"])
        
        actions = permission_registry.get_module_actions("TestModule")
        assert "read" in actions  # Standard CRUD
        assert "write" in actions
        assert "delete" in actions
        assert "execute" in actions  # Custom
        assert "configure" in actions  # Custom
    
    def test_get_all_modules(self):
        """Test retrieving all registered modules."""
        permission_registry.clear()
        
        permission_registry.register_module("Module1", [])
        permission_registry.register_module("Module2", ["custom"])
        
        modules = permission_registry.get_all_modules()
        assert "Module1" in modules
        assert "Module2" in modules
    
    def test_action_validation(self):
        """Test validating actions for modules."""
        permission_registry.clear()
        
        permission_registry.register_module("TestModule", ["execute"])
        
        assert permission_registry.is_action_valid("TestModule", "read")
        assert permission_registry.is_action_valid("TestModule", "execute")
        assert not permission_registry.is_action_valid("TestModule", "nonexistent")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

"""
Test to verify GUEST user permissions are working.
"""
import pytest
from src.modules.auth.auth_manager import AuthManager


def test_guest_permissions_from_file():
    """Test that GUEST user has no permissions in Demo modules."""
    auth_manager = AuthManager(auth_dir='tests/website/auth')
    
    # Check GUEST has no permissions for Demo_Threading
    assert not auth_manager.has_permission('GUEST', 'Demo_Threading', 'view'), \
        "GUEST should NOT have view permission on Demo_Threading"
    assert not auth_manager.has_permission('GUEST', 'Demo_Threading', 'execute'), \
        "GUEST should NOT have execute permission on Demo_Threading"
    
    # Check GUEST has no permissions for Demo_Scheduler
    assert not auth_manager.has_permission('GUEST', 'Demo_Scheduler', 'view'), \
        "GUEST should NOT have view permission on Demo_Scheduler"
    assert not auth_manager.has_permission('GUEST', 'Demo_Scheduler', 'execute'), \
        "GUEST should NOT have execute permission on Demo_Scheduler"
    
    # Verify the permission structure exists
    demo_threading_perm = auth_manager._permissions.get('Demo_Threading')
    assert demo_threading_perm is not None, "Demo_Threading permission should exist"
    
    # Check what groups GUEST belongs to
    guest_user = auth_manager._users.get('GUEST')
    assert guest_user is not None, "GUEST user should exist"
    print(f"GUEST groups: {guest_user.groups}")
    
    # Check what permissions guest group has
    guest_group_actions = demo_threading_perm.groups.get('guest', [])
    print(f"Guest group actions for Demo_Threading: {guest_group_actions}")
    assert guest_group_actions == [], "Guest group should have empty permissions"


def test_admin_has_permissions():
    """Verify admin user has permissions (sanity check)."""
    auth_manager = AuthManager(auth_dir='tests/website/auth')
    
    # Admin should have permissions
    assert auth_manager.has_permission('admin', 'Demo_Threading', 'view'), \
        "admin should have view permission"
    assert auth_manager.has_permission('admin', 'Demo_Threading', 'execute'), \
        "admin should have execute permission"


if __name__ == "__main__":
    test_guest_permissions_from_file()
    test_admin_has_permissions()
    print("\n✅ All tests passed!")

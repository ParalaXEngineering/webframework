# Refactoring: Extract Permission Checking from Displayer

## Problem

`Displayer.add_module()` is 80+ lines mixing multiple concerns:
- Module name resolution
- Permission checking against auth_manager
- User context injection into module instances
- Access denied handling
- Logging

This makes it hard to:
- Test permission logic independently
- Reuse permission checking elsewhere
- Understand what `add_module()` actually does

## Current Code Structure

```python
def add_module(self, module, name_override=None, display=True):
    # 1. Get module name (5 lines)
    default_name = getattr(module, 'm_name', getattr(module, 'm_default_name', 'Generic'))
    
    # 2. Get error (3 lines)
    error_module = None
    if hasattr(module, "m_error"):
        error_module = module.m_error
    
    # 3. Permission checking setup (10 lines)
    access_denied = False
    denied_reason = None
    user_permissions = []
    current_username = None
    is_guest = False
    required_permission = getattr(module, 'm_required_permission', None)
    required_action = getattr(module, 'm_required_action', 'view')
    
    # 4. Auth manager resolution (5 lines)
    auth_manager = auth_manager_module.auth_manager if auth_manager_module else None
    
    # 5. Logging (3 lines)
    logger.info(f"[Displayer] Module: {default_name}...")
    
    # 6. Default permission fallback (5 lines)
    if not required_permission:
        required_permission = default_name
    
    # 7. Permission check logic (25 lines)
    if auth_manager is not None and session is not None:
        current_username = session.get('user')
        if not current_username:
            access_denied = True
            denied_reason = "..."
        else:
            is_guest = current_username.upper() == 'GUEST'
            has_perm = auth_manager.has_permission(...)
            if not has_perm:
                access_denied = True
                denied_reason = "..."
            else:
                user_permissions = auth_manager.get_user_permissions(...)
    
    # 8. User context injection (10 lines)
    if hasattr(module, '_current_user'):
        module._current_user = current_username
    # ... more injections
    
    # 9. Module registration (15 lines)
    self.m_modules[default_name] = {...}
```

## Proposed Solution

### Create ModuleAccessResult Dataclass

```python
# src/modules/auth/access_check.py
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ModuleAccessResult:
    """Result of a module access permission check."""
    
    allowed: bool
    """Whether access is granted."""
    
    denied_reason: Optional[str] = None
    """Human-readable denial reason if not allowed."""
    
    user_permissions: List[str] = field(default_factory=list)
    """List of permission actions user has for this module."""
    
    current_user: Optional[str] = None
    """Username of the current user."""
    
    is_guest: bool = False
    """Whether the current user is GUEST."""
    
    is_readonly: bool = True
    """Whether user only has read permissions."""
    
    @property
    def can_write(self) -> bool:
        """Check if user has any write-like permission."""
        write_actions = {'write', 'edit', 'create', 'delete', 'execute'}
        return bool(set(self.user_permissions) & write_actions)
```

### Create Access Checker Function

```python
# src/modules/auth/access_check.py (continued)

def check_module_access(
    module_name: str,
    required_action: str = 'view',
    auth_manager: Optional['AuthManager'] = None,
    session_user: Optional[str] = None
) -> ModuleAccessResult:
    """
    Check if current user can access a module.
    
    Args:
        module_name: The module/permission name to check
        required_action: Required action (default: 'view')
        auth_manager: Auth manager instance (None = auth disabled = allow all)
        session_user: Current session username
        
    Returns:
        ModuleAccessResult with access decision and context
        
    Example:
        >>> result = check_module_access("FileManager", "upload", auth_mgr, "john")
        >>> if not result.allowed:
        ...     return render_access_denied(result.denied_reason)
    """
    # Auth disabled = full access
    if auth_manager is None:
        return ModuleAccessResult(
            allowed=True,
            user_permissions=['view', 'edit', 'delete', 'create', 'execute'],
            is_readonly=False
        )
    
    # No user = denied
    if not session_user:
        return ModuleAccessResult(
            allowed=False,
            denied_reason=str(ERROR_DISPLAYER_NOT_LOGGED_IN)
        )
    
    # Check permission
    is_guest = session_user.upper() == 'GUEST'
    has_permission = auth_manager.has_permission(session_user, module_name, required_action)
    
    if not has_permission:
        return ModuleAccessResult(
            allowed=False,
            denied_reason=ERROR_DISPLAYER_PERMISSION_DENIED.format(
                required_action=required_action,
                required_permission=module_name
            ),
            current_user=session_user,
            is_guest=is_guest
        )
    
    # Granted - get all permissions for this module
    user_permissions = auth_manager.get_user_permissions(session_user, module_name)
    write_actions = {'write', 'edit', 'create', 'delete', 'execute'}
    is_readonly = not bool(set(user_permissions) & write_actions)
    
    return ModuleAccessResult(
        allowed=True,
        user_permissions=user_permissions,
        current_user=session_user,
        is_guest=is_guest,
        is_readonly=is_readonly
    )
```

### Refactor add_module()

```python
# src/modules/displayer/displayer.py

def add_module(
    self,
    module: Any,
    name_override: Optional[str] = None,
    display: bool = True
) -> None:
    """Add a module to the displayer with automatic permission checking."""
    
    # 1. Resolve module name
    module_name = self._resolve_module_name(module)
    display_name = name_override or module_name
    
    # 2. Check permissions
    from ..auth.access_check import check_module_access
    access = check_module_access(
        module_name=getattr(module, 'm_required_permission', None) or module_name,
        required_action=getattr(module, 'm_required_action', 'view'),
        auth_manager=self._get_auth_manager(),
        session_user=self._get_session_user()
    )
    
    # 3. Inject user context into module
    self._inject_user_context(module, access)
    
    # 4. Register module
    self.m_modules[module_name] = {
        "id": module_name,
        "name_override": display_name if name_override else None,
        "type": getattr(module, 'm_type', None),
        "display": display,
        "error": getattr(module, 'm_error', None),
        "access_denied": not access.allowed,
        "denied_reason": access.denied_reason,
        **access.__dict__  # Include all access result fields
    }
    
    self.m_active_module = module_name


def _resolve_module_name(self, module: Any) -> str:
    """Get the display name for a module."""
    return getattr(module, 'm_name', None) or \
           getattr(module, 'm_default_name', 'Generic')


def _get_auth_manager(self):
    """Get auth manager instance."""
    try:
        from ..auth import auth_manager
        return auth_manager
    except ImportError:
        return None


def _get_session_user(self) -> Optional[str]:
    """Get current session username."""
    try:
        from flask import session
        return session.get('user')
    except (ImportError, RuntimeError):
        return None


def _inject_user_context(self, module: Any, access: 'ModuleAccessResult') -> None:
    """Inject user context into module instance."""
    if hasattr(module, '_current_user'):
        module._current_user = access.current_user
    if hasattr(module, '_user_permissions'):
        module._user_permissions = access.user_permissions
    if hasattr(module, '_is_guest'):
        module._is_guest = access.is_guest
    if hasattr(module, '_is_readonly'):
        module._is_readonly = access.is_readonly
```

## Files to Create/Modify

### New Files
- [ ] `src/modules/auth/access_check.py` - ModuleAccessResult + check_module_access

### Files to Modify
- [ ] `src/modules/displayer/displayer.py` - Refactor add_module()
- [ ] `src/modules/auth/__init__.py` - Export new classes

## Testing

### Unit Tests for Access Check

```python
# tests/unit/test_access_check.py
import pytest
from src.modules.auth.access_check import check_module_access, ModuleAccessResult


def test_auth_disabled_allows_all():
    """When auth_manager is None, all access is granted."""
    result = check_module_access("AnyModule", auth_manager=None)
    assert result.allowed is True
    assert result.is_readonly is False


def test_no_user_denies_access():
    """When no user in session, access is denied."""
    mock_auth = MockAuthManager()
    result = check_module_access("Module", auth_manager=mock_auth, session_user=None)
    assert result.allowed is False
    assert "not logged in" in result.denied_reason.lower()


def test_permission_denied():
    """When user lacks permission, access is denied with reason."""
    mock_auth = MockAuthManager(permissions={})
    result = check_module_access(
        "FileManager", 
        required_action="delete",
        auth_manager=mock_auth, 
        session_user="john"
    )
    assert result.allowed is False
    assert "delete" in result.denied_reason
    assert "FileManager" in result.denied_reason


def test_permission_granted_includes_all_perms():
    """When access granted, result includes all user permissions."""
    mock_auth = MockAuthManager(permissions={"FileManager": ["view", "upload"]})
    result = check_module_access(
        "FileManager",
        required_action="view", 
        auth_manager=mock_auth,
        session_user="john"
    )
    assert result.allowed is True
    assert "view" in result.user_permissions
    assert "upload" in result.user_permissions
```

## Benefits

1. **Single Responsibility**: `add_module()` focuses on module registration
2. **Testable**: Permission logic tested independently
3. **Reusable**: `check_module_access()` usable in routes, APIs, etc.
4. **Type Safe**: `ModuleAccessResult` is a proper dataclass
5. **Clear API**: Result object documents what's available

## Estimated Effort

- Create access_check.py: 1 hour
- Refactor add_module(): 1 hour
- Write tests: 1 hour
- Integration testing: 1 hour

**Total: ~4 hours**

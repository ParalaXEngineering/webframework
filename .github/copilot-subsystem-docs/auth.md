# Auth System

## Purpose
Role-based access control (RBAC) with user/group management, session handling, and permission checks. Replaces legacy access_manager with granular module-level permissions.

## Core Components
- `src/modules/auth/auth_manager.py` - Main AuthManager class, decorators, permission logic
- `src/modules/auth/auth_models.py` - User, ModulePermission, Group dataclasses
- `src/modules/auth/auth_utils.py` - Password hashing, verification, default prefs
- `src/modules/auth/security_utils.py` - Failed login tracking, account lockout
- `website/auth/` - JSON storage: users.json, permissions.json, groups.json, user_prefs/

## Critical Patterns

### Route Protection (MANDATORY)
```python
from modules.auth import auth_manager

# Module-level permission
@auth_manager.require_permission("FileManager", "view")
def file_list():
    return "Files"

# Admin-only
@auth_manager.require_admin()
def admin_panel():
    return "Admin"

# Any authenticated user
@auth_manager.require_login()
def dashboard():
    return "Dashboard"
```

### Manual Permission Check
```python
user = auth_manager.get_current_user()
if not auth_manager.has_permission(user, "FileManager", "edit"):
    return "Access denied"
```

### Threaded Action Permission
```python
class MyAction(Threaded_action):
    m_required_permission = "MyModule"  # Module name
    m_required_action = "execute"  # Action type
    
    def action(self):
        # Framework auto-checks before calling
        pass
```

### Login Flow
```python
from modules.auth import auth_manager

success, error = auth_manager.check_login_attempt(username, password)
if success:
    auth_manager.set_current_user(username)
    flash("Login successful", "success")
else:
    flash(error, "danger")  # e.g., "Account locked. Try again in 4m 32s"
```

### User Preferences
```python
# Get module-specific prefs
prefs = auth_manager.get_user_module_prefs(username, "FileManager")
upload_dir = prefs.get("default_upload_dir", "/uploads")

# Save module prefs
auth_manager.save_user_module_prefs(username, "FileManager", {"default_upload_dir": "/data"})

# Framework setting overrides
auth_manager.set_user_framework_override(username, "framework_ui.theme", "dark")
```

## API Quick Reference
```python
class AuthManager:
    # User Management
    def get_user(username: str) -> Optional[User]
    def create_user(username: str, password: str, groups: List[str], ...) -> bool
    def delete_user(username: str) -> bool
    def update_user_password(username: str, new_password: str) -> bool
    def update_user_groups(username: str, groups: List[str]) -> bool
    
    # Authentication
    def check_login_attempt(username: str, password: str) -> tuple[bool, Optional[str]]
    def verify_login(username: str, password: str) -> bool
    def get_current_user() -> Optional[str]
    def set_current_user(username: str)
    def logout_current_user()
    
    # Permissions
    def has_permission(username: str, module: str, action: str) -> bool
    def get_user_permissions(username: str, module: str) -> List[str]
    def set_module_permissions(module: str, group: str, actions: List[str])
    
    # Groups
    def get_all_groups() -> List[str]
    def create_group(group_name: str) -> bool
    def delete_group(group_name: str) -> bool
    
    # Decorators
    def require_permission(module: str, action: str = "view")
    def require_admin()
    def require_login()

# Default users
# admin/admin (groups: ["admin"])
# guest/passwordless (groups: ["guest"])
```

## Common Pitfalls
1. **Session key** - Use `session['user']` not `session['username']` or `session['current_user']`
2. **Admin bypass** - 'admin' group has access to everything automatically
3. **Empty password** - Empty `password_hash` means passwordless (auto-login)
4. **Module names** - Must match Threaded_action class name for auto-checks
5. **Action names** - Standard: "view", "edit", "delete", "execute" (lowercase)
6. **Decorator order** - Auth decorators must be AFTER @blueprint.route()
7. **Failed login** - Default: 5 attempts, 5-minute lockout (configurable in FailedLoginManager)
8. **Permissions file** - Has both "modules" and "pages" sections (pages for legacy)

## Integration Points
- **Displayer**: Auto-renders access denied pages with `_render_access_denied()`
- **Threaded**: Checks `m_required_permission` before starting threads
- **SocketIO**: User rooms based on `session['user']` for isolated messaging
- **Settings**: User prefs stored in `website/auth/user_prefs/{username}.json`
- **Site_conf**: `enable_authentication()` registers admin pages in navbar

## Files
- `auth_manager.py` - Main manager, singleton `auth_manager` global
- `auth_models.py` - User/ModulePermission/Group with to_dict/from_dict
- `auth_utils.py` - bcrypt wrappers, default_user_prefs structure
- `security_utils.py` - FailedLoginManager with lockout tracking
- `website/auth/users.json` - User accounts (password_hash, groups, metadata)
- `website/auth/permissions.json` - Module permissions by group
- `website/auth/groups.json` - Group registry
- `website/auth/user_prefs/*.json` - Per-user preferences
- `website/auth/failed_logins.json` - Failed login tracking

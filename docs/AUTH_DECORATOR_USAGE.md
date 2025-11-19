# Authentication Decorator Usage

## NEVER Implement Your Own Decorator

The framework provides a `require_permission` decorator in `src.modules.auth`. **Never create your own version.**

## Correct Usage

### Import from Framework

```python
from src.modules.auth import require_permission
```

### Apply to Routes

```python
from flask import Blueprint
from src.modules.auth import require_permission

my_bp = Blueprint('my_module', __name__)

@my_bp.route('/my-page')
@require_permission("MyModule", "view")
def my_page():
    return "Protected page"
```

### How It Works

The framework's decorator automatically:
- ✅ Works when auth is **disabled** (allows all access)
- ✅ Works when auth is **enabled** (checks permissions)
- ✅ Shows proper access denied pages
- ✅ Handles redirects to login
- ✅ Displays user-friendly error messages

### Different Permission Levels

```python
# View permission (default)
@require_permission("FileManager", "view")
def view_files():
    pass

# Edit permission
@require_permission("FileManager", "edit")
def edit_file():
    pass

# Custom action permission
@require_permission("FileManager", "upload")
def upload_file():
    pass

# Delete permission
@require_permission("FileManager", "delete")
def delete_file():
    pass
```

### Inline Permission Checks

For business logic within routes, use inline checks:

```python
from src.modules.auth import auth_manager as auth_module

@require_permission("FileManager", "view")
def file_manager_page():
    # Route-level check passed, now check specific action
    if request.method == 'POST':
        auth_manager = auth_module.auth_manager
        if auth_manager:
            current_user = session.get('user')
            if not auth_manager.has_permission(current_user, "FileManager", "upload"):
                return {"error": "No upload permission"}
        
        # Process upload
```

### Threaded Actions

For background tasks, use class-level permission:

```python
from src.modules.threaded import Threaded_action

class MyBackgroundTask(Threaded_action):
    m_default_name = "My Task"
    m_required_permission = "MyModule"  # Checks MyModule.view
    
    def action(self):
        self.emit_console("Processing...")
```

## Common Mistakes ❌

### DON'T: Create Your Own Decorator

```python
# ❌ WRONG - Don't do this!
def require_permission(module: str, action: str = "view"):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Your custom implementation
            pass
        return decorated_function
    return decorator
```

### DON'T: Import from Wrong Location

```python
# ❌ WRONG
from modules.auth.auth_manager import AuthManager
auth_manager = AuthManager()
decorator = auth_manager.require_permission("Module", "view")

# ✅ CORRECT
from src.modules.auth import require_permission
```

### DON'T: Check Auth Status Manually

```python
# ❌ WRONG - Don't manually check if auth is enabled
@my_bp.route('/page')
def my_page():
    if auth_manager:
        if not auth_manager.has_permission(...):
            return "Access Denied"
    # Your code

# ✅ CORRECT - Use the decorator
@my_bp.route('/page')
@require_permission("Module", "view")
def my_page():
    # Your code
```

## Summary

**Single Source of Truth**: `src.modules.auth.require_permission`

Use it. Don't recreate it.

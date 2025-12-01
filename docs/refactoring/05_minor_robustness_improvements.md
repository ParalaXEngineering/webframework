# Refactoring: Minor Improvements for Robustness

These are smaller changes that don't require major architectural work but improve security and reliability.

---

## 1. Remove Hungarian Notation (`m_` prefix)

### Problem
The `m_` prefix on instance variables is a C++/Java convention from the 90s:

```python
self.m_modules = {}
self.m_topbar = {}
self.m_enable_threads = False
```

In Python, it's visual noise. The underscore convention in Python means "private" (`_private`) or "name mangling" (`__private`).

### Solution
Rename variables to remove `m_` prefix:

```python
# Before
self.m_modules = {}
self.m_enable_threads = False

# After
self.modules = {}
self.enable_threads = False
# Or if meant to be private:
self._modules = {}
self._enable_threads = False
```

### Migration Script

```python
# scripts/remove_hungarian.py
import re
from pathlib import Path

def fix_hungarian(content: str) -> str:
    # Replace self.m_xxx with self._xxx (private convention)
    # Be careful with m_default_name and similar class attributes
    return re.sub(r'\bself\.m_([a-z])', r'self._\1', content)

# Run on all files
for py_file in Path("src").rglob("*.py"):
    content = py_file.read_text()
    new_content = fix_hungarian(content)
    if new_content != content:
        # Review before writing!
        print(f"Would change: {py_file}")
```

### Risk
- **High impact**: This touches almost every file
- **Breaking change**: External code using `module.m_sidebar` would break

### Recommendation
**Low priority** - Do this only if you're doing a major version bump. The framework works fine with `m_` prefixes.

### Estimated Effort
- Script creation: 30 min
- Manual review: 2 hours
- Testing: 2 hours
- **Total: ~5 hours**

---

## 2. Thread Force-Kill Safety

### Problem
The current implementation uses `ctypes` to force-kill threads:

```python
res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
    ctypes.c_long(thread_id),
    ctypes.py_object(SystemExit)
)
```

This is dangerous because:
- Can leave locks held (deadlocks)
- Can corrupt shared state
- Doesn't work reliably on all platforms
- Can crash the Python interpreter

### Solution
Add prominent warnings and a safer alternative:

```python
# src/modules/threaded/threaded_action.py

# At module level, add warning constant
FORCE_KILL_WARNING = """
⚠️  WARNING: Force-killing threads is dangerous and can cause:
- Deadlocks (locks held by killed thread)
- Data corruption (partial writes)
- Resource leaks (files/sockets left open)

Prefer cooperative cancellation by checking self.m_running in your action() loop.
"""

def delete(self):
    """Delete the thread and unregister from manager.
    
    Warning:
        Force-killing uses ctypes.PyThreadState_SetAsyncExc which is unsafe.
        The thread should check self.m_running periodically and exit cleanly.
        Force-kill is a last resort for unresponsive threads.
    """
    self.console_write(FORCE_KILL_WARNING, LOG_LEVEL_WARNING)
    # ... existing code
```

Also add a cooperative cancellation pattern to documentation:

```python
class MyAction(Threaded_action):
    def action(self):
        for i in range(1000):
            # Check for cancellation every iteration
            if not self.m_running:
                self.console_write("Cancelled by user", "INFO")
                return
            
            # Do work...
            self.do_step(i)
```

### Add Timeout-Based Alternative

```python
def delete(self, timeout: float = 5.0, force: bool = False):
    """Stop the thread, optionally force-killing after timeout.
    
    Args:
        timeout: Seconds to wait for graceful shutdown
        force: If True and timeout expires, force-kill the thread
    """
    self.m_running = False
    self.console_write("Stop requested, waiting for graceful shutdown...")
    
    # Wait for thread to finish
    if self.m_thread_action and self.m_thread_action.is_alive():
        self.m_thread_action.join(timeout=timeout)
        
        if self.m_thread_action.is_alive():
            if force:
                self.console_write(FORCE_KILL_WARNING, LOG_LEVEL_WARNING)
                self._force_kill()  # Existing ctypes logic
            else:
                self.console_write(
                    f"Thread did not stop within {timeout}s. "
                    "Call delete(force=True) to force-kill.",
                    LOG_LEVEL_ERROR
                )
                return False
    
    return True
```

### Estimated Effort
- Add warnings: 15 min
- Implement timeout alternative: 1 hour
- Update documentation: 30 min
- **Total: ~2 hours**

---

## 3. Secure Secret Key Generation

### Problem
Default secret key is hardcoded:

```python
DEFAULT_SECRET_KEY = "super secret key"
```

If deployed without changing this, all sessions are compromised.

### Solution

```python
# src/main.py

import os
import secrets
from pathlib import Path

# Domain-specific constants
SECRET_KEY_FILE = ".secret_key"
SECRET_KEY_ENV_VAR = "PARALAX_SECRET_KEY"

def _get_or_create_secret_key(app_path: str) -> str:
    """Get secret key from environment, file, or generate new one.
    
    Priority:
    1. Environment variable PARALAX_SECRET_KEY
    2. .secret_key file in app directory
    3. Generate new key and save to file
    
    Returns:
        Secret key string (64 hex characters)
    """
    # 1. Check environment
    env_key = os.environ.get(SECRET_KEY_ENV_VAR)
    if env_key:
        return env_key
    
    # 2. Check file
    key_file = Path(app_path) / SECRET_KEY_FILE
    if key_file.exists():
        return key_file.read_text().strip()
    
    # 3. Generate and save
    new_key = secrets.token_hex(32)
    try:
        key_file.write_text(new_key)
        key_file.chmod(0o600)  # Owner read/write only
    except OSError:
        pass  # Can't save, but key still works for this session
    
    return new_key


# In setup_app():
def setup_app(app):
    # ... existing code ...
    
    # Replace hardcoded key with secure generation
    app.config["SECRET_KEY"] = _get_or_create_secret_key(app_path)
```

Also add `.secret_key` to `.gitignore`:

```gitignore
# Secret key (auto-generated)
.secret_key
```

### Estimated Effort
- Implement function: 30 min
- Update .gitignore: 5 min
- Test: 15 min
- **Total: ~1 hour**

---

## 4. Fix CSRF Token Regeneration

### Problem
Current implementation regenerates CSRF token on every request:

```python
def generate_csrf_token():
    session['csrf_token'] = str(uuid.uuid4())  # New token every time!
    return session['csrf_token']
```

This breaks:
- Multiple browser tabs (each gets different token)
- AJAX requests (token changes between page load and request)
- Back button (form has old token)

### Solution

```python
# src/main.py - in setup_app()

@app.context_processor
def inject_csrf_token():
    def generate_csrf_token() -> str:
        """Get or create CSRF token for current session.
        
        Token persists for the session lifetime, not regenerated per-request.
        """
        if 'csrf_token' not in session:
            session['csrf_token'] = str(uuid.uuid4())
        return session['csrf_token']
    
    return dict(csrf_token=generate_csrf_token)
```

Also add token validation helper:

```python
# src/modules/utilities.py

def validate_csrf_token(form_token: str) -> bool:
    """Validate CSRF token from form against session token.
    
    Args:
        form_token: Token submitted with form
        
    Returns:
        True if valid, False otherwise
    """
    from flask import session
    session_token = session.get('csrf_token')
    if not session_token or not form_token:
        return False
    # Use constant-time comparison to prevent timing attacks
    import hmac
    return hmac.compare_digest(session_token, form_token)
```

### Estimated Effort
- Fix token generation: 15 min
- Add validation helper: 15 min
- Test multi-tab scenario: 30 min
- **Total: ~1 hour**

---

## 5. Improve Type Coverage

### Problem
Type hints are inconsistent across the codebase. Some functions have full typing, others have none.

### Solution

1. **Add py.typed marker**:
   ```bash
   touch src/py.typed
   ```

2. **Run mypy to find gaps**:
   ```bash
   pip install mypy
   mypy src/ --ignore-missing-imports
   ```

3. **Fix incrementally by module**:
   - Start with `utilities.py` (most used)
   - Then `displayer/` package
   - Then `auth/` package
   - Finally `threaded/` package

4. **Add to CI**:
   ```yaml
   # .github/workflows/lint.yml
   - name: Type check
     run: mypy src/ --ignore-missing-imports --no-error-summary
   ```

### Key Files to Type

```python
# src/modules/utilities.py - add return types
def util_post_to_json(data: dict[str, str], debug: bool = False) -> dict[str, Any]:
    ...

def form_to_nested_dict(data: dict[str, str], separator: str = ".") -> dict[str, Any]:
    ...

def get_config_or_error(
    settings_manager: 'SettingsManager',
    *config_paths: str
) -> tuple[Optional[dict[str, Any]], Optional[str]]:
    ...
```

### Estimated Effort
- Initial mypy setup: 30 min
- Fix utilities.py: 1 hour
- Fix displayer/: 2 hours
- Fix auth/: 1 hour
- Fix threaded/: 1 hour
- **Total: ~6 hours**

---

## 6. Add Rate Limiting for Login

### Problem
No protection against brute-force login attempts.

### Solution
Add simple in-memory rate limiting (no external dependencies):

```python
# src/modules/auth/rate_limiter.py
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Tuple

# Rate limit configuration
MAX_ATTEMPTS = 5
WINDOW_SECONDS = 300  # 5 minutes
LOCKOUT_SECONDS = 900  # 15 minutes after max attempts


@dataclass
class RateLimiter:
    """Simple in-memory rate limiter for login attempts."""
    
    max_attempts: int = MAX_ATTEMPTS
    window_seconds: int = WINDOW_SECONDS
    lockout_seconds: int = LOCKOUT_SECONDS
    
    # {ip_address: [(timestamp, success), ...]}
    _attempts: Dict[str, list] = field(default_factory=lambda: defaultdict(list))
    
    def check(self, identifier: str) -> Tuple[bool, str]:
        """Check if identifier (IP/username) is rate limited.
        
        Args:
            identifier: IP address or username to check
            
        Returns:
            (allowed, message) - allowed=False means rate limited
        """
        now = time.time()
        attempts = self._attempts[identifier]
        
        # Clean old attempts
        attempts[:] = [a for a in attempts if now - a[0] < self.lockout_seconds]
        
        # Check for lockout (too many failed attempts)
        failed_attempts = [a for a in attempts if not a[1]]
        if len(failed_attempts) >= self.max_attempts:
            oldest_fail = min(a[0] for a in failed_attempts)
            remaining = int(self.lockout_seconds - (now - oldest_fail))
            if remaining > 0:
                return False, f"Too many attempts. Try again in {remaining // 60} minutes."
        
        return True, ""
    
    def record_attempt(self, identifier: str, success: bool) -> None:
        """Record a login attempt.
        
        Args:
            identifier: IP address or username
            success: Whether login succeeded
        """
        self._attempts[identifier].append((time.time(), success))
        
        # Clear history on successful login
        if success:
            self._attempts[identifier] = []


# Global instance
login_limiter = RateLimiter()
```

Usage in login route:

```python
# src/pages/common.py (or wherever login is)

from ..modules.auth.rate_limiter import login_limiter

@bp.route('/login', methods=['POST'])
def do_login():
    ip = request.remote_addr
    
    # Check rate limit
    allowed, message = login_limiter.check(ip)
    if not allowed:
        flash(message, "error")
        return redirect(url_for('common.login'))
    
    # Attempt login
    username = request.form.get('username')
    password = request.form.get('password')
    
    if auth_manager.verify_password(username, password):
        login_limiter.record_attempt(ip, success=True)
        session['user'] = username
        return redirect(url_for('index'))
    else:
        login_limiter.record_attempt(ip, success=False)
        flash("Invalid credentials", "error")
        return redirect(url_for('common.login'))
```

### Estimated Effort
- Implement RateLimiter: 45 min
- Integrate with login: 30 min
- Test: 30 min
- **Total: ~2 hours**

---

## Summary

| Item | Priority | Effort | Impact |
|------|----------|--------|--------|
| Hungarian Notation | Low | 5h | Cosmetic |
| Thread Force-Kill Safety | Medium | 2h | Stability |
| Secure Secret Key | **High** | 1h | Security |
| CSRF Token Fix | **High** | 1h | Security |
| Type Coverage | Medium | 6h | Maintainability |
| Rate Limiting | **High** | 2h | Security |

**Recommended order**: 3 → 4 → 6 → 2 → 5 → 1

Total for security fixes (3, 4, 6): **~4 hours**
Total for all items: **~17 hours**

# AI Code Review & Quality Improvement Guide

## Purpose
This document provides instructions for AI-assisted code review and improvement. Feed this file along with any source file to get consistent, high-quality corrections.

---

## 🔧 Pre-Flight Checks

Before making changes:
1. **Read the full file** to understand context
2. **Check for existing tests** in `tests/` matching the module name
3. **Identify the module's role** (page, utility, core system, etc.)
4. **Note framework patterns** from `.github/copilot-instructions.md` if available

---

## 📋 Issue Categories & Fixes

### 1. Import Organization (PRIORITY: HIGH)

**Problem**: Imports scattered throughout the code, not at top of file.

**Fix**:
```python
# Standard library imports (alphabetical)
import os
import sys
from typing import Optional, List, Dict

# Third-party imports (alphabetical)
from flask import Blueprint, request, render_template

# Local imports (alphabetical)
from modules.displayer import Displayer, DisplayerLayout
from modules.utilities import util_post_to_json
```

**Rules**:
- ALL imports at file top (after module docstring)
- Group: stdlib → third-party → local
- Alphabetical within groups
- Use `from x import y` when importing specific items
- Avoid `from x import *`

---

### 2. Hardcoded & Magic Strings (PRIORITY: HIGH)

**Problem**: Strings like `"admin"`, `"error"`, `"/api/v1"` scattered in code.

**Fix**: Extract to constants at module level or dedicated constants file.

```python
# BAD
if user.role == "admin":
    ...

# GOOD
ROLE_ADMIN = "admin"
ROLE_USER = "user"

if user.role == ROLE_ADMIN:
    ...
```

**Common patterns to extract**:
- Route prefixes
- Permission names
- Config keys
- Error messages
- Status values
- Template names

---

### 3. Dead Code Removal (PRIORITY: MEDIUM)

**Identify**:
- Commented-out code blocks (>3 lines)
- Unused imports (use IDE warnings)
- Unreachable code after `return`/`raise`
- Functions never called (search codebase first!)
- Variables assigned but never used

**Action**: Remove completely. Git preserves history.

---

### 4. Logging Improvements (PRIORITY: MEDIUM)

**Problem**: Excessive INFO/WARNING logs, missing DEBUG logs.

**Fix**:
```python
import logging
logger = logging.getLogger(__name__)

# Use appropriate levels:
logger.debug("Processing item %s", item_id)      # Development details
logger.info("User %s logged in", user)           # Normal operations
logger.warning("Config missing, using default")  # Recoverable issues
logger.error("Failed to save: %s", e)            # Errors
logger.exception("Unexpected error")             # With traceback
```

**Rules**:
- Demote verbose INFO → DEBUG
- Use lazy formatting: `logger.info("x=%s", x)` not `logger.info(f"x={x}")`
- Add context: who, what, why
- No print() for logging

---

### 5. Documentation (PRIORITY: MEDIUM)

**Required**:
```python
"""Module docstring: one-line summary.

Extended description if needed.
"""

def function_name(param1: str, param2: int = 0) -> bool:
    """One-line summary of what function does.
    
    Args:
        param1: Description of param1.
        param2: Description with default behavior.
    
    Returns:
        Description of return value.
    
    Raises:
        ValueError: When param1 is empty.
    """
```

**Skip docstrings for**:
- Private methods (`_helper()`) unless complex
- Simple property getters
- Obvious one-liners

---

### 6. Code Bloat Reduction (PRIORITY: MEDIUM)

**Patterns to simplify**:

```python
# BAD: Verbose conditionals
if condition == True:
if len(my_list) > 0:
if x is not None and x != "":

# GOOD
if condition:
if my_list:
if x:

# BAD: Unnecessary else after return
if error:
    return None
else:
    return value

# GOOD
if error:
    return None
return value

# BAD: Manual iteration for dict/list building
result = []
for item in items:
    result.append(transform(item))

# GOOD
result = [transform(item) for item in items]
```

---

### 7. Dependency Injection Pattern (PRIORITY: LOW-MEDIUM)

**When to apply**: Classes with hardcoded dependencies.

```python
# BAD
class ReportGenerator:
    def __init__(self):
        self.db = DatabaseConnection()  # Hardcoded
        self.mailer = EmailService()    # Hardcoded

# GOOD
class ReportGenerator:
    def __init__(self, db: DatabaseConnection, mailer: EmailService):
        self.db = db
        self.mailer = mailer

# Or with defaults
class ReportGenerator:
    def __init__(self, db: DatabaseConnection = None, mailer: EmailService = None):
        self.db = db or DatabaseConnection()
        self.mailer = mailer or EmailService()
```

**Benefits**: Testable, flexible, explicit dependencies.

---

### 8. Design Pattern Opportunities (PRIORITY: LOW)

**Look for**:

| Smell | Pattern |
|-------|---------|
| Multiple `if/elif` on type | Strategy |
| Complex object creation | Factory/Builder |
| Global state access | Singleton (careful!) |
| Repeated try/except | Context Manager |
| Callback chains | Observer |
| Conditional behavior | State |

**Only refactor if**:
- Code is already being modified
- Pattern significantly improves readability
- No over-engineering

---

## 🧪 Testing Requirements

### When to Create/Run Tests

**MUST create tests when**:
- Adding new public function/method
- Fixing a bug (regression test)
- Refactoring complex logic

**MUST run tests when**:
- Any code modification
- Run only relevant tests: `pytest tests/test_<module>.py -v`

### Test Structure

```python
"""Tests for module_name."""
import pytest
from src.modules.module_name import TargetClass

class TestTargetClass:
    """Tests for TargetClass."""
    
    def test_method_happy_path(self):
        """Test normal operation."""
        obj = TargetClass()
        result = obj.method("valid_input")
        assert result == expected
    
    def test_method_edge_case(self):
        """Test boundary condition."""
        ...
    
    def test_method_error_handling(self):
        """Test error cases."""
        with pytest.raises(ValueError):
            obj.method(None)
```

### Test Naming Convention
- File: `test_<module_name>.py`
- Class: `Test<ClassName>`
- Method: `test_<method>_<scenario>`

---

## 🚫 DO NOT

1. **Change public API signatures** without explicit request
2. **Remove code that might be used** elsewhere (search first!)
3. **Add dependencies** not already in project
4. **Over-engineer** simple code
5. **Ignore framework patterns** (check copilot-instructions.md)
6. **Create .md summaries** of changes (unless requested)

---

## ✅ Workflow

1. **Analyze**: Read file, identify issues by category
2. **Prioritize**: HIGH → MEDIUM → LOW
3. **Plan**: List changes to make
4. **Implement**: Make changes using edit tools
5. **Validate**: Run `get_errors` on modified file
6. **Test**: 
   - Find existing tests: `tests/test_<module>.py`
   - Run: `pytest tests/test_<module>.py -v`
   - Create tests if missing for modified code
7. **Report**: Brief summary (3-5 lines max)

---

## 📝 Change Report Format

After modifications, provide:

```
## Changes Made
- [IMPORTS] Reorganized imports to top of file
- [CONSTANTS] Extracted 3 magic strings to constants
- [LOGGING] Demoted 5 verbose logs to DEBUG
- [DEAD CODE] Removed unused function `old_helper()`

## Tests
- Ran: tests/test_module.py (5 passed)
- Added: test_new_function_edge_case
```

---

## 🔍 Quick Reference: Common Issues

| Issue | Search Pattern | Fix |
|-------|---------------|-----|
| Mid-file import | `^import\|^from` not at top | Move to top |
| Magic string | Quoted strings in logic | Extract constant |
| Print debugging | `print(` | Use logger |
| Bare except | `except:` | Specify exception |
| Mutable default | `def f(x=[])` | Use `None` + check |
| Type comparison | `type(x) ==` | Use `isinstance()` |
| String concat in loop | `s += "x"` | Use list + join |

---

## Framework-Specific (ParalaX Web Framework)

### Mandatory Patterns
```python
# Form handling - ALWAYS use
from modules.utilities import util_post_to_json
data = util_post_to_json(request.form.to_dict())

# Config access - ALWAYS use
from modules.utilities import get_config_or_error
configs, error = get_config_or_error(mgr, "key1", "key2")
if error:
    return error

# Auth decorator - NEVER reimplement
from src.modules.auth import require_permission
@require_permission("Module", "action")
```

### File Locations
- Pages: `src/pages/` or `website/pages/`
- Modules: `src/modules/`
- Tests: `tests/test_*.py`
- Config: Check `site_conf.py` for feature flags

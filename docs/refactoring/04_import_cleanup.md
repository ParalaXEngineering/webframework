# Refactoring: Eliminate try/except ImportError Pattern

## Problem

The codebase has ~50+ occurrences of this pattern:

```python
try:
    from .modules import scheduler
except ImportError:
    from modules import scheduler
```

This exists because the framework needs to work:
1. As an installed package (`pip install -e .`)
2. When running tests with different working directories
3. In the Manual_Webapp submodule context

## Root Cause

The package structure isn't consistently used. Sometimes code runs as:
- `python src/main.py` (relative imports fail)
- `python -m src.main` (relative imports work)
- Via pytest with conftest adding `src/` to path

## Solution

### Option A: Always Use Absolute Imports (Recommended)

1. **Ensure package is installed in editable mode**:
   ```bash
   pip install -e .
   ```

2. **Use absolute imports everywhere**:
   ```python
   # Instead of relative imports with fallback
   from src.modules import scheduler
   from src.modules.auth import auth_manager
   ```

3. **For website code (Manual_Webapp)**:
   ```python
   # Website imports framework
   from submodules.framework.src.modules import displayer
   
   # Or if installed as package
   from paralax_webframework.modules import displayer
   ```

### Option B: Smart Import Helper

Create a helper that resolves imports based on context:

```python
# src/modules/_imports.py
import sys
from importlib import import_module
from typing import Any


def framework_import(module_path: str) -> Any:
    """
    Import a framework module regardless of execution context.
    
    Args:
        module_path: Dot-separated path relative to src/modules/
        
    Returns:
        Imported module
        
    Example:
        >>> scheduler = framework_import("scheduler")
        >>> auth_manager = framework_import("auth.auth_manager")
    """
    # Try paths in order of preference
    paths_to_try = [
        f"src.modules.{module_path}",
        f"modules.{module_path}",
        f"submodules.framework.src.modules.{module_path}",
    ]
    
    for path in paths_to_try:
        try:
            return import_module(path)
        except ImportError:
            continue
    
    raise ImportError(f"Could not import {module_path} from any known path")
```

Usage:
```python
from ._imports import framework_import

scheduler = framework_import("scheduler")
auth = framework_import("auth")
```

### Option C: Conditional Import Based on Context (Current State - Not Recommended)

This is what we have now. It works but is verbose and error-prone.

## Recommended Approach

**Go with Option A** - it's the cleanest and most Pythonic.

### Implementation Steps

1. **Verify pyproject.toml is correct** ✓ (already good)

2. **Update conftest.py to install package**:
   ```python
   # tests/conftest.py
   import subprocess
   import sys
   
   @pytest.fixture(scope="session", autouse=True)
   def install_package():
       """Ensure package is installed before tests."""
       subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", "."])
   ```

3. **Create a migration script**:
   ```python
   # scripts/fix_imports.py
   import re
   from pathlib import Path
   
   PATTERN = re.compile(
       r'try:\s*\n\s*from \.(\S+) import (\S+)\s*\n'
       r'except ImportError:\s*\n\s*from (\S+) import (\S+)',
       re.MULTILINE
   )
   
   REPLACEMENT = r'from src.\1 import \2'
   
   def fix_file(path: Path):
       content = path.read_text()
       new_content = PATTERN.sub(REPLACEMENT, content)
       if new_content != content:
           path.write_text(new_content)
           print(f"Fixed: {path}")
   
   if __name__ == "__main__":
       for py_file in Path("src").rglob("*.py"):
           fix_file(py_file)
   ```

4. **Run and test**:
   ```bash
   python scripts/fix_imports.py
   pytest tests/ -v
   ```

## Files with try/except ImportError

Run to find all occurrences:
```bash
grep -r "except ImportError" src/ --include="*.py" | wc -l
```

Key files to update:
- [ ] `src/main.py` - 10+ occurrences
- [ ] `src/modules/site_conf.py` - 3 occurrences
- [ ] `src/modules/displayer/displayer.py` - 2 occurrences
- [ ] `src/modules/threaded/threaded_action.py` - 3 occurrences
- [ ] `src/modules/i18n/__init__.py` - 2 occurrences
- [ ] `src/modules/utilities.py` - 1 occurrence
- [ ] `src/pages/*.py` - Various

## Risks

- **Breaking Manual_Webapp**: Need to ensure website code can still import
- **Breaking CI/CD**: Tests need `pip install -e .` first
- **Breaking standalone scripts**: Any script running individual files

## Mitigation

1. **Add to CI/CD**:
   ```yaml
   - name: Install package
     run: pip install -e .
   ```

2. **Update documentation** to require `pip install -e .`

3. **Add check in conftest.py** to warn if not installed

## Estimated Effort

- Create migration script: 30 min
- Run and fix edge cases: 1 hour
- Test thoroughly: 1 hour
- Update documentation: 30 min

**Total: ~3 hours**

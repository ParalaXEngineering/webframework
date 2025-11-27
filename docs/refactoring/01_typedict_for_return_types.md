# Refactoring: TypedDict for Return Types

**Priority:** Low (Quality of Life improvement)  
**Effort:** Medium (Framework-wide change)  
**Impact:** Developer Experience, Type Safety, IDE Support

## Problem

Currently, the framework returns dictionaries with string keys throughout the codebase. This approach works but has limitations:

- No IDE autocomplete for dictionary keys
- Typos only caught at runtime
- No static type checking
- Documentation exists only in docstrings
- Refactoring is error-prone (must search for string literals)

**Example from `file_manager/manager.py`:**
```python
def get_file_versions(self, group_id: str, filename: str) -> List[Dict]:
    versions = []
    for idx, version in enumerate(all_versions, start=1):
        versions.append({
            'id': version.id,
            'version_number': idx,
            'filename': version.filename,
            'storage_path': version.storage_path,
            # ... 8 more string keys
        })
    return versions
```

## Proposed Solution

Use `TypedDict` to add type hints to dictionary return types **without changing runtime behavior**.

### Why TypedDict (not Dataclasses)?

- **Zero refactoring**: Still returns plain dictionaries
- **JSON-ready**: No conversion needed for Flask `jsonify()`
- **API compatibility**: Existing user code continues to work
- **Type safety**: IDE and type checkers catch errors
- **No runtime overhead**: Pure type hints, no new objects created

### Implementation Pattern

```python
from typing import TypedDict, List, Optional

class FileVersionResponse(TypedDict):
    """Response structure for file version metadata."""
    id: int
    version_number: int
    filename: str
    storage_path: str
    file_size: int
    mime_type: str
    checksum: str
    uploaded_at: str
    uploaded_by: str
    is_current: bool
    tags: List[str]

def get_file_versions(self, group_id: str, filename: str) -> List[FileVersionResponse]:
    """Get all versions of a file.
    
    Returns:
        List of file version metadata (typed dictionaries)
    """
    versions: List[FileVersionResponse] = []
    for idx, version in enumerate(all_versions, start=1):
        versions.append({
            'id': version.id,
            'version_number': idx,
            'filename': version.filename,
            'storage_path': version.storage_path,
            'file_size': version.file_size,
            'mime_type': version.mime_type,
            'checksum': version.checksum,
            'uploaded_at': version.uploaded_at.isoformat() + "Z",
            'uploaded_by': version.uploaded_by,
            'is_current': version.is_current,
            'tags': [tag.tag_name for tag in version.tags]
        })
    return versions
```

## Scope

This pattern should be applied to all framework modules that return structured data:

### High-Priority Modules
- `file_manager/manager.py` - File metadata responses
- `auth/` - User, role, permission structures
- `threaded/` - Task status, progress responses
- `settings/` - Configuration structures
- `displayer/` - Layout, item metadata (if returned as dicts)

### Module Structure
Create a `types.py` in each module to centralize TypedDict definitions:

```
src/modules/file_manager/
├── __init__.py
├── manager.py
├── models.py
├── storage.py
└── types.py          # ← New file with TypedDict definitions
```

## Benefits

1. **IDE Support**: Autocomplete for dictionary keys
2. **Type Checking**: `mypy` or Pylance catches typos/mistakes
3. **Self-Documenting**: Type hints show expected structure
4. **Refactoring Safety**: Renaming a TypedDict key shows all usages
5. **No Breaking Changes**: User code unaffected (still receives dicts)

## Migration Strategy

1. **Phase 1**: Create `types.py` files in core modules
2. **Phase 2**: Add TypedDict definitions for existing return types
3. **Phase 3**: Update function signatures (return types only)
4. **Phase 4**: Enable type checking in CI/CD (optional)

## Compatibility

- **Python Version**: 3.7+ (framework already requires this)
- **Runtime Impact**: None (pure type hints)
- **Breaking Changes**: None (dictionaries remain dictionaries)
- **User Impact**: Positive (better IDE experience for framework users)

## Notes

- TypedDict is for **output/API responses** (data transfer)
- Use **Dataclasses** for internal business logic objects that need methods
- This is a **gradual migration** - can be done module-by-module
- Consider enabling `mypy` or Pylance strict mode after migration

## References

- [PEP 589 - TypedDict](https://peps.python.org/pep-0589/)
- [Python typing documentation](https://docs.python.org/3/library/typing.html#typing.TypedDict)

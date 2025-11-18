# File Manager - AI Continuation Guide

## COMPLETED ✅
- **HashFS-only mode** (2025-11-18): Removed dual storage, all code uses HashFS content-addressable storage
- Fixed thumbnail generation (pass `original_filename` to get extension)
- Fixed Windows long path issue (BytesIO wrapper in download routes)
- All 30 tests passing
- Reference counting deletion works

## ARCHITECTURE

**Files**:
- `src/modules/file_manager.py` - Core FileManager class
- `src/modules/file_manager_models.py` - SQLAlchemy models (FileGroup, FileVersion, FileTag)
- `src/modules/file_storage.py` - HashFS wrapper
- `src/pages/file_handler.py` - Routes (upload/download/delete)
- `src/pages/file_manager_admin.py` - Admin UI

**Storage**: HashFS only (content-addressable by SHA256, automatic deduplication)
**Database**: SQLite `.file_metadata.db`
**Key Logic**: Files with same `group_id` + `filename` = versions. Latest has `is_current=True`

## REMAINING TASKS

### Task 2: Tag/Category Validation (HIGH)
**Goal**: Enforce predefined tags/categories from settings

**Actions**:
1. Add validation in `file_manager.py::upload_file()`:
   ```python
   valid_tags = self.settings.get_setting("file_storage.tags")["value"]
   if tags and any(t not in valid_tags for t in tags):
       raise ValueError(f"Invalid tags. Valid: {valid_tags}")
   ```
2. Add category validation similar to tags
3. Create `DisplayerItemInputTags` multiselect component (or use existing DisplayerItemSelect with multiple=True)
4. Update upload forms to use dropdowns instead of text input
5. Add tests: `TestTagValidation`, `TestCategoryValidation`

### Task 3: Code Reorganization (MEDIUM)
**Goal**: Move to subfolder, merge blueprints

**Actions**:
1. Create `src/modules/file_manager/` folder
2. Move files:
   - `file_manager.py` → `file_manager/manager.py`
   - `file_manager_models.py` → `file_manager/models.py`
   - `file_storage.py` → `file_manager/storage.py`
   - Create `file_manager/__init__.py` exporting FileManager
3. Merge blueprints: `file_handler.py` + `file_manager_admin.py` → `pages/file_manager.py`
4. Update all imports throughout codebase

### Task 4: Orphaned Record Detection (HIGH)
**Goal**: Show file integrity status in admin table

**Actions**:
1. Add `verify_file_integrity(file_id)` method:
   ```python
   def verify_file_integrity(self, file_id: int) -> tuple[bool, str]:
       fv = self.get_file_by_id(file_id)
       path = self.storage.get(fv.storage_path)
       if not path.exists(): return False, "Missing"
       checksum = self._calculate_checksum(path)
       if checksum != fv.checksum: return False, "Checksum mismatch"
       return True, "OK"
   ```
2. Add status column in admin table displaying: ✓ OK | ⚠️ Missing | ❌ Checksum Error
3. User deletes orphaned records manually (no auto-cleanup)

### Task 5: Test Coverage (MEDIUM)
**Missing tests**:
- Tag validation (reject invalid tags)
- Category validation (reject invalid categories)
- Orphaned records detection
- Checksum mismatch detection
- Thumbnail generation failures
- Windows long path handling

### Task 6: Database Constraints (LOW)
**Add**:
- UNIQUE constraint on (group_id, filename, version)
- Index on checksum for deduplication queries
- CHECK constraint: only one `is_current=True` per (group_id, filename)

### Task 7: Admin Code Quality (LOW)
**Fix**:
- Use DisplayerItems consistently (remove direct HTML strings)
- Add docstrings to all functions
- Refactor JavaScript to separate file

## KEY FUNCTIONS

```python
# file_manager.py
upload_file(file_obj, category?, group_id?, tags?) -> metadata_dict
delete_file(file_id) -> bool  # Uses reference counting
get_file_versions(group_id, filename) -> List[dict]
restore_version(file_id, target_version_id) -> FileVersion
search_by_tags(tags, match_all=False) -> List[FileVersion]
verify_file_integrity(file_id) -> tuple[bool, str]  # ADD THIS

# file_storage.py
store(file_stream, original_filename) -> dict  # Returns checksum, storage_path, is_duplicate
get(storage_path) -> Path
exists(checksum) -> bool
```

## SETTINGS

```python
# default_configs.py - FILE_STORAGE_CONFIG
"file_storage": {
    "hashfs_path": "resources/hashfs_storage",  # ONLY path now
    "max_file_size_mb": 50,
    "allowed_extensions": [".pdf", ".jpg", ".png", ...],
    "categories": ["general", "documents", "images"],  # Enforce these
    "tags": ["invoice", "contract", "demo", "test"],   # Enforce these
    "generate_thumbnails": True,
    "thumbnail_sizes": ["150x150", "300x300"],
}
```

## CRITICAL NOTES
- **Windows long paths**: Use BytesIO wrapper when sending files (already fixed in download routes)
- **Thumbnail generation**: Must pass `original_filename` to `_generate_thumbnails()` (HashFS paths have no extension)
- **Reference counting**: Physical file deleted only when no DB records reference its checksum
- **Deduplication**: Same content uploaded twice = 1 physical file, 2 DB records with same checksum
- **Tests**: Run `pytest tests/unit/test_file_manager.py -v` (30 tests, all passing)

## IMPLEMENTATION ORDER
1. Task 2 (tag validation) - most user-facing
2. Task 4 (orphaned records) - integrity critical
3. Task 3 (code reorg) - structural
4. Task 5 (tests) - validation
5. Tasks 6-7 (polish)

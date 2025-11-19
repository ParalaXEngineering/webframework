# File Manager Blueprint Merge Analysis

## Current State

### Two Blueprints:
1. **`file_handler.py`** - API routes at `/files`
2. **`file_manager_admin.py`** - Admin UI at `/file_manager`

### Routes Breakdown:

#### file_handler.py (API):
- `POST /files/upload` - Upload file
- `GET /files/download/<path>` - Download by path
- `GET /files/download/by_id/<id>` - Download by ID
- `DELETE|POST /files/delete/<id>` - Delete file
- `GET /files/list` - List files (JSON)
- `GET /files/versions/<group_id>/<filename>` - **Version history UI** ⚠️
- `POST /files/restore` - Restore version (AJAX)
- `POST /files/update_group_id` - Update group ID (AJAX)

#### file_manager_admin.py (UI):
- `GET /file_manager/` - Main admin page (file list)
- `GET|POST /file_manager/upload_form` - Upload form UI
- `GET|POST /file_manager/edit/<id>` - Edit metadata UI
- `GET|POST /file_manager/confirm-delete` - Delete confirmation UI

## Issues with Current Split

### 1. Mixed Concerns
- `file_handler.py` has `/versions/<group_id>/<filename>` which is a **UI route**, not an API
- Admin UI should be unified

### 2. Inconsistent URL Patterns
- API: `/files/*`
- UI: `/file_manager/*`
- Users confused about which to use

### 3. Duplicate Initialization
Both blueprints need `file_manager` instance injected:
```python
file_handler.file_manager = file_manager_instance
file_manager_admin.file_manager = file_manager_instance
```

## Proposed Merge Structure

### Single Blueprint: `/files`

```python
# All routes under /files

# === API Routes (JSON responses) ===
POST   /files/upload              # Upload file (multipart)
GET    /files/download/<path>     # Download by hashfs path
GET    /files/<int:id>/download   # Download by ID
DELETE /files/<int:id>            # Delete file
GET    /files/                    # List files (JSON)
POST   /files/<int:id>/restore    # Restore version
PATCH  /files/<int:id>/group      # Update group_id

# === UI Routes (HTML pages) ===
GET    /files/admin                      # Main admin page
GET    /files/admin/upload               # Upload form
POST   /files/admin/upload               # Process upload
GET    /files/admin/<int:id>/edit        # Edit metadata
POST   /files/admin/<int:id>/edit        # Save metadata
GET    /files/admin/<int:id>/delete      # Confirm delete
POST   /files/admin/<int:id>/delete      # Execute delete
GET    /files/admin/versions/<group_id>/<filename>  # Version history
```

## Migration Impact

### Files to Modify:
1. **Merge blueprints**: Create new `src/pages/file_manager.py`
2. **Update main.py**: Register single blueprint
3. **Update site_conf.py**: Simplify sidebar registration
4. **Update templates**: Change all `url_for('file_manager_admin.*')` to `url_for('files.*')`
5. **Update tests**: Change endpoint names

### Estimated Changes:
- **Create**: 1 new file (~800 lines - merged)
- **Delete**: 2 old files
- **Modify**: ~15 files (imports, url_for calls, tests)
- **Risk**: Medium (URL changes affect existing bookmarks/links)

## Recommendation

**NOT RECOMMENDED FOR IMMEDIATE FIX** because:

1. **Large scope**: Touches 15+ files
2. **Breaking change**: Existing URLs will break
3. **Testing overhead**: Need to verify all routes still work
4. **Not blocking**: Current split works, just inelegant

**BETTER APPROACH**: Keep as Task 3 for future cleanup sprint.

## What CAN Be Done Now (Low Risk):

1. **Move version history route** from `file_handler.py` to `file_manager_admin.py`
   - Changes: 1 file, ~80 lines moved
   - Risk: Low (just moving within same codebase)
   
2. **Standardize naming**: Rename `file_manager_admin` to `file_admin` internally
   - Changes: 3 files (imports)
   - Risk: Very low

## Conclusion

**Skip the merge for now**. Focus on:
- Bug fixes (empty group_id versioning)
- Type safety (Pylance errors)
- Performance (N+1 integrity checks)
- JavaScript removal (replace with page refresh)

The blueprint structure works functionally, merge is purely cosmetic/organizational.

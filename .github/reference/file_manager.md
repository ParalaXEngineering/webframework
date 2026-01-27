# File Manager

## Purpose
Secure file upload/download with content-addressable storage (hashfs), versioning, thumbnails, and tagging. Prevents duplicates via SHA256 deduplication.

## Core Components
- `src/modules/file_manager/manager.py` - FileManager class, upload/download logic
- `src/modules/file_manager/storage.py` - ContentAddressableStorage (hashfs wrapper)
- `src/modules/file_manager/models.py` - SQLAlchemy models (FileGroup, FileVersion, FileTag)
- `resources/hashfs_storage/` - Physical file storage (content-addressed)
- `resources/.thumbs/` - Generated thumbnails (150x150, 300x300)
- `website/settings/.file_metadata.db` - SQLite database for metadata

## Critical Patterns

### File Upload (MANDATORY)
```python
from modules.file_manager import file_manager
from flask import request

file_obj = request.files['file']  # FileStorage object
metadata = file_manager.upload_file(
    file_obj,
    category="documents",        # Optional, validated against config
    group_id="invoice_2024",     # None = standalone (no versioning)
    tags=["invoice", "important"],  # Optional, validated
    uploaded_by=session.get('user', 'GUEST')
)
# Returns: {"id": 123, "path": "ab/cd/abcd1234...", "checksum": "sha256...",
#           "thumb_150x150": ".thumbs/150x150/...", ...}
```

### File Download
```python
from flask import send_file

file_version = file_manager.get_file_by_id(file_id)
file_path = file_manager.get_file_path(file_version.storage_path)
return send_file(file_path, as_attachment=True, download_name=file_version.filename)
```

### Versioning (group_id Required)
```python
# Upload first version (group_id enables versioning)
v1 = file_manager.upload_file(file, group_id="contract_001")  # version=1, is_current=True

# Upload new version (same filename, same group_id)
v2 = file_manager.upload_file(file, group_id="contract_001")  # version=2, is_current=True (v1 now False)

# List versions
versions = file_manager.get_file_versions("contract_001", "contract.pdf")
# Returns: [{"version_number": 1, "is_current": False, ...}, {"version_number": 2, "is_current": True, ...}]

# Restore old version (creates new version as copy)
restored = file_manager.restore_version(current_id, old_version_id)
```

### Tag Search
```python
# Files with ANY tag
files = file_manager.search_by_tags(["invoice", "important"], match_all=False)

# Files with ALL tags
files = file_manager.search_by_tags(["invoice", "paid"], match_all=True)
```

### List Files
```python
# All current files
files = file_manager.list_files_from_db()

# Filter by group
files = file_manager.list_files_from_db(group_id="invoice_2024")

# Filter by tag
files = file_manager.list_files_from_db(tag="important")

# Limit results
files = file_manager.list_files_from_db(limit=50)
```

### Integrity Check
```python
# Single file
is_valid, status = file_manager.verify_file_integrity(file_id)
# Returns: (True, "OK") or (False, "Missing") or (False, "Checksum mismatch")

# Bulk check (efficient)
results = file_manager.verify_files_bulk([id1, id2, id3])
# Returns: {id1: (True, "OK"), id2: (False, "Missing"), ...}
```

## API Quick Reference
```python
class FileManager:
    def __init__(settings_manager)
    
    # Upload/Download
    def upload_file(file_obj: FileStorage, category: str = None, 
                   group_id: str = None, tags: List[str] = None,
                   uploaded_by: str = None) -> Dict[str, Any]
    def get_file_path(storage_path: str) -> Path
    def delete_file(file_id: int) -> bool
    
    # Metadata
    def get_file_by_id(file_id: int) -> Optional[FileVersion]
    def get_current_file(group_id: str, filename: str) -> Optional[FileVersion]
    def get_file_versions(group_id: str, filename: str) -> List[Dict]
    
    # Versioning
    def restore_version(file_id: int, target_version_id: int) -> FileVersion
    
    # Search
    def search_by_tags(tags: List[str], match_all: bool = False) -> List[FileVersion]
    def list_files_from_db(group_id: str = None, tag: str = None, 
                          limit: int = None) -> List[Dict]
    
    # Integrity
    def verify_file_integrity(file_id: int) -> Tuple[bool, str]
    def verify_files_bulk(file_ids: List[int]) -> Dict[int, Tuple[bool, str]]
    
    # Config access
    def get_categories() -> List[str]
    def get_group_ids() -> List[str]
    def get_tags() -> List[str]

# Settings (in config.json)
"file_storage": {
    "hashfs_path": "resources/hashfs_storage",
    "max_file_size_mb": 50,
    "allowed_extensions": [".pdf", ".jpg", ".png", ...],
    "categories": ["general", "documents", "images", ...],
    "group_ids": ["invoice_group", "contract_group", ...],
    "tags": ["invoice", "important", "draft", ...],
    "generate_thumbnails": true,
    "thumbnail_sizes": ["150x150", "300x300"],
    "image_quality": 85,
    "strip_exif": true
}
```

## Common Pitfalls
1. **Form data** - Use `request.files['file']` not `request.form['file']`
2. **Versioning** - Requires non-null `group_id`; null = standalone file (no versions)
3. **Thumbnails** - Only images (.jpg, .png, .gif, etc.) and PDFs (requires PyMuPDF)
4. **Deduplication** - Same content = same file (checksum-based), only metadata differs
5. **Storage path** - Use `get_file_path()` not direct path (hashfs uses subdirs)
6. **Delete** - Reference-counted; physical file deleted only when no other versions reference it
7. **Category/tag validation** - Raises ValueError if not in config lists
8. **Extension check** - Uses `allowed_extensions` from config, case-insensitive
9. **Filename sanitization** - Auto-sanitizes with `secure_filename()`, removes specials
10. **Original filename** - Preserved in database but not in hashfs (content-addressed)

## Integration Points
- **Settings**: Reads `file_storage.*` config via SettingsManager
- **Displayer**: DisplayerItemFileUpload/DisplayerItemFileDisplay for UI
- **Auth**: Permission checks via `@auth_manager.require_permission("FileManager", "view")`
- **Database**: SQLAlchemy with SQLite at `website/settings/.file_metadata.db`
- **Thumbnails**: PIL (Pillow) for images, PyMuPDF (fitz) for PDFs

## Files
- `manager.py` - Main FileManager class, upload/download/versioning logic
- `storage.py` - ContentAddressableStorage wrapper around hashfs
- `models.py` - FileGroup, FileVersion, FileTag (SQLAlchemy with Continuum versioning)
- `resources/hashfs_storage/` - Content-addressed file storage (ab/cd/abcd1234...)
- `resources/.thumbs/{size}/` - Thumbnail storage (separate from hashfs)
- `website/settings/.file_metadata.db` - SQLite database for file metadata

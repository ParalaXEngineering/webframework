# File Manager Implementation - ParalaX Web Framework

## Status: Phase 1 & 2 Complete ✓ | Phase 3 (Versioning & Tagging) - Pending

## Overview
Complete file upload/download management system for the ParalaX Web Framework. This is a **framework-level feature** enabled via `enable_file_manager()`, following existing patterns for optional features.

## Current Implementation (Phases 1 & 2)
The file manager is **implemented and functional** with:
- ✅ Secure file upload/download with validation
- ✅ Thumbnail generation (images & PDFs)
- ✅ Soft-delete (trash folder)
- ✅ Category-based organization
- ✅ Settings-driven configuration
- ✅ Permission-based access control
- ✅ Admin UI and demo pages
- ✅ Unit test suite

**Key Files:**
- `src/modules/file_manager.py` - Core FileManager class
- `src/pages/file_handler.py` - Upload/download/delete routes
- `src/pages/file_manager_admin.py` - Admin UI
- `tests/demo_support/demo_file_manager.py` - Demo pages
- `tests/test_file_manager.py` - Unit tests
- `src/modules/default_configs.py` - FILE_STORAGE_CONFIG

## Context
The framework uses a 3-tier architecture where:
- Framework code lives in `submodules/framework/` (or `src/` for direct usage)
- User website code lives in `website/`
- Framework provides reusable modules via `Site_conf.enable_*()` methods

Relevant components:
- **Displayer Items**: `DisplayerItemInputFile`, `DisplayerItemInputImage`, `DisplayerItemFile`, `DisplayerItemImage` in `src/modules/displayer/items.py`
- **Settings system**: Configuration via `settings/SettingsManager` with auto-merging from `default_configs.py`
- **Database location**: Settings stored in `config.json` (path set by SettingsManager initialization)

## Phase 3: File Versioning & Tagging System (PLANNED)

### Requirements Summary
Based on user requirements from 2025-11-17, the following enhancements are needed:

### 1. File Versioning with Group ID System

**Problem**: Users may upload files with the same name in the same category but in different contexts.

**Solution**: Implement a **group_id-based versioning system**:

- **Group ID**: Unique identifier for a logical file group (replaces simple category)
  - When uploading to the same `group_id` with same filename → create new version
  - Files in different `group_id`s can have identical names without collision
  - Group IDs can be auto-generated or manually specified

- **Version Management**:
  - When file with same name uploaded to same `group_id` → create new revision
  - Versions stored internally as: `filename_v1.ext`, `filename_v2.ext`, etc.
  - Database tracks all versions with metadata
  - UI shows user-friendly names (original filename) with version info

- **Restore Behavior** (Answer to Q5):
  - Restoring an old version creates a **new revision** (copy)
  - Example: v1→v2→v3, restore v1 → creates v4 as copy of v1
  - Database maintains link to source version
  - Original versions remain unchanged (audit trail)

## Recommended Technology Stack for Phase 3

### Use Existing Framework Infrastructure + Lightweight Additions

**Leverage what you already have:**
- ✅ **SQLAlchemy** (already used in framework for auth, bug tracker)
- ✅ **Existing FileManager** for upload/validation/security
- ➕ **SQLAlchemy-Continuum** for automatic versioning (~200 lines of code saved)
- ➕ **hashfs** (optional) for content-addressable storage and deduplication

### Why This Approach?

1. **SQLAlchemy is already integrated** - Used throughout the framework
2. **SQLAlchemy-Continuum** provides automatic versioning with minimal code:
   - Auto-tracks all changes to models
   - Built-in version history queries
   - Simple restore: `file.revert(version_number)`
   - Maintains full audit trail
   
3. **hashfs** (optional) for smart storage:
   - Content-addressable: same file = same hash = auto-deduplication
   - Saves storage space when same file uploaded multiple times
   - Built-in integrity checking

### Installation

```bash
pip install sqlalchemy-continuum hashfs
```

Add to `requirements.txt`:
```
sqlalchemy-continuum>=1.4.0
hashfs>=0.7.2  # Optional, for deduplication
```

### Database Schema with SQLAlchemy-Continuum

**Much simpler than raw SQL** - Continuum handles versioning automatically:
**Much simpler than raw SQL** - Continuum handles versioning automatically:

```python
# src/modules/file_manager_models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy_continuum import make_versioned
from datetime import datetime

# Enable versioning system
make_versioned(user_cls=None)

Base = declarative_base()

# Association table for many-to-many relationship
file_version_tags = Table(
    'file_version_tags', Base.metadata,
    Column('version_id', Integer, ForeignKey('file_versions.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('file_tags.id'), primary_key=True)
)

class FileGroup(Base):
    """Logical grouping for related files."""
    __tablename__ = 'file_groups'
    
    group_id = Column(String, primary_key=True)
    name = Column(String)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String)
    
    # Relationship to file versions
    files = relationship('FileVersion', back_populates='group')

class FileVersion(Base):
    """File metadata with automatic versioning via SQLAlchemy-Continuum."""
    __tablename__ = 'file_versions'
    __versioned__ = {}  # This enables automatic versioning!
    
    id = Column(Integer, primary_key=True)
    group_id = Column(String, ForeignKey('file_groups.group_id'))
    filename = Column(String)           # User-facing filename
    storage_path = Column(String)       # Actual filesystem path
    file_size = Column(Integer)
    mime_type = Column(String)
    checksum = Column(String)           # SHA256 hash
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    uploaded_by = Column(String)
    is_current = Column(Boolean, default=True)
    source_version_id = Column(Integer, ForeignKey('file_versions.id'), nullable=True)
    
    # Relationships
    group = relationship('FileGroup', back_populates='files')
    tags = relationship('FileTag', secondary=file_version_tags, back_populates='file_versions')
    source_version = relationship('FileVersion', remote_side=[id], uselist=False)

class FileTag(Base):
    """Tags for file organization."""
    __tablename__ = 'file_tags'
    
    id = Column(Integer, primary_key=True)
    tag_name = Column(String, unique=True)
    
    # Relationship
    file_versions = relationship('FileVersion', secondary=file_version_tags, back_populates='tags')

# Configure versioning
from sqlalchemy_continuum import version_class
FileVersionHistory = version_class(FileVersion)  # Auto-generated version table
```

**What SQLAlchemy-Continuum gives you automatically:**
- `file.versions` - Access all versions of a file
- `file.version` - Current version number
- `file.revert(3)` - Restore to version 3
- `file.changeset` - See what changed between versions
- Automatic version table creation (`file_versions_version`)

### Raw SQL Schema (for reference, but Continuum handles this)

If you want to see the underlying structure, here's what Continuum creates automatically:

### Raw SQL Schema (for reference, but Continuum handles this)

If you want to see the underlying structure, here's what Continuum creates automatically:

```sql
-- Main tables (you define these)
CREATE TABLE file_groups (...);
CREATE TABLE file_versions (...);
CREATE TABLE file_tags (...);
CREATE TABLE file_version_tags (...);

-- Version history table (Continuum creates this automatically)
CREATE TABLE file_versions_version (
    id INTEGER,
    group_id TEXT,
    filename TEXT,
    storage_path TEXT,
    -- ... all columns from file_versions ...
    transaction_id INTEGER NOT NULL,  -- Links to version transaction
    end_transaction_id INTEGER,       -- When this version ended
    operation_type INTEGER NOT NULL,  -- 0=insert, 1=update, 2=delete
    PRIMARY KEY (id, transaction_id)
);

CREATE TABLE transaction (
    id INTEGER PRIMARY KEY,
    issued_at DATETIME,
    user_id TEXT
);
```

### Optional: hashfs for Deduplication

```python
# src/modules/file_storage.py
from hashfs import HashFS
import hashlib

class ContentAddressableStorage:
    """Store files by content hash for automatic deduplication."""
    
    def __init__(self, storage_path):
        self.fs = HashFS(storage_path, depth=2, width=2, algorithm='sha256')
    
    def store(self, file_stream, original_filename):
        """Store file and return hash address + metadata."""
        # Calculate hash while reading
        file_stream.seek(0)
        content = file_stream.read()
        checksum = hashlib.sha256(content).hexdigest()
        
        # Store by hash (auto-deduplication!)
        address = self.fs.put(BytesIO(content))
        
        return {
            'hash': checksum,
            'storage_path': address.relpath,
            'abspath': address.abspath,
            'size': len(content)
        }
    
    def get(self, storage_path):
        """Retrieve file by hash path."""
        return self.fs.open(storage_path)
    
    def delete(self, storage_path):
        """Delete file (only if no other references)."""
        self.fs.delete(storage_path)
```

**Benefits:**
- Same file uploaded 10 times = stored once, saves disk space
- Integrity checking built-in (hash verification)
- Fast lookups by content hash


**Purpose**: Internal organization for easier file searching in admin section

**Features**:
- Tags configurable in settings (like categories)
- Can be set programmatically (hardcoded) or via dropdown
- Admin UI shows tag filters
- Multiple tags per file supported
- Tags stored in database, linked to file versions

**Settings Configuration**:
```python
"file_storage": {
    "tags": {
        "type": "array",
        "friendly": "Available File Tags",
        "value": ["invoice", "contract", "photo", "diagram", "report", "archive"],
        "persistent": True
    }
}
```

### 3. DisplayerItemInputFile Enhancements (Answer to Q3)

**New Parameters** (with defaults):
```python
DisplayerItemInputFile(
    id: str,
    text: str,
    fixed_category: Optional[str] = None,      # Hardcoded category, hidden from user
    fixed_group_id: Optional[str] = None,      # Hardcoded group_id, hidden from user
    fixed_tags: Optional[List[str]] = None,    # Hardcoded tags, hidden from user
    show_category: bool = True,                # Show category selector (if not fixed)
    show_group_id: bool = True,                # Show group_id input (if not fixed)
    show_tags: bool = False                    # Show tag selector (admin pages only)
)
```

**Behavior**:
- If `fixed_category` is set → category dropdown hidden, value hardcoded
- If `show_category=False` → category input not rendered
- Same pattern for `group_id` and `tags`
- Allows mix: e.g., fixed category + user-selectable tags

**Example Usage**:
```python
# Demo page: Category locked to "demo"
disp.add_display_item(DisplayerItemInputFile(
    "upload_file", 
    "Select File",
    fixed_category="demo",
    show_category=False  # Don't show dropdown
))

# Admin page: Show all options
disp.add_display_item(DisplayerItemInputFile(
    "upload_file",
    "Select File", 
    show_category=True,
    show_group_id=True,
    show_tags=True
))
```

### 4. Category Selection Fix (Current Issue)

**Problem**: Demo upload uses free text input for category instead of dropdown

**Solution**:
- Change `DisplayerItemInputString("category")` to `DisplayerItemInputSelect("category")`
- Populate options from `file_manager.get_categories()`
- Admin page already should use dropdown

### 5. File History UI (Answer to Q4)

**Design**: Separate history page (not modal)

**Flow**:
1. Gallery shows files with current version info
2. "History" button in actions column
3. Clicking opens `/file_manager/history/<group_id>/<filename>` page
4. History page shows:
   - All versions in timeline view
   - Metadata for each version (date, uploader, size, tags)
   - Preview/thumbnail if available
   - Actions: Download, Restore, View Details
5. "Restore" creates new version (copy)

**Benefits**:
- More flexible than modal
- Can show detailed metadata
- Easier to implement pagination for many versions
- Better for mobile responsiveness

### 6. Database Location (Answer to Q2)

**Location**: `settings/.file_metadata.db` (alongside `config.json`)

**Rationale**:
- Keeps metadata with configuration
- Easier backup (single directory)
- Follows principle of keeping settings together

**Initialization**:
```python
class FileManager:
    def __init__(self, settings_manager):
        # Get settings directory from SettingsManager
        settings_dir = Path(settings_manager.storage.config_path).parent
        self.db_path = settings_dir / ".file_metadata.db"
        self._init_database()
```

## Phase 1 & 2: Current Implementation (COMPLETE)

### File Upload ✓
- Accept files via Flask routes (POST with multipart/form-data)
- Validate file types against whitelist (configurable)
- Validate file size against max limit (configurable)
- Sanitize filenames (remove path traversal, special chars)
- Generate unique filenames on collision (append suffix like `_1`, `_2`)
- Store with organized directory structure: `{base_path}/{category}/{subcategory}/filename.ext`


### File Storage ✓
- Configurable base storage path via settings
- Auto-create directory structure as needed
- Return metadata dict: `{"path": "rel/path", "name": "file.ext", "size": 1024, "uploaded_at": "ISO8601"}`
- Physical storage: Keep original filename when possible

### File Retrieval ✓
- Secure file serving (prevent path traversal attacks)
- Support range requests for large files
- Set proper MIME types
- Inline display for thumbnails

### File Deletion ✓
- Safe deletion with existence checks
- Soft-delete (move to .trash folder) by default
- Optional permanent delete
- Thumbnails deleted with parent file

### Thumbnail Generation ✓
- Auto-generate thumbnails for images (`.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.webp`)
- PDF thumbnail support (first page)
- Use Pillow library for images, PyMuPDF for PDFs
- Configurable sizes (default: 150x150, 300x300)
- Store in `{base_path}/.thumbs/{size}/{original_path}`

### Image Optimization ✓
- Auto-compress images to reduce storage
- Configurable quality (default: 85%)
- Strip EXIF data for privacy
- RGBA to RGB conversion for JPEG compatibility

### Settings Configuration ✓
### Settings Configuration ✓
Current `FILE_STORAGE_CONFIG` in `default_configs.py`:
```python
{
    "file_storage": {
        "friendly": "File Storage Settings",
        "base_path": {
            "type": "path",
            "friendly": "Storage Directory",
            "value": "resources/uploads",
            "persistent": True
        },
        "max_file_size_mb": {
            "type": "int",
            "friendly": "Max File Size (MB)",
            "value": 50,
            "persistent": True
        },
        "allowed_extensions": {
            "type": "array",
            "friendly": "Allowed Extensions",
            "value": [".pdf", ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp",
                     ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
                     ".txt", ".csv", ".zip", ".7z", ".rar"],
            "persistent": True
        },
        "categories": {
            "type": "array",
            "friendly": "File Categories",
            "value": ["general", "documents", "images", "reports", "archives"],
            "persistent": True
        },
        "generate_thumbnails": {
            "type": "bool",
            "friendly": "Generate Thumbnails",
            "value": True,
            "persistent": True
        },
        "thumbnail_sizes": {
            "type": "array",
            "friendly": "Thumbnail Sizes (WxH)",
            "value": ["150x150", "300x300"],
            "persistent": True
        },
        "image_quality": {
            "type": "int",
            "friendly": "Image Compression Quality (1-100)",
            "value": 85,
            "persistent": True
        },
        "strip_exif": {
            "type": "bool",
            "friendly": "Remove EXIF Metadata from Images",
            "value": True,
            "persistent": True
        }
    }
}
```

### API Module ✓
`src/modules/file_manager.py` - FileManager class with methods:
```python
class FileManager:
    """Handles file upload, storage, retrieval, and deletion."""
    
    def upload_file(self, file_obj, category: str, subcategory: str = "") -> dict:
        """Upload file and return metadata dict."""
    
    def get_file_path(self, relative_path: str) -> Path:
        """Get absolute path with security checks."""
    
    def delete_file(self, relative_path: str, soft_delete: bool = True) -> bool:
        """Delete file (soft or permanent)."""
    
    def list_files(self, category: str = "", subcategory: str = "") -> list:
        """List files in category/subcategory."""
    
    def get_mime_type(self, relative_path: str) -> str:
        """Get MIME type for file."""
    
    def get_categories(self) -> List[str]:
        """Get configured categories."""
```

### Routes ✓
`src/pages/file_handler.py` - Blueprint with routes:
- `POST /files/upload` - Handle uploads (JSON response with metadata)
- `GET /files/download/<path:filepath>` - Serve files securely
- `DELETE /files/delete/<path:filepath>` - Delete files
- `GET /files/list` - List files (JSON)
- Permission checks via `_require_permission()`

### Admin UI ✓
`src/pages/file_manager_admin.py` - Admin interface:
- `/file_manager/` - Browse files with DataTable
- `/file_manager/upload_form` - Upload interface
- Statistics display (file count, total size, categories)
- File preview with thumbnails
- Download/Delete actions

### Demo Pages ✓
`tests/demo_support/demo_file_manager.py`:
- `/file-manager-demo` - Overview page
- `/upload-demo` - Upload demonstration
- `/gallery-demo` - Gallery with thumbnails

### Enable Method ✓
In `src/modules/site_conf.py`:
```python
def enable_file_manager(self, add_to_sidebar: bool = False, enable_admin_page: bool = False):
    """Enable file upload/download management."""
```

## Phase 3 Implementation Plan

### Step 1: Database Setup with SQLAlchemy

1. **Create models** (as shown above in `file_manager_models.py`)

2. **Initialize database in FileManager**:
   ```python
   from sqlalchemy import create_engine
   from sqlalchemy.orm import sessionmaker
   from sqlalchemy_continuum import make_versioned
   from .file_manager_models import Base, FileGroup, FileVersion, FileTag
   
   class FileManager:
       def __init__(self, settings_manager):
           # ... existing code ...
           self._init_database()
       
       def _init_database(self):
           """Initialize SQLite database for file metadata."""
           settings_dir = Path(self.settings.storage.config_path).parent
           db_path = settings_dir / ".file_metadata.db"
           
           # Create engine
           self.engine = create_engine(f'sqlite:///{db_path}')
           
           # Create all tables (including version tables)
           Base.metadata.create_all(self.engine)
           
           # Create session maker
           Session = sessionmaker(bind=self.engine)
           self.db_session = Session()
   ```

3. **Add versioning operations** (much simpler with Continuum):
   ```python
   def create_file_group(self, group_id: str, name: str, description: str = "") -> FileGroup:
       """Create a new file group."""
       group = FileGroup(
           group_id=group_id,
           name=name,
           description=description,
           created_by=session.get('user', 'GUEST')
       )
       self.db_session.add(group)
       self.db_session.commit()
       return group
   
   def add_file_version(self, group_id: str, filename: str, storage_path: str, 
                       file_size: int, mime_type: str, checksum: str,
                       tags: List[str] = None) -> FileVersion:
       """Add new file version (Continuum auto-tracks versioning)."""
       # Mark previous versions as not current
       self.db_session.query(FileVersion).filter_by(
           group_id=group_id, 
           filename=filename,
           is_current=True
       ).update({'is_current': False})
       
       # Create new version (Continuum auto-increments version number)
       file_version = FileVersion(
           group_id=group_id,
           filename=filename,
           storage_path=storage_path,
           file_size=file_size,
           mime_type=mime_type,
           checksum=checksum,
           uploaded_by=session.get('user', 'GUEST'),
           is_current=True
       )
       
       # Add tags if provided
       if tags:
           for tag_name in tags:
               tag = self.db_session.query(FileTag).filter_by(tag_name=tag_name).first()
               if not tag:
                   tag = FileTag(tag_name=tag_name)
                   self.db_session.add(tag)
               file_version.tags.append(tag)
       
       self.db_session.add(file_version)
       self.db_session.commit()
       return file_version
   
   def get_file_versions(self, group_id: str, filename: str) -> List[dict]:
       """Get all versions of a file (using Continuum's version tracking)."""
       current = self.db_session.query(FileVersion).filter_by(
           group_id=group_id,
           filename=filename,
           is_current=True
       ).first()
       
       if not current:
           return []
       
       # Get all historical versions via Continuum
       versions = []
       for version in current.versions:  # Continuum magic!
           versions.append({
               'version_number': version.version,
               'filename': version.filename,
               'storage_path': version.storage_path,
               'file_size': version.file_size,
               'uploaded_at': version.uploaded_at.isoformat(),
               'uploaded_by': version.uploaded_by,
               'tags': [tag.tag_name for tag in version.tags],
               'transaction_id': version.transaction_id
           })
       
       return versions
   
   def restore_version(self, file_id: int, target_version_number: int) -> FileVersion:
       """Restore old version by creating new version as copy."""
       current = self.db_session.query(FileVersion).get(file_id)
       
       # Get target version from history
       target_version = None
       for v in current.versions:
           if v.version == target_version_number:
               target_version = v
               break
       
       if not target_version:
           raise ValueError(f"Version {target_version_number} not found")
       
       # Create new version as copy of old version
       restored = FileVersion(
           group_id=current.group_id,
           filename=current.filename,
           storage_path=target_version.storage_path,  # Reuse same file!
           file_size=target_version.file_size,
           mime_type=target_version.mime_type,
           checksum=target_version.checksum,
           uploaded_by=session.get('user', 'GUEST'),
           is_current=True,
           source_version_id=file_id  # Link to original
       )
       
       # Mark old as not current
       current.is_current = False
       
       self.db_session.add(restored)
       self.db_session.commit()
       return restored
   
   def search_by_tags(self, tags: List[str]) -> List[FileVersion]:
       """Search files by tags."""
       return self.db_session.query(FileVersion).join(
           FileVersion.tags
       ).filter(
           FileTag.tag_name.in_(tags),
           FileVersion.is_current == True
       ).all()
   ```

### Step 2: Update Upload Logic

1. Modify `upload_file()` to accept `group_id` and `tags`:
   ```python
   def upload_file(self, file_obj, category: str = None, subcategory: str = "", 
                   group_id: str = None, tags: List[str] = None) -> dict:
       """Upload file with optional group_id and tags for versioning."""
       
       # Validate file
       is_valid, error_msg = self._validate_file(file_obj)
       if not is_valid:
           raise ValueError(error_msg)
       
       # Auto-generate group_id if not provided
       if not group_id:
           if category:
               group_id = f"{category}_{subcategory}" if subcategory else category
           else:
               group_id = "general"
       
       # Check if file already exists in this group
       existing = self.db_session.query(FileVersion).filter_by(
           group_id=group_id,
           filename=file_obj.filename,
           is_current=True
       ).first()
       
       if existing:
           # Create new version
           version_num = len(existing.versions) + 1
           storage_filename = f"{Path(file_obj.filename).stem}_v{version_num}{Path(file_obj.filename).suffix}"
       else:
           # First version
           storage_filename = file_obj.filename
           version_num = 1
       
       # Save file (existing code)
       storage_path = self._save_file(file_obj, storage_filename, category, subcategory)
       
       # Calculate checksum
       checksum = self._calculate_checksum(storage_path)
       
       # Add to database (Continuum handles versioning)
       file_version = self.add_file_version(
           group_id=group_id,
           filename=file_obj.filename,
           storage_path=storage_path,
           file_size=storage_path.stat().st_size,
           mime_type=self.get_mime_type(str(storage_path)),
           checksum=checksum,
           tags=tags
       )
       
       # Generate thumbnails (existing code)
       thumbnails = self._generate_thumbnails(storage_path, str(storage_path))
       
       return {
           "path": str(storage_path),
           "name": file_obj.filename,
           "size": file_version.file_size,
           "version": version_num,
           "group_id": group_id,
           "uploaded_at": file_version.uploaded_at.isoformat(),
           "is_current": True,
           **thumbnails
       }
   
   def _calculate_checksum(self, file_path: Path) -> str:
       """Calculate SHA256 checksum."""
       import hashlib
       sha256_hash = hashlib.sha256()
       with open(file_path, "rb") as f:
           for byte_block in iter(lambda: f.read(4096), b""):
               sha256_hash.update(byte_block)
       return sha256_hash.hexdigest()
   ```

### Step 3: DisplayerItemInputFile Enhancement
1. Add parameters: `fixed_category`, `fixed_group_id`, `fixed_tags`
2. Add display flags: `show_category`, `show_group_id`, `show_tags`
3. Update Jinja2 template to conditionally render fields
4. Populate dropdowns from settings

### Step 4: History Page
1. Create route: `/file_manager/history/<group_id>/<filename>`
2. Query all versions from database
3. Display timeline view with:
   - Version number
   - Upload date/user
   - File size
   - Tags
   - Thumbnail preview
   - Download button
   - Restore button (creates new version)

### Step 5: Update Admin UI
1. Add "History" button to file actions in gallery
2. Add tag filter to file listing
3. Show version info in file table
4. Update upload form to include:
   - Group ID input (with auto-generate option)
   - Tag selector (multiselect)

### Step 6: Settings Update
Add to `FILE_STORAGE_CONFIG`:
```python
"tags": {
    "type": "array",
    "friendly": "Available File Tags",
    "value": ["invoice", "contract", "photo", "diagram", "report", "archive"],
    "persistent": True
},
"auto_generate_group_id": {
    "type": "bool",
    "friendly": "Auto-generate Group IDs",
    "value": True,
    "persistent": True
},
"group_id_prefix": {
    "type": "string",
    "friendly": "Group ID Prefix",
    "value": "FG",
    "persistent": True
}
```

### Step 6: Settings Update

Add to `FILE_STORAGE_CONFIG` in `default_configs.py`:
```python
"tags": {
    "type": "array",
    "friendly": "Available File Tags",
    "value": ["invoice", "contract", "photo", "diagram", "report", "archive"],
    "persistent": True
},
"auto_generate_group_id": {
    "type": "bool",
    "friendly": "Auto-generate Group IDs",
    "value": True,
    "persistent": True
},
"group_id_prefix": {
    "type": "string",
    "friendly": "Group ID Prefix",
    "value": "FG",
    "persistent": True
}
```

### Step 7: Update Tests

Add to `tests/test_file_manager.py`:
```python
class TestVersioningWithContinuum:
    """Test SQLAlchemy-Continuum versioning."""
    
    def test_version_creation_on_duplicate(self, file_manager, sample_text_file):
        """Test creating new version when same filename uploaded."""
        # Upload first version
        v1 = file_manager.upload_file(sample_text_file, group_id="test_group")
        assert v1["version"] == 1
        
        # Upload same filename to same group
        sample_text_file.stream.seek(0)
        v2 = file_manager.upload_file(sample_text_file, group_id="test_group")
        assert v2["version"] == 2
        assert v2["is_current"] == True
        
        # v1 should no longer be current
        versions = file_manager.get_file_versions("test_group", sample_text_file.filename)
        assert len(versions) == 2
    
    def test_version_history_via_continuum(self, file_manager, sample_text_file):
        """Test accessing version history."""
        # Create multiple versions
        for i in range(3):
            sample_text_file.stream.seek(0)
            file_manager.upload_file(sample_text_file, group_id="test_group")
        
        # Query versions (Continuum provides this)
        versions = file_manager.get_file_versions("test_group", sample_text_file.filename)
        assert len(versions) == 3
        assert versions[0]["version_number"] == 1
        assert versions[-1]["version_number"] == 3
    
    def test_restore_creates_new_version(self, file_manager, sample_text_file):
        """Test restoring creates new version as copy."""
        v1 = file_manager.upload_file(sample_text_file, group_id="test_group")
        sample_text_file.stream.seek(0)
        v2 = file_manager.upload_file(sample_text_file, group_id="test_group")
        
        # Restore v1
        restored = file_manager.restore_version(v2["id"], target_version_number=1)
        assert restored.version == 3  # New version created
        assert restored.source_version_id == v1["id"]
        assert restored.storage_path == v1["storage_path"]  # Reuses same file!

class TestGroupID:
    def test_different_groups_same_filename(self, file_manager, sample_text_file):
        """Test same filename in different groups doesn't conflict."""
        v1 = file_manager.upload_file(sample_text_file, group_id="group_a")
        sample_text_file.stream.seek(0)
        v2 = file_manager.upload_file(sample_text_file, group_id="group_b")
        
        # Both should be version 1 (different groups)
        assert v1["version"] == 1
        assert v2["version"] == 1
        assert v1["group_id"] != v2["group_id"]
    
    def test_auto_group_id_generation(self, file_manager, sample_text_file):
        """Test automatic group_id generation."""
        metadata = file_manager.upload_file(sample_text_file, category="documents")
        assert metadata["group_id"] == "documents"

class TestTags:
    def test_add_tags_to_file(self, file_manager, sample_text_file):
        """Test adding tags during upload."""
        metadata = file_manager.upload_file(
            sample_text_file, 
            group_id="test",
            tags=["invoice", "2025"]
        )
        
        # Verify tags stored
        file_version = file_manager.db_session.query(FileVersion).filter_by(
            group_id="test",
            filename=sample_text_file.filename
        ).first()
        tag_names = [tag.tag_name for tag in file_version.tags]
        assert "invoice" in tag_names
        assert "2025" in tag_names
    
    def test_search_by_tags(self, file_manager, sample_text_file, sample_image_file):
        """Test searching files by tags."""
        file_manager.upload_file(sample_text_file, group_id="g1", tags=["invoice"])
        file_manager.upload_file(sample_image_file, group_id="g2", tags=["invoice", "2025"])
        
        results = file_manager.search_by_tags(["invoice"])
        assert len(results) == 2
        
        results_2025 = file_manager.search_by_tags(["2025"])
        assert len(results_2025) == 1

class TestDeduplication:
    """Test hashfs deduplication (if implemented)."""
    
    def test_same_content_same_hash(self, file_manager, sample_text_file):
        """Test identical files get same hash."""
        v1 = file_manager.upload_file(sample_text_file, group_id="g1")
        sample_text_file.stream.seek(0)
        v2 = file_manager.upload_file(sample_text_file, group_id="g2")
        
        # Different groups but same content = same checksum
        file1 = file_manager.db_session.query(FileVersion).get(v1["id"])
        file2 = file_manager.db_session.query(FileVersion).get(v2["id"])
        assert file1.checksum == file2.checksum
```

### Step 8: Update Demo
1. Fix category dropdown in `demo_file_manager.py`
2. Add example with `fixed_category`
3. Add history demonstration

## Implementation Checklist

### Phase 1 & 2 (COMPLETE) ✓
- [x] Core file upload/download
- [x] Security (path traversal prevention)
- [x] Thumbnail generation
- [x] Settings configuration
- [x] Routes and blueprints
- [x] Admin UI
- [x] Demo pages
- [x] Unit tests (basic)

### Phase 3 (PENDING) - Using SQLAlchemy-Continuum
- [ ] Install dependencies: `sqlalchemy-continuum`, `hashfs` (optional)
- [ ] Create `file_manager_models.py` with SQLAlchemy models
- [ ] Configure `make_versioned()` for Continuum
- [ ] Add database initialization to FileManager
- [ ] Update `upload_file()` with group_id and tags support
- [ ] Implement version history queries (via Continuum)
- [ ] Implement restore functionality
- [ ] Create history page route
- [ ] Add tag search/filter
- [ ] Enhance DisplayerItemInputFile (fixed params, show flags)
- [ ] Fix demo category dropdown
- [ ] Update tests for versioning/tags
- [ ] Optional: Implement hashfs deduplication
- [ ] Update documentation

**Estimated code reduction with SQLAlchemy-Continuum**: ~60-70% less code vs. manual versioning

## Code Comparison: Manual vs. SQLAlchemy-Continuum

### Manual Versioning (what we'd write):
```python
# ~200 lines of code for version management
def create_version():
    # Find max version number
    # Increment version
    # Update is_current flags
    # Insert new version row
    # Handle transactions
    pass

def get_versions():
    # Complex JOIN queries
    # Manual pagination
    pass

def restore_version():
    # Copy data manually
    # Update multiple tables
    pass
```

### With SQLAlchemy-Continuum (what we actually write):
```python
# ~30 lines total!
class FileVersion(Base):
    __versioned__ = {}  # That's it for versioning!
    # ... regular columns ...

# Usage:
file.versions  # All versions
file.revert(3)  # Restore to v3
file.changeset  # See changes
```

**Result**: Much cleaner, less error-prone, battle-tested library.

## Code Quality Standards
## Code Quality Standards
- **Type hints**: Use throughout (`from typing import ...`)
- **Docstrings**: Google-style for all public methods
- **Error handling**: Comprehensive try/except with logging
- **Security**: Sanitize all user inputs, prevent path traversal
- **Logging**: Use framework's logging system (`logger = logging.getLogger(__name__)`)

## Testing Requirements
`tests/test_file_manager.py` includes:
- ✓ Unit tests for FileManager methods
- ✓ Security tests for path traversal
- ✓ Validation tests for file type/size limits
- ✓ Thumbnail generation tests
- ✓ File deletion tests (soft/hard)
- ✓ File listing tests
- ⏳ Integration tests for versioning (Phase 3)
- ⏳ Database operation tests (Phase 3)
- ⏳ Tag system tests (Phase 3)

Current coverage: ~80% (Phase 1 & 2 features)

## Security Checklist
- [x] Path traversal prevention (reject `..`, absolute paths, drive letters)
- [x] Filename sanitization (alphanumeric + safe chars only)
- [x] File type validation (whitelist extensions)
- [x] File size limits enforced
- [x] Permissions required for upload/download/delete routes
- [x] No directory listing exposure
- [x] MIME type validation on download
- [ ] Rate limiting (documented, not implemented)

## Framework Integration

### Settings
- ✓ `FILE_STORAGE_CONFIG` registered in `default_configs.py`
- ✓ Auto-merged into `config.json` when `enable_file_manager()` called
- ✓ Appears in Settings UI automatically

### Routes
- ✓ Blueprints registered in `src/main.py` when enabled:
  - `file_handler` - Upload/download/delete APIs
  - `file_manager_admin` - Admin UI (if `enable_admin_page=True`)

### Displayer Items
- ✓ `DisplayerItemInputFile` works with file upload routes
- ✓ `DisplayerItemActionButtons` for download/delete in gallery
- ⏳ Enhanced parameters (Phase 3)

### Dependencies
Added to `requirements.txt`:
- ✓ `Pillow>=10.0.0` (image processing)
- ✓ `PyMuPDF>=1.23.0` (PDF thumbnails)

## Usage Examples

### Basic Usage (Current)
```python
# In website/site_conf.py
from src.modules.site_conf import Site_conf

class MySiteConf(Site_conf):
    def __init__(self):
        super().__init__()
        self.enable_file_manager(add_to_sidebar=True, enable_admin_page=True)

# In website/pages/my_page.py
from src.modules.file_manager import FileManager
from src.modules import settings
from src.modules.displayer import Displayer, DisplayerItemInputFile
from flask import request

@bp.route('/upload_form')
def upload_form():
    disp = Displayer()
    disp.add_display_item(DisplayerItemInputFile("document", "Select Document"))
    return disp.display()

@bp.route('/upload', methods=['POST'])
def upload():
    file_mgr = FileManager(settings.settings_manager)
    if 'document' in request.files:
        file = request.files['document']
        try:
            metadata = file_mgr.upload_file(file, category="documents", subcategory="user123")
            # metadata = {"path": "documents/user123/file.pdf", "name": "file.pdf", 
            #            "size": 12345, "uploaded_at": "...", "thumb_150x150": "..."}
            flash("File uploaded successfully!", "success")
        except ValueError as e:
            flash(f"Upload failed: {e}", "error")
    return redirect("/upload_form")
```

### Phase 3 Usage (Planned)
```python
# With versioning and tags
@bp.route('/upload', methods=['POST'])
def upload():
    file_mgr = FileManager(settings.settings_manager)
    file = request.files['document']
    
    metadata = file_mgr.upload_file(
        file, 
        group_id="project-alpha",  # Files grouped by project
        tags=["contract", "2025"],  # Searchable tags
        category="legal"            # Still supports categories
    )
    # If file exists in same group_id → creates new version
    # Returns: {"version": 2, "is_current": True, ...}

# Upload form with fixed category
disp.add_display_item(DisplayerItemInputFile(
    "contract_upload",
    "Upload Contract",
    fixed_category="legal",      # Hardcoded, not shown to user
    show_tags=True,              # Show tag selector
    show_group_id=True          # Show group_id input
))

# View file history
@bp.route('/file_history/<group_id>/<filename>')
def file_history(group_id, filename):
    file_mgr = FileManager(settings.settings_manager)
    versions = file_mgr.get_file_versions(group_id, filename)
    # Returns list of all versions with metadata
    
# Restore old version
@bp.route('/restore_version/<int:version_id>')
def restore(version_id):
    file_mgr = FileManager(settings.settings_manager)
    new_metadata = file_mgr.restore_version(version_id)
    # Creates new version as copy of old version
    # Returns: {"version": 4, "source_version_id": 1, ...}
```

## Current Status Summary

### ✅ Implemented (Phases 1 & 2)
- Complete file upload/download system
- Thumbnail generation (images + PDFs)
- Soft-delete with trash folder
- Category-based organization
- Settings-driven configuration
- Permission-based access control
- Admin UI with gallery view
- Demo pages for testing
- Unit test suite (80% coverage)
- Logging and error handling

### ⏳ Pending (Phase 3)
- SQLite database for metadata tracking
- Group ID system for logical file grouping
- Automatic versioning on duplicate uploads
- Version history page with timeline view
- Restore functionality (creates new version as copy)
- Tag system for internal organization
- Tag-based search and filtering
- Enhanced DisplayerItemInputFile with fixed/show parameters
- Category dropdown fix in demo page
- Extended test coverage for new features

### 🗄️ Database Location
**Answer to Question 2**: `settings/.file_metadata.db`
- Stored alongside `config.json` in settings directory
- Keeps metadata with configuration for easier backup
- Initialized by FileManager on first use

## Files Modified/Created

### Existing Files (Phase 1 & 2) ✓
1. `src/modules/file_manager.py` - Core FileManager class
2. `src/pages/file_handler.py` - Upload/download/delete routes
3. `src/pages/file_manager_admin.py` - Admin UI
4. `src/modules/default_configs.py` - FILE_STORAGE_CONFIG
5. `src/modules/site_conf.py` - enable_file_manager() method
6. `tests/test_file_manager.py` - Unit tests
7. `tests/demo_support/demo_file_manager.py` - Demo pages
8. `requirements.txt` - Added Pillow, PyMuPDF

### New Files for Phase 3 ⏳
1. `src/modules/file_manager_models.py` - **NEW**: SQLAlchemy models with Continuum
2. `src/modules/file_storage.py` - **NEW** (optional): hashfs wrapper for deduplication

### Files to Modify (Phase 3) ⏳
1. `src/modules/file_manager.py` - Add database session, version operations
2. `src/modules/displayer/items.py` - Enhance DisplayerItemInputFile
3. `src/modules/default_configs.py` - Add tags configuration
4. `src/pages/file_manager_admin.py` - Add history page, tag filters
5. `tests/demo_support/demo_file_manager.py` - Fix category dropdown
6. `tests/test_file_manager.py` - Add versioning/tag tests
7. `templates/displayer/input_file.j2` - Update template for new params (if needed)
8. `requirements.txt` - Add `sqlalchemy-continuum>=1.4.0`, `hashfs>=0.7.2`

## Known Issues to Fix

1. **Demo category input**: Currently uses free text (`DisplayerItemInputString`), should be dropdown (`DisplayerItemInputSelect`) populated from `file_manager.get_categories()`

2. **No versioning**: Files with same name get `_1`, `_2` suffix instead of proper versioning

3. **No history UI**: Can't view or restore previous versions

4. **No tagging**: Can't tag files for easier organization

5. **Database not implemented**: All metadata is filesystem-based only

## Notes for Implementation

### Key Architecture Decisions

1. **Use SQLAlchemy-Continuum for versioning**
   - Reduces implementation from ~500 lines to ~100 lines
   - Automatic version tracking on model changes
   - Built-in restore, history queries, changesets
   - Battle-tested in production systems
   - Integrates with existing SQLAlchemy infrastructure

2. **Database location**: `settings/.file_metadata.db`
   - Alongside `config.json` for easier backup
   - Initialized by FileManager on first use
   - SQLite for simplicity (can migrate to PostgreSQL later)

3. **Version storage strategy**:
   - Physical files: `filename_v1.ext`, `filename_v2.ext`
   - Database tracks versions via Continuum
   - Restore creates new version (copy) = audit trail preserved
   - Optional: hashfs for deduplication (same content = one file)

4. **Group IDs replace simple categories**
   - More flexible organization
   - Same filename in different groups = no conflict
   - Auto-generated from category if not specified

5. **Tags are admin-only**
   - Settings-driven configuration
   - Multiple tags per file
   - Searchable via database queries

6. **DisplayerItemInputFile flexibility**:
   - 3 `fixed_*` params for hardcoded values
   - 3 `show_*` params for UI control
   - Allows any combination (fixed category + user tags, etc.)

### Performance Considerations

- **SQLAlchemy-Continuum overhead**: Minimal (~5-10ms per operation)
- **Version table growth**: Monitor and archive old versions if needed
- **hashfs benefits**: Saves disk space if many duplicate files
- **Database indexing**: Add indexes on group_id, filename, tags for faster queries

### Migration Path (if needed later)

SQLite → PostgreSQL migration is straightforward with SQLAlchemy:
```python
# Just change connection string
engine = create_engine('postgresql://user:pass@host/dbname')
```

## Post-Implementation Verification

After Phase 3 completion:
1. Run full test suite: `pytest tests/test_file_manager.py -v`
2. Verify no regressions: `pytest tests/ -v`
3. Test manual scenarios:
   - Upload same file to same group → creates v2
   - Upload same file to different group → no conflict
   - View history page → shows all versions
   - Restore old version → creates new version as copy
   - Tag files → can search by tags
   - Use fixed_category → category hidden in UI
4. Update documentation
5. Update FILE_SYSTEM.md status

---

**Last Updated**: 2025-11-17 
- Phase 3 requirements documented based on user input
- **Updated with SQLAlchemy-Continuum approach** for automatic versioning
- Added hashfs for optional deduplication
- Reduced implementation complexity by ~60-70%

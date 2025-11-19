File Manager System
===================

The ParalaX Web Framework includes a comprehensive file management system with support for versioning, tagging, content deduplication, thumbnail generation, and integrity verification.

Overview
--------

The File Manager provides:

* **Content-Addressable Storage**: Files stored by SHA256 hash with automatic deduplication
* **File Versioning**: Track multiple versions of files with group IDs
* **Tag-Based Organization**: Flexible categorization system for file searching
* **Thumbnail Generation**: Automatic thumbnails for images and PDFs
* **Integrity Verification**: Checksum validation for data integrity
* **Secure File Handling**: Path traversal prevention and file type validation

Architecture
------------

The file manager consists of four main components:

1. **FileManager** - Main manager class coordinating all operations
2. **Database Models** - SQLAlchemy models for metadata storage (FileGroup, FileVersion, FileTag)
3. **ContentAddressableStorage** - HashFS wrapper for deduplication
4. **File Handler Pages** - Flask blueprints for web UI

Content-Addressable Storage
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Files are stored using HashFS, which organizes files by their SHA256 hash:

.. code-block:: text

   resources/hashfs_storage/
   ├── ab/
   │   └── c1/
   │       └── abc123def456...  (actual file)
   └── df/
       └── 60/
           └── df6012ab34...  (another file)

This enables automatic deduplication - identical files are only stored once regardless of how many times they're uploaded.

Versioning System
~~~~~~~~~~~~~~~~~

Files with the same ``group_id`` and ``filename`` are tracked as versions:

* **group_id**: Logical grouping identifier (can be project name, category, etc.)
* **filename**: Original filename
* **version number**: Automatically incremented
* **is_current**: Flag indicating the latest version

Files without a ``group_id`` are standalone (no versioning).

Tagging System
~~~~~~~~~~~~~~

Tags provide flexible categorization:

* Multiple tags per file
* Configurable tag list
* Fast search by single or multiple tags
* Tag-based filtering in the UI

Configuration
-------------

File manager settings are stored in the framework's settings system:

.. code-block:: json

   {
     "file_storage": {
       "hashfs_path": {
         "value": "resources/hashfs_storage",
         "description": "Root path for content-addressable storage"
       },
       "max_file_size_mb": {
         "value": 50,
         "description": "Maximum file size in megabytes"
       },
       "allowed_extensions": {
         "value": [".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx"],
         "description": "List of allowed file extensions"
       },
       "generate_thumbnails": {
         "value": true,
         "description": "Enable thumbnail generation"
       },
       "thumbnail_sizes": {
         "value": ["150x150", "300x300"],
         "description": "Thumbnail sizes to generate"
       },
       "categories": {
         "value": ["general", "documents", "images"],
         "description": "Available file categories"
       },
       "tags": {
         "value": ["invoice", "contract", "photo", "report"],
         "description": "Available file tags"
       }
     }
   }

Usage Examples
--------------

Basic Setup
~~~~~~~~~~~

.. code-block:: python

   from src.modules.settings.settings_manager import SettingsManager
   from src.modules.file_manager import FileManager
   
   # Initialize settings manager
   settings = SettingsManager()
   
   # Create file manager instance
   file_manager = FileManager(settings)

Uploading Files
~~~~~~~~~~~~~~~

.. code-block:: python

   from flask import request
   
   @app.route('/upload', methods=['POST'])
   def upload():
       # Get file from request
       file_obj = request.files['file']
       
       # Upload with versioning
       metadata = file_manager.upload_file(
           file_obj,
           category="documents",
           group_id="project_alpha",
           tags=["invoice", "2025"],
           uploaded_by="john.doe"
       )
       
       print(f"Uploaded: {metadata['name']}")
       print(f"Version: {metadata['version']}")
       print(f"Checksum: {metadata['checksum']}")
       
       # Upload standalone file (no versioning)
       standalone = file_manager.upload_file(
           file_obj,
           group_id=None  # No versioning
       )

Retrieving Files
~~~~~~~~~~~~~~~~

.. code-block:: python

   # Get file by ID
   file_version = file_manager.get_file_by_id(123)
   
   # Get physical path
   file_path = file_manager.get_file_path(file_version.storage_path)
   
   # Send to user
   from flask import send_file
   return send_file(file_path, as_attachment=True, 
                    download_name=file_version.filename)

Listing Files
~~~~~~~~~~~~~

.. code-block:: python

   # List all current versions
   all_files = file_manager.list_files_from_db()
   
   # Filter by group
   project_files = file_manager.list_files_from_db(group_id="project_alpha")
   
   # Filter by tag
   invoices = file_manager.list_files_from_db(tag="invoice")
   
   # Limit results
   recent = file_manager.list_files_from_db(limit=10)

Version Management
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Get all versions of a file
   versions = file_manager.get_file_versions(
       group_id="project_alpha",
       filename="report.pdf"
   )
   
   for v in versions:
       print(f"Version {v['version_number']}: {v['uploaded_at']}")
       print(f"  Uploaded by: {v['uploaded_by']}")
       print(f"  Current: {v['is_current']}")
   
   # Get current version only
   current = file_manager.get_current_file("project_alpha", "report.pdf")
   
   # Restore old version
   restored = file_manager.restore_version(
       file_id=current.id,
       target_version_id=versions[0]['id']
   )

Tag-Based Search
~~~~~~~~~~~~~~~~

.. code-block:: python

   # Search by single tag
   invoices = file_manager.search_by_tags(["invoice"])
   
   # Search by multiple tags (any match)
   results = file_manager.search_by_tags(["invoice", "urgent"])
   
   # Search by multiple tags (all must match)
   results = file_manager.search_by_tags(
       ["invoice", "2025", "paid"],
       match_all=True
   )

Integrity Verification
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Verify single file
   is_valid, status = file_manager.verify_file_integrity(file_id=123)
   
   if is_valid:
       print("File is intact")
   else:
       print(f"File integrity issue: {status}")
       # status can be: "Missing", "Checksum mismatch", "Not found"
   
   # Bulk verification (more efficient)
   file_ids = [1, 2, 3, 4, 5]
   results = file_manager.verify_files_bulk(file_ids)
   
   for fid, (is_valid, status) in results.items():
       print(f"File {fid}: {status}")

Deleting Files
~~~~~~~~~~~~~~

.. code-block:: python

   # Delete file (reference-counted for deduplication)
   success = file_manager.delete_file(file_id=123)
   
   if success:
       print("File deleted from database")
       print("Physical file deleted only if no other references exist")

Web Interface
-------------

The file manager includes two Flask blueprints:

File Handler API
~~~~~~~~~~~~~~~~

RESTful API endpoints for file operations:

* ``POST /files/upload`` - Upload file
* ``GET /files/download/<filepath>`` - Download file
* ``GET /files/download_by_id/<file_id>`` - Download by database ID
* ``DELETE /files/delete/<file_id>`` - Delete file
* ``GET /files/list`` - List files (with filters)
* ``GET /files/versions`` - Get file versions

File Manager Admin
~~~~~~~~~~~~~~~~~~

Web UI for file management:

* ``/file_manager/`` - Browse files with DataTables
* ``/file_manager/upload_form`` - Upload interface
* ``/file_manager/edit/<file_id>`` - Edit metadata (group_id, tags)
* ``/file_manager/confirm-delete`` - Delete confirmation

Features:

* Interactive file browser with thumbnails
* Search and filter by group, tag, filename
* Multi-select bulk operations
* File integrity status indicators
* Version history viewer
* Inline thumbnail previews

Permissions
-----------

The file manager integrates with the framework's RBAC system:

Required Permissions
~~~~~~~~~~~~~~~~~~~~

* ``FileManager.view`` - View file list
* ``FileManager.upload`` - Upload files
* ``FileManager.download`` - Download files
* ``FileManager.delete`` - Delete files
* ``FileManager.edit`` - Edit metadata

Example Permission Setup
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from src.modules.auth.auth_manager import auth_manager
   
   # Register module permissions
   auth_manager.register_module_permissions(
       "FileManager",
       ["view", "upload", "download", "delete", "edit"]
   )
   
   # Assign to role
   auth_manager.assign_module_to_role("editor", "FileManager", 
                                      ["view", "upload", "download"])
   auth_manager.assign_module_to_role("admin", "FileManager", 
                                      ["view", "upload", "download", "delete", "edit"])

Thumbnail Generation
--------------------

Automatic thumbnail generation for supported file types:

Supported Formats
~~~~~~~~~~~~~~~~~

* **Images**: JPEG, PNG, GIF, BMP, WebP (via Pillow)
* **PDFs**: First page thumbnail (via PyMuPDF)
* **Office Files**: Not yet implemented (requires LibreOffice)

Configuration
~~~~~~~~~~~~~

.. code-block:: json

   {
     "generate_thumbnails": true,
     "thumbnail_sizes": ["150x150", "300x300"],
     "image_quality": 85,
     "strip_exif": true
   }

Thumbnail Storage
~~~~~~~~~~~~~~~~~

Thumbnails are stored separately from the main HashFS:

.. code-block:: text

   resources/.thumbs/
   ├── 150x150/
   │   └── ab/c1/
   │       └── abc123_thumb.jpg
   └── 300x300/
       └── ab/c1/
           └── abc123_thumb.jpg

Database Schema
---------------

The file manager uses three main tables:

FileGroup
~~~~~~~~~

.. code-block:: sql

   CREATE TABLE file_groups (
       group_id TEXT PRIMARY KEY,
       name TEXT,
       description TEXT,
       created_at DATETIME,
       created_by TEXT
   );

FileVersion
~~~~~~~~~~~

.. code-block:: sql

   CREATE TABLE file_versions (
       id INTEGER PRIMARY KEY,
       group_id TEXT REFERENCES file_groups(group_id),
       filename TEXT NOT NULL,
       storage_path TEXT NOT NULL,
       file_size INTEGER,
       mime_type TEXT,
       checksum TEXT,
       uploaded_at DATETIME,
       uploaded_by TEXT,
       is_current BOOLEAN DEFAULT 1,
       source_version_id INTEGER REFERENCES file_versions(id),
       
       UNIQUE(group_id, filename, uploaded_at)
   );
   
   CREATE INDEX idx_checksum ON file_versions(checksum);
   CREATE INDEX idx_group_filename_current 
       ON file_versions(group_id, filename, is_current);

FileTag
~~~~~~~

.. code-block:: sql

   CREATE TABLE file_tags (
       id INTEGER PRIMARY KEY,
       tag_name TEXT UNIQUE NOT NULL
   );
   
   CREATE TABLE file_version_tags (
       version_id INTEGER REFERENCES file_versions(id),
       tag_id INTEGER REFERENCES file_tags(id),
       PRIMARY KEY (version_id, tag_id)
   );

Best Practices
--------------

1. **Use Group IDs for Related Files**

   Files that should be versioned together need the same ``group_id`` and ``filename``.

2. **Standalone Files Don't Need Groups**

   For one-off uploads without versioning, use ``group_id=None``.

3. **Configure Allowed Extensions Carefully**

   Restrict file types for security and storage efficiency.

4. **Use Bulk Verification**

   When checking many files, use ``verify_files_bulk()`` instead of individual calls.

5. **Reference Counting is Automatic**

   Physical files are only deleted when no database records reference them.

6. **Tag Standardization**

   Use a consistent tag vocabulary across your application.

API Reference
-------------

FileManager Class
~~~~~~~~~~~~~~~~~

.. autoclass:: src.modules.file_manager.manager.FileManager
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Database Models
~~~~~~~~~~~~~~~

.. autoclass:: src.modules.file_manager.models.FileGroup
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

.. autoclass:: src.modules.file_manager.models.FileVersion
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

.. autoclass:: src.modules.file_manager.models.FileTag
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Storage Backend
~~~~~~~~~~~~~~~

.. autoclass:: src.modules.file_manager.storage.ContentAddressableStorage
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

Troubleshooting
---------------

Missing Thumbnails
~~~~~~~~~~~~~~~~~~

**Symptom**: No thumbnails appear in the file browser

**Possible Causes**:

1. Thumbnail generation disabled in settings
2. PIL or PyMuPDF not installed
3. Unsupported file format
4. Thumbnail directory permissions

**Solutions**:

.. code-block:: bash

   # Install dependencies
   pip install Pillow PyMuPDF
   
   # Check settings
   # generate_thumbnails should be true
   
   # Verify thumbnail directory
   ls -la resources/.thumbs/

Checksum Mismatches
~~~~~~~~~~~~~~~~~~~

**Symptom**: Files fail integrity verification

**Possible Causes**:

1. File corruption
2. Manual file system modifications
3. Interrupted uploads

**Solutions**:

.. code-block:: python

   # Re-upload corrupted files
   # Or restore from backup
   
   # Run bulk verification to identify issues
   all_files = file_manager.list_files_from_db()
   file_ids = [f['id'] for f in all_files]
   results = file_manager.verify_files_bulk(file_ids)
   
   # Find corrupted files
   corrupted = [fid for fid, (valid, status) in results.items() 
                if not valid]
   print(f"Corrupted files: {corrupted}")

Large Database Files
~~~~~~~~~~~~~~~~~~~~

**Symptom**: ``.file_metadata.db`` grows very large

**Possible Causes**:

1. Many file versions accumulated
2. Soft-delete without cleanup

**Solutions**:

.. code-block:: python

   # Implement periodic cleanup of old versions
   # Keep only last N versions per file
   
   def cleanup_old_versions(file_manager, keep_versions=5):
       # Get all groups
       groups = file_manager.db_session.query(FileGroup).all()
       
       for group in groups:
           # Get files in group
           files = file_manager.db_session.query(FileVersion).filter(
               FileVersion.group_id == group.group_id
           ).all()
           
           # Group by filename
           by_filename = {}
           for f in files:
               if f.filename not in by_filename:
                   by_filename[f.filename] = []
               by_filename[f.filename].append(f)
           
           # Keep only latest N versions
           for filename, versions in by_filename.items():
               sorted_versions = sorted(versions, 
                                       key=lambda v: v.uploaded_at,
                                       reverse=True)
               
               for old_version in sorted_versions[keep_versions:]:
                   file_manager.delete_file(old_version.id)

Migration Guide
---------------

From Simple File Storage
~~~~~~~~~~~~~~~~~~~~~~~~~

If you're migrating from a simple file storage system:

1. **Create file groups** for existing file collections
2. **Import files** with appropriate group IDs and tags
3. **Update references** in your application code

.. code-block:: python

   # Example migration script
   import os
   from pathlib import Path
   
   # Create groups
   file_manager.create_file_group(
       group_id="legacy_docs",
       name="Legacy Documents",
       description="Migrated from old file system"
   )
   
   # Import files
   old_files_dir = Path("/old/files/directory")
   for file_path in old_files_dir.glob("**/*"):
       if file_path.is_file():
           with open(file_path, 'rb') as f:
               # Create FileStorage-like object
               from werkzeug.datastructures import FileStorage
               file_obj = FileStorage(
                   stream=f,
                   filename=file_path.name,
                   content_type="application/octet-stream"
               )
               
               metadata = file_manager.upload_file(
                   file_obj,
                   group_id="legacy_docs",
                   tags=["migrated"],
                   uploaded_by="migration_script"
               )
               
               print(f"Migrated: {file_path.name}")

Dependencies
------------

Required
~~~~~~~~

* SQLAlchemy >= 1.4
* hashfs >= 0.7
* Flask >= 2.0
* werkzeug >= 2.0

Optional
~~~~~~~~

* Pillow >= 9.0 (for image thumbnails)
* PyMuPDF >= 1.18 (for PDF thumbnails)

Install all dependencies:

.. code-block:: bash

   pip install sqlalchemy hashfs flask werkzeug Pillow PyMuPDF

"""
File Manager Module - Handles file upload, storage, retrieval, and deletion.

This module provides secure file management capabilities with support for:
- File upload with type/size validation
- Thumbnail generation for images and documents (PDF, Office files)
- Secure file serving with path traversal prevention
- Organized storage structure by category/subcategory
- File deletion with soft-delete support
- File versioning with group IDs
- Tag-based organization
- Content-addressable storage with hashfs (deduplication)
"""

from pathlib import Path
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from flask import session
import logging
import os
import re
import shutil
import mimetypes
import hashlib

# Database imports
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker, Session
from .file_manager_models import Base, FileGroup, FileVersion, FileTag
from .file_storage import ContentAddressableStorage

# Image processing
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Document thumbnail generation
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

logger = logging.getLogger(__name__)


class FileManager:
    """Manages file upload, storage, retrieval, and deletion with versioning and tagging."""
    
    def __init__(self, settings_manager):
        """Initialize FileManager with settings and database.
        
        Args:
            settings_manager: SettingsManager instance for configuration
        """
        self.settings = settings_manager
        self._load_config()
        self._init_database()
        self._init_storage()
    
    def _load_config(self):
        """Load configuration from settings manager."""
        try:
            # Base path for file storage
            base_path_config = self.settings.get_setting("file_storage.base_path")
            self.base_path = Path(base_path_config.get("value", "resources/uploads"))
            
            # Max file size in bytes
            max_size_mb = self.settings.get_setting("file_storage.max_file_size_mb")
            self.max_file_size = int(max_size_mb.get("value", 50)) * 1024 * 1024
            
            # Allowed extensions
            allowed_ext = self.settings.get_setting("file_storage.allowed_extensions")
            self.allowed_extensions = set(allowed_ext.get("value", [
                ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp",
                ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
                ".txt", ".csv", ".zip", ".7z", ".rar"
            ]))
            
            # Thumbnail settings
            thumbnails_config = self.settings.get_setting("file_storage.generate_thumbnails")
            self.generate_thumbnails = thumbnails_config.get("value", True)
            
            sizes_config = self.settings.get_setting("file_storage.thumbnail_sizes")
            self.thumbnail_sizes = sizes_config.get("value", ["150x150", "300x300"])
            
            quality_config = self.settings.get_setting("file_storage.image_quality")
            self.image_quality = int(quality_config.get("value", 85))
            
            exif_config = self.settings.get_setting("file_storage.strip_exif")
            self.strip_exif = exif_config.get("value", True)
            
            # Categories
            categories_config = self.settings.get_setting("file_storage.categories")
            self.categories = categories_config.get("value", ["general", "documents", "images"])
            
            # Tags (Phase 3)
            tags_config = self.settings.get_setting("file_storage.tags")
            self.tags = tags_config.get("value", ["invoice", "contract", "photo", "report"])
            
            # HashFS settings (Phase 3)
            use_hashfs_config = self.settings.get_setting("file_storage.use_hashfs")
            self.use_hashfs = use_hashfs_config.get("value", True)
            
            hashfs_path_config = self.settings.get_setting("file_storage.hashfs_path")
            self.hashfs_path = Path(hashfs_path_config.get("value", "resources/hashfs_storage"))
            
        except Exception as e:
            logger.warning(f"Failed to load file storage config, using defaults: {e}")
            # Fallback to defaults
            self.base_path = Path("resources/uploads")
            self.max_file_size = 50 * 1024 * 1024
            self.allowed_extensions = {
                ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp",
                ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
                ".txt", ".csv", ".zip", ".7z", ".rar"
            }
            self.generate_thumbnails = True
            self.thumbnail_sizes = ["150x150", "300x300"]
            self.image_quality = 85
            self.strip_exif = True
            self.categories = ["general", "documents", "images"]
            self.tags = ["invoice", "contract", "photo", "report"]
            self.use_hashfs = True
            self.hashfs_path = Path("resources/hashfs_storage")
        
        # Ensure base path exists
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _init_database(self):
        """Initialize SQLite database for file metadata."""
        try:
            # Get settings directory from SettingsManager
            settings_dir = Path(self.settings.storage.config_path).parent
            self.db_path = settings_dir / ".file_metadata.db"
            
            # Create SQLAlchemy engine
            self.engine = create_engine(f'sqlite:///{self.db_path}', echo=False)
            
            # Create all tables (including version tables via Continuum)
            Base.metadata.create_all(self.engine)
            
            # Create session maker
            SessionLocal = sessionmaker(bind=self.engine)
            self.db_session: Session = SessionLocal()
            
            logger.info(f"File manager database initialized at {self.db_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize file manager database: {e}", exc_info=True)
            raise
    
    def _init_storage(self):
        """Initialize content-addressable storage (hashfs) if enabled."""
        if self.use_hashfs:
            try:
                self.storage = ContentAddressableStorage(self.hashfs_path)
                logger.info("Content-addressable storage (hashfs) initialized")
            except Exception as e:
                logger.error(f"Failed to initialize hashfs: {e}", exc_info=True)
                self.use_hashfs = False
                self.storage = None
        else:
            self.storage = None
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent security issues.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Use werkzeug's secure_filename as base
        safe_name = secure_filename(filename)
        
        # Additional sanitization: remove any remaining special chars
        safe_name = re.sub(r'[^\w\-_\. ]', '', safe_name)
        
        # Limit length
        name, ext = os.path.splitext(safe_name)
        if len(name) > 200:
            name = name[:200]
        
        return f"{name}{ext}".strip()
    
    def _validate_file(self, file_obj: FileStorage) -> Tuple[bool, Optional[str]]:
        """Validate file against security and configuration rules.
        
        Args:
            file_obj: Flask FileStorage object
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if file exists
        if not file_obj or not file_obj.filename:
            return False, "No file provided"
        
        # Check file extension
        ext = os.path.splitext(file_obj.filename)[1].lower()
        if ext not in self.allowed_extensions:
            return False, f"File type '{ext}' not allowed. Allowed types: {', '.join(sorted(self.allowed_extensions))}"
        
        # Check file size
        file_obj.seek(0, os.SEEK_END)
        size = file_obj.tell()
        file_obj.seek(0)  # Reset to beginning
        
        if size > self.max_file_size:
            max_mb = self.max_file_size / (1024 * 1024)
            actual_mb = size / (1024 * 1024)
            return False, f"File too large ({actual_mb:.1f}MB). Maximum allowed: {max_mb:.0f}MB"
        
        if size == 0:
            return False, "File is empty"
        
        return True, None
    
    def _get_unique_filename(self, directory: Path, filename: str) -> str:
        """Generate unique filename if collision exists.
        
        Args:
            directory: Target directory
            filename: Desired filename
            
        Returns:
            Unique filename (may have suffix like _1, _2, etc.)
        """
        target_path = directory / filename
        if not target_path.exists():
            return filename
        
        # File exists, add numeric suffix
        name, ext = os.path.splitext(filename)
        counter = 1
        while True:
            new_filename = f"{name}_{counter}{ext}"
            if not (directory / new_filename).exists():
                return new_filename
            counter += 1
    
    def _secure_path(self, relative_path: str) -> Path:
        """Validate and resolve path to prevent traversal attacks.
        
        Args:
            relative_path: Path relative to base_path
            
        Returns:
            Resolved absolute Path
            
        Raises:
            ValueError: If path traversal attempt detected
        """
        # Normalize path separators
        relative_path = relative_path.replace('\\', '/')
        
        # Check for path traversal attempts
        if '..' in relative_path or relative_path.startswith('/') or ':' in relative_path:
            raise ValueError(f"Invalid path: path traversal attempt detected in '{relative_path}'")
        
        # Resolve absolute path
        abs_path = (self.base_path / relative_path).resolve()
        
        # Ensure resolved path is within base_path
        try:
            abs_path.relative_to(self.base_path.resolve())
        except ValueError:
            raise ValueError(f"Invalid path: '{relative_path}' resolves outside storage directory")
        
        return abs_path
    
    def upload_file(self, file_obj: FileStorage, category: str = None, subcategory: str = "", 
                    group_id: str = None, tags: List[str] = None) -> Dict:
        """Upload file with versioning support.
        
        Args:
            file_obj: Flask FileStorage object from request.files
            category: Category for file organization (deprecated for group_id, kept for compatibility)
            subcategory: Subcategory (deprecated for group_id, kept for compatibility)
            group_id: Logical group ID for versioning (empty field shown in admin)
            tags: List of tags for file organization
            
        Returns:
            Dictionary with file metadata:
            {
                "id": Database ID,
                "path": "storage/path/in/hashfs or filesystem",
                "name": "filename.ext",
                "size": 12345,
                "group_id": "group identifier",
                "version": 2,
                "is_current": True,
                "uploaded_at": "2025-11-17T10:30:00Z",
                "uploaded_by": "username",
                "checksum": "sha256hash...",
                "tags": ["tag1", "tag2"],
                "thumbnail_150x150": "path/to/thumb" (if generated)
            }
            
        Raises:
            ValueError: Invalid file type, size, or name
            IOError: File system errors
        """
        # Validate file
        is_valid, error_msg = self._validate_file(file_obj)
        if not is_valid:
            raise ValueError(error_msg)
        
        # Sanitize filename
        original_filename = file_obj.filename
        safe_filename = self._sanitize_filename(original_filename)
        
        if not safe_filename:
            raise ValueError(f"Invalid filename: '{original_filename}'")
        
        # Determine group_id (admin can specify, or empty string for user to see)
        if not group_id:
            # Empty group_id - will be shown as empty field in admin
            group_id = ""
        
        # Get current user
        current_user = session.get('user', 'GUEST')
        
        # Check if file group exists, create if needed (only if group_id specified)
        if group_id:
            file_group = self.db_session.query(FileGroup).filter_by(group_id=group_id).first()
            if not file_group:
                file_group = FileGroup(
                    group_id=group_id,
                    name=group_id,
                    description=f"Auto-created group for {group_id}",
                    created_by=current_user
                )
                self.db_session.add(file_group)
                self.db_session.commit()
        
        # Check for existing versions of this file in the same group
        if group_id:
            existing_versions = self.db_session.query(FileVersion).filter(
                and_(
                    FileVersion.group_id == group_id,
                    FileVersion.filename == safe_filename
                )
            ).all()
            version_number = len(existing_versions) + 1
            
            # Mark all existing versions as not current
            for existing in existing_versions:
                existing.is_current = False
        else:
            # No group_id means standalone file
            version_number = 1
        
        # Store file content
        storage_path = None
        checksum = None
        file_size = 0
        
        if self.use_hashfs and self.storage:
            # Use content-addressable storage
            try:
                storage_metadata = self.storage.store(file_obj.stream, safe_filename)
                storage_path = storage_metadata['storage_path']
                checksum = storage_metadata['checksum']
                file_size = storage_metadata['size']
                
                if storage_metadata['is_duplicate']:
                    logger.info(f"File deduplicated (existing content): {safe_filename}")
            except Exception as e:
                logger.error(f"HashFS storage failed, falling back to filesystem: {e}")
                self.use_hashfs = False  # Disable for this session
        
        if not self.use_hashfs or not storage_path:
            # Fallback to traditional filesystem storage
            category_safe = self._sanitize_filename(category) if category else "general"
            subcategory_safe = self._sanitize_filename(subcategory) if subcategory else ""
            
            if subcategory_safe:
                storage_dir = self.base_path / category_safe / subcategory_safe
                relative_dir = f"{category_safe}/{subcategory_safe}"
            else:
                storage_dir = self.base_path / category_safe
                relative_dir = category_safe
            
            storage_dir.mkdir(parents=True, exist_ok=True)
            
            # Add version suffix to physical filename
            if version_number > 1:
                name_part = Path(safe_filename).stem
                ext_part = Path(safe_filename).suffix
                versioned_filename = f"{name_part}_v{version_number}{ext_part}"
            else:
                versioned_filename = safe_filename
            
            file_path = storage_dir / versioned_filename
            storage_path = f"{relative_dir}/{versioned_filename}"
            
            # Save file
            try:
                file_obj.seek(0)  # Reset stream position
                file_obj.save(str(file_path))
                file_size = file_path.stat().st_size
                
                # Calculate checksum
                checksum = self._calculate_checksum(file_path)
            except Exception as e:
                logger.error(f"Failed to save file {file_path}: {e}")
                raise IOError(f"Failed to save file: {e}")
        
        # Get MIME type
        mime_type = mimetypes.guess_type(safe_filename)[0] or 'application/octet-stream'
        
        # Create database record
        file_version = FileVersion(
            group_id=group_id if group_id else None,
            filename=safe_filename,
            storage_path=storage_path,
            file_size=file_size,
            mime_type=mime_type,
            checksum=checksum,
            uploaded_by=current_user,
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
        
        # Prepare metadata response
        metadata = {
            "id": file_version.id,
            "path": storage_path,
            "name": safe_filename,
            "size": file_size,
            "group_id": group_id or "",
            "version": version_number,
            "is_current": True,
            "uploaded_at": file_version.uploaded_at.isoformat() + "Z",
            "uploaded_by": current_user,
            "checksum": checksum,
            "tags": [tag.tag_name for tag in file_version.tags]
        }
        
        # Generate thumbnails
        if self.generate_thumbnails:
            # Get actual file path for thumbnail generation
            if self.use_hashfs and self.storage:
                actual_file_path = self.storage.get(storage_path)
            else:
                actual_file_path = self.base_path / storage_path
            
            thumbnails = self._generate_thumbnails(actual_file_path, storage_path)
            metadata.update(thumbnails)
        
        logger.info(f"File uploaded: {safe_filename} (group: {group_id or 'none'}, version: {version_number}, size: {file_size} bytes)")
        return metadata
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum for a file.
        
        Args:
            file_path: Path to file
            
        Returns:
            SHA256 hash as hex string
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _generate_thumbnails(self, file_path: Path, relative_path: str) -> Dict:
        """Generate thumbnails for images and documents.
        
        Args:
            file_path: Absolute path to file
            relative_path: Relative path for thumbnail naming
            
        Returns:
            Dictionary with thumbnail paths (e.g., {"thumbnail_small": "path"})
        """
        thumbnails = {}
        ext = file_path.suffix.lower()
        
        # Determine file type and generate thumbnails
        if ext in {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}:
            # Image files - use Pillow
            if PIL_AVAILABLE:
                thumbnails = self._generate_image_thumbnails(file_path, relative_path)
        
        elif ext == '.pdf':
            # PDF files - use PyMuPDF
            if PYMUPDF_AVAILABLE:
                thumbnails = self._generate_pdf_thumbnails(file_path, relative_path)
        
        elif ext in {'.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'}:
            # Office files - would need LibreOffice or similar, skip for now
            # Could be added as Phase 3 enhancement
            logger.debug(f"Thumbnail generation for {ext} not yet implemented")
        
        return thumbnails
    
    def _generate_image_thumbnails(self, file_path: Path, relative_path: str) -> Dict:
        """Generate thumbnails for image files using Pillow.
        
        Args:
            file_path: Absolute path to image
            relative_path: Relative path for thumbnail storage
            
        Returns:
            Dictionary with thumbnail paths
        """
        if not PIL_AVAILABLE:
            return {}
        
        thumbnails = {}
        
        try:
            # Open image
            with Image.open(file_path) as img:
                # Convert RGBA to RGB if needed (for JPEG)
                if img.mode == 'RGBA':
                    # Create white background
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
                    img = background
                elif img.mode not in ('RGB', 'L'):
                    img = img.convert('RGB')
                
                # Strip EXIF if configured
                if self.strip_exif:
                    # Create new image without EXIF
                    data = list(img.getdata())
                    image_without_exif = Image.new(img.mode, img.size)
                    image_without_exif.putdata(data)
                    img = image_without_exif
                
                # Generate thumbnails for each size
                for size_str in self.thumbnail_sizes:
                    try:
                        width, height = map(int, size_str.split('x'))
                        thumb_name = f"thumb_{width}x{height}"
                        
                        # Create thumbnail directory
                        thumb_dir = self.base_path / ".thumbs" / size_str / Path(relative_path).parent
                        thumb_dir.mkdir(parents=True, exist_ok=True)
                        
                        # Generate thumbnail path
                        thumb_filename = f"{file_path.stem}_thumb.jpg"
                        thumb_path = thumb_dir / thumb_filename
                        thumb_relative = f".thumbs/{size_str}/{Path(relative_path).parent}/{thumb_filename}"
                        
                        # Create thumbnail
                        img_copy = img.copy()
                        img_copy.thumbnail((width, height), Image.Resampling.LANCZOS)
                        img_copy.save(thumb_path, 'JPEG', quality=self.image_quality, optimize=True)
                        
                        thumbnails[thumb_name] = thumb_relative.replace('\\', '/')
                        logger.debug(f"Generated thumbnail: {thumb_relative}")
                        
                    except Exception as e:
                        logger.warning(f"Failed to generate {size_str} thumbnail for {relative_path}: {e}")
        
        except Exception as e:
            logger.error(f"Failed to process image {file_path}: {e}")
        
        return thumbnails
    
    def _generate_pdf_thumbnails(self, file_path: Path, relative_path: str) -> Dict:
        """Generate thumbnails for PDF files using PyMuPDF.
        
        Args:
            file_path: Absolute path to PDF
            relative_path: Relative path for thumbnail storage
            
        Returns:
            Dictionary with thumbnail paths
        """
        if not PYMUPDF_AVAILABLE:
            return {}
        
        thumbnails = {}
        
        try:
            # Open PDF
            doc = fitz.open(file_path)
            
            # Only process first page for thumbnail
            if len(doc) == 0:
                return {}
            
            page = doc[0]
            
            # Generate thumbnails for each size
            for size_str in self.thumbnail_sizes:
                try:
                    width, height = map(int, size_str.split('x'))
                    thumb_name = f"thumb_{width}x{height}"
                    
                    # Create thumbnail directory
                    thumb_dir = self.base_path / ".thumbs" / size_str / Path(relative_path).parent
                    thumb_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Generate thumbnail path
                    thumb_filename = f"{file_path.stem}_thumb.jpg"
                    thumb_path = thumb_dir / thumb_filename
                    thumb_relative = f".thumbs/{size_str}/{Path(relative_path).parent}/{thumb_filename}"
                    
                    # Calculate zoom to fit within thumbnail size
                    page_rect = page.rect
                    zoom_x = width / page_rect.width
                    zoom_y = height / page_rect.height
                    zoom = min(zoom_x, zoom_y)
                    
                    # Render page to pixmap
                    mat = fitz.Matrix(zoom, zoom)
                    pix = page.get_pixmap(matrix=mat, alpha=False)
                    
                    # Save as JPEG
                    pix.save(thumb_path, "jpeg", jpg_quality=self.image_quality)
                    
                    thumbnails[thumb_name] = thumb_relative.replace('\\', '/')
                    logger.debug(f"Generated PDF thumbnail: {thumb_relative}")
                    
                except Exception as e:
                    logger.warning(f"Failed to generate {size_str} thumbnail for PDF {relative_path}: {e}")
            
            doc.close()
            
        except Exception as e:
            logger.error(f"Failed to process PDF {file_path}: {e}")
        
        return thumbnails
    
    def get_file_path(self, relative_path: str) -> Path:
        """Get absolute path for a relative file path with security checks.
        
        Args:
            relative_path: Path relative to base_path
            
        Returns:
            Absolute Path object
            
        Raises:
            ValueError: Path traversal attempt detected
            FileNotFoundError: File does not exist
        """
        abs_path = self._secure_path(relative_path)
        
        if not abs_path.exists():
            raise FileNotFoundError(f"File not found: {relative_path}")
        
        return abs_path
    
    def delete_file(self, relative_path: str, soft_delete: bool = True) -> bool:
        """Delete a file.
        
        Args:
            relative_path: Path relative to base_path
            soft_delete: Move to .trash instead of permanent delete (default: True)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            file_path = self._secure_path(relative_path)
            
            if not file_path.exists():
                logger.warning(f"Attempted to delete non-existent file: {relative_path}")
                return False
            
            if soft_delete:
                # Move to trash
                trash_dir = self.base_path / ".trash"
                trash_dir.mkdir(parents=True, exist_ok=True)
                
                # Preserve directory structure in trash
                trash_path = trash_dir / relative_path
                trash_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Add timestamp to avoid collisions
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                trash_filename = f"{file_path.stem}_{timestamp}{file_path.suffix}"
                trash_path = trash_path.parent / trash_filename
                
                shutil.move(str(file_path), str(trash_path))
                logger.info(f"File moved to trash: {relative_path} -> {trash_path}")
            else:
                # Permanent delete
                file_path.unlink()
                logger.info(f"File permanently deleted: {relative_path}")
            
            # Delete associated thumbnails
            self._delete_thumbnails(relative_path)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete file {relative_path}: {e}")
            return False
    
    def _delete_thumbnails(self, relative_path: str):
        """Delete all thumbnails associated with a file.
        
        Args:
            relative_path: Original file's relative path
        """
        file_stem = Path(relative_path).stem
        file_parent = Path(relative_path).parent
        
        for size_str in self.thumbnail_sizes:
            thumb_dir = self.base_path / ".thumbs" / size_str / file_parent
            if thumb_dir.exists():
                thumb_file = thumb_dir / f"{file_stem}_thumb.jpg"
                if thumb_file.exists():
                    try:
                        thumb_file.unlink()
                        logger.debug(f"Deleted thumbnail: {thumb_file}")
                    except Exception as e:
                        logger.warning(f"Failed to delete thumbnail {thumb_file}: {e}")
    
    def list_files(self, category: str = "", subcategory: str = "") -> List[Dict]:
        """List all files in a category/subcategory.
        
        Args:
            category: Top-level category (empty = all categories)
            subcategory: Subcategory (empty = all subcategories)
            
        Returns:
            List of metadata dicts (same format as upload_file)
        """
        files = []
        
        if category:
            category_safe = self._sanitize_filename(category)
            if subcategory:
                subcategory_safe = self._sanitize_filename(subcategory)
                search_dir = self.base_path / category_safe / subcategory_safe
            else:
                search_dir = self.base_path / category_safe
        else:
            search_dir = self.base_path
        
        if not search_dir.exists():
            return []
        
        # Walk through directory tree
        for file_path in search_dir.rglob('*'):
            # Skip directories, hidden files, and special folders
            if file_path.is_dir() or file_path.name.startswith('.'):
                continue
            
            # Skip files in special folders (.thumbs, .trash)
            if any(part.startswith('.') for part in file_path.parts):
                continue
            
            try:
                relative_path = file_path.relative_to(self.base_path)
                stat = file_path.stat()
                
                metadata = {
                    "path": str(relative_path).replace('\\', '/'),
                    "name": file_path.name,
                    "size": stat.st_size,
                    "uploaded_at": datetime.fromtimestamp(stat.st_mtime).isoformat() + "Z"
                }
                
                # Add thumbnail paths if they exist
                for size_str in self.thumbnail_sizes:
                    width, height = map(int, size_str.split('x'))
                    thumb_key = f"thumb_{width}x{height}"
                    thumb_path = self.base_path / ".thumbs" / size_str / relative_path.parent / f"{file_path.stem}_thumb.jpg"
                    
                    if thumb_path.exists():
                        thumb_relative = str(thumb_path.relative_to(self.base_path)).replace('\\', '/')
                        metadata[thumb_key] = thumb_relative
                
                files.append(metadata)
                
            except Exception as e:
                logger.warning(f"Failed to process file {file_path}: {e}")
        
        # Sort by upload date (most recent first)
        files.sort(key=lambda x: x['uploaded_at'], reverse=True)
        
        return files
    
    def get_mime_type(self, relative_path: str) -> str:
        """Get MIME type for a file.
        
        Args:
            relative_path: Path relative to base_path
            
        Returns:
            MIME type string (e.g., "image/jpeg")
        """
        file_path = self._secure_path(relative_path)
        mime_type, _ = mimetypes.guess_type(str(file_path))
        return mime_type or 'application/octet-stream'
    
    def get_categories(self) -> List[str]:
        """Get list of configured file categories.
        
        Returns:
            List of category names
        """
        return self.categories.copy()
    
    def get_tags(self) -> List[str]:
        """Get list of configured file tags.
        
        Returns:
            List of tag names
        """
        return self.tags.copy()
    
    def create_file_group(self, group_id: str, name: str, description: str = "") -> FileGroup:
        """Create a new file group.
        
        Args:
            group_id: Unique identifier for the group
            name: Human-readable name
            description: Optional description
            
        Returns:
            FileGroup object
        """
        file_group = FileGroup(
            group_id=group_id,
            name=name,
            description=description,
            created_by=session.get('user', 'GUEST')
        )
        self.db_session.add(file_group)
        self.db_session.commit()
        return file_group
    
    def get_file_by_id(self, file_id: int) -> Optional[FileVersion]:
        """Get file version by database ID.
        
        Args:
            file_id: Database ID
            
        Returns:
            FileVersion object or None
        """
        return self.db_session.query(FileVersion).filter_by(id=file_id).first()
    
    def get_current_file(self, group_id: str, filename: str) -> Optional[FileVersion]:
        """Get current version of a file in a group.
        
        Args:
            group_id: Group identifier
            filename: Filename to search for
            
        Returns:
            FileVersion object or None
        """
        return self.db_session.query(FileVersion).filter(
            and_(
                FileVersion.group_id == group_id,
                FileVersion.filename == filename,
                FileVersion.is_current == True
            )
        ).first()
    
    def get_file_versions(self, group_id: str, filename: str) -> List[Dict]:
        """Get all versions of a file using SQLAlchemy-Continuum.
        
        Args:
            group_id: Group identifier
            filename: Filename
            
        Returns:
            List of version dictionaries with metadata
        """
        # Get all versions (current and historical)
        all_versions = self.db_session.query(FileVersion).filter(
            and_(
                FileVersion.group_id == group_id,
                FileVersion.filename == filename
            )
        ).order_by(FileVersion.uploaded_at).all()
        
        versions = []
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
    
    def restore_version(self, file_id: int, target_version_id: int) -> FileVersion:
        """Restore an old version by creating a new version as a copy.
        
        This preserves the audit trail by creating a new version record that points
        to the same physical file as the target version.
        
        Args:
            file_id: ID of current file version
            target_version_id: ID of version to restore from
            
        Returns:
            New FileVersion object (the restored copy)
            
        Raises:
            ValueError: If files not found
        """
        current = self.db_session.query(FileVersion).get(file_id)
        target = self.db_session.query(FileVersion).get(target_version_id)
        
        if not current or not target:
            raise ValueError("File version not found")
        
        if current.group_id != target.group_id or current.filename != target.filename:
            raise ValueError("Cannot restore from different file")
        
        # Mark current as not current
        current.is_current = False
        
        # Create new version as copy of target
        restored = FileVersion(
            group_id=current.group_id,
            filename=current.filename,
            storage_path=target.storage_path,  # Reuse same physical file!
            file_size=target.file_size,
            mime_type=target.mime_type,
            checksum=target.checksum,
            uploaded_by=session.get('user', 'GUEST'),
            is_current=True,
            source_version_id=target_version_id
        )
        
        # Copy tags from target version
        for tag in target.tags:
            restored.tags.append(tag)
        
        self.db_session.add(restored)
        self.db_session.commit()
        
        logger.info(f"Restored file version: {current.filename} (from v{target_version_id} to new version)")
        return restored
    
    def search_by_tags(self, tags: List[str], match_all: bool = False) -> List[FileVersion]:
        """Search files by tags.
        
        Args:
            tags: List of tag names to search for
            match_all: If True, file must have ALL tags. If False, any tag matches.
            
        Returns:
            List of FileVersion objects matching the search
        """
        query = self.db_session.query(FileVersion).join(
            FileVersion.tags
        ).filter(
            FileTag.tag_name.in_(tags),
            FileVersion.is_current == True
        )
        
        if match_all:
            # Must have all tags
            for tag_name in tags:
                query = query.filter(
                    FileVersion.tags.any(FileTag.tag_name == tag_name)
                )
        
        return query.distinct().all()
    
    def list_files_from_db(self, group_id: str = None, tag: str = None, limit: int = None) -> List[Dict]:
        """List files from database (replaces filesystem-based list_files).
        
        Args:
            group_id: Filter by group ID (optional)
            tag: Filter by tag (optional)
            limit: Maximum number of results (optional)
            
        Returns:
            List of file metadata dictionaries
        """
        query = self.db_session.query(FileVersion).filter(FileVersion.is_current == True)
        
        if group_id:
            query = query.filter(FileVersion.group_id == group_id)
        
        if tag:
            query = query.join(FileVersion.tags).filter(FileTag.tag_name == tag)
        
        query = query.order_by(FileVersion.uploaded_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        files = []
        for file_version in query.all():
            metadata = {
                "id": file_version.id,
                "path": file_version.storage_path,
                "name": file_version.filename,
                "size": file_version.file_size,
                "group_id": file_version.group_id or "",
                "uploaded_at": file_version.uploaded_at.isoformat() + "Z",
                "uploaded_by": file_version.uploaded_by,
                "checksum": file_version.checksum,
                "tags": [tag.tag_name for tag in file_version.tags],
                "mime_type": file_version.mime_type
            }
            
            # Add thumbnail paths if they exist
            for size_str in self.thumbnail_sizes:
                width, height = map(int, size_str.split('x'))
                thumb_key = f"thumb_{width}x{height}"
                
                # Construct thumbnail path
                storage_path_obj = Path(file_version.storage_path)
                thumb_path = self.base_path / ".thumbs" / size_str / storage_path_obj.parent / f"{storage_path_obj.stem}_thumb.jpg"
                
                if thumb_path.exists():
                    thumb_relative = str(thumb_path.relative_to(self.base_path)).replace('\\', '/')
                    metadata[thumb_key] = thumb_relative
            
            files.append(metadata)
        
        return files
    
    def update_group_id(self, file_id: int, new_group_id: str) -> bool:
        """Update the group_id of a file (admin function).
        
        Args:
            file_id: Database ID of file
            new_group_id: New group ID to assign
            
        Returns:
            True if successful
        """
        file_version = self.db_session.query(FileVersion).get(file_id)
        if not file_version:
            return False
        
        # Create group if it doesn't exist
        if new_group_id:
            file_group = self.db_session.query(FileGroup).filter_by(group_id=new_group_id).first()
            if not file_group:
                self.create_file_group(new_group_id, new_group_id, "Auto-created")
        
        file_version.group_id = new_group_id if new_group_id else None
        self.db_session.commit()
        
        logger.info(f"Updated group_id for file {file_id}: {new_group_id}")
        return True


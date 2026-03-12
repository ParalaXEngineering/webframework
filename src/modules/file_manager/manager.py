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
from typing import Optional, Dict, List, Tuple, Any
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
import os
import re
import mimetypes
import hashlib

# Database imports
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker, Session
from .models import Base, FileGroup, FileVersion, FileTag, file_version_tags
from .storage import ContentAddressableStorage

# Framework i18n
from ..i18n.messages import (
    ERROR_NO_FILE_PROVIDED_VALIDATION,
    ERROR_FILE_TYPE_NOT_ALLOWED,
    ERROR_FILE_TOO_LARGE_VALIDATION,
    ERROR_FILE_IS_EMPTY,
    ERROR_FILENAME_REQUIRED_VALIDATION,
    ERROR_INVALID_FILENAME,
    ERROR_INVALID_TAGS,
    ERROR_INVALID_CATEGORY,
    ERROR_FILE_VERSION_NOT_FOUND,
    ERROR_CANNOT_RESTORE_DIFFERENT_FILE,
)

# Image processing
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Document thumbnail generation
try:
    import pymupdf as fitz  # PyMuPDF (new import style for version 1.24+)
    PYMUPDF_AVAILABLE = True
except ImportError:
    try:
        import fitz  # PyMuPDF (legacy import style)
        PYMUPDF_AVAILABLE = True
    except ImportError:
        PYMUPDF_AVAILABLE = False

try:
    from ..log.logger_factory import get_logger
except ImportError:
    from log.logger_factory import get_logger

logger = get_logger("file_manager.manager")


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
        """Load configuration from settings manager.
        
        Framework's default_configs.py ensures all values exist, so no manual fallbacks needed.
        """
        # HashFS path for file storage
        self.hashfs_path = Path(self.settings.get_setting("file_storage.hashfs_path"))
        
        # Max file size in bytes
        self.max_file_size = int(self.settings.get_setting("file_storage.max_file_size_mb")) * 1024 * 1024
        
        # Allowed extensions (convert to set for fast lookup)
        self.allowed_extensions = set(self.settings.get_setting("file_storage.allowed_extensions"))
        
        # Thumbnail settings
        self.generate_thumbnails = self.settings.get_setting("file_storage.generate_thumbnails")
        self.thumbnail_sizes = self.settings.get_setting("file_storage.thumbnail_sizes")
        self.image_quality = int(self.settings.get_setting("file_storage.image_quality"))
        self.strip_exif = self.settings.get_setting("file_storage.strip_exif")
        
        # Categories, group IDs, and tags
        self.categories = self.settings.get_setting("file_storage.categories")
        self.group_ids = self.settings.get_setting("file_storage.group_ids")
        self.tags = self.settings.get_setting("file_storage.tags")
        
        # Ensure hashfs path exists
        self.hashfs_path.mkdir(parents=True, exist_ok=True)
    
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
            
            logger.info("File manager database initialized at %s", self.db_path)
            
        except Exception as e:
            logger.error("Failed to initialize file manager database: %s", e, exc_info=True)
            raise
    
    def _init_storage(self):
        """Initialize content-addressable storage (hashfs)."""
        try:
            self.storage = ContentAddressableStorage(self.hashfs_path)
            logger.info("Content-addressable storage (hashfs) initialized")
        except Exception as e:
            logger.error("Failed to initialize hashfs: %s", e, exc_info=True)
            raise RuntimeError(f"HashFS initialization failed: {e}")
    
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
            return False, str(ERROR_NO_FILE_PROVIDED_VALIDATION)
        
        # Check file extension
        ext = os.path.splitext(file_obj.filename)[1].lower()
        if ext not in self.allowed_extensions:
            allowed_types = ', '.join(sorted(self.allowed_extensions))
            return False, ERROR_FILE_TYPE_NOT_ALLOWED.format(ext=ext, allowed_types=allowed_types)
        
        # Check file size
        file_obj.seek(0, os.SEEK_END)
        size = file_obj.tell()
        file_obj.seek(0)  # Reset to beginning
        
        if size > self.max_file_size:
            max_mb = self.max_file_size / (1024 * 1024)
            actual_mb = size / (1024 * 1024)
            return False, ERROR_FILE_TOO_LARGE_VALIDATION.format(actual_mb=actual_mb, max_mb=max_mb)
        
        if size == 0:
            return False, str(ERROR_FILE_IS_EMPTY)
        
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
    
    def upload_file(self, file_obj: FileStorage, category: Optional[str] = None, subcategory: str = "", 
                    group_id: Optional[str] = None, tags: Optional[List[str]] = None, 
                    uploaded_by: Optional[str] = None) -> Dict[str, Any]:
        """Upload file with versioning support.
        
        Args:
            file_obj: Flask FileStorage object from request.files
            category: Category for file organization (optional, validated against config)
            subcategory: Deprecated, kept for backward compatibility (not validated)
            group_id: Logical group ID for versioning (None = standalone file, no versioning)
            tags: List of tags for file organization (optional, validated against config)
            uploaded_by: Username of uploader (optional, defaults to 'GUEST')
            
        Returns:
            Dictionary with file metadata::
            
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
        if not original_filename:
            raise ValueError(str(ERROR_FILENAME_REQUIRED_VALIDATION))
        safe_filename = self._sanitize_filename(original_filename)
        
        if not safe_filename:
            raise ValueError(ERROR_INVALID_FILENAME.format(filename=original_filename))
        
        # Validate tags (if provided)
        if tags:
            valid_tags = self.tags
            # Extract tag names from FileTag objects or use strings directly
            tag_names = [t.tag_name if isinstance(t, FileTag) else t for t in tags]
            invalid_tags = [t for t in tag_names if t not in valid_tags]
            if invalid_tags:
                raise ValueError(
                    ERROR_INVALID_TAGS.format(invalid_tags=invalid_tags, valid_tags=valid_tags)
                )
        
        # Validate category (if provided and not empty)
        if category and category != 'general':
            valid_categories = self.categories
            if category not in valid_categories:
                raise ValueError(
                    ERROR_INVALID_CATEGORY.format(category=category, valid_categories=valid_categories)
                )
        
        # Determine group_id (admin can specify, or None for files without a group)
        # Convert empty strings to None for consistent NULL handling in database
        if not group_id:
            group_id = None
        
        # Get current user from parameter or default
        current_user = uploaded_by if uploaded_by else 'GUEST'
        
        # Handle group_id: accept both string and FileGroup object
        if group_id:
            if isinstance(group_id, FileGroup):
                # Already a FileGroup object, use its group_id
                file_group = group_id
                group_id = file_group.group_id
            else:
                # String group_id - query for existing (should already exist if pre-resolved)
                file_group = self.db_session.query(FileGroup).filter_by(group_id=group_id).first()
                if not file_group:
                    # Fallback: create if not found (backward compatibility)
                    file_group = FileGroup(
                        group_id=group_id,
                        name=group_id,
                        description=f"Auto-created group for {group_id}",
                        created_by=current_user
                    )
                    self.db_session.add(file_group)
                    self.db_session.flush()
        
        # Check for existing versions of this file
        # ONLY files with a group_id have versioning
        # Files without group_id are standalone (no versioning)
        if group_id:
            # Files with a specific group - enable versioning
            existing_versions = self.db_session.query(FileVersion).filter(
                and_(
                    FileVersion.group_id == group_id,
                    FileVersion.filename == safe_filename
                )
            ).all()
            
            version_number = len(existing_versions) + 1
            
            # Mark all existing versions as not current
            for existing in existing_versions:
                existing.is_current = False  # type: ignore[assignment]
        else:
            # Files without a group are standalone (no versioning)
            existing_versions = []
            version_number = 1
        
        # Store file content in HashFS
        try:
            storage_metadata = self.storage.store(file_obj.stream, safe_filename)  # type: ignore[arg-type]
            storage_path = storage_metadata['storage_path']
            checksum = storage_metadata['checksum']
            file_size = storage_metadata['size']
            
            if storage_metadata['is_duplicate']:
                logger.info("File deduplicated (existing content): %s", safe_filename)
        except Exception as e:
            logger.error("HashFS storage failed: %s", e, exc_info=True)
            raise IOError(f"Failed to store file in HashFS: {e}")
        
        # Get MIME type
        mime_type = mimetypes.guess_type(safe_filename)[0] or 'application/octet-stream'
        
        # Create database record
        # Note: group_id can be None (NULL in database) for files without a group
        # Prepare tag list BEFORE creating FileVersion
        tag_list = []
        if tags:
            for tag in tags:
                # Tag can be either a FileTag object or a string (backward compatibility)
                if isinstance(tag, str):
                    # Legacy mode: query tag (may cause session issues)
                    tag_obj = self.db_session.query(FileTag).filter_by(tag_name=tag).first()
                    if not tag_obj:
                        tag_obj = FileTag(tag_name=tag)
                        self.db_session.add(tag_obj)
                        self.db_session.flush()  # Flush to get ID
                    tag_list.append(tag_obj)
                else:
                    # New mode: pre-resolved tag object
                    tag_list.append(tag)
        
        # Create FileVersion with tags already assigned
        file_version = FileVersion(
            group_id=group_id,
            filename=safe_filename,
            storage_path=storage_path,
            file_size=file_size,
            mime_type=mime_type,
            checksum=checksum,
            uploaded_by=current_user,
            is_current=True,
            tags=tag_list  # Assign tags during construction
        )
        
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
            # Get actual file path from HashFS
            actual_file_path = self.storage.get(storage_path)
            logger.info("Generating thumbnails for %s at %s", safe_filename, actual_file_path)
            thumbnails = self._generate_thumbnails(actual_file_path, storage_path, safe_filename)
            if thumbnails:
                logger.info("Adding %s thumbnails to metadata: %s", len(thumbnails), list(thumbnails.keys()))
                metadata.update(thumbnails)
            else:
                logger.warning("No thumbnails generated for %s", safe_filename)
        else:
            logger.info("Thumbnail generation is disabled")
        
        logger.info("File uploaded: %s (group: %s, version: %s, size: %s bytes)", safe_filename, group_id or 'none', version_number, file_size)
        return metadata

    def get_or_create_group(self, group_id: str, created_by: str = 'GUEST') -> 'FileGroup':
        """
        Get existing file group or create new one.
        Uses flush() instead of commit() to resolve IDs without closing transaction.
        
        Args:
            group_id: The group identifier
            created_by: Username creating the group (default: 'GUEST')
            
        Returns:
            FileGroup object (either existing or newly created)
        """
        # Query for existing group
        file_group = self.db_session.query(FileGroup).filter_by(group_id=group_id).first()
        
        if not file_group:
            # Create new group
            file_group = FileGroup(
                group_id=group_id,
                name=group_id,
                description=f"Auto-created group for {group_id}",
                created_by=created_by
            )
            self.db_session.add(file_group)
            # Flush to assign ID without committing
            self.db_session.flush()
        
        return file_group

    def get_or_create_tag(self, tag_name: str) -> 'FileTag':
        """Get existing tag or create new one.
        
        This method should be called BEFORE upload_file to pre-resolve tags
        and avoid session state conflicts during upload.
        
        Args:
            tag_name: Name of the tag
            
        Returns:
            FileTag object (may be unsaved if new)
        """
        # Try to find existing tag
        tag = self.db_session.query(FileTag).filter_by(tag_name=tag_name).first()
        
        if not tag:
            # Create new tag (but don't commit yet)
            tag = FileTag(tag_name=tag_name)
            self.db_session.add(tag)
            # Flush to get the ID but don't commit the transaction
            self.db_session.flush()
        
        return tag
    
    def regenerate_thumbnail(self, thumb_relative_path: str) -> Optional[Path]:
        """Try to regenerate a missing thumbnail from the original stored file.

        Args:
            thumb_relative_path: Relative path like ".thumbs/150x150/ab/c1/abc123_thumb.jpg"

        Returns:
            Absolute Path to the regenerated thumbnail, or None if regeneration failed
        """
        from .models import THUMB_DIR, THUMB_SUFFIX
        try:
            # Parse: .thumbs/SIZE/hash_dirs/hash_thumb.jpg
            if not thumb_relative_path.startswith(THUMB_DIR + '/'):
                return None
            without_thumbdir = thumb_relative_path[len(THUMB_DIR) + 1:]  # e.g. "150x150/ab/c1/hash_thumb.jpg"
            slash_pos = without_thumbdir.find('/')
            if slash_pos < 0:
                return None
            rest = without_thumbdir[slash_pos + 1:]  # e.g. "ab/c1/hash_thumb.jpg"

            if not rest.endswith(THUMB_SUFFIX):
                return None
            storage_path = rest[:-len(THUMB_SUFFIX)]  # e.g. "ab/c1/hash"

            # Look up file version in DB to get original filename (for extension)
            file_version = self.db_session.query(FileVersion).filter_by(storage_path=storage_path).first()
            if not file_version:
                logger.debug("Thumbnail regen: no file version for storage_path=%s", storage_path)
                return None

            # Get original file from HashFS
            try:
                actual_file_path = self.storage.get(storage_path)
            except IOError:
                logger.debug("Thumbnail regen: original file not found in storage: %s", storage_path)
                return None

            # Regenerate thumbnails
            thumbnails = self._generate_thumbnails(actual_file_path, storage_path, file_version.filename)

            if thumbnails:
                thumb_abs = self.hashfs_path.parent / thumb_relative_path
                if thumb_abs.exists():
                    logger.info("Thumbnail regenerated for: %s", thumb_relative_path)
                    return thumb_abs

        except Exception as e:
            logger.debug("Thumbnail regeneration failed for %s: %s", thumb_relative_path, e)

        return None

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
    
    def _generate_thumbnails(self, file_path: Path, relative_path: str, original_filename: str) -> Dict:
        """Generate thumbnails for images and documents.
        
        Args:
            file_path: Absolute path to file (may not have extension in HashFS)
            relative_path: Relative path for thumbnail naming
            original_filename: Original filename with extension (for type determination)
            
        Returns:
            Dictionary with thumbnail paths (e.g., {"thumbnail_small": "path"})
        """
        thumbnails = {}
        # Get extension from original filename, not the HashFS path
        ext = Path(original_filename).suffix.lower()
        
        logger.info("Attempting thumbnail generation for %s (ext: %s)", original_filename, ext)
        
        # Determine file type and generate thumbnails
        if ext in {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}:
            # Image files - use Pillow
            if PIL_AVAILABLE:
                logger.info("Generating image thumbnails for %s", original_filename)
                thumbnails = self._generate_image_thumbnails(file_path, relative_path)
            else:
                logger.warning("PIL not available - cannot generate image thumbnails")
        
        elif ext == '.pdf':
            # PDF files - use PyMuPDF
            if PYMUPDF_AVAILABLE:
                logger.info("Generating PDF thumbnails for %s", original_filename)
                thumbnails = self._generate_pdf_thumbnails(file_path, relative_path)
            else:
                logger.warning("PyMuPDF not available - cannot generate PDF thumbnails")
        
        elif ext in {'.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'}:
            # Office files - would need LibreOffice or similar, skip for now
            # Could be added as Phase 3 enhancement
            logger.debug("Thumbnail generation for %s not yet implemented", ext)
        
        logger.info("Generated %s thumbnails for %s: %s", len(thumbnails), original_filename, list(thumbnails.keys()))
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
            with Image.open(file_path) as img:  # type: ignore[possibly-unbound]
                # Convert RGBA to RGB if needed (for JPEG)
                if img.mode == 'RGBA':
                    # Create white background
                    background = Image.new('RGB', img.size, (255, 255, 255))  # type: ignore[possibly-unbound]
                    background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
                    img = background
                elif img.mode not in ('RGB', 'L'):
                    img = img.convert('RGB')
                
                # Strip EXIF if configured
                if self.strip_exif:
                    # Create new image without EXIF
                    data = list(img.getdata())
                    image_without_exif = Image.new(img.mode, img.size)  # type: ignore[possibly-unbound]
                    image_without_exif.putdata(data)
                    img = image_without_exif
                
                # Generate thumbnails for each size
                for size_str in self.thumbnail_sizes:
                    try:
                        width, height = map(int, size_str.split('x'))
                        thumb_name = f"thumb_{width}x{height}"
                        
                        # Create thumbnail directory (separate from hashfs)
                        thumb_base = self.hashfs_path.parent / ".thumbs"
                        thumb_dir = thumb_base / size_str / Path(relative_path).parent
                        thumb_dir.mkdir(parents=True, exist_ok=True)
                        
                        # Generate thumbnail path
                        thumb_filename = f"{file_path.stem}_thumb.jpg"
                        thumb_path = thumb_dir / thumb_filename
                        thumb_relative = f".thumbs/{size_str}/{Path(relative_path).parent}/{thumb_filename}"
                        
                        # Create thumbnail
                        img_copy = img.copy()
                        img_copy.thumbnail((width, height), Image.Resampling.LANCZOS)  # type: ignore[possibly-unbound]
                        img_copy.save(thumb_path, 'JPEG', quality=self.image_quality, optimize=True)
                        
                        thumbnails[thumb_name] = thumb_relative.replace('\\', '/')
                        logger.info("Generated thumbnail: %s at %s", thumb_relative, thumb_path)
                        
                    except Exception as e:
                        logger.error("Failed to generate %s thumbnail for %s: %s", size_str, relative_path, e, exc_info=True)
        
        except Exception as e:
            logger.error("Failed to process image %s: %s", file_path, e)
        
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
            doc = fitz.open(file_path)  # type: ignore[possibly-unbound]
            
            # Only process first page for thumbnail
            if len(doc) == 0:
                return {}
            
            page = doc[0]
            
            # Generate thumbnails for each size
            for size_str in self.thumbnail_sizes:
                try:
                    width, height = map(int, size_str.split('x'))
                    thumb_name = f"thumb_{width}x{height}"
                    
                    # Create thumbnail directory (separate from hashfs)
                    thumb_base = self.hashfs_path.parent / ".thumbs"
                    thumb_dir = thumb_base / size_str / Path(relative_path).parent
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
                    mat = fitz.Matrix(zoom, zoom)  # type: ignore[possibly-unbound]
                    pix = page.get_pixmap(matrix=mat, alpha=False)  # type: ignore
                    
                    # Save as JPEG
                    pix.save(thumb_path, "jpeg", jpg_quality=self.image_quality)
                    
                    thumbnails[thumb_name] = thumb_relative.replace('\\', '/')
                    logger.debug("Generated PDF thumbnail: %s", thumb_relative)
                    
                except Exception as e:
                    logger.warning("Failed to generate %s thumbnail for PDF %s: %s", size_str, relative_path, e)
            
            doc.close()
            
        except Exception as e:
            logger.error("Failed to process PDF %s: %s", file_path, e)
        
        return thumbnails
    
    def get_file_path(self, storage_path: str) -> Path:
        """Get absolute path for a file from HashFS storage.
        
        Args:
            storage_path: Storage path returned from upload (hashfs relative path)
            
        Returns:
            Absolute Path object
            
        Raises:
            FileNotFoundError: File does not exist
        """
        try:
            abs_path = self.storage.get(storage_path)
            if not abs_path.exists():
                raise FileNotFoundError(f"File not found in storage: {storage_path}")
            return abs_path
        except IOError as e:
            raise FileNotFoundError(f"File not found: {storage_path}") from e
    
    def delete_file(self, file_id: int, delete_all_versions: bool = False) -> bool:
        """Delete a file by database ID.
        
        Note: HashFS files are reference-counted. Physical deletion only occurs
        when no other file versions reference the same content.
        
        Args:
            file_id: Database ID of file version to delete
            delete_all_versions: If True, delete ALL versions of this file (same group_id + filename).
                                 If False (default), only delete the specified version.
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get file from database
            file_version = self.db_session.query(FileVersion).get(file_id)
            
            if not file_version:
                logger.warning("Attempted to delete non-existent file ID: %s", file_id)
                return False
            
            # Collect versions to delete
            if delete_all_versions and file_version.group_id:
                # Get all versions with same group_id and filename
                versions_to_delete = self.db_session.query(FileVersion).filter(
                    and_(
                        FileVersion.group_id == file_version.group_id,
                        FileVersion.filename == file_version.filename
                    )
                ).all()
                logger.info("Deleting all %s versions of %s in group %s", len(versions_to_delete), file_version.filename, file_version.group_id)
            else:
                versions_to_delete = [file_version]
            
            # Track checksums and storage paths for physical deletion
            checksums_to_check = set()
            storage_paths_to_check = {}  # checksum -> storage_path
            group_id_to_check = file_version.group_id
            
            for version in versions_to_delete:
                checksums_to_check.add(version.checksum)
                storage_paths_to_check[version.checksum] = version.storage_path
                
                # Remove database record (thumbnails deleted later if no other refs)
                self.db_session.delete(version)
            
            self.db_session.commit()
            
            # Check each checksum and delete physical files + thumbnails if no longer referenced
            for checksum in checksums_to_check:
                other_refs = self.db_session.query(FileVersion).filter_by(checksum=checksum).count()
                
                if other_refs == 0:
                    storage_path = storage_paths_to_check[checksum]
                    
                    # Delete associated thumbnails (only when no other refs)
                    self._delete_thumbnails(storage_path)
                    
                    # No other references, safe to delete physical file
                    try:
                        self.storage.delete(storage_path)
                        logger.info("Deleted physical file and thumbnails (no other references): %s", storage_path)
                    except Exception as e:
                        logger.warning("Failed to delete physical file %s: %s", storage_path, e)
                else:
                    logger.info("Physical file and thumbnails retained (%s other references): %s", other_refs, storage_paths_to_check[checksum])
            
            # Clean up orphaned FileGroup if no files remain in the group
            if group_id_to_check:
                self._cleanup_orphaned_group(group_id_to_check)
            
            return True
            
        except Exception as e:
            logger.error("Failed to delete file %s: %s", file_id, e, exc_info=True)
            self.db_session.rollback()
            return False
    
    def _cleanup_orphaned_group(self, group_id: str) -> bool:
        """Remove FileGroup if it has no remaining files.
        
        Args:
            group_id: Group ID to check and potentially delete
            
        Returns:
            True if group was deleted, False otherwise
        """
        try:
            remaining_files = self.db_session.query(FileVersion).filter_by(group_id=group_id).count()
            if remaining_files == 0:
                group = self.db_session.query(FileGroup).get(group_id)
                if group:
                    self.db_session.delete(group)
                    self.db_session.commit()
                    logger.info("Deleted orphaned FileGroup: %s", group_id)
                    return True
        except Exception as e:
            logger.warning("Failed to cleanup orphaned group %s: %s", group_id, e)
        return False
    
    def _delete_thumbnails(self, storage_path: str):
        """Delete all thumbnails associated with a file.
        
        Args:
            storage_path: HashFS storage path
        """
        file_stem = Path(storage_path).stem
        file_parent = Path(storage_path).parent
        
        thumb_base = self.hashfs_path.parent / ".thumbs"
        for size_str in self.thumbnail_sizes:
            thumb_dir = thumb_base / size_str / file_parent
            if thumb_dir.exists():
                thumb_file = thumb_dir / f"{file_stem}_thumb.jpg"
                if thumb_file.exists():
                    try:
                        thumb_file.unlink()
                        logger.debug("Deleted thumbnail: %s", thumb_file)
                    except Exception as e:
                        logger.warning("Failed to delete thumbnail %s: %s", thumb_file, e)
    
    def get_mime_type(self, storage_path: str) -> str:
        """Get MIME type for a file from its storage path.
        
        Args:
            storage_path: HashFS storage path
            
        Returns:
            MIME type string (e.g., "image/jpeg")
        """
        # Extract filename from storage path
        filename = Path(storage_path).name
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or 'application/octet-stream'
    
    def get_categories(self) -> List[str]:
        """Get list of configured file categories.
        
        Returns:
            List of category names
        """
        return self.categories.copy()
    
    def get_group_ids(self) -> List[str]:
        """Get list of configured group IDs.
        
        Returns:
            List of group IDs
        """
        return self.group_ids.copy()
    
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
            created_by='SYSTEM'  # Future: pass user parameter from auth context
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
    
    def file_exists_on_disk(self, file_id: int) -> bool:
        """Check if the physical file exists on disk for a given file ID.
        
        Useful for detecting orphaned database records where the physical file
        has been deleted but the DB record remains.
        
        Args:
            file_id: Database ID of the file version
            
        Returns:
            True if both DB record and physical file exist, False otherwise
        """
        file_version = self.get_file_by_id(file_id)
        if not file_version:
            return False
        
        try:
            file_path = self.storage.get(file_version.storage_path)
            return file_path.exists()
        except (IOError, FileNotFoundError):
            return False
    
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
                FileVersion.is_current.is_(True)
            )
        ).first()
    
    def get_file_versions(self, group_id: str, filename: str) -> List[Dict]:
        """Get all versions of a file using SQLAlchemy-Continuum.
        
        Args:
            group_id: Group identifier (can be None or empty string for files without a group)
            filename: Filename
            
        Returns:
            List of version dictionaries with metadata
        """
        # Get all versions (current and historical)
        # Handle None/empty string group_id for files without a group
        if group_id:
            all_versions = self.db_session.query(FileVersion).filter(
                and_(
                    FileVersion.group_id == group_id,
                    FileVersion.filename == filename
                )
            ).order_by(FileVersion.uploaded_at).all()
        else:
            all_versions = self.db_session.query(FileVersion).filter(
                and_(
                    FileVersion.group_id.is_(None),
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
    
    def get_file_version(self, file_id: int, version_number: int) -> Optional[FileVersion]:
        """Get a specific version of a file by file_id and version number.
        
        Args:
            file_id: Database ID of the file (any version of it)
            version_number: Version number (1-indexed)
            
        Returns:
            FileVersion object for that specific version, or None if not found
        """
        # Get the file to find its group_id and filename
        base_file = self.db_session.query(FileVersion).get(file_id)
        if not base_file:
            return None
        
        # Get all versions of this file
        versions = self.get_file_versions(base_file.group_id or "", base_file.filename)
        
        # Find the requested version number
        for v in versions:
            if v['version_number'] == version_number:
                return self.db_session.query(FileVersion).get(v['id'])
        
        return None
    
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
            raise ValueError(str(ERROR_FILE_VERSION_NOT_FOUND))
        
        if current.group_id != target.group_id or current.filename != target.filename:
            raise ValueError(str(ERROR_CANNOT_RESTORE_DIFFERENT_FILE))
        
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
           uploaded_by='GUEST',  # Future: pass user parameter from auth context
           is_current=True,
           source_version_id=target_version_id
        )
        
        # Copy tags from target version
        for tag in target.tags:
            restored.tags.append(tag)
        
        self.db_session.add(restored)
        self.db_session.commit()
        
        logger.info("Restored file version: %s (from v%s to new version)", current.filename, target_version_id)
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
            FileVersion.is_current.is_(True)
        )
        
        if match_all:
            # Must have all tags
            for tag_name in tags:
                query = query.filter(
                    FileVersion.tags.any(FileTag.tag_name == tag_name)
                )
        
        return query.distinct().all()
    
    def list_files_from_db(self, group_id: Optional[str] = None, tag: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """List files from database (replaces filesystem-based list_files).
        
        Args:
            group_id: Filter by group ID (optional)
            tag: Filter by tag (optional)
            limit: Maximum number of results (optional)
            
        Returns:
            List of file metadata dictionaries
        """
        query = self.db_session.query(FileVersion).filter(FileVersion.is_current.is_(True))
        
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
            thumb_base = self.hashfs_path.parent / ".thumbs"
            for size_str in self.thumbnail_sizes:
                width, height = map(int, size_str.split('x'))
                thumb_key = f"thumb_{width}x{height}"
                
                # Construct thumbnail path
                storage_path_obj = Path(file_version.storage_path)  # type: ignore[arg-type]
                thumb_path = thumb_base / size_str / storage_path_obj.parent / f"{storage_path_obj.stem}_thumb.jpg"
                
                if thumb_path.exists():
                    thumb_relative = f".thumbs/{size_str}/{storage_path_obj.parent}/{storage_path_obj.stem}_thumb.jpg"
                    metadata[thumb_key] = thumb_relative.replace('\\', '/')
                    logger.debug("Found thumbnail for %s: %s", file_version.filename, thumb_relative)
                else:
                    logger.debug("No thumbnail for %s", file_version.filename)
            
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
        
        logger.info("Updated group_id for file %s: %s", file_id, new_group_id)
        return True
    
    def verify_files_bulk(self, file_ids: List[int]) -> Dict[int, Tuple[bool, str]]:
        """Verify integrity of multiple files in bulk (more efficient than individual checks).
        
        Args:
            file_ids: List of database IDs to verify
            
        Returns:
            Dictionary mapping file_id to (is_valid, status_message) tuples
        """
        results: Dict[int, Tuple[bool, str]] = {}
        
        # Fetch all file versions in one query
        file_versions = self.db_session.query(FileVersion).filter(
            FileVersion.id.in_(file_ids)
        ).all()
        
        # Create lookup map
        version_map = {fv.id: fv for fv in file_versions}
        
        # Check each file
        for file_id in file_ids:
            if file_id not in version_map:
                results[file_id] = (False, "Not found")
                continue
            
            file_version = version_map[file_id]  # type: ignore[index]
            
            try:
                # Get physical file path
                file_path = self.storage.get(file_version.storage_path)  # type: ignore[arg-type]
                
                if not file_path.exists():
                    results[file_id] = (False, "Missing")
                    continue
                
                # Verify checksum
                actual_checksum = self._calculate_checksum(file_path)
                if actual_checksum != file_version.checksum:
                    results[file_id] = (False, "Checksum mismatch")
                else:
                    results[file_id] = (True, "OK")
                    
            except IOError:
                results[file_id] = (False, "Missing")
            except Exception as e:
                results[file_id] = (False, f"Error: {str(e)}")
        
        return results
    
    def verify_file_integrity(self, file_id: int) -> Tuple[bool, str]:
        """Verify file integrity by checking existence and checksum.
        
        Args:
            file_id: Database ID of file version to verify
            
        Returns:
            Tuple of (is_valid, status_message):
            - (True, "OK"): File exists and checksum matches
            - (False, "Missing"): Physical file not found
            - (False, "Checksum mismatch"): File exists but checksum doesn't match
            - (False, "Not found"): File record not in database
        """
        # Get file from database
        file_version = self.db_session.query(FileVersion).get(file_id)
        
        if not file_version:
            return False, "Not found"
        
        try:
            # Get physical file path (this may raise IOError if not found)
            file_path = self.storage.get(file_version.storage_path)
        except IOError:
            # File not found in storage
            logger.warning("File integrity check failed - missing: %s", file_version.storage_path)
            return False, "Missing"
        
        try:
            # Check if file exists (double-check after get())
            if not file_path.exists():
                logger.warning("File integrity check failed - missing: %s", file_version.storage_path)
                return False, "Missing"
            
            # Verify checksum
            actual_checksum = self._calculate_checksum(file_path)
            if actual_checksum != file_version.checksum:
                logger.error(
                    f"File integrity check failed - checksum mismatch: {file_version.storage_path} "
                    f"(expected: {file_version.checksum[:8]}..., actual: {actual_checksum[:8]}...)"
                )
                return False, "Checksum mismatch"
            
            # All checks passed
            return True, "OK"
            
        except Exception as e:
            logger.error("File integrity check error for file %s: %s", file_id, e)
            return False, f"Error: {str(e)}"

    # ── DataTables server-side processing helpers ──────────────────────────

    def count_current_files(self) -> int:
        """Count all current (non-superseded) file versions."""
        return self.db_session.query(FileVersion).filter(
            FileVersion.is_current.is_(True)
        ).count()

    def count_filtered_files(
        self,
        search: str = "",
        group_ids: Optional[List[str]] = None,
        mime_types: Optional[List[str]] = None,
        uploaders: Optional[List[str]] = None,
        tag_names: Optional[List[str]] = None,
    ) -> int:
        """Count current files matching the given search/filter criteria."""
        query = self._build_filtered_query(search, group_ids, mime_types, uploaders, tag_names)
        return query.count()

    def list_files_paginated(
        self,
        offset: int = 0,
        limit: int = 50,
        search: str = "",
        group_ids: Optional[List[str]] = None,
        mime_types: Optional[List[str]] = None,
        uploaders: Optional[List[str]] = None,
        tag_names: Optional[List[str]] = None,
    ) -> List[FileVersion]:
        """Return a page of current file versions matching filters.

        Results are ordered by ``uploaded_at DESC``.
        """
        query = self._build_filtered_query(search, group_ids, mime_types, uploaders, tag_names)
        return (
            query
            .order_by(FileVersion.uploaded_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_version_number(self, file_version: "FileVersion") -> int:
        """Return the 1-based version number for *file_version* within its group."""
        query = self.db_session.query(FileVersion.id).filter(
            FileVersion.filename == file_version.filename
        )
        if file_version.group_id:
            query = query.filter(FileVersion.group_id == file_version.group_id)
        else:
            query = query.filter(FileVersion.group_id.is_(None))
        ordered_ids = [
            row[0] for row in query.order_by(FileVersion.uploaded_at).all()
        ]
        try:
            return ordered_ids.index(file_version.id) + 1
        except ValueError:
            return 1

    def get_searchpane_options(
        self,
        column: str,
        search: str = "",
        exclude_filters: Optional[Dict[str, List[str]]] = None,
        max_options: int = 500,
    ) -> List[Dict[str, Any]]:
        """Return SearchPanes option list for a paneable column.

        Each item is ``{label, value, total, count}`` where *total* is the
        number with only cross-pane filters applied and *count* additionally
        applies the global search.

        Supported columns: ``"group_id"``, ``"mime_type"``, ``"uploaded_by"``, ``"tags"``.
        """
        from sqlalchemy import func, case, literal_column

        if exclude_filters is None:
            exclude_filters = {}

        def _base_query():
            """Base query with is_current + cross-pane filters (excluding *column*)."""
            q = self.db_session.query(FileVersion).filter(FileVersion.is_current.is_(True))
            for col, vals in exclude_filters.items():
                if col == column or not vals:
                    continue
                q = self._apply_pane_filter(q, col, vals)
            return q

        def _search_case():
            """CASE expression: 1 when row matches global search, else 0."""
            if not search:
                return literal_column("1")
            pattern = f"%{search}%"
            return case(
                (
                    (FileVersion.filename.ilike(pattern))
                    | (FileVersion.group_id.ilike(pattern))
                    | (FileVersion.mime_type.ilike(pattern))
                    | (FileVersion.uploaded_by.ilike(pattern)),
                    1,
                ),
                else_=0,
            )

        results: List[Dict[str, Any]] = []

        if column == "tags":
            base_q = _base_query().subquery()
            rows = (
                self.db_session.query(
                    FileTag.tag_name.label("label"),
                    func.count(func.distinct(base_q.c.id)).label("total"),
                    func.sum(_search_case()).label("cnt"),
                )
                .select_from(FileTag)
                .join(file_version_tags, FileTag.id == file_version_tags.c.tag_id)
                .join(base_q, file_version_tags.c.version_id == base_q.c.id)
                .group_by(FileTag.tag_name)
                .order_by(func.count(func.distinct(base_q.c.id)).desc())
                .limit(max_options)
                .all()
            )
            for r in rows:
                results.append({"label": r.label, "value": r.label,
                                "total": r.total, "count": r.cnt or 0})
        else:
            col_attr = {
                "group_id": FileVersion.group_id,
                "mime_type": FileVersion.mime_type,
                "uploaded_by": FileVersion.uploaded_by,
            }.get(column)
            if col_attr is None:
                return results

            base_q = _base_query()
            if column != "group_id":
                base_q = base_q.filter(col_attr.isnot(None), col_attr != "")

            label_expr = func.coalesce(col_attr, "")
            rows = (
                base_q
                .with_entities(
                    label_expr.label("label"),
                    func.count().label("total"),
                    func.sum(_search_case()).label("cnt"),
                )
                .group_by(label_expr)
                .order_by(func.count().desc())
                .limit(max_options)
                .all()
            )
            for r in rows:
                display = r.label if r.label else "(none)"
                results.append({"label": display, "value": r.label,
                                "total": r.total, "count": r.cnt or 0})

        return results

    # ── Private helpers for DataTables queries ─────────────────────────────

    def _build_filtered_query(
        self,
        search: str = "",
        group_ids: Optional[List[str]] = None,
        mime_types: Optional[List[str]] = None,
        uploaders: Optional[List[str]] = None,
        tag_names: Optional[List[str]] = None,
    ):
        """Build a SQLAlchemy query for current file versions with filters."""
        query = self.db_session.query(FileVersion).filter(FileVersion.is_current.is_(True))

        if search:
            pattern = f"%{search}%"
            query = query.filter(
                (FileVersion.filename.ilike(pattern))
                | (FileVersion.group_id.ilike(pattern))
                | (FileVersion.mime_type.ilike(pattern))
                | (FileVersion.uploaded_by.ilike(pattern))
            )

        if group_ids is not None:
            query = self._apply_pane_filter(query, "group_id", group_ids)
        if mime_types is not None:
            query = self._apply_pane_filter(query, "mime_type", mime_types)
        if uploaders is not None:
            query = self._apply_pane_filter(query, "uploaded_by", uploaders)
        if tag_names is not None:
            query = self._apply_pane_filter(query, "tags", tag_names)

        return query

    @staticmethod
    def _apply_pane_filter(query, column: str, values: List[str]):
        """Apply a SearchPanes filter to *query*."""
        if column == "tags":
            query = query.filter(
                FileVersion.id.in_(
                    query.session.query(file_version_tags.c.version_id)
                    .join(FileTag, FileTag.id == file_version_tags.c.tag_id)
                    .filter(FileTag.tag_name.in_(values))
                )
            )
        elif column == "group_id":
            query = query.filter(FileVersion.group_id.in_(values))
        elif column == "mime_type":
            query = query.filter(FileVersion.mime_type.in_(values))
        elif column == "uploaded_by":
            query = query.filter(FileVersion.uploaded_by.in_(values))
        return query


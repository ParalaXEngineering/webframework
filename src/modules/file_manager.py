"""
File Manager Module - Handles file upload, storage, retrieval, and deletion.

This module provides secure file management capabilities with support for:
- File upload with type/size validation
- Thumbnail generation for images and documents (PDF, Office files)
- Secure file serving with path traversal prevention
- Organized storage structure by category/subcategory
- File deletion with soft-delete support
"""

from pathlib import Path
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
import logging
import os
import re
import shutil
import mimetypes

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
    """Manages file upload, storage, retrieval, and deletion with thumbnail support."""
    
    def __init__(self, settings_manager):
        """Initialize FileManager with settings.
        
        Args:
            settings_manager: SettingsManager instance for configuration
        """
        self.settings = settings_manager
        self._load_config()
    
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
        
        # Ensure base path exists
        self.base_path.mkdir(parents=True, exist_ok=True)
    
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
    
    def upload_file(self, file_obj: FileStorage, category: str, subcategory: str = "") -> Dict:
        """Upload file and return metadata.
        
        Args:
            file_obj: Flask FileStorage object from request.files
            category: Top-level category (e.g., "documents", "images")
            subcategory: Optional subcategory (e.g., user ID, module name)
            
        Returns:
            Dictionary with file metadata:
            {
                "path": "category/subcategory/filename.ext",
                "name": "filename.ext",
                "size": 12345,
                "uploaded_at": "2025-11-14T10:30:00Z",
                "thumbnail_small": "path/to/thumb_150.jpg" (if generated),
                "thumbnail_medium": "path/to/thumb_300.jpg" (if generated)
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
        
        # Construct storage path
        category_safe = self._sanitize_filename(category)
        subcategory_safe = self._sanitize_filename(subcategory) if subcategory else ""
        
        if subcategory_safe:
            storage_dir = self.base_path / category_safe / subcategory_safe
            relative_dir = f"{category_safe}/{subcategory_safe}"
        else:
            storage_dir = self.base_path / category_safe
            relative_dir = category_safe
        
        # Create directory if needed
        storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Get unique filename
        unique_filename = self._get_unique_filename(storage_dir, safe_filename)
        file_path = storage_dir / unique_filename
        relative_path = f"{relative_dir}/{unique_filename}"
        
        # Save file
        try:
            file_obj.save(str(file_path))
        except Exception as e:
            logger.error(f"Failed to save file {file_path}: {e}")
            raise IOError(f"Failed to save file: {e}")
        
        # Get file size
        file_size = file_path.stat().st_size
        
        # Prepare metadata
        metadata = {
            "path": relative_path.replace('\\', '/'),
            "name": unique_filename,
            "size": file_size,
            "uploaded_at": datetime.utcnow().isoformat() + "Z"
        }
        
        # Generate thumbnails for images and documents
        if self.generate_thumbnails:
            thumbnails = self._generate_thumbnails(file_path, relative_path)
            metadata.update(thumbnails)
        
        logger.info(f"File uploaded successfully: {relative_path} ({file_size} bytes)")
        return metadata
    
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

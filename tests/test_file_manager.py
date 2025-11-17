"""
Test suite for File Manager module.

Tests cover:
- File upload (valid/invalid files, size limits, type validation)
- Path security (traversal prevention)
- File deletion (soft/hard delete)
- File listing
- Thumbnail generation
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from io import BytesIO
from werkzeug.datastructures import FileStorage
from PIL import Image
import os


class MockSettingsManager:
    """Mock settings manager for testing."""
    
    def __init__(self, base_path=None):
        self.base_path_value = base_path or "test_uploads"
        
    def get_setting(self, section, key):
        """Return mock settings."""
        settings_map = {
            ("file_storage", "base_path"): {"value": self.base_path_value},
            ("file_storage", "max_file_size_mb"): {"value": 10},
            ("file_storage", "allowed_extensions"): {
                "value": [".pdf", ".jpg", ".jpeg", ".png", ".txt", ".zip"]
            },
            ("file_storage", "generate_thumbnails"): {"value": True},
            ("file_storage", "thumbnail_sizes"): {"value": ["150x150", "300x300"]},
            ("file_storage", "image_quality"): {"value": 85},
            ("file_storage", "strip_exif"): {"value": True}
        }
        return settings_map.get((section, key), {"value": None})


@pytest.fixture
def temp_storage_dir():
    """Create temporary directory for file storage tests."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def file_manager(temp_storage_dir):
    """Create FileManager with test settings."""
    from src.modules.file_manager import FileManager
    
    settings_mgr = MockSettingsManager(base_path=str(temp_storage_dir))
    fm = FileManager(settings_mgr)
    return fm


@pytest.fixture
def sample_text_file():
    """Create a sample text file for testing."""
    content = b"This is a test file content.\nLine 2\nLine 3"
    return FileStorage(
        stream=BytesIO(content),
        filename="test_document.txt",
        content_type="text/plain"
    )


@pytest.fixture
def sample_image_file():
    """Create a sample image file for testing."""
    # Create a simple 100x100 red image
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = BytesIO()
    img.save(img_bytes, 'JPEG')
    img_bytes.seek(0)
    
    return FileStorage(
        stream=img_bytes,
        filename="test_image.jpg",
        content_type="image/jpeg"
    )


@pytest.fixture
def malicious_file():
    """Create a malicious executable file for security testing."""
    content = b"MZ\x90\x00"  # PE executable header
    return FileStorage(
        stream=BytesIO(content),
        filename="malware.exe",
        content_type="application/x-executable"
    )


# ============================================================================
# UNIT TESTS - File Upload
# ============================================================================

class TestFileUpload:
    """Test file upload functionality."""
    
    def test_valid_text_file_upload(self, file_manager, sample_text_file):
        """Test uploading a valid text file."""
        metadata = file_manager.upload_file(sample_text_file, "documents")
        
        assert metadata["name"] == "test_document.txt"
        assert metadata["size"] > 0
        assert "uploaded_at" in metadata
        assert "documents" in metadata["path"]
        
        # Verify file exists
        file_path = file_manager.get_file_path(metadata["path"])
        assert file_path.exists()
    
    def test_valid_image_upload_with_thumbnails(self, file_manager, sample_image_file):
        """Test uploading an image generates thumbnails."""
        metadata = file_manager.upload_file(sample_image_file, "images", "gallery")
        
        assert metadata["name"] == "test_image.jpg"
        assert "images/gallery" in metadata["path"]
        
        # Check thumbnails were generated
        assert "thumb_150x150" in metadata
        assert "thumb_300x300" in metadata
        
        # Verify thumbnail files exist
        for thumb_key in ["thumb_150x150", "thumb_300x300"]:
            thumb_path = file_manager.get_file_path(metadata[thumb_key])
            assert thumb_path.exists()
            
            # Verify it's a valid image
            img = Image.open(thumb_path)
            assert img.format == 'JPEG'
    
    def test_invalid_file_extension(self, file_manager, malicious_file):
        """Test rejecting files with disallowed extensions."""
        with pytest.raises(ValueError, match="File type.*not allowed"):
            file_manager.upload_file(malicious_file, "uploads")
    
    def test_file_size_limit(self, file_manager):
        """Test rejecting oversized files."""
        # Create 11MB file (exceeds 10MB limit)
        large_content = b"X" * (11 * 1024 * 1024)
        large_file = FileStorage(
            stream=BytesIO(large_content),
            filename="large.txt",
            content_type="text/plain"
        )
        
        with pytest.raises(ValueError, match="File too large"):
            file_manager.upload_file(large_file, "uploads")
    
    def test_empty_file_rejected(self, file_manager):
        """Test rejecting empty files."""
        empty_file = FileStorage(
            stream=BytesIO(b""),
            filename="empty.txt",
            content_type="text/plain"
        )
        
        with pytest.raises(ValueError, match="File is empty"):
            file_manager.upload_file(empty_file, "uploads")
    
    def test_filename_collision_handling(self, file_manager, sample_text_file):
        """Test unique filename generation on collision."""
        # Upload same file twice
        metadata1 = file_manager.upload_file(sample_text_file, "docs")
        
        # Reset stream for second upload
        sample_text_file.stream.seek(0)
        metadata2 = file_manager.upload_file(sample_text_file, "docs")
        
        # Should have different names (second gets suffix)
        assert metadata1["name"] == "test_document.txt"
        assert metadata2["name"] == "test_document_1.txt"
    
    def test_filename_sanitization(self, file_manager):
        """Test dangerous filenames are sanitized."""
        dangerous_file = FileStorage(
            stream=BytesIO(b"content"),
            filename="../../../etc/passwd.txt",
            content_type="text/plain"
        )
        
        metadata = file_manager.upload_file(dangerous_file, "uploads")
        
        # Should strip path traversal
        assert ".." not in metadata["name"]
        assert "/" not in metadata["name"]
        assert "\\" not in metadata["name"]


# ============================================================================
# UNIT TESTS - Path Security
# ============================================================================

class TestPathSecurity:
    """Test path traversal prevention."""
    
    def test_path_traversal_with_dotdot(self, file_manager):
        """Test preventing ../ path traversal."""
        with pytest.raises(ValueError, match="path traversal"):
            file_manager.get_file_path("../../etc/passwd")
    
    def test_path_traversal_with_absolute(self, file_manager):
        """Test preventing absolute paths."""
        with pytest.raises(ValueError, match="path traversal"):
            file_manager.get_file_path("/etc/passwd")
    
    def test_path_traversal_with_drive_letter(self, file_manager):
        """Test preventing Windows drive letters."""
        with pytest.raises(ValueError, match="path traversal"):
            file_manager.get_file_path("C:/Windows/System32/config")
    
    def test_valid_relative_path_allowed(self, file_manager, sample_text_file):
        """Test valid relative paths work correctly."""
        metadata = file_manager.upload_file(sample_text_file, "docs", "2025")
        
        # Should be able to retrieve with valid path
        file_path = file_manager.get_file_path(metadata["path"])
        assert file_path.exists()
        assert "docs" in str(file_path)
        assert "2025" in str(file_path)


# ============================================================================
# UNIT TESTS - File Deletion
# ============================================================================

class TestFileDeletion:
    """Test file deletion functionality."""
    
    def test_soft_delete_moves_to_trash(self, file_manager, sample_text_file):
        """Test soft delete moves file to trash folder."""
        metadata = file_manager.upload_file(sample_text_file, "temp")
        file_path = file_manager.get_file_path(metadata["path"])
        
        # Soft delete
        success = file_manager.delete_file(metadata["path"], soft_delete=True)
        assert success
        
        # Original file should not exist
        assert not file_path.exists()
        
        # File should be in trash
        trash_dir = file_manager.base_path / ".trash"
        assert trash_dir.exists()
        assert len(list(trash_dir.rglob("test_document*"))) > 0
    
    def test_permanent_delete_removes_file(self, file_manager, sample_text_file):
        """Test permanent delete removes file completely."""
        metadata = file_manager.upload_file(sample_text_file, "temp")
        file_path = file_manager.get_file_path(metadata["path"])
        
        # Permanent delete
        success = file_manager.delete_file(metadata["path"], soft_delete=False)
        assert success
        
        # File should not exist anywhere
        assert not file_path.exists()
    
    def test_delete_nonexistent_file_returns_false(self, file_manager):
        """Test deleting non-existent file returns False."""
        success = file_manager.delete_file("nonexistent/file.txt")
        assert success is False
    
    def test_delete_removes_thumbnails(self, file_manager, sample_image_file):
        """Test deleting file also removes its thumbnails."""
        metadata = file_manager.upload_file(sample_image_file, "images")
        
        # Verify thumbnails exist
        thumb_paths = []
        for thumb_key in ["thumb_150x150", "thumb_300x300"]:
            if thumb_key in metadata:
                thumb_path = file_manager.get_file_path(metadata[thumb_key])
                thumb_paths.append(thumb_path)
                assert thumb_path.exists()
        
        # Delete file
        file_manager.delete_file(metadata["path"], soft_delete=False)
        
        # Thumbnails should be deleted
        for thumb_path in thumb_paths:
            assert not thumb_path.exists()


# ============================================================================
# UNIT TESTS - File Listing
# ============================================================================

class TestFileListing:
    """Test file listing functionality."""
    
    def test_list_all_files(self, file_manager, sample_text_file, sample_image_file):
        """Test listing all files in storage."""
        file_manager.upload_file(sample_text_file, "docs")
        sample_image_file.stream.seek(0)
        file_manager.upload_file(sample_image_file, "images")
        
        files = file_manager.list_files()
        assert len(files) == 2
        
        # Check metadata structure
        for file_meta in files:
            assert "path" in file_meta
            assert "name" in file_meta
            assert "size" in file_meta
            assert "uploaded_at" in file_meta
    
    def test_list_files_by_category(self, file_manager, sample_text_file, sample_image_file):
        """Test filtering files by category."""
        file_manager.upload_file(sample_text_file, "docs")
        sample_image_file.stream.seek(0)
        file_manager.upload_file(sample_image_file, "images")
        
        docs_files = file_manager.list_files(category="docs")
        assert len(docs_files) == 1
        assert docs_files[0]["name"] == "test_document.txt"
        
        images_files = file_manager.list_files(category="images")
        assert len(images_files) == 1
        assert images_files[0]["name"] == "test_image.jpg"
    
    def test_list_files_excludes_hidden_folders(self, file_manager, sample_text_file):
        """Test that .thumbs and .trash folders are excluded from listing."""
        file_manager.upload_file(sample_text_file, "docs")
        
        files = file_manager.list_files()
        
        # Should not include files from .thumbs or .trash
        for file_meta in files:
            assert not file_meta["path"].startswith(".")
            assert ".thumbs" not in file_meta["path"]
            assert ".trash" not in file_meta["path"]


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestFileManagerIntegration:
    """Integration tests for complete workflows."""
    
    def test_complete_upload_download_delete_workflow(self, file_manager, sample_text_file):
        """Test full file lifecycle."""
        # Upload
        metadata = file_manager.upload_file(sample_text_file, "workflow_test")
        assert metadata["name"] == "test_document.txt"
        
        # Verify exists
        file_path = file_manager.get_file_path(metadata["path"])
        assert file_path.exists()
        
        # Read content
        content = file_path.read_bytes()
        assert b"This is a test file content" in content
        
        # List
        files = file_manager.list_files(category="workflow_test")
        assert len(files) == 1
        
        # Delete
        success = file_manager.delete_file(metadata["path"])
        assert success
        
        # Verify deleted
        files_after = file_manager.list_files(category="workflow_test")
        assert len(files_after) == 0
    
    def test_multiple_file_uploads_same_category(self, file_manager, sample_text_file, sample_image_file):
        """Test uploading multiple files to same category."""
        metadata1 = file_manager.upload_file(sample_text_file, "mixed", "batch1")
        sample_image_file.stream.seek(0)
        metadata2 = file_manager.upload_file(sample_image_file, "mixed", "batch1")
        
        files = file_manager.list_files(category="mixed", subcategory="batch1")
        assert len(files) == 2
        
        # Check both files are present
        filenames = [f["name"] for f in files]
        assert "test_document.txt" in filenames
        assert "test_image.jpg" in filenames


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

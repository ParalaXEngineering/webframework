"""
Test suite for File Manager module with Phase 3 versioning and tagging.

Tests cover:
- File upload (valid/invalid files, size limits, type validation)
- Path security (traversal prevention)
- File deletion (soft/hard delete)
- File listing
- Thumbnail generation
- Versioning with group IDs
- Tagging system
- HashFS deduplication
- Database operations
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from io import BytesIO
from werkzeug.datastructures import FileStorage
from PIL import Image
import os
import sqlite3


class MockSettingsManager:
    """Mock settings manager for testing."""
    
    def __init__(self, base_path=None, db_path=None):
        self.base_path_value = base_path or "test_uploads"
        self.db_path = db_path or Path(tempfile.mkdtemp()) / ".file_metadata.db"
        
        # Create a mock storage object with config_path
        class MockStorage:
            def __init__(self, db_path):
                self.config_path = str(db_path.parent / "config.json")
        
        self.storage = MockStorage(self.db_path)
        
    def get_setting(self, key):
        """Return mock settings (handles dot notation keys)."""
        settings_map = {
            "file_storage.base_path": {"value": self.base_path_value},
            "file_storage.max_file_size_mb": {"value": 10},
            "file_storage.allowed_extensions": {
                "value": [".pdf", ".jpg", ".jpeg", ".png", ".txt", ".zip"]
            },
            "file_storage.generate_thumbnails": {"value": True},
            "file_storage.thumbnail_sizes": {"value": ["150x150", "300x300"]},
            "file_storage.image_quality": {"value": 85},
            "file_storage.strip_exif": {"value": True},
            "file_storage.categories": {
                "value": ["general", "documents", "images", "test"]
            },
            "file_storage.tags": {
                "value": ["test", "demo", "invoice", "important"]
            },
            "file_storage.use_hashfs": {"value": True},
            "file_storage.hashfs_path": {"value": str(Path(self.base_path_value).parent / "hashfs_storage")}
        }
        return settings_map.get(key, {"value": None})


@pytest.fixture
def temp_storage_dir():
    """Create temporary directory for file storage tests."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def file_manager(temp_storage_dir):
    """Create FileManager with test settings and mock Flask session."""
    from src.modules.file_manager import FileManager
    from flask import Flask
    
    # Create Flask app context for session
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test_secret_key'
    
    with app.test_request_context():
        # Mock session user
        from flask import session
        session['user'] = 'test_user'
        
        settings_mgr = MockSettingsManager(
            base_path=str(temp_storage_dir),
            db_path=temp_storage_dir / ".file_metadata.db"
        )
        fm = FileManager(settings_mgr)
        yield fm
        
        # Cleanup: close database session
        if hasattr(fm, 'db_session'):
            fm.db_session.close()


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
        """Test versioning system handles filename collision."""
        # Upload same file twice to same group
        metadata1 = file_manager.upload_file(sample_text_file, "docs", group_id="test_group")
        
        # Reset stream for second upload
        sample_text_file.stream.seek(0)
        metadata2 = file_manager.upload_file(sample_text_file, "docs", group_id="test_group")
        
        # Both should keep same filename (versioning handles collision)
        assert metadata1["name"] == "test_document.txt"
        assert metadata2["name"] == "test_document.txt"
        # Second upload should be version 2
        assert metadata1.get("version", 1) == 1
        assert metadata2.get("version", 1) == 2
    
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
# PHASE 3 TESTS: VERSIONING, TAGGING, HASHFS
# ============================================================================

class TestVersioning:
    """Test file versioning with group IDs."""
    
    def test_upload_creates_version_1(self, file_manager, sample_text_file):
        """Test first upload creates version 1."""
        metadata = file_manager.upload_file(sample_text_file, group_id="test_group")
        
        assert metadata['version'] == 1
        assert metadata['group_id'] == "test_group"
        assert metadata['is_current'] == True
    
    def test_upload_same_name_different_group_no_conflict(self, file_manager, sample_text_file):
        """Test same filename in different groups doesn't create versions."""
        meta1 = file_manager.upload_file(sample_text_file, group_id="group_a")
        
        sample_text_file.stream.seek(0)
        meta2 = file_manager.upload_file(sample_text_file, group_id="group_b")
        
        # Both should be version 1 (different groups)
        assert meta1['version'] == 1
        assert meta2['version'] == 1
        assert meta1['group_id'] != meta2['group_id']
    
    def test_upload_same_name_same_group_creates_version(self, file_manager, sample_text_file):
        """Test uploading same filename to same group creates new version."""
        # Upload version 1
        meta1 = file_manager.upload_file(sample_text_file, group_id="test_group")
        assert meta1['version'] == 1
        assert meta1['is_current'] == True
        
        # Upload version 2 (same filename, same group)
        sample_text_file.stream.seek(0)
        meta2 = file_manager.upload_file(sample_text_file, group_id="test_group")
        
        assert meta2['version'] == 2
        assert meta2['is_current'] == True
        
        # Verify version 1 is no longer current
        v1 = file_manager.get_file_by_id(meta1['id'])
        assert v1.is_current == False
    
    def test_get_file_versions_returns_all_versions(self, file_manager, sample_text_file):
        """Test retrieving all versions of a file."""
        # Upload 3 versions
        for i in range(3):
            sample_text_file.stream.seek(0)
            file_manager.upload_file(sample_text_file, group_id="ver_test")
        
        versions = file_manager.get_file_versions("ver_test", "test_document.txt")
        
        assert len(versions) == 3
        assert versions[0]['version_number'] == 1
        assert versions[1]['version_number'] == 2
        assert versions[2]['version_number'] == 3
        assert versions[2]['is_current'] == True
    
    def test_restore_version_creates_new_version(self, file_manager, sample_text_file):
        """Test restoring creates new version as copy."""
        # Upload v1 and v2
        meta1 = file_manager.upload_file(sample_text_file, group_id="restore_test")
        sample_text_file.stream.seek(0)
        meta2 = file_manager.upload_file(sample_text_file, group_id="restore_test")
        
        # Restore v1
        restored = file_manager.restore_version(meta2['id'], meta1['id'])
        
        assert restored.is_current == True
        assert restored.source_version_id == meta1['id']
        assert restored.checksum == meta1['checksum']
        
        # Should now have 3 versions
        versions = file_manager.get_file_versions("restore_test", "test_document.txt")
        assert len(versions) == 3


class TestTagging:
    """Test file tagging system."""
    
    def test_upload_with_tags(self, file_manager, sample_text_file):
        """Test uploading file with tags."""
        metadata = file_manager.upload_file(
            sample_text_file, 
            group_id="tag_test",
            tags=["invoice", "2025"]
        )
        
        assert "invoice" in metadata['tags']
        assert "2025" in metadata['tags']
        assert len(metadata['tags']) == 2
    
    def test_search_by_single_tag(self, file_manager, sample_text_file, sample_image_file):
        """Test searching files by tag."""
        file_manager.upload_file(sample_text_file, group_id="g1", tags=["invoice"])
        sample_image_file.stream.seek(0)
        file_manager.upload_file(sample_image_file, group_id="g2", tags=["invoice", "2025"])
        
        results = file_manager.search_by_tags(["invoice"])
        assert len(results) == 2
    
    def test_search_by_multiple_tags_any_match(self, file_manager, sample_text_file, sample_image_file):
        """Test searching files matching any tag."""
        file_manager.upload_file(sample_text_file, group_id="g1", tags=["invoice"])
        sample_image_file.stream.seek(0)
        file_manager.upload_file(sample_image_file, group_id="g2", tags=["contract"])
        
        results = file_manager.search_by_tags(["invoice", "contract"], match_all=False)
        assert len(results) == 2
    
    def test_search_by_multiple_tags_all_match(self, file_manager, sample_text_file, sample_image_file):
        """Test searching files matching all tags."""
        file_manager.upload_file(sample_text_file, group_id="g1", tags=["invoice", "2025"])
        sample_image_file.stream.seek(0)
        file_manager.upload_file(sample_image_file, group_id="g2", tags=["invoice"])
        
        results = file_manager.search_by_tags(["invoice", "2025"], match_all=True)
        assert len(results) == 1
        assert results[0].filename == "test_document.txt"


class TestHashFS:
    """Test content-addressable storage with hashfs."""
    
    def test_hashfs_stores_file_by_content_hash(self, file_manager, sample_text_file):
        """Test hashfs stores files by content hash."""
        metadata = file_manager.upload_file(sample_text_file, group_id="hashfs_test")
        
        assert 'checksum' in metadata
        assert len(metadata['checksum']) == 64  # SHA256 hex length
    
    def test_hashfs_deduplicates_identical_files(self, file_manager, sample_text_file):
        """Test identical files are deduplicated."""
        meta1 = file_manager.upload_file(sample_text_file, group_id="g1")
        sample_text_file.stream.seek(0)
        meta2 = file_manager.upload_file(sample_text_file, group_id="g2")
        
        # Same content = same checksum
        assert meta1['checksum'] == meta2['checksum']
        
        # Both should reference same physical file (in hashfs)
        if file_manager.use_hashfs:
            # Storage paths should be same for identical content
            file1 = file_manager.get_file_by_id(meta1['id'])
            file2 = file_manager.get_file_by_id(meta2['id'])
            assert file1.checksum == file2.checksum


class TestDatabaseOperations:
    """Test database-backed file operations."""
    
    def test_list_files_from_db(self, file_manager, sample_text_file, sample_image_file):
        """Test listing files from database."""
        file_manager.upload_file(sample_text_file, group_id="db_test")
        sample_image_file.stream.seek(0)
        file_manager.upload_file(sample_image_file, group_id="db_test")
        
        files = file_manager.list_files_from_db()
        assert len(files) >= 2
    
    def test_list_files_filter_by_group_id(self, file_manager, sample_text_file, sample_image_file):
        """Test filtering files by group_id."""
        file_manager.upload_file(sample_text_file, group_id="group_x")
        sample_image_file.stream.seek(0)
        file_manager.upload_file(sample_image_file, group_id="group_y")
        
        files_x = file_manager.list_files_from_db(group_id="group_x")
        assert len(files_x) == 1
        assert files_x[0]['group_id'] == "group_x"
    
    def test_list_files_filter_by_tag(self, file_manager, sample_text_file, sample_image_file):
        """Test filtering files by tag."""
        file_manager.upload_file(sample_text_file, group_id="g1", tags=["important"])
        sample_image_file.stream.seek(0)
        file_manager.upload_file(sample_image_file, group_id="g2", tags=["draft"])
        
        important_files = file_manager.list_files_from_db(tag="important")
        assert len(important_files) == 1
        assert "important" in important_files[0]['tags']
    
    def test_update_group_id(self, file_manager, sample_text_file):
        """Test updating group_id of a file."""
        metadata = file_manager.upload_file(sample_text_file, group_id="old_group")
        
        success = file_manager.update_group_id(metadata['id'], "new_group")
        assert success
        
        # Verify update
        file_version = file_manager.get_file_by_id(metadata['id'])
        assert file_version.group_id == "new_group"
    
    def test_get_current_file(self, file_manager, sample_text_file):
        """Test retrieving current version of a file."""
        # Upload 2 versions
        file_manager.upload_file(sample_text_file, group_id="current_test")
        sample_text_file.stream.seek(0)
        meta2 = file_manager.upload_file(sample_text_file, group_id="current_test")
        
        current = file_manager.get_current_file("current_test", "test_document.txt")
        
        assert current is not None
        assert current.is_current == True
        assert current.id == meta2['id']


class TestEmptyGroupID:
    """Test behavior with empty group_id (admin can fill later)."""
    
    def test_upload_with_empty_group_id(self, file_manager, sample_text_file):
        """Test uploading with empty group_id."""
        metadata = file_manager.upload_file(sample_text_file, group_id="")
        
        assert metadata['group_id'] == ""
        assert metadata['version'] == 1  # Standalone file, no versioning
    
    def test_empty_group_id_no_versioning(self, file_manager, sample_text_file):
        """Test files with empty group_id don't create versions."""
        meta1 = file_manager.upload_file(sample_text_file, group_id="")
        sample_text_file.stream.seek(0)
        meta2 = file_manager.upload_file(sample_text_file, group_id="")
        
        # Both should be version 1 (no group = no versioning)
        assert meta1['version'] == 1
        assert meta2['version'] == 1


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])


"""
Test suite for File Manager integrity verification.

Tests Task 4: Orphaned Record Detection
- Verify file existence
- Verify checksum matches
- Detect missing files (orphaned records)
- Detect checksum mismatches
"""

import pytest
from io import BytesIO
from werkzeug.datastructures import FileStorage
from pathlib import Path
import tempfile
import shutil


class MockSettingsManager:
    """Mock settings manager for integrity testing."""
    
    def __init__(self, base_path=None, db_path=None):
        self.base_path_value = base_path or "test_uploads"
        self.db_path = db_path or Path(tempfile.mkdtemp()) / ".file_metadata.db"
        
        class MockStorage:
            def __init__(self, db_path):
                self.config_path = str(db_path.parent / "config.json")
        
        self.storage = MockStorage(self.db_path)
        
    def get_setting(self, key):
        """Return mock settings."""
        settings_map = {
            "file_storage.max_file_size_mb": {"value": 10},
            "file_storage.allowed_extensions": {
                "value": [".pdf", ".jpg", ".jpeg", ".png", ".txt", ".zip"]
            },
            "file_storage.generate_thumbnails": {"value": False},
            "file_storage.thumbnail_sizes": {"value": ["150x150"]},
            "file_storage.image_quality": {"value": 85},
            "file_storage.strip_exif": {"value": True},
            "file_storage.categories": {"value": ["general", "documents", "images"]},
            "file_storage.tags": {"value": ["test", "demo", "invoice"]},
            "file_storage.hashfs_path": {"value": str(Path(self.base_path_value) / "hashfs_storage")}
        }
        return settings_map.get(key, {"value": None})


@pytest.fixture
def temp_storage_dir():
    """Create temporary directory for file storage tests."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def file_manager(temp_storage_dir):
    """Create FileManager with test settings."""
    from src.modules.file_manager import FileManager
    from flask import Flask
    
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test_secret_key'
    
    with app.test_request_context():
        from flask import session
        session['user'] = 'test_user'
        
        settings_mgr = MockSettingsManager(
            base_path=str(temp_storage_dir),
            db_path=temp_storage_dir / ".file_metadata.db"
        )
        fm = FileManager(settings_mgr)
        yield fm
        
        if hasattr(fm, 'db_session'):
            fm.db_session.close()


@pytest.fixture
def sample_file():
    """Create a simple text file for testing."""
    content = b"Test file content for integrity verification"
    file_obj = FileStorage(
        stream=BytesIO(content),
        filename="integrity_test.txt",
        content_type="text/plain"
    )
    return file_obj


class TestFileIntegrityVerification:
    """Test file integrity checking."""
    
    def test_verify_intact_file(self, file_manager, sample_file):
        """Valid file should pass integrity check."""
        # Upload file
        result = file_manager.upload_file(sample_file)
        file_id = result["id"]
        
        # Verify integrity
        is_valid, status = file_manager.verify_file_integrity(file_id)
        
        assert is_valid is True
        assert status == "OK"
    
    def test_verify_missing_file(self, file_manager, sample_file):
        """Missing physical file should be detected."""
        # Upload file
        result = file_manager.upload_file(sample_file)
        file_id = result["id"]
        
        # Get file path and delete physical file
        file_version = file_manager.get_file_by_id(file_id)
        file_path = file_manager.storage.get(file_version.storage_path)
        file_path.unlink()  # Delete physical file
        
        # Verify integrity
        is_valid, status = file_manager.verify_file_integrity(file_id)
        
        assert is_valid is False
        assert status == "Missing"
    
    def test_verify_corrupted_file(self, file_manager, sample_file):
        """File with corrupted content (wrong checksum) should be detected."""
        # Upload file
        result = file_manager.upload_file(sample_file)
        file_id = result["id"]
        
        # Get file path and corrupt content
        file_version = file_manager.get_file_by_id(file_id)
        file_path = file_manager.storage.get(file_version.storage_path)
        
        # Overwrite file with different content
        with open(file_path, 'wb') as f:
            f.write(b"CORRUPTED CONTENT - CHECKSUM WILL NOT MATCH")
        
        # Verify integrity
        is_valid, status = file_manager.verify_file_integrity(file_id)
        
        assert is_valid is False
        assert status == "Checksum mismatch"
    
    def test_verify_nonexistent_file_id(self, file_manager):
        """Non-existent file ID should return 'Not found'."""
        is_valid, status = file_manager.verify_file_integrity(99999)
        
        assert is_valid is False
        assert status == "Not found"
    
    def test_verify_multiple_files(self, file_manager):
        """Should correctly verify multiple files."""
        # Create multiple test files
        files = []
        for i in range(3):
            content = f"Test file {i}".encode()
            file_obj = FileStorage(
                stream=BytesIO(content),
                filename=f"test_{i}.txt",
                content_type="text/plain"
            )
            result = file_manager.upload_file(file_obj)
            files.append(result["id"])
        
        # All should be valid
        for file_id in files:
            is_valid, status = file_manager.verify_file_integrity(file_id)
            assert is_valid is True
            assert status == "OK"
        
        # Corrupt one file
        file_version = file_manager.get_file_by_id(files[1])
        file_path = file_manager.storage.get(file_version.storage_path)
        with open(file_path, 'wb') as f:
            f.write(b"CORRUPTED")
        
        # First and third should still be valid
        is_valid, status = file_manager.verify_file_integrity(files[0])
        assert is_valid is True
        assert status == "OK"
        
        is_valid, status = file_manager.verify_file_integrity(files[2])
        assert is_valid is True
        assert status == "OK"
        
        # Second should be corrupted
        is_valid, status = file_manager.verify_file_integrity(files[1])
        assert is_valid is False
        assert status == "Checksum mismatch"
    
    def test_checksum_calculation_matches_upload(self, file_manager, sample_file):
        """Checksum calculated during verification should match upload."""
        # Upload file
        result = file_manager.upload_file(sample_file)
        file_id = result["id"]
        original_checksum = result["checksum"]
        
        # Get file and recalculate checksum
        file_version = file_manager.get_file_by_id(file_id)
        file_path = file_manager.storage.get(file_version.storage_path)
        recalculated = file_manager._calculate_checksum(file_path)
        
        assert recalculated == original_checksum
        
        # Verify should pass
        is_valid, status = file_manager.verify_file_integrity(file_id)
        assert is_valid is True
        assert status == "OK"


class TestOrphanedRecordDetection:
    """Test detection of orphaned database records."""
    
    def test_detect_orphaned_after_manual_deletion(self, file_manager, sample_file):
        """Should detect orphaned record if physical file manually deleted."""
        # Upload file
        result = file_manager.upload_file(sample_file)
        file_id = result["id"]
        
        # Manually delete physical file (simulate external deletion)
        file_version = file_manager.get_file_by_id(file_id)
        file_path = file_manager.storage.get(file_version.storage_path)
        file_path.unlink()
        
        # Verify should detect missing file
        is_valid, status = file_manager.verify_file_integrity(file_id)
        assert is_valid is False
        assert status == "Missing"
    
    def test_batch_integrity_check(self, file_manager):
        """Test checking integrity of multiple files (batch operation)."""
        # Upload several files
        file_ids = []
        for i in range(5):
            content = f"File content {i}".encode()
            file_obj = FileStorage(
                stream=BytesIO(content),
                filename=f"batch_test_{i}.txt",
                content_type="text/plain"
            )
            result = file_manager.upload_file(file_obj)
            file_ids.append(result["id"])
        
        # Delete physical files for some records
        for i in [1, 3]:
            file_version = file_manager.get_file_by_id(file_ids[i])
            file_path = file_manager.storage.get(file_version.storage_path)
            file_path.unlink()
        
        # Check integrity of all files
        results = {}
        for file_id in file_ids:
            is_valid, status = file_manager.verify_file_integrity(file_id)
            results[file_id] = (is_valid, status)
        
        # Files 0, 2, 4 should be OK
        assert results[file_ids[0]] == (True, "OK")
        assert results[file_ids[2]] == (True, "OK")
        assert results[file_ids[4]] == (True, "OK")
        
        # Files 1, 3 should be missing
        assert results[file_ids[1]] == (False, "Missing")
        assert results[file_ids[3]] == (False, "Missing")
    
    def test_partial_corruption_detection(self, file_manager):
        """Test detecting files with partial corruption."""
        # Upload file
        content = b"Original content that will be partially corrupted"
        file_obj = FileStorage(
            stream=BytesIO(content),
            filename="partial_corrupt.txt",
            content_type="text/plain"
        )
        result = file_manager.upload_file(file_obj)
        file_id = result["id"]
        
        # Partially corrupt file (change one byte)
        file_version = file_manager.get_file_by_id(file_id)
        file_path = file_manager.storage.get(file_version.storage_path)
        
        with open(file_path, 'r+b') as f:
            f.seek(0)
            f.read(1)  # Read and discard first byte
            f.seek(0)
            f.write(b'X')  # Change first byte
        
        # Should detect checksum mismatch
        is_valid, status = file_manager.verify_file_integrity(file_id)
        assert is_valid is False
        assert status == "Checksum mismatch"

"""
Test suite for admin UI integrity status display.

Tests that the admin page correctly shows file integrity status.
"""

import pytest
from io import BytesIO
from werkzeug.datastructures import FileStorage
from pathlib import Path
import tempfile
import shutil


class MockSettingsManager:
    """Mock settings manager for admin testing."""
    
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


class TestAdminIntegrityDisplay:
    """Test admin page integrity status display."""
    
    def test_integrity_check_for_valid_file(self, file_manager):
        """Admin should show OK status for valid file."""
        # Upload a valid file
        content = b"Valid file content"
        file_obj = FileStorage(
            stream=BytesIO(content),
            filename="valid_file.txt",
            content_type="text/plain"
        )
        result = file_manager.upload_file(file_obj)
        file_id = result["id"]
        
        # Verify integrity (simulates what admin page does)
        is_valid, status = file_manager.verify_file_integrity(file_id)
        
        assert is_valid is True
        assert status == "OK"
    
    def test_integrity_check_for_missing_file(self, file_manager):
        """Admin should show Missing status for orphaned record."""
        # Upload file then delete physical file
        content = b"File to be deleted"
        file_obj = FileStorage(
            stream=BytesIO(content),
            filename="missing_file.txt",
            content_type="text/plain"
        )
        result = file_manager.upload_file(file_obj)
        file_id = result["id"]
        
        # Delete physical file
        file_version = file_manager.get_file_by_id(file_id)
        file_path = file_manager.storage.get(file_version.storage_path)
        file_path.unlink()
        
        # Verify integrity
        is_valid, status = file_manager.verify_file_integrity(file_id)
        
        assert is_valid is False
        assert status == "Missing"
    
    def test_integrity_check_for_corrupted_file(self, file_manager):
        """Admin should show Corrupted status for checksum mismatch."""
        # Upload file then corrupt it
        content = b"File to be corrupted"
        file_obj = FileStorage(
            stream=BytesIO(content),
            filename="corrupted_file.txt",
            content_type="text/plain"
        )
        result = file_manager.upload_file(file_obj)
        file_id = result["id"]
        
        # Corrupt physical file
        file_version = file_manager.get_file_by_id(file_id)
        file_path = file_manager.storage.get(file_version.storage_path)
        with open(file_path, 'wb') as f:
            f.write(b"CORRUPTED CONTENT")
        
        # Verify integrity
        is_valid, status = file_manager.verify_file_integrity(file_id)
        
        assert is_valid is False
        assert status == "Checksum mismatch"
    
    def test_batch_integrity_status_display(self, file_manager):
        """Admin should correctly show mixed integrity statuses."""
        file_statuses = []
        
        # Upload 3 files
        for i in range(3):
            content = f"File {i} content".encode()
            file_obj = FileStorage(
                stream=BytesIO(content),
                filename=f"file_{i}.txt",
                content_type="text/plain"
            )
            result = file_manager.upload_file(file_obj)
            file_statuses.append(result["id"])
        
        # Corrupt file 0 (checksum mismatch)
        file_version_0 = file_manager.get_file_by_id(file_statuses[0])
        file_path_0 = file_manager.storage.get(file_version_0.storage_path)
        with open(file_path_0, 'wb') as f:
            f.write(b"CORRUPTED")
        
        # Delete file 1 (missing)
        file_version_1 = file_manager.get_file_by_id(file_statuses[1])
        file_path_1 = file_manager.storage.get(file_version_1.storage_path)
        file_path_1.unlink()
        
        # Leave file 2 intact (OK)
        
        # Check all statuses (simulates admin page loop)
        results = []
        for file_id in file_statuses:
            is_valid, status = file_manager.verify_file_integrity(file_id)
            results.append((is_valid, status))
        
        # Verify expected statuses
        assert results[0] == (False, "Checksum mismatch")
        assert results[1] == (False, "Missing")
        assert results[2] == (True, "OK")

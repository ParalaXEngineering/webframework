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



# Using shared fixtures from tests.unit.fixtures.file_manager_fixtures


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

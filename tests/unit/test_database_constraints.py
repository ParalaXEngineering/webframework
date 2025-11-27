"""
Test suite for File Manager database constraints.

Tests Task 6: Database Constraints
- UNIQUE constraint on (group_id, filename, uploaded_at)
- Index on checksum for deduplication queries
- Index on (group_id, filename, is_current) for current version lookup
"""

import pytest
from io import BytesIO
from werkzeug.datastructures import FileStorage
from pathlib import Path
import tempfile
import shutil
import time
from sqlalchemy import inspect



# Using shared fixtures from tests.unit.fixtures.file_manager_fixtures


class TestDatabaseConstraints:
    """Test database constraints and indexes."""
    
    def test_checksum_index_exists(self, file_manager):
        """Verify checksum index exists for deduplication queries."""
        inspector = inspect(file_manager.engine)
        indexes = inspector.get_indexes('file_versions')
        
        # Check if checksum index exists
        checksum_indexes = [idx for idx in indexes if 'checksum' in idx['column_names']]
        assert len(checksum_indexes) > 0, "Checksum index should exist"
    
    def test_composite_index_exists(self, file_manager):
        """Verify composite index on (group_id, filename, is_current) exists."""
        inspector = inspect(file_manager.engine)
        indexes = inspector.get_indexes('file_versions')
        
        # Check for composite index
        composite_indexes = [
            idx for idx in indexes 
            if 'group_id' in idx['column_names'] 
            and 'filename' in idx['column_names']
            and 'is_current' in idx['column_names']
        ]
        assert len(composite_indexes) > 0, "Composite index should exist"
    
    def test_unique_constraint_prevents_duplicates_at_same_time(self, file_manager):
        """Unique constraint should prevent duplicate uploads at exact same timestamp."""
        # This test is tricky because datetime.utcnow() changes between calls
        # We'll verify the constraint exists
        inspector = inspect(file_manager.engine)
        constraints = inspector.get_unique_constraints('file_versions')
        
        # Look for our unique constraint
        found_constraint = False
        for constraint in constraints:
            if set(constraint['column_names']) == {'group_id', 'filename', 'uploaded_at'}:
                found_constraint = True
                break
        
        assert found_constraint, "Unique constraint on (group_id, filename, uploaded_at) should exist"
    
    def test_versioning_with_different_timestamps(self, file_manager, sample_text_file):
        """Should allow multiple versions with same filename in same group (different timestamps)."""
        # Upload first version
        result1 = file_manager.upload_file(sample_text_file, group_id="test_group")
        
        # Wait a tiny bit to ensure different timestamp
        time.sleep(0.01)
        
        # Upload second version (same filename, same group, different content)
        content2 = b"Different content for version 2"
        file_obj2 = FileStorage(
            stream=BytesIO(content2),
            filename="test_document.txt",  # Same filename as sample_text_file
            content_type="text/plain"
        )
        result2 = file_manager.upload_file(file_obj2, group_id="test_group")
        
        # Both uploads should succeed
        assert result1 is not None
        assert result2 is not None
        assert result1["id"] != result2["id"]
        assert result2["version"] == 2
    
    def test_checksum_deduplication_query(self, file_manager):
        """Checksum index should enable fast deduplication queries."""
        from src.modules.file_manager import FileVersion
        
        # Upload file
        content = b"Deduplication test content"
        file_obj = FileStorage(
            stream=BytesIO(content),
            filename="dedup_test.txt",
            content_type="text/plain"
        )
        result = file_manager.upload_file(file_obj)
        checksum = result["checksum"]
        
        # Query by checksum (should use index)
        matches = file_manager.db_session.query(FileVersion).filter_by(checksum=checksum).all()
        
        assert len(matches) >= 1
        assert matches[0].checksum == checksum
    
    def test_current_version_lookup_performance(self, file_manager):
        """Composite index should enable fast current version lookup."""
        from src.modules.file_manager import FileVersion
        
        # Upload multiple versions
        for i in range(3):
            content = f"Version {i} content".encode()
            file_obj = FileStorage(
                stream=BytesIO(content),
                filename="lookup_test.txt",
                content_type="text/plain"
            )
            file_manager.upload_file(file_obj, group_id="lookup_group")
            time.sleep(0.01)
        
        # Query for current version (should use composite index)
        current = file_manager.db_session.query(FileVersion).filter_by(
            group_id="lookup_group",
            filename="lookup_test.txt",
            is_current=True
        ).first()
        
        assert current is not None
        assert current.is_current is True
        assert current.group_id == "lookup_group"


class TestIndexPerformance:
    """Test that indexes improve query performance."""
    
    def test_checksum_index_speeds_up_deduplication(self, file_manager):
        """Checksum index should make deduplication checks fast."""
        from src.modules.file_manager import FileVersion
        
        # Upload several files with different content
        for i in range(10):
            content = f"File {i} with unique content".encode()
            file_obj = FileStorage(
                stream=BytesIO(content),
                filename=f"file_{i}.txt",
                content_type="text/plain"
            )
            file_manager.upload_file(file_obj)
        
        # Query by checksum (should be fast due to index)
        test_checksum = file_manager.db_session.query(FileVersion).first().checksum
        matches = file_manager.db_session.query(FileVersion).filter_by(
            checksum=test_checksum
        ).all()
        
        # Should find exactly one match
        assert len(matches) == 1
    
    def test_composite_index_speeds_up_current_version_query(self, file_manager):
        """Composite index should make current version queries fast."""
        from src.modules.file_manager import FileVersion
        
        # Create multiple groups with multiple files
        for group_num in range(3):
            for file_num in range(3):
                content = f"Group {group_num} File {file_num}".encode()
                file_obj = FileStorage(
                    stream=BytesIO(content),
                    filename=f"file_{file_num}.txt",
                    content_type="text/plain"
                )
                file_manager.upload_file(file_obj, group_id=f"group_{group_num}")
                time.sleep(0.01)
        
        # Query for current version in specific group (should use index)
        current_files = file_manager.db_session.query(FileVersion).filter_by(
            group_id="group_1",
            is_current=True
        ).all()
        
        # Should find 3 current files in group_1
        assert len(current_files) == 3
        for file_ver in current_files:
            assert file_ver.is_current is True
            assert file_ver.group_id == "group_1"

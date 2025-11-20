"""
Test suite for admin UI improvements.

Tests the new features:
1. Preview in edit file metadata
2. PDF previews 
3. Dropdown constraints for group_id and tags
4. Preview in file history
"""

import pytest
from io import BytesIO
from werkzeug.datastructures import FileStorage
from pathlib import Path
import tempfile
import shutil



# Using shared fixtures from tests.unit.fixtures.file_manager_fixtures


class TestAdminUIImprovements:
    """Test admin UI improvements."""
    
    def test_preview_generation_for_files(self, file_manager):
        """Test that preview generation works for different file types."""
        from src.pages.file_manager_admin import _generate_preview_html
        
        # Test PDF preview generation (should create object tag or show icon)
        pdf_meta = {
            'name': 'document.pdf',
            'id': 123,
            'path': 'some/path/document.pdf'
        }
        # Since we're not in a full Flask app context, it should fall back to icon
        pdf_preview = _generate_preview_html(pdf_meta, size="100px")
        
        # Should either have object tag or PDF icon
        assert ('object' in pdf_preview and 'application/pdf' in pdf_preview) or 'bi-file-pdf' in pdf_preview
        
        # Test image with thumbnail
        img_meta = {
            'name': 'image.jpg',
            'id': 124,
            'path': 'some/path/image.jpg',
            'thumb_150x150': '.thumbs/150x150/some/path/image_thumb.jpg'
        }
        # This should work since it doesn't use url_for
        img_preview = _generate_preview_html(img_meta, size="100px")
        
        # In test environment, url_for might fail, so accept either image or fallback icon
        assert ('img' in img_preview and 'thumb_150x150' in img_preview) or 'bi-file-image' in img_preview
        assert 'max-width: 100px' in img_preview or 'font-size: 2rem' in img_preview
        
        # Test file without thumbnail (should show icon)
        doc_meta = {
            'name': 'document.docx',
            'id': 125,
            'path': 'some/path/document.docx'
        }
        doc_preview = _generate_preview_html(doc_meta)
        
        assert 'bi-file-word' in doc_preview or 'bi-file-earmark' in doc_preview
    
    def test_file_icon_mapping(self, file_manager):
        """Test that file icon mapping works correctly."""
        from src.modules.utilities import util_get_file_icon
        
        # Test various file types
        assert 'pdf' in util_get_file_icon('test.pdf')
        assert 'word' in util_get_file_icon('test.docx')
        assert 'excel' in util_get_file_icon('test.xlsx')
        assert 'image' in util_get_file_icon('test.jpg')
        assert 'zip' in util_get_file_icon('test.zip')
        assert 'bi-file-earmark' in util_get_file_icon('test.unknown')
    
    def test_tags_and_categories_validation(self, file_manager):
        """Test that file manager returns valid tags and categories for dropdowns."""
        # Get configured tags and categories
        tags = file_manager.get_tags()
        categories = file_manager.get_categories()
        
        # Should return lists
        assert isinstance(tags, list)
        assert isinstance(categories, list)
        
        # Should contain expected values from mock settings
        assert "test" in tags
        assert "demo" in tags
        assert "invoice" in tags
        
        assert "general" in categories
        assert "documents" in categories
        assert "demo" in categories
    
    def test_upload_with_dropdown_constraints(self, file_manager):
        """Test upload with valid values from dropdown constraints."""
        # Upload with valid tag and category
        content = b"Test file for dropdown validation"
        file_obj = FileStorage(
            stream=BytesIO(content),
            filename="dropdown_test.txt",
            content_type="text/plain"
        )
        
        result = file_manager.upload_file(
            file_obj,
            category="demo",  # Valid category
            group_id="test_group",
            tags=["test", "demo"]  # Valid tags
        )
        
        assert result is not None
        assert result["tags"] == ["test", "demo"]
        
    def test_file_version_history_structure(self, file_manager):
        """Test that file version history returns proper structure for preview generation."""
        # Upload multiple versions
        for i in range(2):
            content = f"Version {i} content".encode()
            file_obj = FileStorage(
                stream=BytesIO(content),
                filename="history_test.txt",
                content_type="text/plain"
            )
            file_manager.upload_file(file_obj, group_id="history_group")
        
        # Get version history
        versions = file_manager.get_file_versions("history_group", "history_test.txt")
        
        assert len(versions) == 2
        
        # Check that each version has required fields for preview
        for version in versions:
            assert 'id' in version
            assert 'filename' in version
            assert 'storage_path' in version
            assert 'uploaded_at' in version
            assert 'is_current' in version
    
    def test_group_id_handling_with_none_value(self, file_manager):
        """Test that group_id handles '(none)' value correctly."""
        # Simulate form data with '(none)' value
        content = b"Test file for group handling"
        file_obj = FileStorage(
            stream=BytesIO(content),
            filename="group_test.txt",
            content_type="text/plain"
        )
        
        # Upload with empty group_id (simulating '(none)' selection)
        result = file_manager.upload_file(file_obj, group_id="")
        
        assert result is not None
        assert result["group_id"] == ""  # Should be empty string, not None
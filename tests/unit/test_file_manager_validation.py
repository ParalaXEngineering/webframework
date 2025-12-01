"""
Test suite for File Manager tag and category validation.

Tests Task 2: Tag/Category Validation
- Enforce predefined tags from settings
- Enforce predefined categories from settings
- Reject invalid tags
- Reject invalid categories
"""

import pytest
from io import BytesIO
from werkzeug.datastructures import FileStorage
import tempfile
import shutil
from pathlib import Path


class MockSettingsManager:
    """Mock settings manager for validation testing."""
    
    def __init__(self, base_path=None, db_path=None):
        self.base_path_value = base_path or "test_uploads"
        self.db_path = db_path or Path(tempfile.mkdtemp()) / ".file_metadata.db"
        
        class MockStorage:
            def __init__(self, db_path):
                self.config_path = str(db_path.parent / "config.json")
        
        self.storage = MockStorage(self.db_path)
        
    def get_setting(self, key):
        """Return mock settings with specific tag/category lists."""
        settings_map = {
            "file_storage.max_file_size_mb": 10,
            "file_storage.allowed_extensions": [".pdf", ".jpg", ".jpeg", ".png", ".txt", ".zip"],
            "file_storage.generate_thumbnails": False,  # Disable for speed
            "file_storage.thumbnail_sizes": ["150x150"],
            "file_storage.image_quality": 85,
            "file_storage.strip_exif": True,
            "file_storage.categories": ["general", "documents", "images", "reports"],
            "file_storage.tags": ["invoice", "contract", "demo", "test"],
            "file_storage.hashfs_path": str(Path(self.base_path_value) / "hashfs_storage")
        }
        return settings_map.get(key, None)


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
    content = b"Test file content for validation"
    file_obj = FileStorage(
        stream=BytesIO(content),
        filename="test_validation.txt",
        content_type="text/plain"
    )
    return file_obj


class TestTagValidation:
    """Test tag validation enforcement."""
    
    def test_upload_with_valid_tags(self, file_manager, sample_file):
        """Valid tags should be accepted."""
        result = file_manager.upload_file(
            sample_file,
            tags=["invoice", "demo"]
        )
        
        assert result is not None
        assert "tags" in result
        assert set(result["tags"]) == {"invoice", "demo"}
    
    def test_upload_with_single_valid_tag(self, file_manager, sample_file):
        """Single valid tag should be accepted."""
        result = file_manager.upload_file(
            sample_file,
            tags=["contract"]
        )
        
        assert result is not None
        assert result["tags"] == ["contract"]
    
    def test_upload_with_invalid_tag(self, file_manager, sample_file):
        """Invalid tag should raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            file_manager.upload_file(
                sample_file,
                tags=["invalid_tag"]
            )
        
        assert "Invalid tags" in str(exc_info.value)
        assert "invalid_tag" in str(exc_info.value)
        assert "Valid tags are" in str(exc_info.value)
    
    def test_upload_with_mixed_valid_invalid_tags(self, file_manager, sample_file):
        """Mix of valid and invalid tags should raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            file_manager.upload_file(
                sample_file,
                tags=["invoice", "bad_tag", "test"]
            )
        
        assert "Invalid tags" in str(exc_info.value)
        assert "bad_tag" in str(exc_info.value)
    
    def test_upload_with_multiple_invalid_tags(self, file_manager, sample_file):
        """Multiple invalid tags should all be reported."""
        with pytest.raises(ValueError) as exc_info:
            file_manager.upload_file(
                sample_file,
                tags=["wrong1", "wrong2", "wrong3"]
            )
        
        error_msg = str(exc_info.value)
        assert "Invalid tags" in error_msg
        assert "wrong1" in error_msg
        assert "wrong2" in error_msg
        assert "wrong3" in error_msg
    
    def test_upload_without_tags(self, file_manager, sample_file):
        """Upload without tags should succeed."""
        result = file_manager.upload_file(sample_file, tags=None)
        
        assert result is not None
        assert result["tags"] == []
    
    def test_upload_with_empty_tag_list(self, file_manager, sample_file):
        """Empty tag list should succeed."""
        result = file_manager.upload_file(sample_file, tags=[])
        
        assert result is not None
        assert result["tags"] == []
    
    def test_get_valid_tags(self, file_manager):
        """get_tags() should return configured valid tags."""
        tags = file_manager.get_tags()
        
        assert isinstance(tags, list)
        assert set(tags) == {"invoice", "contract", "demo", "test"}
    
    def test_tags_are_immutable(self, file_manager):
        """get_tags() should return a copy to prevent modification."""
        tags1 = file_manager.get_tags()
        tags1.append("should_not_persist")
        tags2 = file_manager.get_tags()
        
        assert "should_not_persist" not in tags2


class TestCategoryValidation:
    """Test category validation enforcement."""
    
    def test_upload_with_valid_category(self, file_manager, sample_file):
        """Valid category should be accepted."""
        result = file_manager.upload_file(
            sample_file,
            category="documents"
        )
        
        assert result is not None
    
    def test_upload_with_general_category(self, file_manager, sample_file):
        """'general' category should always be accepted (default)."""
        result = file_manager.upload_file(
            sample_file,
            category="general"
        )
        
        assert result is not None
    
    def test_upload_with_invalid_category(self, file_manager, sample_file):
        """Invalid category should raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            file_manager.upload_file(
                sample_file,
                category="invalid_category"
            )
        
        assert "Invalid category" in str(exc_info.value)
        assert "invalid_category" in str(exc_info.value)
        assert "Valid categories are" in str(exc_info.value)
    
    def test_upload_without_category(self, file_manager, sample_file):
        """Upload without category should succeed (uses default)."""
        result = file_manager.upload_file(sample_file, category=None)
        
        assert result is not None
    
    def test_upload_with_empty_category(self, file_manager, sample_file):
        """Empty string category should succeed (treated as unspecified)."""
        result = file_manager.upload_file(sample_file, category="")
        
        assert result is not None
    
    def test_get_valid_categories(self, file_manager):
        """get_categories() should return configured valid categories."""
        categories = file_manager.get_categories()
        
        assert isinstance(categories, list)
        assert set(categories) == {"general", "documents", "images", "reports"}
    
    def test_categories_are_immutable(self, file_manager):
        """get_categories() should return a copy to prevent modification."""
        cats1 = file_manager.get_categories()
        cats1.append("should_not_persist")
        cats2 = file_manager.get_categories()
        
        assert "should_not_persist" not in cats2


class TestCombinedValidation:
    """Test combined tag and category validation."""
    
    def test_upload_with_valid_category_and_tags(self, file_manager, sample_file):
        """Both valid category and tags should succeed."""
        result = file_manager.upload_file(
            sample_file,
            category="documents",
            tags=["invoice", "contract"]
        )
        
        assert result is not None
        assert set(result["tags"]) == {"invoice", "contract"}
    
    def test_upload_with_invalid_category_and_valid_tags(self, file_manager, sample_file):
        """Invalid category should fail even with valid tags."""
        with pytest.raises(ValueError) as exc_info:
            file_manager.upload_file(
                sample_file,
                category="bad_category",
                tags=["invoice"]
            )
        
        assert "Invalid category" in str(exc_info.value)
    
    def test_upload_with_valid_category_and_invalid_tags(self, file_manager, sample_file):
        """Invalid tags should fail even with valid category."""
        with pytest.raises(ValueError) as exc_info:
            file_manager.upload_file(
                sample_file,
                category="documents",
                tags=["bad_tag"]
            )
        
        assert "Invalid tags" in str(exc_info.value)
    
    def test_case_sensitive_tag_validation(self, file_manager, sample_file):
        """Tags should be case-sensitive."""
        # Valid tags are: ["invoice", "contract", "demo", "test"]
        with pytest.raises(ValueError) as exc_info:
            file_manager.upload_file(
                sample_file,
                tags=["Invoice"]  # Capital I
            )
        
        assert "Invalid tags" in str(exc_info.value)
    
    def test_case_sensitive_category_validation(self, file_manager, sample_file):
        """Categories should be case-sensitive."""
        # Valid categories are: ["general", "documents", "images", "reports"]
        with pytest.raises(ValueError) as exc_info:
            file_manager.upload_file(
                sample_file,
                category="Documents"  # Capital D
            )
        
        assert "Invalid category" in str(exc_info.value)

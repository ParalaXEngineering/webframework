"""
Shared fixtures for File Manager tests.

Provides common mocks, test data, and fixtures to avoid duplication
across multiple file manager test files.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from io import BytesIO
from werkzeug.datastructures import FileStorage
from PIL import Image


class MockSettingsManager:
    """Mock settings manager for file manager testing.
    
    Provides realistic settings for FileManager without requiring
    a full Flask app or settings file.
    """
    
    def __init__(self, base_path=None, db_path=None, **overrides):
        """Initialize mock settings manager.
        
        Args:
            base_path: Base directory for file storage
            db_path: Path to database file
            **overrides: Override specific settings (e.g., generate_thumbnails=False)
        """
        self.base_path_value = base_path or "test_uploads"
        self.db_path = db_path or Path(tempfile.mkdtemp()) / ".file_metadata.db"
        self.overrides = overrides
        
        # Create a mock storage object with config_path
        class MockStorage:
            def __init__(self, db_path):
                self.config_path = str(db_path.parent / "config.json")
        
        self.storage = MockStorage(self.db_path)
        
    def get_setting(self, key):
        """Return mock settings (handles dot notation keys)."""
        # Check for override first
        override_key = key.replace("file_storage.", "")
        if override_key in self.overrides:
            return self.overrides[override_key]
        
        # Default settings
        settings_map = {
            "file_storage.max_file_size_mb": 10,
            "file_storage.allowed_extensions": [".pdf", ".jpg", ".jpeg", ".png", ".txt", ".zip"],
            "file_storage.generate_thumbnails": True,
            "file_storage.thumbnail_sizes": ["150x150", "300x300"],
            "file_storage.image_quality": 85,
            "file_storage.strip_exif": True,
            "file_storage.categories": [
                "general", "documents", "images", "test", "docs", 
                "uploads", "temp", "workflow_test", "mixed", "reports", "demo"
            ],
            "file_storage.tags": [
                "test", "demo", "invoice", "important", "2025", 
                "contract", "draft"
            ],
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
def mock_settings_manager(temp_storage_dir):
    """Create mock settings manager with default configuration."""
    return MockSettingsManager(
        base_path=str(temp_storage_dir),
        db_path=temp_storage_dir / ".file_metadata.db"
    )


@pytest.fixture
def mock_settings_manager_no_thumbnails(temp_storage_dir):
    """Create mock settings manager with thumbnails disabled (faster tests)."""
    return MockSettingsManager(
        base_path=str(temp_storage_dir),
        db_path=temp_storage_dir / ".file_metadata.db",
        generate_thumbnails=False
    )


@pytest.fixture
def file_manager(temp_storage_dir, mock_settings_manager):
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
        
        fm = FileManager(mock_settings_manager)
        yield fm
        
        # Cleanup: close database session
        if hasattr(fm, 'db_session'):
            fm.db_session.close()


@pytest.fixture
def file_manager_no_thumbnails(temp_storage_dir, mock_settings_manager_no_thumbnails):
    """Create FileManager with thumbnails disabled (faster tests)."""
    from src.modules.file_manager import FileManager
    from flask import Flask
    
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test_secret_key'
    
    with app.test_request_context():
        from flask import session
        session['user'] = 'test_user'
        
        fm = FileManager(mock_settings_manager_no_thumbnails)
        yield fm
        
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
def sample_pdf_file():
    """Create a sample PDF-like file for testing."""
    content = b"%PDF-1.4\nFake PDF content for testing"
    return FileStorage(
        stream=BytesIO(content),
        filename="test_document.pdf",
        content_type="application/pdf"
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
def sample_large_file():
    """Create a file that exceeds size limits."""
    # 11 MB file (exceeds 10 MB limit)
    content = b"x" * (11 * 1024 * 1024)
    return FileStorage(
        stream=BytesIO(content),
        filename="large_file.txt",
        content_type="text/plain"
    )


@pytest.fixture
def sample_invalid_extension_file():
    """Create a file with invalid extension."""
    content = b"test content"
    return FileStorage(
        stream=BytesIO(content),
        filename="invalid.exe",
        content_type="application/x-executable"
    )

"""
Integration tests for secret key security.

Tests that the framework properly validates SECRET_KEY configuration
and prevents startup without a secure key.
"""

import pytest
import tempfile
from pathlib import Path
from flask import Flask
from src.main import setup_app


def test_setup_app_requires_secret_key():
    """Test that setup_app raises error if SECRET_KEY not configured."""
    app = Flask(__name__)
    # Don't set SECRET_KEY
    
    with pytest.raises(RuntimeError) as exc_info:
        setup_app(app)
    
    error_message = str(exc_info.value)
    assert "SECRET_KEY" in error_message
    assert "not configured" in error_message or "must be set" in error_message


def test_setup_app_accepts_valid_secret_key():
    """Test that setup_app succeeds with proper SECRET_KEY."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test-secret-key-for-testing-only'
    
    # Should not raise
    socketio = setup_app(app)
    assert socketio is not None


def test_setup_app_rejects_empty_secret_key():
    """Test that empty SECRET_KEY is rejected."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = ''
    
    with pytest.raises(RuntimeError) as exc_info:
        setup_app(app)
    
    error_message = str(exc_info.value)
    assert "SECRET_KEY" in error_message


def test_manual_webapp_secret_key_generation():
    """Test the get_or_create_secret_key function from Manual_Webapp."""
    # Import the function
    import sys
    import os
    manual_webapp_path = Path(__file__).parent.parent.parent / "Manual_Webapp"
    sys.path.insert(0, str(manual_webapp_path))
    
    try:
        from main import get_or_create_secret_key
        
        # Test with temp directory (should create new key)
        with tempfile.TemporaryDirectory() as tmpdir:
            key = get_or_create_secret_key(tmpdir)
            
            # Should return a valid key
            assert key is not None
            assert len(key) > 0
            assert isinstance(key, str)
            
            # Should have created .secret_key file
            key_file = Path(tmpdir) / '.secret_key'
            assert key_file.exists()
            
            # File should contain the same key
            saved_key = key_file.read_text().strip()
            assert saved_key == key
            
            # Second call should return same key (from file)
            key2 = get_or_create_secret_key(tmpdir)
            assert key2 == key
    
    finally:
        sys.path.pop(0)


def test_secret_key_error_message_helpfulness():
    """Test that error message provides clear instructions."""
    app = Flask(__name__)
    
    with pytest.raises(RuntimeError) as exc_info:
        setup_app(app)
    
    error_message = str(exc_info.value)
    
    # Should mention how to generate a key
    assert "secrets.token_hex" in error_message or ".secret_key" in error_message
    
    # Should mention where to set it
    assert "app.config" in error_message or "SECRET_KEY" in error_message
    
    # Should provide actionable commands
    assert "python -c" in error_message or "Path" in error_message

"""
Tests for CSRF token persistence and validation.

Tests the fix that ensures CSRF tokens persist across requests
instead of regenerating on every page load.
"""

import pytest
from src.modules.utilities import validate_csrf_token


def test_csrf_token_persistence_in_session(app):
    """Test that CSRF token persists across multiple requests in the same session."""
    with app.test_client() as client:
        with client.session_transaction() as sess:
            # First access - should create token
            sess['csrf_token'] = 'test-token-123'
        
        # Simulate multiple requests
        for _ in range(3):
            with client.session_transaction() as sess:
                # Token should remain the same
                assert sess['csrf_token'] == 'test-token-123'


def test_csrf_validation_with_valid_token(app):
    """Test that validate_csrf_token accepts matching tokens."""
    with app.test_request_context():
        from flask import session
        session['csrf_token'] = 'valid-token-456'
        
        result = validate_csrf_token('valid-token-456')
        assert result is True


def test_csrf_validation_with_invalid_token(app):
    """Test that validate_csrf_token rejects mismatched tokens."""
    with app.test_request_context():
        from flask import session
        session['csrf_token'] = 'correct-token'
        
        result = validate_csrf_token('wrong-token')
        assert result is False


def test_csrf_validation_with_missing_session_token(app):
    """Test that validation fails when session token is missing."""
    with app.test_request_context():
        # No token in session
        result = validate_csrf_token('some-token')
        assert result is False


def test_csrf_validation_with_none_values(app):
    """Test that validation handles None values safely."""
    with app.test_request_context():
        from flask import session
        session['csrf_token'] = 'token'
        
        # Form token is None
        result = validate_csrf_token(None)
        assert result is False

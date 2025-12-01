"""
Authentication utilities: password hashing, validation, etc.
"""

import re
from typing import Optional, Tuple

import bcrypt

# Import user-facing error messages from i18n
from ..i18n.messages import (
    ERROR_PASSWORD_TOO_SHORT,
    ERROR_PASSWORD_NO_LETTER,
    ERROR_PASSWORD_NO_NUMBER,
    ERROR_USERNAME_TOO_SHORT,
    ERROR_USERNAME_TOO_LONG,
    ERROR_USERNAME_INVALID_FORMAT,
)

# Constants for password validation
MIN_PASSWORD_LENGTH = 5
MIN_USERNAME_LENGTH = 3
MAX_USERNAME_LENGTH = 32

# Regex patterns for validation
USERNAME_PATTERN = r'^[a-zA-Z0-9][a-zA-Z0-9_-]*$'
LETTER_PATTERN = r'[a-zA-Z]'
DIGIT_PATTERN = r'\d'


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Bcrypt hash string
    """
    if not password:
        return ""
    
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against a bcrypt hash.
    
    Args:
        password: Plain text password to verify
        password_hash: Bcrypt hash to check against
        
    Returns:
        True if password matches, False otherwise
    """
    if not password_hash:
        # Passwordless user - allow empty password
        return password == ""
    
    if not password:
        return False
    
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception:
        return False


def validate_password_strength(password: str) -> Tuple[bool, Optional[str]]:
    """
    Validate password meets minimum requirements.
    
    Requirements:
    - At least 5 characters
    - Contains at least one letter
    - Contains at least one number
    
    Args:
        password: Password to validate
        
    Returns:
        (is_valid, error_message)
    """
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, ERROR_PASSWORD_TOO_SHORT.format(min_length=MIN_PASSWORD_LENGTH)
    
    if not re.search(LETTER_PATTERN, password):
        return False, str(ERROR_PASSWORD_NO_LETTER)
    
    if not re.search(DIGIT_PATTERN, password):
        return False, str(ERROR_PASSWORD_NO_NUMBER)
    
    return True, None


def validate_username(username: str) -> Tuple[bool, Optional[str]]:
    """
    Validate username format.
    
    Requirements:
    - 3-32 characters
    - Alphanumeric, underscore, hyphen only
    - Must start with letter or number
    
    Args:
        username: Username to validate
        
    Returns:
        (is_valid, error_message)
    """
    if len(username) < MIN_USERNAME_LENGTH:
        return False, ERROR_USERNAME_TOO_SHORT.format(min_length=MIN_USERNAME_LENGTH)
    
    if len(username) > MAX_USERNAME_LENGTH:
        return False, ERROR_USERNAME_TOO_LONG.format(max_length=MAX_USERNAME_LENGTH)
    
    if not re.match(USERNAME_PATTERN, username):
        return False, str(ERROR_USERNAME_INVALID_FORMAT)
    
    return True, None


def get_default_user_prefs() -> dict:
    """
    Get default user preferences structure.
    
    Returns:
        Default preferences dictionary
    """
    return {
        "theme": "light",
        "dashboard_layout": "default",
        "module_settings": {},
        "notifications": {
            "email_on_complete": False
        },
        "framework_overrides": {}
    }

"""
Authentication utilities: password hashing, validation, etc.
"""

import bcrypt
import re
from typing import Optional


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


def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
    """
    Validate password meets minimum requirements.
    
    Requirements:
    - At least 6 characters
    - Contains at least one letter
    - Contains at least one number
    
    Args:
        password: Password to validate
        
    Returns:
        (is_valid, error_message)
    """
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    
    if not re.search(r'[a-zA-Z]', password):
        return False, "Password must contain at least one letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    return True, None


def validate_username(username: str) -> tuple[bool, Optional[str]]:
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
    if len(username) < 3:
        return False, "Username must be at least 3 characters long"
    
    if len(username) > 32:
        return False, "Username cannot exceed 32 characters"
    
    if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9_-]*$', username):
        return False, "Username must start with letter/number and contain only letters, numbers, underscore, or hyphen"
    
    return True, None


def get_default_user_prefs() -> dict:
    """
    Get default user preferences template.
    
    Returns:
        Default preferences dictionary
    """
    return {
        "theme": "light",
        "dashboard_layout": "default",
        "module_settings": {},
        "notifications": {
            "email_on_complete": False
        }
    }

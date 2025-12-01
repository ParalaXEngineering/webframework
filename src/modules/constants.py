"""
Framework-wide constants for ParalaX Web Framework.

This module contains technical constants used across multiple modules.
Domain-specific constants should remain in their respective modules.
User-facing strings should be in i18n/messages.py for translation support.
"""

# =============================================================================
# HTTP Status Codes
# =============================================================================
STATUS_OK = 200
STATUS_BAD_REQUEST = 400
STATUS_NOT_FOUND = 404
STATUS_SERVER_ERROR = 500

# =============================================================================
# HTTP Methods
# =============================================================================
METHOD_GET = "GET"
METHOD_POST = "POST"
METHOD_PUT = "PUT"
METHOD_DELETE = "DELETE"
GET_POST = ["GET", "POST"]

# =============================================================================
# Common Delimiters
# =============================================================================
DELIMITER_SPLIT = "#"
DELIMITER_JOIN = ","
DELIMITER_PATH = "."

# =============================================================================
# Boolean Representations
# =============================================================================
BOOL_TRUE_VALUES = [True, "true", "on", "1", 1]
BOOL_FALSE_VALUES = [False, "false", "off", "0", 0]

# =============================================================================
# Common Query Parameters
# =============================================================================
PARAM_FILE = "file"
PARAM_FILENAME = "filename"
PARAM_USER = "user"
PARAM_PASSWORD = "password"

# =============================================================================
# Common Form Fields
# =============================================================================
FIELD_CSRF_TOKEN = "csrf_token"

# =============================================================================
# User and Session Constants
# =============================================================================
USER_GUEST_NAME = "GUEST"
SESSION_GUEST = "guest"
SESSION_USER = "user"

# =============================================================================
# Image Processing
# =============================================================================
IMAGE_MAX_SIZE = (1024, 1024)
IMAGE_QUALITY_HIGH = 95
IMAGE_QUALITY_MEDIUM = 75
IMAGE_QUALITY_LOW = 50

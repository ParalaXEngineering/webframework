"""
User-facing messages for internationalization with automatic translation.

This module provides a clever workaround for i18n: each message is a class that
acts like a string but translates itself when converted to string.

Usage (works both ways):
    from modules.i18n.messages import MSG_SETTINGS_SAVED, ERROR_NOT_LOGGED_IN
    
    flash(MSG_SETTINGS_SAVED, "success")  # Automatic translation!
    flash(str(MSG_SETTINGS_SAVED), "success")  # Also works
    return ERROR_NOT_LOGGED_IN, 401  # Works in tuples too

The TranslatableString class ensures messages are translated based on the 
current request context. When Babel is not initialized, it returns the English string.
"""

try:
    from flask_babel import gettext
    BABEL_AVAILABLE = True
except ImportError:
    BABEL_AVAILABLE = False


class TranslatableString(str):
    """
    A string subclass that translates itself when converted to string.
    This allows seamless integration with existing code.
    """
    _content: str  # type annotation for Pylance
    
    def __new__(cls, content):
        # Store the untranslated content
        instance = super().__new__(cls, content)
        instance._content = content  # type: ignore
        return instance
    
    def __str__(self):
        """Apply translation when converted to string."""
        if BABEL_AVAILABLE:
            try:
                return gettext(self._content)  # type: ignore
            except (RuntimeError, AttributeError):
                # Babel not initialized, no request context, or _content not set
                return self._content  # type: ignore
        return self._content  # type: ignore
    
    def __repr__(self):
        return f"TranslatableString({self._content!r})"  # type: ignore
    
    def format(self, *args, **kwargs):
        """Support string formatting with translation."""
        return str(self).format(*args, **kwargs)
    
    def lower(self):
        """Support string methods with translation."""
        return str(self).lower()
    
    def upper(self):
        """Support string methods with translation."""
        return str(self).upper()

# =============================================================================
# Common Errors
# =============================================================================
ERROR_CONFIG_NOT_INIT = TranslatableString("Site configuration not initialized")
ERROR_AUTH_NOT_INIT = TranslatableString("Authentication system not initialized")
ERROR_NOT_LOGGED_IN = TranslatableString("Not logged in")
ERROR_USER_NOT_FOUND = TranslatableString("User not found.")
ERROR_INVALID_FOLDER = TranslatableString("Invalid folder type")
ERROR_FILENAME_REQUIRED = TranslatableString("Filename required")
ERROR_FILE_NOT_FOUND = TranslatableString("Markdown file not found.")

# =============================================================================
# Settings Module Messages
# =============================================================================
ERROR_SETTINGS_MANAGER_NOT_INIT = TranslatableString("Settings manager not initialized")
ERROR_SETTING_UNKNOWN_TYPE = TranslatableString("Unknown setting type")
ERROR_SAVING_USER_OVERRIDE = TranslatableString("Error setting user framework override")
ERROR_SAVING_GLOBAL_CONFIG = TranslatableString("Error setting global config value")
ERROR_SAVING_SETTINGS = TranslatableString("Error saving settings")

MSG_SETTINGS_SAVED = TranslatableString("Settings saved successfully!")
MSG_NO_OVERRIDABLE_SETTINGS = TranslatableString("No settings are currently configured as user-overridable. Contact your administrator.")

TEXT_SETTINGS = TranslatableString("Settings")
TEXT_CONFIGURATION_SETTINGS = TranslatableString("Configuration Settings")
TEXT_SETTINGS_CATEGORIES = TranslatableString("Settings Categories")
TEXT_CATEGORY = TranslatableString("Category")
TEXT_DESCRIPTION = TranslatableString("Description")
TEXT_SETTINGS_COUNT = TranslatableString("Settings Count")
TEXT_ACTIONS = TranslatableString("Actions")
TEXT_SETTING = TranslatableString("Setting")
TEXT_TYPE = TranslatableString("Type")
TEXT_VALUE = TranslatableString("Value")
TEXT_USER_OVERRIDABLE = TranslatableString("User Overridable")
TEXT_USER_FRAMEWORK_SETTINGS = TranslatableString("My Framework Settings")
TEXT_VIEW_SETTINGS = TranslatableString("View Settings")
TEXT_SAVE_SETTINGS = TranslatableString("Save Settings")
TEXT_CONFIGURATION_OPTIONS = TranslatableString("Configuration options for")

# =============================================================================
# Common Module Messages
# =============================================================================
# Template names are not translated (they're file paths)
TEXT_404_TEMPLATE = "404.j2"
TEXT_LOGIN_TEMPLATE = "login.j2"
TEXT_TEMPLATE_BASE = "base.j2"
TEXT_TEMPLATE_BASE_CONTENT = "base_content.j2"

DEFAULT_HELP_TITLE = TranslatableString("Documentation: {}")

# =============================================================================
# User Profile Module Messages
# =============================================================================
TEXT_ACCESS_RESTRICTED = TranslatableString("Access Restricted")
TEXT_GUEST_ACCESS = TranslatableString("Guest Access")
TEXT_PROFILE_NOT_AVAILABLE = TranslatableString("Profile Not Available for Guest Users")
TEXT_GUEST_CANNOT_ACCESS = TranslatableString("Guest users cannot access or modify profile settings.")
TEXT_GUEST_LOGIN_MESSAGE = TranslatableString("Please log in with a registered account to access your profile.")
TEXT_MY_PROFILE = TranslatableString("My Profile")
TEXT_PROFILE_BREADCRUMB = TranslatableString("Profile")
TEXT_PROFILE_INFO = TranslatableString("Profile Information")
TEXT_DISPLAY_NAME = TranslatableString("Display Name")
TEXT_EMAIL = TranslatableString("Email")
TEXT_UPDATE_PROFILE = TranslatableString("Update Profile")
TEXT_PROFILE_PICTURE = TranslatableString("Profile Picture")
TEXT_UPLOAD_NEW_AVATAR = TranslatableString("Upload New Avatar")
TEXT_AVATAR_HELP = TranslatableString("Allowed: JPEG, PNG, SVG. Max size: 1024x1024 (auto-resized for raster images)")
TEXT_CHANGE_PASSWORD = TranslatableString("Change Password")
TEXT_CURRENT_PASSWORD = TranslatableString("Current Password")
TEXT_NEW_PASSWORD = TranslatableString("New Password")
TEXT_CONFIRM_PASSWORD = TranslatableString("Confirm Password")
TEXT_CHANGE_PASSWORD_BTN = TranslatableString("Change Password")
TEXT_PASSWORD_REQUIREMENTS = TranslatableString("Password must be at least 5 characters with letters and numbers.")
TEXT_PASSWORDLESS_ACCOUNT = TranslatableString("This is a passwordless account.")
TEXT_ACCOUNT_INFO = TranslatableString("Account Information")
TEXT_USERNAME = TranslatableString("Username")
TEXT_GROUPS = TranslatableString("Groups")
TEXT_ACCOUNT_CREATED = TranslatableString("Account Created")
TEXT_LAST_LOGIN = TranslatableString("Last Login")
TEXT_UNKNOWN = TranslatableString("Unknown")
TEXT_NEVER = TranslatableString("Never")
TEXT_PROPERTY = TranslatableString("Property")

MSG_PROFILE_UPDATED = TranslatableString("Profile updated successfully!")
MSG_DISPLAY_NAME_EMPTY = TranslatableString("Display name cannot be empty.")
MSG_CURRENT_PASSWORD_INCORRECT = TranslatableString("Current password is incorrect.")
MSG_PASSWORDS_NO_MATCH = TranslatableString("New passwords do not match.")
MSG_PASSWORD_INVALID = TranslatableString("Invalid password")
MSG_PASSWORD_CHANGED = TranslatableString("Password changed successfully!")

# =============================================================================
# Thread Module Messages
# =============================================================================
TEXT_THREAD_MONITOR = TranslatableString("Thread Monitor")
TEXT_BREADCRUMB_THREADS = TranslatableString("Threads")
TEXT_LOADING_THREADS = TranslatableString("<p class='text-muted text-center'><i class='mdi mdi-loading mdi-spin'></i> Loading threads...</p>")
TEXT_THREAD_STOPPED = TranslatableString("✓ Stopped thread: {}")
TEXT_THREAD_NOT_FOUND_STOP = TranslatableString("✗ Thread not found: {}")
TEXT_THREAD_FORCE_KILLED = TranslatableString("✓ Force killed thread: {}")
TEXT_THREAD_NOT_FOUND_KILL = TranslatableString("✗ Thread not found: {}")
TEXT_THREAD_MANAGER_NOT_INIT = TranslatableString("Thread manager not initialized")
TEXT_STAT_TOTAL = TranslatableString("Total Threads")
TEXT_STAT_RUNNING = TranslatableString("Running")
TEXT_STAT_WITH_PROCESS = TranslatableString("With Process")
TEXT_STAT_WITH_ERROR = TranslatableString("With Errors")

# =============================================================================
# File Manager Module Messages
# =============================================================================
# Error Messages
ERROR_FILE_MANAGER_NOT_INITIALIZED = TranslatableString("File manager not initialized")

# User-Facing Messages
TEXT_NO_FILES_UPLOAD = TranslatableString("No files found. Upload files to get started!")
TEXT_NO_FILES_PERMISSION = TranslatableString("No files found. You need 'upload' permission to add files. Contact your administrator.")
TEXT_NO_DELETE_PERMISSION = TranslatableString("You need 'delete' permission to remove files. Contact your administrator.")
TEXT_VERSIONING_INFO = TranslatableString("Group ID for versioning. Files with the same group_id and filename are treated as versions of the same file.")
TEXT_TAGS_INFO = TranslatableString("Organize files with tags for easy searching and filtering.")
TEXT_VERSIONS_DELETED_WARNING = TranslatableString("Files with version history will have <strong>all versions</strong> deleted.")

# Flash Messages
MSG_NO_FILES_SELECTED = TranslatableString("No files selected for deletion.")
MSG_UPDATE_SUCCESS = TranslatableString("Metadata for '{filename}' updated successfully.")
MSG_VERSION_RESTORED = TranslatableString("Version restored successfully! A new version has been created.")
MSG_VERSION_DELETED = TranslatableString("Version deleted successfully.")
MSG_VERSIONS_DELETED = TranslatableString("All versions deleted. File no longer exists.")

# Confirmation and Result Messages
DELETE_CONFIRM_SINGLE = TranslatableString("You are about to permanently delete the following file: <strong>{filename}</strong><br><br>This action cannot be undone.")
DELETE_CONFIRM_MULTIPLE = TranslatableString("You are about to permanently delete <strong>{count} files</strong><br><br>This action cannot be undone.")
DELETE_RESULT_PARTIAL = TranslatableString("<p><strong>{deleted_count}</strong> file(s) deleted successfully.</p>\n            <p><strong>{failed_count}</strong> file(s) failed to delete.</p>")
DELETE_RESULT_SUCCESS = TranslatableString("<p><strong>{deleted_count}</strong> file(s) deleted successfully.</p>")

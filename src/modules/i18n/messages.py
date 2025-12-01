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
    from flask_babel import gettext, _
    BABEL_AVAILABLE = True
    print("[i18n] ✓ Flask-Babel imported successfully")
except ImportError:
    BABEL_AVAILABLE = False
    print("[i18n] ✗ Flask-Babel not available")
    # Fallback gettext that returns original string
    def gettext(s): return s
    def _(s): return s


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
                from flask import has_request_context, current_app
                from flask_babel import get_locale
                
                # Debug info
                if self._content in ["Settings", "My Profile", "Settings saved successfully!", "Upload New Avatar"]:
                    if has_request_context():
                        current_locale = get_locale()
                        print(f"[TranslatableString] Translating '{self._content}' with locale={current_locale}")
                    else:
                        print(f"[TranslatableString] WARNING: No request context for '{self._content}'")
                
                translated = gettext(self._content)  # type: ignore
                
                # Debug output
                if self._content in ["Settings", "My Profile", "Settings saved successfully!", "Upload New Avatar"]:
                    print(f"[TranslatableString] '{self._content}' -> '{translated}'")
                    if translated == self._content:
                        print(f"[TranslatableString] ⚠ Translation not found for '{self._content}'!")
                
                return translated
            except (RuntimeError, AttributeError) as e:
                # Babel not initialized, no request context, or _content not set
                print(f"[TranslatableString] ERROR translating '{self._content}': {e}")
                return self._content  # type: ignore
        print(f"[TranslatableString] BABEL NOT AVAILABLE for '{self._content}'")
        return self._content  # type: ignore
    
    def __repr__(self):
        return f"TranslatableString({self._content!r})"  # type: ignore
    
    def __html__(self):
        """Support Jinja2 autoescape - treat as safe HTML."""
        return str(self)
    
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
ERROR_FILE_NOT_FOUND_FM = TranslatableString("File Not Found")
ERROR_FILE_NOT_FOUND_DESC = TranslatableString("The requested file could not be found.")
ERROR_UPDATE_FAILED = TranslatableString("Update Failed")
ERROR_LOADING_FILES = TranslatableString("Error Loading Files")
ERROR_LOADING_VERSION_HISTORY = TranslatableString("Error Loading Version History")

# Page Titles
TEXT_FILE_MANAGER = TranslatableString("File Manager")
TEXT_FILE_MANAGER_BROWSE = TranslatableString("File Manager - Browse Files")
TEXT_EDIT_FILE_METADATA = TranslatableString("Edit File Metadata")
TEXT_CONFIRM_DELETE = TranslatableString("Confirm Delete")
TEXT_DELETION_COMPLETE = TranslatableString("Deletion Complete")
TEXT_VERSION_HISTORY = TranslatableString("Version History")
TEXT_VERSION_HISTORY_FILE = TranslatableString("Version History: {filename}")

# Breadcrumbs
TEXT_BREADCRUMB_FILE_MANAGER = TranslatableString("File Manager")
TEXT_BREADCRUMB_EDIT_FILE = TranslatableString("Edit File")
TEXT_BREADCRUMB_CONFIRM_DELETE = TranslatableString("Confirm Delete")
TEXT_BREADCRUMB_DELETION_COMPLETE = TranslatableString("Deletion Complete")
TEXT_BREADCRUMB_VERSION_HISTORY = TranslatableString("Version History")

# Buttons
BUTTON_DELETE_SELECTED = TranslatableString("Delete Selected")
BUTTON_SAVE_CHANGES = TranslatableString("Save Changes")
BUTTON_CANCEL = TranslatableString("Cancel")
BUTTON_YES_DELETE = TranslatableString("Yes, Delete")
BUTTON_RETURN_FILE_MANAGER = TranslatableString("Return to File Manager")
BUTTON_BACK_FILE_MANAGER = TranslatableString("Back to File Manager")

# Tooltips
TOOLTIP_DOWNLOAD = TranslatableString("Download")
TOOLTIP_EDIT_METADATA = TranslatableString("Edit Metadata")
TOOLTIP_VIEW_HISTORY = TranslatableString("View History")
TOOLTIP_DELETE = TranslatableString("Delete")
TOOLTIP_DOWNLOAD_VERSION = TranslatableString("Download this version")
TOOLTIP_RESTORE_VERSION = TranslatableString("Restore v{version} as current")
TOOLTIP_DELETE_VERSION = TranslatableString("Delete v{version} only")

# Badges
BADGE_MISSING = TranslatableString("Missing")
BADGE_CORRUPTED = TranslatableString("Corrupted")
BADGE_NOT_FOUND = TranslatableString("Not Found")
BADGE_CURRENT = TranslatableString("Current")
BADGE_ARCHIVED = TranslatableString("Archived")
BADGE_VERSION = TranslatableString("v{version}")

# Labels and Sections
LABEL_FILE_INFORMATION = TranslatableString("File Information")
LABEL_EDIT_METADATA = TranslatableString("Edit Metadata")
LABEL_FILES_TO_DELETE = TranslatableString("Files to Delete")
LABEL_ALL_VERSIONS = TranslatableString("All Versions")
LABEL_GROUP_ID = TranslatableString("Group ID")
LABEL_TAGS = TranslatableString("Tags")
LABEL_SIZE = TranslatableString("Size")
LABEL_TYPE = TranslatableString("Type")
LABEL_UPLOADED = TranslatableString("Uploaded")
LABEL_VERSION = TranslatableString("Version")
LABEL_CHECKSUM = TranslatableString("Checksum")
LABEL_UPLOADED_BY = TranslatableString("Uploaded By")

# Table Headers
TABLE_HEADER_SELECT = TranslatableString("Select")
TABLE_HEADER_PREVIEW = TranslatableString("Preview")
TABLE_HEADER_FILENAME = TranslatableString("Filename")
TABLE_HEADER_GROUP_ID = TranslatableString("Group ID")
TABLE_HEADER_TAGS = TranslatableString("Tags")
TABLE_HEADER_VERSION = TranslatableString("Version")
TABLE_HEADER_SIZE = TranslatableString("Size")
TABLE_HEADER_UPLOADED = TranslatableString("Uploaded")
TABLE_HEADER_INTEGRITY = TranslatableString("Integrity")
TABLE_HEADER_ACTIONS = TranslatableString("Actions")
TABLE_HEADER_STATUS = TranslatableString("Status")
TABLE_HEADER_CHECKSUM = TranslatableString("Checksum")

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
MSG_FILE_MANAGER_NOT_INIT = TranslatableString("File manager not initialized")
MSG_TARGET_VERSION_NOT_FOUND = TranslatableString("Target version not found")
MSG_CURRENT_VERSION_NOT_FOUND = TranslatableString("Current version not found")
MSG_DELETE_VERSION_FAILED = TranslatableString("Failed to delete version.")
MSG_DELETE_VERSION_ERROR = TranslatableString("Failed to delete version: {error}")
MSG_RESTORE_VERSION_ERROR = TranslatableString("Failed to restore version: {error}")

# Confirmation and Result Messages
DELETE_CONFIRM_SINGLE = TranslatableString("You are about to permanently delete the following file: <strong>{filename}</strong><br><br>This action cannot be undone.")
DELETE_CONFIRM_MULTIPLE = TranslatableString("You are about to permanently delete <strong>{count} files</strong><br><br>This action cannot be undone.")
DELETE_RESULT_PARTIAL = TranslatableString("<p><strong>{deleted_count}</strong> file(s) deleted successfully.</p>\n            <p><strong>{failed_count}</strong> file(s) failed to delete.</p>")
DELETE_RESULT_SUCCESS = TranslatableString("<p><strong>{deleted_count}</strong> file(s) deleted successfully.</p>")

# Titles with Icons
TITLE_CONFIRM_DELETION = TranslatableString("Confirm Deletion")
TITLE_PARTIALLY_COMPLETE = TranslatableString("Partially Complete")
TITLE_SUCCESS = TranslatableString("Success")

# =============================================================================
# File Handler Module Messages
# =============================================================================
# Error Messages
ERROR_FILE_HANDLER_NOT_INIT = TranslatableString("File manager not initialized")
ERROR_NO_FILE_PROVIDED = TranslatableString("No file provided")
ERROR_NO_FILE_SELECTED = TranslatableString("No file selected")
ERROR_INVALID_UPLOAD_PATH = TranslatableString("Invalid upload path")
ERROR_FAILED_SAVE_FILE = TranslatableString("Failed to save file")
ERROR_PERMISSION_DENIED_UPLOAD = TranslatableString("Permission denied: You need 'upload' permission for FileManager. Contact your administrator.")
ERROR_PERMISSION_DENIED_DOWNLOAD = TranslatableString("Permission denied: You need 'download' permission for FileManager. Contact your administrator.")
ERROR_PERMISSION_DENIED_DELETE = TranslatableString("Permission denied: You need 'delete' permission for FileManager. Contact your administrator.")
ERROR_PERMISSION_DENIED_VIEW = TranslatableString("Permission denied: You need 'view' permission for FileManager. Contact your administrator.")
ERROR_FILE_NOT_FOUND_HANDLER = TranslatableString("File not found")
ERROR_THUMBNAIL_NOT_FOUND = TranslatableString("Thumbnail not found")
ERROR_ORPHANED_FILE = TranslatableString("File not found on disk")
ERROR_INTERNAL_SERVER = TranslatableString("Internal server error")

# Success Messages
MSG_FILE_DELETED_SUCCESS = TranslatableString("File deleted successfully")
MSG_FILE_TOO_LARGE = TranslatableString("File too large")

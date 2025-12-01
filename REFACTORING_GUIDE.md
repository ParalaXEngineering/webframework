# Constants Refactoring Methodology

## Goal
Refactor constants in Python files to follow the framework pattern:
1. **User-facing strings** → `modules/i18n/messages.py` (as `TranslatableString`)
2. **Generic technical constants** → `modules/constants.py`
3. **Domain-specific constants** → stay in their module
4. **Unused constants** → delete

## Reference Example
Study `src/pages/settings.py` - it demonstrates the correct pattern:
- Imports from `constants.py` (STATUS_OK, BOOL_TRUE_VALUES, DELIMITER_SPLIT)
- Imports from `i18n/messages.py` (ERROR_*, MSG_*, TEXT_* as TranslatableString)
- Keeps module-specific constants (TYPE_STRING, TYPE_INT, CONFIG_WRAPPER, etc.)

---

## Analysis Methodology

### Step 1: Extract All Constants
Find all constant definitions in the target file:
```bash
grep -n "^[A-Z][A-Z_]* = " target_file.py
```

### Step 2: Check Actual Usage
For each constant, count how many times it's actually used:
```bash
# For a specific constant
grep -c "\bCONSTANT_NAME\b" target_file.py

# Batch check multiple constants
for const in CONSTANT_1 CONSTANT_2 CONSTANT_3; do
    echo "=== $const ==="
    grep -c "\b$const\b" target_file.py || echo "0"
done
```

**Key insight**: If count = 1, the constant is **ONLY the definition** → it's ORPHANED → DELETE IT

### Step 3: Categorize Each Constant

#### 🌍 **User-Facing Strings** → Move to `i18n/messages.py`

**Indicators:**
- Variable names start with: `TEXT_`, `MSG_`, `BUTTON_`, `LABEL_`, `ERROR_` (when shown to user), `INFO_`, `SUBTITLE_`
- String values contain:
  - User instructions or help text
  - Error messages for users
  - Button labels
  - Page titles or headings
  - Flash messages
  - Confirmation dialogs
  - Status messages shown in UI
- Contains HTML formatting for display
- Contains format placeholders for user display (`{filename}`, `{count}`)

**Examples:**
```python
# YES - Move to i18n/messages.py
TEXT_FILE_MANAGER = "File Manager"
ERROR_FILE_NOT_FOUND = "File Not Found"  # User sees this
MSG_UPLOAD_SUCCESS = "File uploaded successfully!"
BUTTON_SAVE = "Save Changes"
INFO_NO_FILES = "No files found. Upload files to get started!"
STATUS_UPLOADING = "Uploading file..."  # Shown to user
DELETE_CONFIRM = "Are you sure you want to delete {count} files?"

# NO - Not user-facing (see below categories)
ERROR_LONG_PATH_CODE = errno.ENAMETOOLONG  # Technical error code
STATUS_OK = 200  # HTTP status code
PERMISSION_UPLOAD = "upload"  # Technical permission key
```

#### ⚙️ **Generic Technical Constants** → Move to `constants.py`

**Indicators:**
- Used across multiple modules
- HTTP status codes
- Common delimiters
- Boolean representations
- Standard query parameters

**Examples:**
```python
# YES - Move to constants.py (if not already there)
STATUS_OK = 200
STATUS_NOT_FOUND = 404
DELIMITER_SPLIT = "#"
BOOL_TRUE_VALUES = [True, "true", "on", "1", 1]
PARAM_FILENAME = "filename"

# Already exist in constants.py - just import them:
# STATUS_OK, STATUS_NOT_FOUND, STATUS_BAD_REQUEST, STATUS_SERVER_ERROR
# DELIMITER_SPLIT, DELIMITER_JOIN, DELIMITER_PATH
# BOOL_TRUE_VALUES, BOOL_FALSE_VALUES
```

#### 🏠 **Domain-Specific Constants** → Keep in Module

**Indicators:**
- Configuration keys specific to this module
- API constants (status codes, field IDs)
- File/directory paths specific to module function
- Permission names for this module
- Form field names specific to module
- HTML templates specific to module
- Data structure definitions (table columns)
- Technical enum values
- Archive formats
- Module-specific magic numbers

**Examples:**
```python
# Keep in module - domain/module specific
CONFIG_REDMINE_ADDRESS = "redmine.address.value"  # Redmine-specific
REDMINE_STATUS_CLOSED = 5  # Redmine API constant
PERMISSION_MODULE = "FileManager"  # This module's permission namespace
DIR_UPDATES = "updates"  # Update module's directory
FILE_BOOTLOADER = "BTL.bat"  # Bootloader module's file
TABLE_COLUMNS_MAIN = ["ID", "Name", "Actions"]  # This page's table structure
FORM_FIELD_FILE_IDS = "file_ids[]"  # This form's field name
ARCHIVE_FORMAT_TAR_GZ = "r:gz"  # Archive handling constant
PROGRESS_START = 103  # This module's progress code
SOURCE_FOLDER = "Folder"  # This module's source type enum
ACTION_DOWNLOAD = "download"  # This module's action type
REDMINE_CUSTOM_FIELD_VERSION = 10  # Redmine API field ID
TABLE_PAGE_LENGTH = 25  # This table's default page size
THUMB_DIR = ".thumbs"  # This module's thumbnail directory
```

#### 🗑️ **Orphaned Constants** → DELETE

**Indicators:**
- Defined but never used (grep count = 1, only the definition line)
- Hardcoded inline instead of using the constant
- Duplicate definitions

**How to identify:**
```bash
# If this returns 1, the constant is orphaned (only the definition exists)
grep -c "\bICON_ARROW_LEFT\b" file.py
# Output: 1 → DELETE IT

# Check if it's used inline instead:
grep "icon=\"arrow-left\"" file.py
# If found, either:
# a) Replace all inline uses with the constant, OR
# b) Delete the constant and keep inline usage
```

**Example from file_manager_admin.py:**
```python
# DEFINED but NEVER USED:
ICON_ARROW_LEFT = "arrow-left"  # Line 99

# ACTUALLY USED INLINE:
icon="arrow-left"  # Lines 854, 1014

# Solution: DELETE the constant definition (it's orphaned)
```

---

## Refactoring Process

### Step 1: Analyze and Inventory

Create a table for the file:
```
Constant Name          | Usage Count | Category        | Action
-----------------------|-------------|-----------------|------------------
TEXT_FILE_MANAGER      | 3          | User-facing     | Move to i18n
STATUS_OK              | 5          | Generic         | Import from constants.py
CONFIG_REDMINE_ADDRESS | 4          | Domain-specific | Keep in module
ICON_ARROW_LEFT        | 1          | Orphaned        | DELETE
```

### Step 2: Add to `i18n/messages.py`

For all user-facing strings, add to the appropriate section in `modules/i18n/messages.py`:

```python
# =============================================================================
# [Module Name] Module Messages
# =============================================================================
# Error Messages
ERROR_FILE_NOT_FOUND = TranslatableString("File Not Found")
ERROR_CONNECTION_FAILED = TranslatableString("Connection failed: {error}")

# UI Text and Labels  
TEXT_FILE_MANAGER = TranslatableString("File Manager")
TEXT_EDIT_FILE = TranslatableString("Edit File")

# Status Messages (user-visible)
STATUS_UPLOADING = TranslatableString("Uploading file...")
STATUS_PROCESSING = TranslatableString("Processing, please wait...")

# Flash Messages
MSG_UPLOAD_SUCCESS = TranslatableString("File uploaded successfully!")
MSG_DELETE_CONFIRM = TranslatableString("Are you sure you want to delete {count} files?")

# Buttons
BUTTON_SAVE = TranslatableString("Save Changes")
BUTTON_CANCEL = TranslatableString("Cancel")
```

**Important**: Use format placeholders like `{filename}`, `{count}`, `{error}` instead of Python f-strings or % formatting.

### Step 3: Update Target File Imports

Add imports at the top of the target file:

```python
# Framework modules - constants and i18n
from ..modules.constants import (
    STATUS_OK,
    STATUS_NOT_FOUND,
    STATUS_SERVER_ERROR,
    BOOL_TRUE_VALUES,
    DELIMITER_SPLIT,
)
from ..modules.i18n.messages import (
    ERROR_FILE_NOT_FOUND,
    ERROR_CONNECTION_FAILED,
    TEXT_FILE_MANAGER,
    TEXT_EDIT_FILE,
    STATUS_UPLOADING,
    STATUS_PROCESSING,
    MSG_UPLOAD_SUCCESS,
    MSG_DELETE_CONFIRM,
    BUTTON_SAVE,
    BUTTON_CANCEL,
)
```

### Step 4: Remove Local Definitions

Delete the constant definitions that were moved:
```python
# DELETE THESE LINES:
ERROR_FILE_NOT_FOUND = "File Not Found"  # Now in i18n/messages.py
TEXT_FILE_MANAGER = "File Manager"  # Now in i18n/messages.py
STATUS_OK = 200  # Now imported from constants.py
ICON_ARROW_LEFT = "arrow-left"  # Orphaned, never used
```

### Step 5: Update Usage Sites

Replace format strings with `.format()` method:
```python
# OLD:
flash(f"Metadata for '{filename}' updated successfully.", "success")

# NEW:
flash(MSG_UPDATE_SUCCESS.format(filename=filename), "success")

# OLD:
return f"Error connecting to {server}: {error}", 500

# NEW:
return ERROR_CONNECTION_FAILED.format(error=error), STATUS_SERVER_ERROR
```

### Step 6: Keep Domain-Specific Constants

Leave these untouched in the module:
```python
# Domain-specific - keep in module
CONFIG_REDMINE_ADDRESS = "redmine.address.value"
PERMISSION_MODULE = "FileManager"
DIR_UPDATES = "updates"
FORM_FIELD_FILE_IDS = "file_ids[]"
TABLE_COLUMNS = ["ID", "Name", "Actions"]
REDMINE_STATUS_CLOSED = 5
```

---

## Validation Checklist

After refactoring, verify:

### ✅ Correctness
- [ ] All imports resolve (no ImportError)
- [ ] No NameError for undefined constants
- [ ] Format strings work: `MSG_TEXT.format(key=value)`
- [ ] Flash messages display correctly
- [ ] Error messages show proper text

### ✅ Completeness
- [ ] No user-facing strings left as plain constants in module
- [ ] No orphaned constant definitions remaining
- [ ] Generic constants imported from `constants.py` not redefined
- [ ] All TranslatableString objects work (convert to str automatically)

### ✅ Testing
```bash
# Run tests to catch regressions
pytest tests/ -v

# Check for undefined names
python -m py_compile src/pages/target_file.py

# Search for remaining plain string constants that might need translation
grep -n "^[A-Z_]* = \"" src/pages/target_file.py
```

---

## Common Patterns and Edge Cases

### Pattern 1: Status Messages
```python
# User-visible status → i18n/messages.py
STATUS_UPLOADING = TranslatableString("Uploading file...")

# HTTP status code → constants.py (already exists)
STATUS_OK = 200

# Technical status enum → keep in module
STATUS_PENDING = "pending"  # Database enum value
```

### Pattern 2: Error Messages
```python
# User sees this → i18n/messages.py
ERROR_FILE_NOT_FOUND = TranslatableString("File not found")

# Technical error code → keep in module
ERROR_LONG_PATH_CODE = errno.ENAMETOOLONG
```

### Pattern 3: Icon Constants (Often Orphaned!)
```python
# Defined but unused (grep count = 1):
ICON_DOWNLOAD = "mdi mdi-download"  # DELETE THIS

# Actually used inline everywhere:
icon="mdi mdi-download"  # Keep as-is

# OR refactor to use constant consistently:
ICON_DOWNLOAD = "mdi mdi-download"  # Keep
icon=ICON_DOWNLOAD  # Use everywhere
```

### Pattern 4: HTML Templates
```python
# User-facing text in HTML → i18n/messages.py
DELETE_CONFIRM = TranslatableString("Are you sure?")

# HTML structure template → keep in module
CHECKBOX_TEMPLATE = '<input type="checkbox" name="{name}" value="{value}">'
```

### Pattern 5: Configuration Keys
```python
# Always keep in module (technical identifiers)
CONFIG_SERVER_ADDRESS = "server.address.value"
CONFIG_PORT = "server.port.value"
```

---

## Quick Decision Tree

```
Is the constant used in the code?
├─ NO (grep count = 1) → DELETE IT
└─ YES → Continue...
    │
    ├─ Is it a user-facing string (error, label, message, button)?
    │  └─ YES → Move to i18n/messages.py as TranslatableString
    │
    ├─ Is it generic and used across modules (HTTP codes, delimiters)?
    │  └─ YES → Move to constants.py (or import if already there)
    │
    └─ Is it domain/module-specific (config keys, API constants, paths)?
       └─ YES → KEEP in module
```

---

## Example Workflow for a New File

```bash
# 1. Extract all constants
grep -n "^[A-Z][A-Z_]* = " src/pages/new_file.py > constants_list.txt

# 2. Check usage for each
for const in $(cut -d'=' -f1 constants_list.txt | cut -d':' -f2); do
    count=$(grep -c "\b$const\b" src/pages/new_file.py)
    echo "$const: $count"
done

# 3. Identify orphans (count = 1)
# 4. Categorize remaining (user-facing, generic, domain-specific)
# 5. Refactor following the process above
# 6. Test
pytest tests/ -v
```

---

## Notes

- **TranslatableString**: Automatically converts to translated string when used. Works in f-strings, concatenation, flash messages, etc.
- **Format method**: Always use `.format(key=value)` not f-strings with TranslatableString
- **Existing constants.py entries**: Don't duplicate - just import and use
- **When in doubt**: Check `settings.py` for the reference pattern

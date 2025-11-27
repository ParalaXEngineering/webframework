# Frontend Integration Tests

This directory contains Playwright-based frontend tests for the ParalaX Web Framework.

## Overview

Frontend tests use Playwright to simulate real user interactions with the web interface. They verify:
- Pages load without "Internal server error"
- Forms work correctly
- User actions (clicks, inputs) have the expected effects
- Changes persist correctly
- Error handling and validation work

## Setup

### 1. Install Dependencies

```powershell
# Activate venv
.venv\Scripts\activate

# Install dev dependencies (includes playwright)
pip install -e .[dev]

# Install Playwright browsers (first time only)
playwright install chromium
```

### 2. Start Flask Server

Frontend tests require a running Flask server. Start it manually:

```powershell
# Terminal 1: Start the server
.venv\Scripts\activate
python src/main.py
```

Wait for the server to start (you'll see "Running on http://127.0.0.1:5000").

### 3. Run Tests

In a separate terminal:

```powershell
# Terminal 2: Run tests
.venv\Scripts\activate

# Run all frontend tests
pytest tests/frontend/ -v

# Run specific test file
pytest tests/frontend/test_user_profile.py -v

# Run specific test
pytest tests/frontend/test_user_profile.py::TestUserProfilePage::test_01_profile_page_loads -v

# Run in HUMAN_MODE (visible browser, slower)
$env:HUMAN_MODE="true"; pytest tests/frontend/ -v
```

## Test Structure

```
tests/frontend/
├── __init__.py
├── conftest.py              # Fixtures and helper functions
├── test_avatar.jpg          # Test image for avatar uploads
├── test_user_profile.py     # Tests for /user/profile
└── test_user_preferences.py # Tests for /user/preferences
```

## Test Files

### test_user_profile.py

Tests the user profile page (`/user/profile`):
- ✅ Page loads without errors
- ✅ Display name and email updates
- ✅ Avatar upload (with validation)
- ✅ Password changes (with validation)
- ✅ Error handling (wrong password, weak password, etc.)
- ✅ Account information display

**14 tests total**, ordered to build on each other.

### test_user_preferences.py

Tests the user preferences page (`/user/preferences`):
- ✅ Page loads without errors
- ✅ Theme selection (light/dark)
- ✅ Dashboard layout selection (default/compact/wide)
- ✅ GUEST user restrictions (read-only mode)
- ✅ Preferences persistence across sessions
- ✅ Framework preferences redirect

**13 tests total** across 4 test classes.

## Helper Functions (conftest.py)

### Fixtures
- `browser`: Playwright browser instance (session-scoped)
- `flask_server`: Auto-start/stop Flask server (session-scoped)
- `page`: New page for each test (function-scoped)
- `logged_in_page`: Page with admin user logged in

### Navigation
- `navigate_to(page, path)`: Navigate and check for errors
- `login(page, username, password)`: Login to the app
- `logout(page)`: Logout from the app

### Form Interactions
- `fill_form_field(page, name, value)`: Fill text inputs
- `select_form_option(page, name, value)`: Select dropdown options
- `click_button(page, button_name)`: Click buttons

### Verification
- `page_contains_text(page, text)`: Check if text exists on page
- `check_flash_message(page, message_text, message_type)`: Check for flash messages
- `get_page_text(page)`: Get all visible text from page

## Configuration

Edit `conftest.py` to configure:

```python
# Watch tests run visually (overridden by HUMAN_MODE env var)
HUMAN_MODE = False  # Set to True for debugging

# Test server configuration
BASE_URL = "http://localhost:5000"
TEST_ADMIN_USERNAME = "admin"
TEST_ADMIN_PASSWORD = "admin123"
```

## Test Order

Frontend tests run after integration tests:
1. Integration tests (displayer, resources, auth) - Generate HTML files
2. **Frontend tests (70-71)** - Test user management pages

Order defined in `tests/conftest.py::pytest_collection_modifyitems`.

## Tips

### Debugging Failing Tests

1. **Enable HUMAN_MODE** to watch tests run:
   ```powershell
   $env:HUMAN_MODE="true"; pytest tests/frontend/test_user_profile.py::TestUserProfilePage::test_03_update_display_name -v
   ```

2. **Check browser console output** - printed during test run with 🖥️ prefix

3. **Add wait time** to inspect state:
   ```python
   page.wait_for_timeout(5000)  # 5 second pause
   ```

4. **Check page content**:
   ```python
   print(page.content())  # Full HTML
   print(page.locator('body').inner_text())  # Visible text
   ```

### Writing New Tests

1. **Use ordered test names** (`test_01_`, `test_02_`, etc.) to ensure execution order
2. **Check for "Internal server error"** using `navigate_to()` or `page_contains_text()`
3. **Verify changes by reloading** the page and checking updated values
4. **Use framework-aware helpers** that handle nested form names (`Module.field`)

Example test:
```python
def test_01_my_feature(self, logged_in_page: Page):
    """Test that my feature works."""
    page = logged_in_page
    
    print("\n📄 Test: My feature")
    navigate_to(page, "/my/page")  # Auto-checks for errors
    
    # Interact with page
    fill_form_field(page, "my_field", "test value")
    click_button(page, "btn_submit")
    
    # Verify result
    assert page_contains_text(page, "Success"), \
        "Should show success message"
    
    print("✅ Feature works correctly")
```

## Common Issues

### "Server is NOT running"
- Tests require a running Flask server
- Start the server manually: `python src/main.py`
- Ensure it's running on the correct port (default: 5000)
- Check BASE_URL in conftest.py matches your server URL

### "Could not find select field"
- Use browser DevTools to inspect actual field names
- Framework may nest names as `"Module.field"`
- Helper functions try multiple patterns automatically

### Tests fail but pass in HUMAN_MODE
- Race condition - add `page.wait_for_timeout()` after actions
- Use `wait_for_page_ready()` after navigation/clicks

### Playwright not found
- Run `playwright install chromium` after installing dependencies
- Ensure you're in the virtual environment

## Future Tests

To add tests for other pages:
1. Create new test file: `test_<page_name>.py`
2. Add to test order in `tests/conftest.py`
3. Use existing fixtures and helpers from `conftest.py`
4. Follow naming convention: `TestClassName::test_XX_description`

Example pages to test:
- Admin pages (`/admin/*`)
- File manager (`/file_manager/*`)
- Threading page (`/threads`)
- Settings page (`/settings/*`)

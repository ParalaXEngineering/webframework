"""
Pytest configuration for frontend tests using Playwright.

Provides fixtures for:
- Playwright browser and page (SYNC API)
- Login helper
- Automatic Flask server management (start/stop)
- Helper functions for common UI operations

Set HUMAN_MODE=True to watch tests run with visible browser and slower execution.
"""

import pytest
import subprocess
import time
import requests
from pathlib import Path
from typing import Optional

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page, Playwright


# ============================================================================
# TEST CONFIGURATION
# ============================================================================

# Set to True to watch tests run visually with pauses between actions
HUMAN_MODE = True  # Set to False for headless mode

# Test configuration
BASE_URL = "http://localhost:5001"
TEST_ADMIN_USERNAME = "admin"
TEST_ADMIN_PASSWORD = "admin123"


# ============================================================================
# SESSION FIXTURES - Playwright
# ============================================================================

@pytest.fixture(scope="session")
def playwright_instance() -> Playwright:
    """Start Playwright for the test session."""
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser(playwright_instance: Playwright) -> Browser:
    """Launch browser for the test session."""
    launch_options = {
        'headless': not HUMAN_MODE,
        'args': ['--no-sandbox']
    }
    
    if HUMAN_MODE:
        launch_options['slow_mo'] = 50  # 50ms delay between actions
    
    mode_str = "HUMAN MODE (visible, slow)" if HUMAN_MODE else "headless mode"
    print(f"\n🌐 Launching browser in {mode_str}...")
    
    browser = playwright_instance.chromium.launch(**launch_options)
    yield browser
    browser.close()


@pytest.fixture(scope="session")
def reset_auth_state():
    """
    Reset authentication state before tests start.
    
    This ensures admin password is 'admin' and failed login attempts are cleared.
    Prevents test failures due to locked accounts or changed passwords from previous runs.
    """
    import json
    import bcrypt
    
    print("\n" + "="*80)
    print("🔄 Resetting authentication state...")
    print("="*80)
    
    # Reset admin password to 'admin'
    users_file = Path("Manual_Webapp/website/auth/users.json")
    if users_file.exists():
        try:
            with open(users_file, 'r') as f:
                users_data = json.load(f)
            
            # Generate hash for 'admin' password
            password_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            if 'admin' in users_data:
                users_data['admin']['password_hash'] = password_hash
                with open(users_file, 'w') as f:
                    json.dump(users_data, f, indent=2)
                print("  ✅ Reset admin password to 'admin'")
        except Exception as e:
            print(f"  ⚠️  Could not reset users file: {e}")
    
    # Clear failed login attempts
    failed_logins_file = Path("Manual_Webapp/website/auth/failed_logins.json")
    if failed_logins_file.exists():
        try:
            with open(failed_logins_file, 'r') as f:
                failed_data = json.load(f)
            
            if 'admin' in failed_data:
                failed_data['admin'] = {'count': 0, 'locked_until': None}
                with open(failed_logins_file, 'w') as f:
                    json.dump(failed_data, f, indent=4)
                print("  ✅ Cleared failed login attempts for admin")
        except Exception as e:
            print(f"  ⚠️  Could not reset failed logins file: {e}")
    
    print("="*80 + "\n")
    yield


@pytest.fixture(scope="session")
def flask_server(reset_auth_state):
    """
    Verify Flask server is running before tests.
    
    This fixture checks that the server is already running at BASE_URL.
    Tests assume you have started the server manually with: python src/main.py
    
    Depends on reset_auth_state to ensure clean authentication state.
    """
    print("\n" + "="*80)
    print("🔍 Checking if Flask server is running...")
    print("="*80)
    
    # Check if server is running
    max_attempts = 2
    for attempt in range(max_attempts):
        try:
            print(f"  Attempt {attempt + 1}/{max_attempts}: Connecting to {BASE_URL}...")
            response = requests.get(BASE_URL, timeout=10)
            print(f"  Response: HTTP {response.status_code}")
            if response.status_code == 200:
                print(f"✅ Server is running at {BASE_URL}")
                print("="*80 + "\n")
                yield None
                return
        except requests.exceptions.RequestException as e:
            print(f"  Connection failed: {type(e).__name__}: {e}")
            if attempt < max_attempts - 1:
                time.sleep(0.5)
    
    # Server not running
    print(f"❌ Server is NOT running at {BASE_URL}")
    print("\n⚠️  Please start the server manually before running tests:")
    print("   1. Open a terminal")
    print("   2. Activate venv: .venv\\Scripts\\activate")
    print("   3. Run: python src/main.py")
    print("   4. Wait for server to start")
    print("   5. Run tests in another terminal")
    print("="*80 + "\n")
    
    pytest.skip(f"Flask server is not running at {BASE_URL}. Please start it manually.")


# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def browser_context(browser: Browser) -> "BrowserContext":
    """Create a shared browser context for the session to persist cookies/login state."""
    context = browser.new_context(
        viewport={'width': 1280, 'height': 720}
    )
    yield context
    context.close()


@pytest.fixture
def page(browser_context, flask_server) -> Page:
    """Create a new page for each test, but reuse the browser context.
    
    This allows cookies/session to persist across tests for faster execution.
    Depends on flask_server to ensure server is running before creating page.
    """
    page = browser_context.new_page()
    
    # Set default timeout to 2 seconds for faster failure detection
    page.set_default_timeout(2000)
    
    # Enable console message logging
    page.on("console", lambda msg: print(f"🖥️  Browser console [{msg.type}]: {msg.text}"))
    
    # Enable error logging
    page.on("pageerror", lambda exc: print(f"❌ Page error: {exc}"))
    
    # Enable response logging to catch 500 errors
    def log_response(response):
        if response.status >= 400:
            print(f"⚠️  HTTP {response.status}: {response.url}")
    
    page.on("response", log_response)
    
    yield page
    page.close()


@pytest.fixture
def logged_in_page(page: Page) -> Page:
    """Provide a logged-in page with admin credentials.
    
    Checks if already logged in before performing login to speed up tests.
    """
    # Check if already logged in
    if is_logged_in_as_admin(page):
        print(f"  ⚡ Already logged in as {TEST_ADMIN_USERNAME}, skipping login")
        return page
    
    # Reset any account lockouts before logging in
    reset_account_lockout(TEST_ADMIN_USERNAME)
    
    # Perform login
    login(page, TEST_ADMIN_USERNAME, TEST_ADMIN_PASSWORD)
    
    # Verify we're actually logged in
    if is_logged_in_as_admin(page):
        print(f"  ✅ Logged in as {TEST_ADMIN_USERNAME}")
        return page
    
    # If verification failed, we might be GUEST - try logging in again
    print(f"  ⚠️  Login verification failed, retrying...")
    login(page, TEST_ADMIN_USERNAME, TEST_ADMIN_PASSWORD)
    return page


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def login(
    page: Page,
    username: str = TEST_ADMIN_USERNAME,
    password: str = TEST_ADMIN_PASSWORD,
    base_url: str = BASE_URL
):
    """Login to the application.
    
    Args:
        page: Playwright page object
        username: Username for login
        password: Password for login
        base_url: Base URL of the application
    """
    # Try navigating to login page with increased timeout
    # Sometimes the server is slow to respond, especially on slower machines
    try:
        page.goto(f"{base_url}/common/login", timeout=20000)
    except Exception as e:
        # If goto fails, try once more after a brief wait
        print(f"  ⚠️  First login attempt failed: {e}")
        page.wait_for_timeout(1000)
        page.goto(f"{base_url}/common/login", timeout=20000)
    
    # Wait for login form to load
    page.wait_for_selector('select[name="user"]', timeout=5000)
    
    # Select user from dropdown
    page.select_option('select[name="user"]', username)
    
    # Fill password
    page.fill('input[name="password"]', password)
    
    # Submit form
    page.click('button.btn-primary')
    
    # Wait for redirect - use 'load' instead of 'networkidle' to avoid SocketIO timeout issues
    # SocketIO keeps connections open, so networkidle may never trigger
    page.wait_for_load_state('load', timeout=10000)
    
    # Give a brief moment for SocketIO to initialize
    page.wait_for_timeout(500)


def is_logged_in_as_admin(page: Page) -> bool:
    """Check if currently logged in as admin.
    
    Args:
        page: Playwright page object
        
    Returns:
        True if logged in as admin, False otherwise
    """
    try:
        # Navigate to a safe page if not already there to check session
        current_url = page.url
        if not current_url.startswith(BASE_URL):
            page.goto(BASE_URL, timeout=5000)
        
        # Look for the topbar button containing the username
        topbar_button = page.locator('#topbar_target')
        if topbar_button.count() > 0:
            button_text = topbar_button.inner_text().strip().lower()
            return TEST_ADMIN_USERNAME.lower() in button_text
    except Exception:
        pass
    
    return False


def logout(page: Page, base_url: str = BASE_URL):
    """Logout from the application."""
    page.goto(f"{base_url}/common/logout")
    page.wait_for_load_state('load')


def navigate_to(page: Page, path: str, base_url: str = BASE_URL):
    """Navigate to a specific path and check for errors.
    
    Args:
        page: Playwright page
        path: URL path (e.g., '/user/profile')
        base_url: Base URL of the application
    
    Raises:
        AssertionError: If page contains "Internal server error" or HTTP error
    """
    url = f"{base_url}{path}"
    response = page.goto(url, timeout=10000)
    
    # Check for HTTP errors
    if response and response.status >= 400:
        page_content = page.content()[:500]
        raise AssertionError(
            f"❌ HTTP {response.status} error when navigating to {url}\n"
            f"Page content preview: {page_content}"
        )
    
    wait_for_page_ready(page, f"navigation to {path}")
    
    # Check for internal server error in page content
    page_text = page.content().lower()
    if "internal server error" in page_text:
        raise AssertionError(
            f"❌ Page contains 'Internal server error' at {url}\n"
            f"Page title: {page.title()}"
        )


def wait_for_page_ready(page: Page, context: str = "page load", timeout: int = 2000):
    """
    Wait for page to be ready with better error handling.
    
    Args:
        page: Playwright page
        context: Description of what we're waiting for
        timeout: Timeout in milliseconds
    """
    page.wait_for_timeout(200)


def fill_form_field(page: Page, name: str, value: str):
    """Fill a form field by name.
    
    Handles both simple names and framework-nested names (Module.field).
    
    Args:
        page: Playwright page
        name: Field name (e.g., 'input_display_name' or 'User Profile.input_display_name')
        value: Value to fill
    """
    # Try exact match first
    selector = f'input[name="{name}"], textarea[name="{name}"]'
    if page.locator(selector).count() > 0:
        page.fill(selector, value, timeout=2000)
        return
    
    # Try partial match (framework nesting)
    selector = f'input[name$=".{name}"], textarea[name$=".{name}"]'
    if page.locator(selector).count() > 0:
        page.fill(selector, value, timeout=2000)
        return
    
    # Try contains match
    selector = f'input[name*="{name}"], textarea[name*="{name}"]'
    if page.locator(selector).count() > 0:
        page.fill(selector, value, timeout=2000)
        return
    
    # If nothing found, fail with helpful error
    all_inputs = page.locator('input, textarea').all()
    input_names = [inp.get_attribute('name') for inp in all_inputs[:10]]  # First 10
    raise AssertionError(
        f"❌ Could not find input field for '{name}'!\n"
        f"Available input fields (first 10): {input_names}\n"
        f"Current URL: {page.url}"
    )


def fill_tinymce_field(page: Page, name: str, value: str):
    """Fill a TinyMCE rich text editor field.
    
    TinyMCE hides the original textarea and uses an iframe for editing.
    This helper uses JavaScript to set the content directly.
    
    Args:
        page: Playwright page
        name: Field name (e.g., 'Create Tooltip.content')
        value: HTML content to set
    """
    # Find the textarea (it's hidden but still exists in DOM)
    selector = f'textarea[name="{name}"]'
    if page.locator(selector).count() == 0:
        # Try partial match
        selector = f'textarea[name*="{name}"]'
    
    field = page.locator(selector).first
    if field.count() > 0:
        # Use JavaScript to set the value and trigger TinyMCE update
        field.evaluate(f"el => {{ el.value = `{value}`; if (tinymce && tinymce.get(el.id)) {{ tinymce.get(el.id).setContent(`{value}`); }} }}")
        page.wait_for_timeout(100)
    else:
        raise AssertionError(
            f"❌ Could not find textarea for TinyMCE field '{name}'!\n"
            f"Current URL: {page.url}"
        )


def select_form_option(page: Page, name: str, value: str, timeout: int = 2000):
    """Select an option from a dropdown.
    
    Args:
        page: Playwright page
        name: Field name
        value: Value to select
        timeout: Timeout in milliseconds
    """
    # Pattern 1: Exact match
    selector = f'select[name="{name}"]'
    if page.locator(selector).count() > 0:
        page.select_option(selector, value, timeout=timeout)
        return
    
    # Pattern 2: Ends with .name (framework nesting)
    selector = f'select[name$=".{name}"]'
    if page.locator(selector).count() > 0:
        page.select_option(selector, value, timeout=timeout)
        return
    
    # Pattern 3: Contains the name
    selector = f'select[name*="{name}"]'
    if page.locator(selector).count() > 0:
        page.select_option(selector, value, timeout=timeout)
        return
    
    # If nothing found, fail with helpful error
    all_selects = page.locator('select').all()
    select_names = [sel.get_attribute('name') for sel in all_selects]
    raise AssertionError(
        f"❌ Could not find select field for '{name}'!\n"
        f"Available select fields: {select_names}\n"
        f"Current URL: {page.url}"
    )


def click_button(page: Page, button_name: str, timeout: int = 2000):
    """Click a button by its name attribute or text content.
    
    Args:
        page: Playwright page
        button_name: Button name attribute (e.g., 'btn_update_info') or text
        timeout: Timeout in milliseconds
    """
    # Try by name attribute first
    selector = f'button[name="{button_name}"]'
    if page.locator(selector).count() > 0:
        page.click(selector, timeout=timeout)
        return
    
    # Try by name ending with button_name (framework nesting)
    selector = f'button[name$=".{button_name}"]'
    if page.locator(selector).count() > 0:
        page.click(selector, timeout=timeout)
        return
    
    # Try by text content
    selector = f'button:has-text("{button_name}")'
    if page.locator(selector).count() > 0:
        page.click(selector, timeout=timeout)
        return
    
    # If nothing found, fail
    all_buttons = page.locator('button').all()
    button_info = [(btn.get_attribute('name'), btn.inner_text()) for btn in all_buttons]
    raise AssertionError(
        f"❌ Could not find button '{button_name}'!\n"
        f"Available buttons (name, text): {button_info}\n"
        f"Current URL: {page.url}"
    )


def check_flash_message(page: Page, message_text: Optional[str] = None, message_type: Optional[str] = None) -> bool:
    """Check for flash messages.
    
    Args:
        page: Playwright page
        message_text: Optional text to search for in the message
        message_type: Optional message type (success, danger, warning, info)
    
    Returns:
        True if message found matching criteria, False otherwise
    """
    # Wait a bit for flash messages to appear
    page.wait_for_timeout(300)
    
    # Look for flash messages (Bootstrap alerts)
    selector = '.alert'
    if message_type:
        selector = f'.alert-{message_type}'
    
    alerts = page.locator(selector).all()
    
    if not alerts:
        return False
    
    if message_text:
        for alert in alerts:
            if message_text.lower() in alert.inner_text().lower():
                return True
        return False
    
    return True


def get_page_text(page: Page) -> str:
    """Get all visible text from the page.
    
    Args:
        page: Playwright page
    
    Returns:
        Page text content
    """
    return page.locator('body').inner_text()


def page_contains_text(page: Page, text: str) -> bool:
    """Check if page contains specific text.
    
    Args:
        page: Playwright page
        text: Text to search for (case-insensitive)
    
    Returns:
        True if text found, False otherwise
    """
    page_text = get_page_text(page).lower()
    return text.lower() in page_text


def select_multi_list_values(page: Page, field_id: str, values: list, timeout: int = 2000):
    """Select multiple values in a DisplayerItemInputMultiSelect field.
    
    This handles the framework's multi-select pattern where clicking "+" adds
    additional select dropdowns, and each dropdown can hold one value.
    
    Args:
        page: Playwright page
        field_id: The field ID (e.g., "Create Tooltip.contexts")
        values: List of values to select (one per dropdown)
        timeout: Timeout in milliseconds
        
    Example:
        select_multi_list_values(page, "Create Tooltip.contexts", 
                               ["Global - Global context", "Custom - My context"])
    """
    if not values:
        return
    
    # Select the first value in the first dropdown (always exists)
    first_select = page.locator(f'select[name="{field_id}.list0"]')
    first_select.select_option(values[0], timeout=timeout)
    
    # For additional values, click "+" and select in new dropdowns
    for i, value in enumerate(values[1:], start=1):
        # Click the "+" button to add a new dropdown
        add_button = page.locator(f'a[onclick*="setting_add_list(\'{field_id}\')"]')
        add_button.click()
        page.wait_for_timeout(100)  # Brief wait for DOM update
        
        # Select the value in the newly created dropdown
        new_select = page.locator(f'select[name="{field_id}.list{i}"]')
        new_select.select_option(value, timeout=timeout)


def reset_account_lockout(username: str):
    """Reset failed login attempts for a user to prevent account lockout.
    
    Args:
        username: Username to reset
    """
    from pathlib import Path
    import json
    
    lockout_file = Path("website/auth/failed_logins.json")
    if lockout_file.exists():
        try:
            with open(lockout_file, 'r') as f:
                data = json.load(f)
            
            if username in data:
                data[username] = {'count': 0, 'locked_until': None}
                with open(lockout_file, 'w') as f:
                    json.dump(data, f, indent=2)
        except Exception:
            pass  # Ignore errors - file might not exist or be malformed

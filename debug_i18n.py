#!/usr/bin/env python
"""
Debug tool to check i18n locale detection.
Run this to see what locale is being selected and why.
"""
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Change to framework root
os.chdir(os.path.dirname(__file__))

from flask import Flask, session

# Create test app
app = Flask(
    __name__,
    static_folder=os.path.join("webengine", "assets"),
    template_folder=os.path.join("templates")
)
app.config["SECRET_KEY"] = "test-debug"
app.config['TESTING'] = True

# Initialize Babel
from modules.i18n import init_babel
babel = init_babel(app)

def test_scenario(description, setup_func):
    """Test a specific locale detection scenario."""
    print(f"\n{'='*60}")
    print(f"Scenario: {description}")
    print('='*60)
    
    with app.test_request_context():
        setup_func()
        
        from flask_babel import get_locale
        from modules.i18n.messages import TEXT_SETTINGS, MSG_SETTINGS_SAVED
        
        locale = get_locale()
        
        print(f"Session locale: {session.get('locale', 'Not set')}")
        print(f"Detected locale: {locale}")
        print(f"\nTranslation test:")
        print(f"  TEXT_SETTINGS = '{str(TEXT_SETTINGS)}'")
        print(f"  MSG_SETTINGS_SAVED = '{str(MSG_SETTINGS_SAVED)}'")
        
        if locale == 'fr':
            if str(TEXT_SETTINGS) == "Paramètres":
                print(f"\n✓ French translation working!")
            else:
                print(f"\n✗ French locale detected but translation not working!")
                print(f"   Expected: 'Paramètres', Got: '{str(TEXT_SETTINGS)}'")
        elif locale == 'en':
            if str(TEXT_SETTINGS) == "Settings":
                print(f"\n✓ English translation working!")
            else:
                print(f"\n✗ English locale detected but unexpected translation!")
        
        # Force refresh and test again
        from flask_babel import refresh
        refresh()
        print(f"\nAfter refresh():")
        print(f"  TEXT_SETTINGS = '{str(TEXT_SETTINGS)}'")

print("="*60)
print("i18n Locale Detection Debug Tool")
print("="*60)

# Scenario 1: No session, default
test_scenario("Default (no session)", lambda: None)

# Scenario 2: English in session
test_scenario("English in session", lambda: session.update({'locale': 'en'}))

# Scenario 3: French in session
test_scenario("French in session", lambda: session.update({'locale': 'fr'}))

print("\n" + "="*60)
print("Debug complete!")
print("="*60)
print("\nIf French is not working:")
print("1. Check that translations/fr/LC_MESSAGES/messages.mo exists")
print("2. Verify your config.json has framework_ui.language setting")
print("3. In your browser, check Network tab to see session cookies")
print("4. Try clearing browser cache and Flask session")

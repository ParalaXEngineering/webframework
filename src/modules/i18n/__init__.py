"""
Internationalization (i18n) support using Flask-Babel.

This module provides Babel initialization and configuration for the framework.
Import this in your main application setup to enable i18n support.
"""
from flask import session
from flask_babel import Babel

babel = Babel()


def get_locale():
    """
    Determine the locale for the current user.
    
    Priority:
    1. Session-stored locale (set when user changes language in settings)
    2. User's framework_ui.language setting (if authenticated)
    3. Global framework_ui.language setting
    4. Browser's Accept-Language header
    5. Default to 'en'
    
    Returns:
        str: Locale code (e.g., 'en', 'fr')
    """
    # Priority 1: Session locale (set when user explicitly changes language)
    if 'locale' in session:
        locale = session['locale']
        print(f"[i18n] ✓ Locale from session: {locale}")
        return locale
    
    print("[i18n] No locale in session, checking settings...")
    
    # Priority 2 & 3: Try to get from settings (user override or global)
    try:
        from ..auth import auth_manager
        from ..settings import settings_manager
        
        if settings_manager:
            # Try user override first (if authenticated)
            if auth_manager:
                current_user = auth_manager.get_current_user()
                if current_user and current_user.upper() != 'GUEST':
                    lang_override = auth_manager.get_user_framework_override(
                        current_user, "framework_ui.language"
                    )
                    if lang_override:
                        print(f"[i18n] ✓ Locale from user override ({current_user}): {lang_override}")
                        return lang_override
            
            # Fall back to global setting
            try:
                global_lang = settings_manager.get_setting("framework_ui.language")
                if global_lang:
                    print(f"[i18n] ✓ Locale from global setting: {global_lang}")
                    return global_lang
            except (KeyError, AttributeError) as e:
                print(f"[i18n] No global language setting: {e}")
    except (ImportError, AttributeError, RuntimeError, KeyError) as e:
        print(f"[i18n] Error reading settings: {e}")
    
    # Priority 4: Browser preference
    try:
        from flask import request
        browser_lang = request.accept_languages.best_match(['en', 'fr'])
        if browser_lang:
            print(f"[i18n] ✓ Locale from browser: {browser_lang}")
            return browser_lang
    except RuntimeError:
        # No request context
        pass
    
    # Priority 5: Default
    print("[i18n] ✓ Using default locale: en")
    return 'en'


def init_babel(app):
    """
    Initialize Babel with Flask app and register locale selector.
    
    Args:
        app: Flask application instance
        
    Returns:
        Babel: Initialized Babel instance
        
    Example:
        from modules.i18n import init_babel
        
        app = Flask(__name__)
        babel = init_babel(app)
    """
    import os
    
    # Debug: Show current working directory
    cwd = os.getcwd()
    print(f"[i18n] Current working directory: {cwd}")
    print(f"[i18n] Translation directory exists: {os.path.exists('translations')}")
    print(f"[i18n] French .mo file exists: {os.path.exists('translations/fr/LC_MESSAGES/messages.mo')}")
    
    # Use absolute path to translations directory
    # Get framework root (3 levels up from this file: src/modules/i18n/__init__.py -> src/modules -> src -> framework_root)
    this_file = os.path.abspath(__file__)
    i18n_dir = os.path.dirname(this_file)  # src/modules/i18n/
    modules_dir = os.path.dirname(i18n_dir)  # src/modules/
    src_dir = os.path.dirname(modules_dir)  # src/
    framework_root = os.path.dirname(src_dir)  # framework root
    translations_dir = os.path.join(framework_root, 'translations')
    
    print(f"[i18n] Using absolute translations path: {translations_dir}")
    print(f"[i18n] Absolute .mo file exists: {os.path.exists(os.path.join(translations_dir, 'fr/LC_MESSAGES/messages.mo'))}")
    
    # Configure Babel
    app.config['BABEL_DEFAULT_LOCALE'] = 'en'
    app.config['BABEL_SUPPORTED_LOCALES'] = ['en', 'fr']
    app.config['BABEL_TRANSLATION_DIRECTORIES'] = translations_dir  # Use absolute path!
    
    babel.init_app(app, locale_selector=get_locale)
    print(f"[i18n] ✓ Babel initialized with locale_selector")
    return babel

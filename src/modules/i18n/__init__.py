"""
Internationalization (i18n) support using Flask-Babel.

This module provides Babel initialization and configuration for the framework.
Import this in your main application setup to enable i18n support.
"""
from flask_babel import Babel

babel = Babel()


def init_babel(app):
    """
    Initialize Babel with Flask app.
    
    Args:
        app: Flask application instance
        
    Returns:
        Babel: Initialized Babel instance
        
    Example:
        from modules.i18n import init_babel
        
        app = Flask(__name__)
        babel = init_babel(app)
        
        @babel.localeselector
        def get_locale():
            return request.accept_languages.best_match(['en', 'fr', 'es'])
    """
    babel.init_app(app)
    return babel

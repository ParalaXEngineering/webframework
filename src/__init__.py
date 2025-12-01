"""ParalaX Web Framework - A robust Flask-based web framework.

A comprehensive framework for building display and management applications
with integrated authentication, file management, scheduling, and real-time
thread monitoring via SocketIO.
"""

__version__ = "1.0.0"
__author__ = "ParalaX Engineering"

# Make the main app accessible from the package
# Note: app and setup_app import will only work if Flask is available
try:
    from .main import app, setup_app
    __all__ = ['app', 'setup_app']
except (ImportError, FileNotFoundError):
    # During testing or when dependencies are missing, gracefully degrade
    app = None
    setup_app = None
    __all__ = []

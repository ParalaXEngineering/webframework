"""
Pages package - Flask blueprints and route handlers.

This package contains all HTTP route handlers (views/controllers) that handle
web requests and responses. Pages should focus on:
- Request/response handling
- Template rendering
- Form validation
- Session management
- Calling business logic from modules

Business logic should be in src.modules instead.
"""

from . import common
from . import settings
from . import updater
from . import packager
from . import bug_tracker

__all__ = ['common', 'settings', 'updater', 'packager', 'bug_tracker']

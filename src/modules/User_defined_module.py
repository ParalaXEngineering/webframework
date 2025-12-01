"""Generic user-defined module with custom permissions.

Provides a base class for user-specific modules that inherit from Threaded_action
to support background tasks with real-time progress updates via SocketIO.
"""

try:
    from .threaded import Threaded_action
    from .i18n.messages import TEXT_CUSTOM_MODULE_DEFAULT
except ImportError:
    from threaded import Threaded_action
    from i18n.messages import TEXT_CUSTOM_MODULE_DEFAULT


class User_defined_module(Threaded_action):
    """Generic module template with user-specific permission control.
    
    Extends Threaded_action to support background tasks. Subclasses should
    override the `action()` method to implement custom behavior and use
    `emit_console()` for real-time updates to the user's SocketIO room.
    """

    m_default_name = TEXT_CUSTOM_MODULE_DEFAULT

    def __init__(self):
        """Initialize the user-defined module."""
        super().__init__()

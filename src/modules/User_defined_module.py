try:
    from .threaded import Threaded_action
except ImportError:
    from threaded import Threaded_action


class User_defined_module(Threaded_action):
    """Generic module with user specific permission"""

    m_default_name = " "

    def __init__(self):
        super().__init__()

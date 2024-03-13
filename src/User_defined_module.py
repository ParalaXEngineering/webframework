from website import threaded_action


class User_defined_module(threaded_action.Threaded_action):
    """Generic module with user specific permission"""

    m_default_name = " "

    def __init__(self):
        super().__init__()

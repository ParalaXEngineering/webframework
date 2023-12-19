class Action:
    """Base class to execute immediate action. This module is a simplified version of the thraded_action, which provides the minimum in order to successfully integrate with web display engine
    """

    m_default_name = "Default"
    """Name of the action"""

    m_type = "Action"
    """The type of the module"""

    def start(self):
        """Main function 
        """
        return

    def get_name(self) -> str:
        """ Return the name of the instance

        :return: The name of the instance
        :rtype: str
        """
        if self.m_name:
            return self.m_name

        return self.m_default_name
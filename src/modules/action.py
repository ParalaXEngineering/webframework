class Action:
    """Base class to execute immediate action.
    This module is a simplified version of the thraded_action,
    which provides the minimum in order to successfully
    integrate with web display engine
    """

    m_default_name = "Default"
    """Name of the action"""

    m_type = "Action"
    """The type of the module"""
    
    m_required_permission = None
    """The permission module name required to access this module (e.g., 'Demo_Threading'). None means no permission check."""
    
    m_required_action = 'view'
    """The action required to access this module (e.g., 'view', 'execute', 'edit'). Default is 'view'."""
    
    # User context - set by framework when module is loaded
    _current_user = None
    _user_permissions = []
    _is_guest = False
    _is_readonly = True

    def start(self):
        """Main function"""
        return
    
    def get_current_user(self):
        """
        Get the current logged-in username.
        
        Returns:
            Username or None if not set
        """
        return self._current_user
    
    def get_user_permissions(self):
        """
        Get all permissions the current user has for this module.
        
        Returns:
            List of permission actions (e.g., ['view', 'edit', 'execute'])
        """
        return self._user_permissions.copy() if self._user_permissions else []
    
    def is_guest_user(self):
        """
        Check if the current user is a guest.
        
        Returns:
            True if user is GUEST
        """
        return self._is_guest
    
    def is_readonly_mode(self):
        """
        Check if the module is in read-only mode for the current user.
        
        A module is read-only if the user doesn't have write/edit/execute permissions.
        
        Returns:
            True if read-only (user can only view)
        """
        return self._is_readonly
    
    def has_permission(self, action):
        """
        Check if the current user has a specific permission for this module.
        
        Args:
            action: Permission to check (e.g., 'write', 'edit', 'execute')
        
        Returns:
            True if user has the permission
        """
        return action in self._user_permissions if self._user_permissions else False

    def get_name(self) -> str:
        """Return the name of the instance

        :return: The name of the instance
        :rtype: str
        """
        if hasattr(self, 'm_name') and self.m_name:  # type: ignore
            return self.m_name  # type: ignore

        return self.m_default_name

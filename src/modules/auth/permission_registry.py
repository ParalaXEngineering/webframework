"""
Module permission registry for action registration.
"""

from typing import Dict, List, Set

# =============================================================================
# Permission System Constants (Domain-Specific)
# =============================================================================
# Default permission action that all modules have implicitly
PERMISSION_ACTION_VIEW = "view"


class PermissionRegistry:
    """
    Global registry for module permissions.
    Modules register their available actions here.
    """
    
    _instance = None
    _modules: Dict[str, Set[str]] = {}
    
    def __new__(cls):
        """
        Singleton pattern.
        
        Returns:
            The single PermissionRegistry instance
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def register_module(self, module_name: str, actions: List[str]):
        """
        Register a module with its available actions.
        
        By default, all modules have 'view' permission (implicit).
        Use this method to register additional custom actions beyond 'view'.
        
        Args:
            module_name: Name of the module (e.g., "FileManager")
            actions: Additional action names beyond 'view' (e.g., ["upload", "download", "delete"])
            
        Example:
            # At the top of your module file:
            permission_registry.register_module("FileManager", ["upload", "download", "delete"])
            # This creates: view (implicit), upload, download, delete
        """
        if module_name not in self._modules:
            self._modules[module_name] = set()
        
        # Always include 'view' as the base permission
        self._modules[module_name].add(PERMISSION_ACTION_VIEW)
        
        # Add custom actions
        self._modules[module_name].update(actions)
    
    def get_module_actions(self, module_name: str) -> List[str]:
        """
        Get all registered actions for a module.
        
        Args:
            module_name: Name of the module
            
        Returns:
            List of action names, sorted alphabetically
        """
        return sorted(self._modules.get(module_name, set()))
    
    def get_all_modules(self) -> List[str]:
        """
        Get all registered module names.
        
        Returns:
            List of module names, sorted alphabetically
        """
        return sorted(self._modules.keys())
    
    def is_action_valid(self, module_name: str, action: str) -> bool:
        """
        Check if an action is valid for a module.
        
        Args:
            module_name: Name of the module
            action: Action name to check
            
        Returns:
            True if action is registered for module
        """
        return action in self._modules.get(module_name, set())
    
    def clear(self):
        """Clear all registered modules (for testing)."""
        self._modules.clear()


# Global singleton instance
permission_registry = PermissionRegistry()

"""
Module permission registry for action registration.
"""

from typing import Dict, List, Set


class PermissionRegistry:
    """
    Global registry for module permissions.
    Modules register their available actions here.
    """
    
    _instance = None
    _modules: Dict[str, Set[str]] = {}
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def register_module(self, module_name: str, actions: List[str]):
        """
        Register a module with its available actions.
        
        Args:
            module_name: Name of the module (e.g., "DEV_example")
            actions: List of action names (e.g., ["read", "write", "execute"])
        """
        if module_name not in self._modules:
            self._modules[module_name] = set()
        
        # Always include standard CRUD actions
        standard_actions = {"read", "write", "delete"}
        self._modules[module_name].update(standard_actions)
        
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

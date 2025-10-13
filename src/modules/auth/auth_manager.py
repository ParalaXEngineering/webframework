"""
Main authentication and authorization manager.
"""

import json
from pathlib import Path
from typing import Optional, List, Dict, Set
from datetime import datetime
from flask import session

from .auth_models import User, ModulePermission
from .auth_utils import hash_password, verify_password, get_default_user_prefs


class AuthManager:
    """
    Manages user authentication, permissions, and preferences.
    
    Replaces the old access_manager with a cleaner, more granular approach.
    """
    
    def __init__(self, auth_dir: str = "website/auth"):
        """
        Initialize AuthManager.
        
        Args:
            auth_dir: Directory containing auth data files
        """
        self.auth_dir = Path(auth_dir)
        self.users_file = self.auth_dir / "users.json"
        self.permissions_file = self.auth_dir / "permissions.json"
        self.groups_file = self.auth_dir / "groups.json"
        self.user_prefs_dir = self.auth_dir / "user_prefs"
        
        # In-memory cache
        self._users: Dict[str, User] = {}
        self._permissions: Dict[str, ModulePermission] = {}
        self._groups: Set[str] = set()  # Set of group names
        
        # Create directories if needed
        self.auth_dir.mkdir(parents=True, exist_ok=True)
        self.user_prefs_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize with defaults if files don't exist
        self._initialize_defaults()
        
        # Load data
        self.reload()
    
    def _initialize_defaults(self):
        """Create default users and permissions if files don't exist."""
        if not self.users_file.exists():
            default_users = {
                "admin": {
                    "password_hash": hash_password("admin"),
                    "groups": ["admin"],
                    "display_name": "Administrator",
                    "email": None,
                    "avatar": "default.jpg",
                    "created_at": datetime.now().isoformat(),
                    "last_login": None
                },
                "GUEST": {
                    "password_hash": "",  # Passwordless
                    "groups": ["guest"],
                    "display_name": "Guest",
                    "email": None,
                    "avatar": "default.jpg",
                    "created_at": datetime.now().isoformat(),
                    "last_login": None
                }
            }
            self._save_json(self.users_file, default_users)
        
        if not self.permissions_file.exists():
            default_permissions = {
                "modules": {},
                "pages": {
                    "admin_auth.manage_users": ["admin"],
                    "admin_auth.manage_permissions": ["admin"],
                    "admin_auth.manage_groups": ["admin"]
                }
            }
            self._save_json(self.permissions_file, default_permissions)
        
        if not self.groups_file.exists():
            default_groups = ["admin", "guest"]
            self._save_json(self.groups_file, {"groups": default_groups})
        
        # Create default user preferences
        for username in ["admin", "GUEST"]:
            prefs_file = self.user_prefs_dir / f"{username}.json"
            if not prefs_file.exists():
                self._save_json(prefs_file, get_default_user_prefs())
    
    def reload(self):
        """Reload all auth data from disk."""
        self._load_users()
        self._load_permissions()
        self._load_groups()
    
    def _load_users(self):
        """Load users from JSON file."""
        self._users.clear()
        if self.users_file.exists():
            data = self._load_json(self.users_file)
            for username, user_data in data.items():
                self._users[username] = User.from_dict(username, user_data)
    
    def _load_permissions(self):
        """Load permissions from JSON file."""
        self._permissions.clear()
        if self.permissions_file.exists():
            data = self._load_json(self.permissions_file)
            modules = data.get("modules", {})
            for module_name, module_data in modules.items():
                self._permissions[module_name] = ModulePermission.from_dict(module_name, module_data)
    
    def _save_users(self):
        """Save users to JSON file."""
        data = {username: user.to_dict() for username, user in self._users.items()}
        self._save_json(self.users_file, data)
    
    def _save_permissions(self):
        """Save permissions to JSON file."""
        data = {
            "modules": {name: perm.to_dict() for name, perm in self._permissions.items()},
            "pages": self._get_page_permissions()
        }
        self._save_json(self.permissions_file, data)
    
    def _load_groups(self):
        """Load groups from JSON file."""
        self._groups.clear()
        if self.groups_file.exists():
            data = self._load_json(self.groups_file)
            self._groups.update(data.get("groups", []))
        # Always include groups from users to catch any not in file
        for user in self._users.values():
            self._groups.update(user.groups)
    
    def _save_groups(self):
        """Save groups to JSON file."""
        self._save_json(self.groups_file, {"groups": sorted(self._groups)})
    
    def _get_page_permissions(self) -> dict:
        """Get page-level permissions from permissions file."""
        if self.permissions_file.exists():
            data = self._load_json(self.permissions_file)
            return data.get("pages", {})
        return {}
    
    def _load_json(self, filepath: Path) -> dict:
        """Load JSON file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
            return {}
    
    def _save_json(self, filepath: Path, data: dict):
        """Save JSON file."""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving {filepath}: {e}")
    
    # ==================== User Management ====================
    
    def get_user(self, username: str) -> Optional[User]:
        """Get user by username."""
        return self._users.get(username)
    
    def get_all_users(self) -> List[User]:
        """Get all users."""
        return list(self._users.values())
    
    def create_user(self, username: str, password: str, groups: List[str], 
                   display_name: Optional[str] = None, email: Optional[str] = None) -> bool:
        """
        Create a new user.
        
        Args:
            username: Username
            password: Plain text password (empty for passwordless)
            groups: List of group names
            display_name: Display name (defaults to username)
            email: Email address
            
        Returns:
            True if created, False if user already exists
        """
        if username in self._users:
            return False
        
        user = User(
            username=username,
            password_hash=hash_password(password) if password else "",
            groups=groups,
            display_name=display_name or username,
            email=email,
            avatar="default.jpg",
            created_at=datetime.now().isoformat(),
            last_login=None
        )
        
        self._users[username] = user
        self._save_users()
        
        # Create default preferences
        prefs_file = self.user_prefs_dir / f"{username}.json"
        self._save_json(prefs_file, get_default_user_prefs())
        
        return True
    
    def delete_user(self, username: str) -> bool:
        """
        Delete a user.
        
        Args:
            username: Username to delete
            
        Returns:
            True if deleted, False if user not found
        """
        if username not in self._users:
            return False
        
        del self._users[username]
        self._save_users()
        
        # Delete user preferences
        prefs_file = self.user_prefs_dir / f"{username}.json"
        if prefs_file.exists():
            prefs_file.unlink()
        
        return True
    
    def update_user_password(self, username: str, new_password: str) -> bool:
        """
        Update user password.
        
        Args:
            username: Username
            new_password: New plain text password
            
        Returns:
            True if updated, False if user not found
        """
        user = self._users.get(username)
        if not user:
            return False
        
        user.password_hash = hash_password(new_password) if new_password else ""
        self._save_users()
        return True
    
    def update_user_avatar(self, username: str, avatar_filename: str) -> bool:
        """
        Update user avatar.
        
        Args:
            username: Username
            avatar_filename: Avatar filename (e.g., "alice.jpg")
            
        Returns:
            True if updated, False if user not found
        """
        user = self._users.get(username)
        if not user:
            return False
        
        user.avatar = avatar_filename
        self._save_users()
        return True
    
    def update_user_info(self, username: str, display_name: Optional[str] = None, 
                        email: Optional[str] = None) -> bool:
        """
        Update user display name and email.
        
        Args:
            username: Username
            display_name: New display name
            email: New email
            
        Returns:
            True if updated, False if user not found
        """
        user = self._users.get(username)
        if not user:
            return False
        
        if display_name is not None:
            user.display_name = display_name
        if email is not None:
            user.email = email
        
        self._save_users()
        return True
    
    def update_user_groups(self, username: str, groups: List[str]) -> bool:
        """
        Update user groups.
        
        Args:
            username: Username
            groups: New list of groups
            
        Returns:
            True if updated, False if user not found
        """
        user = self._users.get(username)
        if not user:
            return False
        
        user.groups = groups
        self._save_users()
        return True
    
    def update_last_login(self, username: str):
        """Update user's last login timestamp."""
        user = self._users.get(username)
        if user:
            user.last_login = datetime.now().isoformat()
            self._save_users()
    
    # ==================== Authentication ====================
    
    def verify_login(self, username: str, password: str) -> bool:
        """
        Verify login credentials.
        
        Args:
            username: Username
            password: Plain text password
            
        Returns:
            True if credentials valid
        """
        user = self._users.get(username)
        if not user:
            return False
        
        if verify_password(password, user.password_hash):
            self.update_last_login(username)
            return True
        
        return False
    
    def get_current_user(self) -> Optional[str]:
        """Get current logged-in user from session."""
        return session.get('user')
    
    def set_current_user(self, username: str):
        """Set current user in session."""
        session['user'] = username
    
    def logout_current_user(self):
        """Logout current user."""
        session.pop('user', None)
    
    # ==================== Permissions ====================
    
    def has_permission(self, username: str, module_name: str, action: str) -> bool:
        """
        Check if user has permission to perform action on module.
        
        Args:
            username: Username
            module_name: Module name (e.g., "DEV_example")
            action: Action name (e.g., "read", "write", "execute")
            
        Returns:
            True if user has permission
        """
        user = self._users.get(username)
        if not user:
            return False
        
        # Get module permissions
        module_perm = self._permissions.get(module_name)
        if not module_perm:
            return False
        
        # Check each user group
        for group in user.groups:
            allowed_actions = module_perm.groups.get(group, [])
            if action in allowed_actions:
                return True
        
        return False
    
    def get_user_permissions(self, username: str, module_name: str) -> List[str]:
        """
        Get all permissions user has for a module.
        
        Args:
            username: Username
            module_name: Module name
            
        Returns:
            List of action names user can perform
        """
        user = self._users.get(username)
        if not user:
            return []
        
        module_perm = self._permissions.get(module_name)
        if not module_perm:
            return []
        
        # Collect all actions from all user groups
        actions = set()
        for group in user.groups:
            actions.update(module_perm.groups.get(group, []))
        
        return sorted(actions)
    
    def set_module_permissions(self, module_name: str, group: str, actions: List[str]):
        """
        Set permissions for a group on a module.
        
        Args:
            module_name: Module name
            group: Group name
            actions: List of action names to grant
        """
        if module_name not in self._permissions:
            self._permissions[module_name] = ModulePermission(module_name)
        
        self._permissions[module_name].groups[group] = actions
        self._save_permissions()
    
    def get_module_permissions(self, module_name: str) -> Dict[str, List[str]]:
        """
        Get all group permissions for a module.
        
        Args:
            module_name: Module name
            
        Returns:
            Dictionary of {group: [actions]}
        """
        module_perm = self._permissions.get(module_name)
        if not module_perm:
            return {}
        return module_perm.groups.copy()
    
    def get_all_module_names(self) -> List[str]:
        """Get all modules that have permissions defined."""
        return sorted(self._permissions.keys())
    
    # ==================== User Preferences ====================
    
    def get_user_prefs(self, username: str) -> dict:
        """
        Load user preferences.
        
        Args:
            username: Username
            
        Returns:
            User preferences dictionary
        """
        prefs_file = self.user_prefs_dir / f"{username}.json"
        if prefs_file.exists():
            return self._load_json(prefs_file)
        return get_default_user_prefs()
    
    def save_user_prefs(self, username: str, prefs: dict) -> bool:
        """
        Save user preferences.
        
        Args:
            username: Username
            prefs: Preferences dictionary
            
        Returns:
            True if saved successfully
        """
        prefs_file = self.user_prefs_dir / f"{username}.json"
        self._save_json(prefs_file, prefs)
        return True
    
    def get_user_module_prefs(self, username: str, module_name: str) -> dict:
        """
        Get user preferences for a specific module.
        
        Args:
            username: Username
            module_name: Module name
            
        Returns:
            Module-specific preferences dictionary
        """
        prefs = self.get_user_prefs(username)
        return prefs.get("module_settings", {}).get(module_name, {})
    
    def save_user_module_prefs(self, username: str, module_name: str, module_prefs: dict) -> bool:
        """
        Save user preferences for a specific module.
        
        Args:
            username: Username
            module_name: Module name
            module_prefs: Module preferences dictionary
            
        Returns:
            True if saved successfully
        """
        prefs = self.get_user_prefs(username)
        if "module_settings" not in prefs:
            prefs["module_settings"] = {}
        prefs["module_settings"][module_name] = module_prefs
        return self.save_user_prefs(username, prefs)
    
    # ==================== Group Management ====================
    
    def get_all_groups(self) -> List[str]:
        """
        Get all unique group names from both the groups registry and users.
        
        Returns:
            Sorted list of group names
        """
        # Start with registered groups
        all_groups = set(self._groups)
        # Add any groups from users (in case groups.json is out of sync)
        for user in self._users.values():
            all_groups.update(user.groups)
        return sorted(all_groups)
    
    def create_group(self, group_name: str) -> bool:
        """
        Create a new group by adding it to the groups registry.
        
        Args:
            group_name: Group name to create
            
        Returns:
            True if created successfully
        """
        if group_name in self._groups:
            return False  # Already exists
        
        self._groups.add(group_name)
        self._save_groups()
        return True
    
    def delete_group(self, group_name: str) -> bool:
        """
        Delete a group by removing it from all users and permissions.
        
        Args:
            group_name: Group name to delete
            
        Returns:
            True if deleted
        """
        # Remove from groups registry
        self._groups.discard(group_name)
        self._save_groups()
        
        # Remove from all users
        for user in self._users.values():
            if group_name in user.groups:
                user.groups.remove(group_name)
        self._save_users()
        
        # Remove from all module permissions
        for module_perm in self._permissions.values():
            if group_name in module_perm.groups:
                del module_perm.groups[group_name]
        self._save_permissions()
        
        return True
    
    def rename_group(self, old_name: str, new_name: str) -> bool:
        """
        Rename a group everywhere it's referenced.
        
        Args:
            old_name: Current group name
            new_name: New group name
            
        Returns:
            True if renamed
        """
        # Rename in groups registry
        if old_name in self._groups:
            self._groups.discard(old_name)
            self._groups.add(new_name)
            self._save_groups()
        
        # Rename in all users
        for user in self._users.values():
            if old_name in user.groups:
                user.groups.remove(old_name)
                user.groups.append(new_name)
        self._save_users()
        
        # Rename in all module permissions
        for module_perm in self._permissions.values():
            if old_name in module_perm.groups:
                module_perm.groups[new_name] = module_perm.groups[old_name]
                del module_perm.groups[old_name]
        self._save_permissions()
        
        return True


# Global singleton instance (created by setup_app)
auth_manager: Optional[AuthManager] = None

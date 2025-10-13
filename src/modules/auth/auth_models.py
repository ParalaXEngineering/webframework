"""
Data models for authentication and authorization.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class User:
    """User account model."""
    username: str
    password_hash: str
    groups: List[str] = field(default_factory=list)
    display_name: Optional[str] = None
    email: Optional[str] = None
    avatar: str = "default.jpg"
    created_at: Optional[str] = None
    last_login: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "password_hash": self.password_hash,
            "groups": self.groups,
            "display_name": self.display_name or self.username,
            "email": self.email,
            "avatar": self.avatar,
            "created_at": self.created_at or datetime.now().isoformat(),
            "last_login": self.last_login
        }
    
    @classmethod
    def from_dict(cls, username: str, data: dict) -> 'User':
        """Create User from dictionary."""
        return cls(
            username=username,
            password_hash=data.get("password_hash", ""),
            groups=data.get("groups", []),
            display_name=data.get("display_name"),
            email=data.get("email"),
            avatar=data.get("avatar", "default.jpg"),
            created_at=data.get("created_at"),
            last_login=data.get("last_login")
        )


@dataclass
class ModulePermission:
    """Permission definition for a module."""
    module_name: str
    groups: Dict[str, List[str]] = field(default_factory=dict)  # {group: [actions]}
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "groups": self.groups
        }
    
    @classmethod
    def from_dict(cls, module_name: str, data: dict) -> 'ModulePermission':
        """Create ModulePermission from dictionary."""
        return cls(
            module_name=module_name,
            groups=data.get("groups", {})
        )


@dataclass
class Group:
    """User group model."""
    name: str
    description: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "description": self.description
        }
    
    @classmethod
    def from_dict(cls, name: str, data: dict) -> 'Group':
        """Create Group from dictionary."""
        return cls(
            name=name,
            description=data.get("description")
        )

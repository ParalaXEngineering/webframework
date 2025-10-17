"""
SocketIO Manager for Multi-User Isolation

Manages user-specific SocketIO rooms to ensure messages only go to intended recipients.
Critical for production multi-user deployments.

Usage:
    from modules.socketio_manager import socketio_manager
    
    # In your emitter:
    socketio_manager.emit_to_user('event_name', data, username='user1')
"""

from flask import session
from flask_socketio import join_room, leave_room, emit
from typing import Dict, Set, Optional, Any
import logging

try:
    from .log.logger_factory import get_logger
except ImportError:
    from log.logger_factory import get_logger


class SocketIOManager:
    """
    Manages user-specific SocketIO rooms for multi-user isolation.
    
    Each user connection joins a unique room based on their username and session ID.
    This ensures messages are only delivered to the intended recipient.
    """
    
    def __init__(self, socketio=None):
        """
        Initialize SocketIO manager.
        
        Args:
            socketio: Flask-SocketIO instance (can be set later with set_socketio)
        """
        self.socketio = socketio
        self._user_rooms: Dict[str, Set[str]] = {}  # {username: set(room_ids)}
        self._room_to_user: Dict[str, str] = {}  # {room_id: username}
        self.logger = get_logger("socketio_manager")
        
    def set_socketio(self, socketio):
        """
        Set or update the SocketIO instance.
        
        Args:
            socketio: Flask-SocketIO instance
        """
        self.socketio = socketio
        self.logger.info("SocketIO instance configured")
    
    def get_user_room(self, username: Optional[str] = None, sid: Optional[str] = None) -> str:
        """
        Get room name for a user session.
        
        Args:
            username: Username (defaults to current session user)
            sid: Session ID (defaults to current session sid)
            
        Returns:
            Room identifier string
        """
        if username is None:
            username = session.get('user', 'anonymous')
        if sid is None:
            sid = session.get('_id', 'unknown')
        
        return f"user_{username}_{sid}"
    
    def join_user_room(self, username: Optional[str] = None, sid: Optional[str] = None) -> str:
        """
        Join user-specific room on connection.
        
        Args:
            username: Username (defaults to current session user)
            sid: Session ID (defaults to current session sid)
            
        Returns:
            Room identifier that was joined
        """
        # Ensure we have valid username and sid - never None
        if username is None:
            username = session.get('user') or 'anonymous'
        if sid is None:
            sid = session.get('_id') or 'unknown'
        
        # At this point, both are guaranteed to be str, not None
        assert isinstance(username, str), "username must be a string"
        assert isinstance(sid, str), "sid must be a string"
            
        room = self.get_user_room(username, sid)
        join_room(room)
        
        # Track the room
        if username not in self._user_rooms:
            self._user_rooms[username] = set()
        self._user_rooms[username].add(room)
        self._room_to_user[room] = username
        
        self.logger.info(f"User '{username}' joined room '{room}'")
        return room
    
    def leave_user_room(self, username: Optional[str] = None, sid: Optional[str] = None):
        """
        Leave user room on disconnect.
        
        Args:
            username: Username (defaults to current session user)
            sid: Session ID (defaults to current session sid)
        """
        # Ensure we have valid username and sid - never None
        if username is None:
            username = session.get('user') or 'anonymous'
        if sid is None:
            sid = session.get('_id') or 'unknown'
        
        # At this point, both are guaranteed to be str, not None
        assert isinstance(username, str), "username must be a string"
        assert isinstance(sid, str), "sid must be a string"
            
        room = self.get_user_room(username, sid)
        leave_room(room)
        
        # Clean up tracking
        if username in self._user_rooms:
            self._user_rooms[username].discard(room)
            if not self._user_rooms[username]:
                del self._user_rooms[username]
        
        if room in self._room_to_user:
            del self._room_to_user[room]
        
        self.logger.info(f"User '{username}' left room '{room}'")
    
    def emit_to_user(self, event: str, data: Any, username: Optional[str] = None, 
                     namespace: str = '/'):
        """
        Emit event to specific user's room(s).
        
        If username is not provided, emits to current session user.
        If username has multiple active sessions, emits to all of them.
        
        Args:
            event: Event name
            data: Data to send
            username: Target username (defaults to current session user)
            namespace: SocketIO namespace (default: '/')
        """
        if self.socketio is None:
            self.logger.warning("SocketIO not configured, cannot emit")
            return
        
        if username is None:
            username = session.get('user') or 'anonymous'
        
        # At this point, username is guaranteed to be str, not None
        assert isinstance(username, str), "username must be a string"
        
        # Emit to all active sessions of this user
        if username in self._user_rooms:
            for room in self._user_rooms[username]:
                try:
                    self.socketio.emit(event, data, room=room, namespace=namespace)
                    # Removed DEBUG logging to reduce spam
                except Exception as e:
                    self.logger.error(f"Error emitting to room '{room}': {e}")
        else:
            self.logger.warning(f"No active rooms found for user '{username}'")
    
    def emit_to_current_user(self, event: str, data: Any, namespace: str = '/'):
        """
        Emit event to current session user only.
        
        Convenience method that uses current session context.
        
        Args:
            event: Event name
            data: Data to send
            namespace: SocketIO namespace (default: '/')
        """
        self.emit_to_user(event, data, username=None, namespace=namespace)
    
    def emit_to_all(self, event: str, data: Any, namespace: str = '/'):
        """
        Broadcast to all connected users.
        
        Use sparingly - only for system-wide announcements.
        For user-specific data, use emit_to_user instead.
        
        Args:
            event: Event name
            data: Data to send
            namespace: SocketIO namespace (default: '/')
        """
        if self.socketio is None:
            self.logger.warning("SocketIO not configured, cannot emit")
            return
        
        try:
            self.socketio.emit(event, data, namespace=namespace)
            # Removed DEBUG logging to reduce spam
        except Exception as e:
            self.logger.error(f"Error broadcasting: {e}")
    
    def get_active_users(self) -> Set[str]:
        """
        Get set of currently connected usernames.
        
        Returns:
            Set of active usernames
        """
        return set(self._user_rooms.keys())
    
    def get_user_session_count(self, username: str) -> int:
        """
        Get number of active sessions for a user.
        
        Args:
            username: Username to check
            
        Returns:
            Number of active sessions
        """
        return len(self._user_rooms.get(username, set()))
    
    def is_user_connected(self, username: str) -> bool:
        """
        Check if user has any active connections.
        
        Args:
            username: Username to check
            
        Returns:
            True if user has at least one active session
        """
        return username in self._user_rooms and len(self._user_rooms[username]) > 0
    
    def cleanup_stale_rooms(self):
        """
        Clean up tracking for disconnected rooms.
        
        This is called periodically to prevent memory leaks from disconnected clients.
        """
        # Note: In production with Redis, this becomes less important as
        # Redis handles room cleanup automatically
        initial_count = len(self._room_to_user)
        
        # Clean up empty user sets
        users_to_remove = [u for u, rooms in self._user_rooms.items() if not rooms]
        for username in users_to_remove:
            del self._user_rooms[username]
        
        if users_to_remove:
            self.logger.info(f"Cleaned up {len(users_to_remove)} stale user entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get connection statistics.
        
        Returns:
            Dictionary with connection stats
        """
        return {
            'total_users': len(self._user_rooms),
            'total_rooms': len(self._room_to_user),
            'users': {
                username: len(rooms) 
                for username, rooms in self._user_rooms.items()
            }
        }


# Global singleton instance
socketio_manager = SocketIOManager()


def initialize_socketio_manager(socketio):
    """
    Initialize the global SocketIO manager.
    
    Call this during app setup after creating the SocketIO instance.
    
    Args:
        socketio: Flask-SocketIO instance
        
    Returns:
        The initialized SocketIOManager singleton
    """
    socketio_manager.set_socketio(socketio)
    return socketio_manager

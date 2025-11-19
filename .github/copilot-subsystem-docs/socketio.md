# SocketIO Manager

## Purpose
User-isolated real-time communication via SocketIO rooms. Ensures messages only reach intended users in multi-user environments.

## Core Components
- `src/modules/socketio_manager.py` - SocketIOManager class, user room management
- Global singleton: `socketio_manager`

## Critical Patterns

### Initialization (in setup_app)
```python
from modules.socketio_manager import initialize_socketio_manager

socketio = SocketIO(app)
initialize_socketio_manager(socketio)
```

### Connection Handling
```python
from modules.socketio_manager import socketio_manager
from flask_socketio import SocketIO

@socketio.on('connect')
def handle_connect():
    room = socketio_manager.join_user_room()  # Auto-joins user's room
    logger.info(f"User connected to room: {room}")

@socketio.on('disconnect')
def handle_disconnect():
    socketio_manager.leave_user_room()
```

### Emit to Specific User
```python
from modules.socketio_manager import socketio_manager

# Emit to specific user (all sessions)
socketio_manager.emit_to_user('event_name', {"data": "value"}, username='user1')

# Emit to current session user
socketio_manager.emit_to_current_user('event_name', {"data": "value"})
```

### Broadcast (Use Sparingly)
```python
# Broadcast to ALL users (system announcements only)
socketio_manager.emit_to_all('maintenance_notice', {"message": "System restarting"})
```

### User Status Checks
```python
# Check if user connected
is_online = socketio_manager.is_user_connected('user1')

# Get active users
active_users = socketio_manager.get_active_users()  # Returns: {"user1", "user2", ...}

# Count user sessions
session_count = socketio_manager.get_user_session_count('user1')
```

### Room Management
```python
# Get room name for user
room = socketio_manager.get_user_room(username='user1', sid='session_abc')

# Manual join/leave (rarely needed)
socketio_manager.join_user_room(username='user1', sid='session_abc')
socketio_manager.leave_user_room(username='user1', sid='session_abc')
```

### Stats and Monitoring
```python
# Get connection statistics
stats = socketio_manager.get_stats()
# Returns: {"total_users": 3, "total_rooms": 5, 
#           "users": {"user1": 2, "user2": 1, "user3": 2}}

# Cleanup stale rooms (periodic maintenance)
socketio_manager.cleanup_stale_rooms()
```

## API Quick Reference
```python
class SocketIOManager:
    def __init__(socketio=None)
    def set_socketio(socketio)
    
    # Room management
    def get_user_room(username: str = None, sid: str = None) -> str
    def join_user_room(username: str = None, sid: str = None) -> str
    def leave_user_room(username: str = None, sid: str = None)
    
    # Emission
    def emit_to_user(event: str, data: Any, username: str = None, namespace: str = '/')
    def emit_to_current_user(event: str, data: Any, namespace: str = '/')
    def emit_to_all(event: str, data: Any, namespace: str = '/')
    
    # Status
    def is_user_connected(username: str) -> bool
    def get_active_users() -> Set[str]
    def get_user_session_count(username: str) -> int
    def get_stats() -> Dict[str, Any]
    
    # Maintenance
    def cleanup_stale_rooms()

# Room naming format
# "user_{username}_{session_id}"

# Global singleton
from modules.socketio_manager import socketio_manager
```

## Common Pitfalls
1. **User isolation critical** - Always emit to user-specific room, not broadcast
2. **Session context** - Room auto-determined from Flask session; rarely pass manually
3. **Multiple sessions** - Same user can have multiple rooms (desktop + mobile)
4. **GUEST user** - Has special room "user_GUEST_unknown" (shared across guests)
5. **Scheduler integration** - Scheduler auto-routes messages via _get_current_username()
6. **Anonymous users** - Fallback to 'anonymous' if no session user
7. **Redis scaling** - In production with Redis, room tracking less critical (Redis handles it)
8. **Cleanup frequency** - Call cleanup_stale_rooms() periodically (e.g., every hour)

## Integration Points
- **Scheduler**: Uses emit_to_user() for thread progress/status updates
- **Threaded**: Thread username captured for isolated emission
- **Auth**: Room names based on session['user']
- **Flask-SocketIO**: Wraps emit() with user-specific rooms
- **MessageEmitter**: Scheduler's emitter uses socketio_manager internally

## Files
- `socketio_manager.py` - SocketIOManager class, room tracking, emission logic
- Global singleton: `socketio_manager` (initialized in setup_app)

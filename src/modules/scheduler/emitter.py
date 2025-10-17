"""
SocketIO Message Emitter

Handles emission of messages via SocketIO with error handling.
Decoupled from message queueing for better testability.
"""
from typing import Protocol, List, Dict, Any

try:
    from ..log.logger_factory import get_logger
    from ..socketio_manager import socketio_manager
except ImportError:
    from log.logger_factory import get_logger
    from socketio_manager import socketio_manager


class SocketIOProtocol(Protocol):
    """Protocol defining the SocketIO interface we need."""
    
    def emit(self, event: str, data: Any) -> None:
        """Emit an event with data."""
        ...


class MessageEmitter:
    """
    Emits messages via SocketIO with proper error handling.
    
    Handles filtering, formatting, and emission of all message types.
    Each emission is wrapped in error handling to prevent cascade failures.
    
    Messages are now emitted per-user using SocketIO room isolation.
    """
    
    def __init__(self, socket_io: SocketIOProtocol, logger=None):
        """
        Initialize emitter.
        
        Args:
            socket_io: SocketIO instance (or mock for testing)
            logger: Optional logger for error reporting (if None, creates default)
        """
        self.socket = socket_io
        self.logger = logger or get_logger("scheduler_emitter")
    
    def emit_status(self, statuses: List[List], username: str) -> None:
        """
        Emit status messages with duplicate filtering.
        
        Filters duplicates by keeping only the last occurrence of each
        unique status string (identified by second element).
        
        Args:
            statuses: List of [category, string, status, supplement]
            username: Username to emit to
        """
        if not statuses:
            return
        
        self.logger.info(f"[EMITTER] emit_status: {len(statuses)} status messages to process for user {username}")
        
        # Filter duplicates - keep last occurrence of each unique string
        seen = {}
        for category, string, status, supplement in reversed(statuses):
            if string not in seen:
                seen[string] = (category, string, status, supplement)
        
        # Emit in reverse order (newest first)
        for category, string, status, supplement in reversed(seen.values()):
            try:
                data = {category: [string, status, supplement]}
                self.logger.info(f"[EMITTER] Emitting status to user {username}: {data}")
                socketio_manager.emit_to_user("action_status", data, username)
            except Exception as e:
                self.logger.error(f"Error emitting status to user {username}: {e}")
    
    def emit_popups(self, popups: List[List], username: str) -> None:
        """
        Emit popup messages.
        
        Args:
            popups: List of [logLevel, message]
            username: Username to emit to
        """
        if popups:
            self.logger.info(f"[EMITTER] emit_popups: {len(popups)} popup messages for user {username}")
        
        for item in popups:
            try:
                level = item[0].name if hasattr(item[0], 'name') else str(item[0])
                data = {level: item[1]}
                # Use repr() to avoid encoding issues with emojis in logs
                self.logger.info(f"[EMITTER] Emitting popup to user {username}: level={level}, length={len(item[1])} chars")
                socketio_manager.emit_to_user("popup", data, username)
            except Exception as e:
                self.logger.error(f"Error emitting popup to user {username}: {e}")
    
    def emit_results(self, results: List[List], username: str) -> None:
        """
        Emit result messages.
        
        Args:
            results: List of [category, content]
            username: Username to emit to
        """
        for category, content in results:
            try:
                socketio_manager.emit_to_user("result", {
                    "category": category,
                    "text": content
                }, username)
            except Exception as e:
                self.logger.error(f"Error emitting result to user {username}: {e}")
    
    def emit_modals(self, modals: List[List], username: str) -> None:
        """
        Emit modal dialog updates.
        
        Args:
            modals: List of [id, content]
            username: Username to emit to
        """
        for modal_id, content in modals:
            try:
                socketio_manager.emit_to_user("modal", {
                    "id": modal_id,
                    "text": content
                }, username)
            except Exception as e:
                self.logger.error(f"Error emitting modal to user {username}: {e}")
    
    def emit_buttons(self, buttons: List[List], username: str) -> None:
        """
        Emit button updates.
        
        Args:
            buttons: List of [id, icon, text, style]
            username: Username to emit to
        """
        for button_id, icon, text, style in buttons:
            try:
                socketio_manager.emit_to_user("button", {
                    button_id: [icon, text, style]
                }, username)
            except Exception as e:
                self.logger.error(f"Error emitting button to user {username}: {e}")
    
    def emit_reloads(self, reloads: List[List], username: str) -> None:
        """
        Emit content reload requests.
        
        Args:
            reloads: List of [id, content]
            username: Username to emit to
        """
        if reloads:
            self.logger.info(f"[EMITTER] emit_reloads: {len(reloads)} reload messages for user {username}")
        
        for item_id, content in reloads:
            try:
                self.logger.info(f"[EMITTER] Emitting reload to user {username} for ID: {item_id}, content length: {len(content)} chars")
                socketio_manager.emit_to_user("reload", {
                    "id": item_id,
                    "content": content
                }, username)
            except Exception as e:
                self.logger.error(f"Error emitting reload to user {username}: {e}")
    
    def emit_button_states(self, disable_list: List[str], enable_list: List[str], username: str) -> None:
        """
        Emit button state changes (enable/disable).
        
        Args:
            disable_list: List of button IDs to disable
            enable_list: List of button IDs to enable
            username: Username to emit to
        """
        try:
            if disable_list:
                socketio_manager.emit_to_user("disable_button", disable_list, username)
        except Exception as e:
            self.logger.error(f"Error emitting button disable to user {username}: {e}")
        
        try:
            if enable_list:
                socketio_manager.emit_to_user("enable_button", enable_list, username)
        except Exception as e:
            self.logger.error(f"Error emitting button enable to user {username}: {e}")
    
    def emit_threads(self, thread_info: List[Dict[str, Any]]) -> None:
        """
        Emit thread status information.
        
        Args:
            thread_info: List of dicts with 'name' and 'state' keys
        """
        try:
            socketio_manager.emit_to_all("threads", thread_info)
        except Exception as e:
            self.logger.error(f"Error emitting thread info: {e}")

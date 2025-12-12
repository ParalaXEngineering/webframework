"""
SocketIO Message Emitter

Handles emission of messages via SocketIO with error handling.
Decoupled from message queueing for better testability.
"""
from typing import List, Dict, Any

from src.modules.log.logger_factory import get_logger
from src.modules.socketio_manager import socketio_manager

try:
    from typing import Protocol
except ImportError:
    # Python < 3.8: Protocol not available, use ABC
    from abc import ABC as Protocol  # type: ignore


# =============================================================================
# SocketIO Event Names (domain-specific technical constants)
# =============================================================================
EVENT_ACTION_STATUS = "action_status"
EVENT_POPUP = "popup"
EVENT_RESULT = "result"
EVENT_MODAL = "modal"
EVENT_BUTTON = "button"
EVENT_RELOAD = "reload"
EVENT_DISABLE_BUTTON = "disable_button"
EVENT_ENABLE_BUTTON = "enable_button"
EVENT_THREADS = "threads"

# Logger name
LOGGER_NAME = "scheduler_emitter"


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
        self.logger = logger or get_logger(LOGGER_NAME)
    
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
        
        self.logger.debug("[EMITTER] emit_status: %d status messages to process for user %s", len(statuses), username)
        
        # Filter duplicates - keep last occurrence of each unique string
        seen = {}
        for category, string, status, supplement in reversed(statuses):
            if string not in seen:
                seen[string] = (category, string, status, supplement)
        
        # Emit in reverse order (newest first)
        for category, string, status, supplement in reversed(seen.values()):
            try:
                data = {category: [string, status, supplement]}
                self.logger.debug("[EMITTER] Emitting status to user %s", username)
                socketio_manager.emit_to_user(EVENT_ACTION_STATUS, data, username)
            except Exception as e:
                self.logger.error("Error emitting status to user %s: %s", username, e)
    
    def emit_popups(self, popups: List[List], username: str) -> None:
        """
        Emit popup messages.
        
        Args:
            popups: List of [logLevel, message]
            username: Username to emit to
        """
        if popups:
            self.logger.debug("[EMITTER] emit_popups: %d popup messages for user %s", len(popups), username)
        
        for item in popups:
            try:
                level = item[0].name if hasattr(item[0], 'name') else str(item[0])
                data = {level: item[1]}
                self.logger.debug("[EMITTER] Emitting popup to user %s: level=%s, length=%d chars", username, level, len(item[1]))
                socketio_manager.emit_to_user(EVENT_POPUP, data, username)
            except Exception as e:
                self.logger.error("Error emitting popup to user %s: %s", username, e)
    
    def emit_results(self, results: List[List], username: str) -> None:
        """
        Emit result messages.
        
        Args:
            results: List of [category, content]
            username: Username to emit to
        """
        for category, content in results:
            try:
                socketio_manager.emit_to_user(EVENT_RESULT, {
                    "category": category,
                    "text": content
                }, username)
            except Exception as e:
                self.logger.error("Error emitting result to user {username}: {error}".format(username=username, error=e))
    
    def emit_modals(self, modals: List[List], username: str) -> None:
        """
        Emit modal dialog updates.
        
        Args:
            modals: List of [id, content]
            username: Username to emit to
        """
        for modal_id, content in modals:
            try:
                socketio_manager.emit_to_user(EVENT_MODAL, {
                    "id": modal_id,
                    "text": content
                }, username)
            except Exception as e:
                self.logger.error("Error emitting modal to user {username}: {error}".format(username=username, error=e))
    
    def emit_buttons(self, buttons: List[List], username: str) -> None:
        """
        Emit button updates.
        
        Args:
            buttons: List of [id, icon, text, style]
            username: Username to emit to
        """
        for button_id, icon, text, style in buttons:
            try:
                socketio_manager.emit_to_user(EVENT_BUTTON, {
                    button_id: [icon, text, style]
                }, username)
            except Exception as e:
                self.logger.error("Error emitting button to user {username}: {error}".format(username=username, error=e))
    
    def emit_reloads(self, reloads: List[List], username: str) -> None:
        """
        Emit content reload requests.
        
        Args:
            reloads: List of [id, content]
            username: Username to emit to
        """
        if reloads:
            self.logger.debug("[EMITTER] emit_reloads: %d reload messages for user %s", len(reloads), username)
        
        for item_id, content in reloads:
            try:
                self.logger.debug("[EMITTER] Emitting reload to user %s for ID: %s, content length: %d chars", username, item_id, len(content))
                socketio_manager.emit_to_user(EVENT_RELOAD, {
                    "id": item_id,
                    "content": content
                }, username)
            except Exception as e:
                self.logger.error("Error emitting reload to user %s: %s", username, e)
    
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
                socketio_manager.emit_to_user(EVENT_DISABLE_BUTTON, disable_list, username)
        except Exception as e:
            self.logger.error("Error emitting button disable to user {username}: {error}".format(username=username, error=e))
        
        try:
            if enable_list:
                socketio_manager.emit_to_user(EVENT_ENABLE_BUTTON, enable_list, username)
        except Exception as e:
            self.logger.error("Error emitting button enable to user {username}: {error}".format(username=username, error=e))
    
    def emit_threads(self, thread_info: List[Dict[str, Any]]) -> None:
        """
        Emit thread status information.
        
        Args:
            thread_info: List of dicts with 'name' and 'state' keys
        """
        try:
            socketio_manager.emit_to_all(EVENT_THREADS, thread_info)
        except Exception as e:
            self.logger.error("Error emitting thread info: {error}".format(error=e))

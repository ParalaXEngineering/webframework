"""
SocketIO Message Emitter

Handles emission of messages via SocketIO with error handling.
Decoupled from message queueing for better testability.
"""
from typing import Protocol, List, Dict, Any

try:
    from ..log.logger_factory import get_logger
except ImportError:
    from log.logger_factory import get_logger


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
    
    def emit_status(self, statuses: List[List]) -> None:
        """
        Emit status messages with duplicate filtering.
        
        Filters duplicates by keeping only the last occurrence of each
        unique status string (identified by second element).
        
        Args:
            statuses: List of [category, string, status, supplement]
        """
        if not statuses:
            return
        
        self.logger.info(f"[EMITTER] emit_status: {len(statuses)} status messages to process")
        
        # Filter duplicates - keep last occurrence of each unique string
        seen = {}
        for category, string, status, supplement in reversed(statuses):
            if string not in seen:
                seen[string] = (category, string, status, supplement)
        
        # Emit in reverse order (newest first)
        for category, string, status, supplement in reversed(seen.values()):
            try:
                data = {category: [string, status, supplement]}
                self.logger.info(f"[EMITTER] Emitting status: {data}")
                self.socket.emit("action_status", data)
            except Exception as e:
                self.logger.error(f"Error emitting status: {e}")
    
    def emit_popups(self, popups: List[List]) -> None:
        """
        Emit popup messages.
        
        Args:
            popups: List of [logLevel, message]
        """
        if popups:
            self.logger.info(f"[EMITTER] emit_popups: {len(popups)} popup messages")
        
        for item in popups:
            try:
                level = item[0].name if hasattr(item[0], 'name') else str(item[0])
                data = {level: item[1]}
                # Use repr() to avoid encoding issues with emojis in logs
                self.logger.info(f"[EMITTER] Emitting popup: level={level}, length={len(item[1])} chars")
                self.socket.emit("popup", data)
            except Exception as e:
                self.logger.error(f"Error emitting popup: {e}")
    
    def emit_results(self, results: List[List]) -> None:
        """
        Emit result messages.
        
        Args:
            results: List of [category, content]
        """
        for category, content in results:
            try:
                self.socket.emit("result", {
                    "category": category,
                    "text": content
                })
            except Exception as e:
                self.logger.error(f"Error emitting result: {e}")
    
    def emit_modals(self, modals: List[List]) -> None:
        """
        Emit modal dialog updates.
        
        Args:
            modals: List of [id, content]
        """
        for modal_id, content in modals:
            try:
                self.socket.emit("modal", {
                    "id": modal_id,
                    "text": content
                })
            except Exception as e:
                self.logger.error(f"Error emitting modal: {e}")
    
    def emit_buttons(self, buttons: List[List]) -> None:
        """
        Emit button updates.
        
        Args:
            buttons: List of [id, icon, text, style]
        """
        for button_id, icon, text, style in buttons:
            try:
                self.socket.emit("button", {
                    button_id: [icon, text, style]
                })
            except Exception as e:
                self.logger.error(f"Error emitting button: {e}")
    
    def emit_reloads(self, reloads: List[List]) -> None:
        """
        Emit content reload requests.
        
        Args:
            reloads: List of [id, content]
        """
        for item_id, content in reloads:
            try:
                self.socket.emit("reload", {
                    "id": item_id,
                    "content": content
                })
            except Exception as e:
                self.logger.error(f"Error emitting reload: {e}")
    
    def emit_button_states(self, disable_list: List[str], enable_list: List[str]) -> None:
        """
        Emit button state changes (enable/disable).
        
        Args:
            disable_list: List of button IDs to disable
            enable_list: List of button IDs to enable
        """
        try:
            if disable_list:
                self.socket.emit("disable_button", disable_list)
        except Exception as e:
            self.logger.error(f"Error emitting button disable: {e}")
        
        try:
            if enable_list:
                self.socket.emit("enable_button", enable_list)
        except Exception as e:
            self.logger.error(f"Error emitting button enable: {e}")
    
    def emit_threads(self, thread_info: List[Dict[str, Any]]) -> None:
        """
        Emit thread status information.
        
        Args:
            thread_info: List of dicts with 'name' and 'state' keys
        """
        try:
            self.socket.emit("threads", thread_info)
        except Exception as e:
            self.logger.error(f"Error emitting thread info: {e}")

"""
Message Queue Manager

Handles thread-safe message queueing for scheduler.
Provides typed message queues with size limits to prevent memory leaks.
"""
from collections import deque
from threading import Lock
from typing import List, Any, Dict
from enum import Enum
import logging


class MessageType(Enum):
    """Types of messages that can be queued."""
    STATUS = "status"
    POPUP = "popup"
    RESULT = "result"
    MODAL = "modal"
    BUTTON = "button"
    RELOAD = "reload"
    BUTTON_DISABLE = "button_disable"
    BUTTON_ENABLE = "button_enable"


class MessageQueue:
    """
    Thread-safe message queue with size limits.
    
    Prevents memory leaks by limiting queue sizes and provides
    thread-safe operations for producer-consumer pattern.
    """
    
    def __init__(self, max_size: int = 1000, modal_limit: int = 5):
        """
        Initialize message queues.
        
        Args:
            max_size: Maximum size for most queues
            modal_limit: Special limit for modal queue (smaller to prevent memory issues)
        """
        self._queues: Dict[MessageType, deque] = {}
        self._locks: Dict[MessageType, Lock] = {}
        self._logger = logging.getLogger(__name__)
        
        # Initialize queues with appropriate size limits
        for msg_type in MessageType:
            if msg_type == MessageType.MODAL:
                self._queues[msg_type] = deque(maxlen=modal_limit)
            else:
                self._queues[msg_type] = deque(maxlen=max_size)
            self._locks[msg_type] = Lock()
    
    def add(self, msg_type: MessageType, data: Any) -> None:
        """
        Add message to queue (thread-safe).
        
        Args:
            msg_type: Type of message to add
            data: Message data (structure depends on message type)
        """
        with self._locks[msg_type]:
            self._queues[msg_type].append(data)
            self._logger.info(f"[QUEUE] Added {msg_type.name} message: {data}")
    
    def get_all(self, msg_type: MessageType) -> List[Any]:
        """
        Get all messages of given type and clear queue (thread-safe).
        
        Args:
            msg_type: Type of messages to retrieve
            
        Returns:
            List of all queued messages of that type
        """
        with self._locks[msg_type]:
            messages = list(self._queues[msg_type])
            self._queues[msg_type].clear()
            return messages
    
    def peek(self, msg_type: MessageType) -> List[Any]:
        """
        Get all messages without clearing (thread-safe).
        
        Args:
            msg_type: Type of messages to peek at
            
        Returns:
            List of all queued messages (queue not modified)
        """
        with self._locks[msg_type]:
            return list(self._queues[msg_type])
    
    def clear(self, msg_type: MessageType) -> None:
        """
        Clear specific message queue.
        
        Args:
            msg_type: Type of queue to clear
        """
        with self._locks[msg_type]:
            self._queues[msg_type].clear()
    
    def clear_all(self) -> None:
        """Clear all message queues."""
        for msg_type in MessageType:
            self.clear(msg_type)
    
    def size(self, msg_type: MessageType) -> int:
        """
        Get current size of queue.
        
        Args:
            msg_type: Type of queue to check
            
        Returns:
            Number of messages in queue
        """
        with self._locks[msg_type]:
            return len(self._queues[msg_type])

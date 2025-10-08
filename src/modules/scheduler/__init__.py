"""
Scheduler Module

Provides message queueing and emission for real-time updates via SocketIO.
"""
from .message_queue import MessageQueue, MessageType
from .emitter import MessageEmitter

# Global scheduler object (initialized by main application)
scheduler_obj = None

__all__ = [
    'MessageQueue',
    'MessageType',
    'MessageEmitter',
    'scheduler_obj',
]

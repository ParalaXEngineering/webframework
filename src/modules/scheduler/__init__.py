"""
Scheduler Module

Provides scheduler classes, message queueing and emission for real-time updates via SocketIO.
"""
from .message_queue import MessageQueue, MessageType
from .emitter import MessageEmitter
from .scheduler import Scheduler, Scheduler_LongTerm, logLevel

# Global scheduler objects (initialized by main application)
scheduler_obj = None
scheduler_ltobj = None

__all__ = [
    'MessageQueue',
    'MessageType',
    'MessageEmitter',
    'Scheduler',
    'Scheduler_LongTerm',
    'logLevel',
    'scheduler_obj',
    'scheduler_ltobj',
]

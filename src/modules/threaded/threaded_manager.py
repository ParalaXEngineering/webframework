"""
Thread Manager - Manages all running threads in the framework.

This module provides centralized management of all threads created through
the Threaded_action base class.
"""

import threading
from typing import List, Tuple

try:
    from ..log.logger_factory import get_logger
except ImportError:
    from log.logger_factory import get_logger

# Constants
DEFAULT_LOCK_TIMEOUT = 2.0
MAX_HISTORY_SIZE = 50
DEFAULT_STATS = {
    "total": 0,
    "running": 0,
    "with_process": 0,
    "with_error": 0,
    "unique_names": 0
}

# Log level constants (for consistency)
LOG_LEVEL_INFO = "INFO"
LOG_LEVEL_DEBUG = "DEBUG"
LOG_LEVEL_WARNING = "WARNING"
LOG_LEVEL_ERROR = "ERROR"

# Error messages
ERR_LOCK_TIMEOUT_ADD = "Failed to acquire lock for add_thread (timeout=%ss)"
ERR_LOCK_TIMEOUT_DEL = "Failed to acquire lock for del_thread (timeout=%ss)"
ERR_LOCK_TIMEOUT_GET_ALL = "Failed to acquire lock for get_all_threads (timeout=%ss)"
ERR_LOCK_TIMEOUT_GET_COMPLETED = "Failed to acquire lock for get_completed_threads (timeout=%ss)"
ERR_LOCK_TIMEOUT_GET_ALL_HISTORY = "Failed to acquire lock for get_all_threads_with_history (timeout=%ss)"
ERR_LOCK_TIMEOUT_GET_BY_NAME = "Failed to acquire lock for get_threads_by_name (timeout=%ss)"
ERR_LOCK_TIMEOUT_GET_UNIQUE = "Failed to acquire lock for get_unique_names (timeout=%ss)"
ERR_LOCK_TIMEOUT_GET_NAMES = "Failed to acquire lock for get_names (timeout=%ss)"
ERR_LOCK_TIMEOUT_GET_THREAD = "Failed to acquire lock for get_thread (timeout=%ss)"
ERR_LOCK_TIMEOUT_REMOVE_HISTORY = "Failed to acquire lock for remove_from_history (timeout=%ss)"
ERR_LOCK_TIMEOUT_KILL_ALL = "Failed to acquire lock for kill_all_threads (timeout=%ss)"
ERR_LOCK_TIMEOUT_COUNT = "Failed to acquire lock for get_thread_count (timeout=%ss)"
ERR_LOCK_TIMEOUT_STATS = "Failed to acquire lock for get_thread_stats (timeout=%ss)"
ERR_COULD_NOT_ACQUIRE = "Could not acquire lock within %ss"

thread_manager_obj = None


class Threaded_manager:
    """Manage the different threads of the framework"""

    def __init__(self, lock_timeout=DEFAULT_LOCK_TIMEOUT):
        """Initialize the thread manager
        
        Args:
            lock_timeout: Default timeout in seconds for lock acquisition (default: 2.0)
        """
        self.m_running_threads = []
        self.m_completed_threads = []  # History of completed threads
        self.max_history = MAX_HISTORY_SIZE  # Keep last 50 completed threads
        self._lock = threading.Lock()  # Thread-safe operations
        self.lock_timeout = lock_timeout  # Configurable lock timeout
        
        # Initialize logger using centralized factory
        self.m_logger = get_logger("threaded_manager")
        self.m_logger.debug("Thread Manager started")

    def add_thread(self, thread: threading.Thread):
        """Add a new thread to the pool.
        
        Args:
            thread: The thread to add
        """
        if not self._lock.acquire(timeout=self.lock_timeout):
            self.m_logger.error(ERR_LOCK_TIMEOUT_ADD, self.lock_timeout)
            raise TimeoutError(ERR_COULD_NOT_ACQUIRE % self.lock_timeout)
        
        try:
            if thread in self.m_running_threads:
                thread_name = getattr(thread, 'name', str(thread))
                self.m_logger.debug("Thread '%s' already in pool", thread_name)
                return
            self.m_running_threads.append(thread)
            thread_name = getattr(thread, 'name', str(thread))
            self.m_logger.info("Added thread '%s' to pool", thread_name)
        finally:
            self._lock.release()

    def del_thread(self, thread: threading.Thread):
        """Delete a thread from the pool and archive it to history.
        
        Args:
            thread: The thread to delete
        """
        thread_name = getattr(thread, 'name', str(thread))
        
        # Try to close connections and processes
        try:
            if hasattr(thread, 'command_close'):
                thread.command_close()  # type: ignore
        except Exception as e:
            self.m_logger.debug("Thread '%s' command_close failed: %s", thread_name, e)
            
        try:
            if hasattr(thread, 'process_close'):
                thread.process_close()  # type: ignore
        except Exception as e:
            self.m_logger.debug("Thread '%s' process_close failed: %s", thread_name, e)

        # Remove from pool and add to history
        if not self._lock.acquire(timeout=self.lock_timeout):
            self.m_logger.error(ERR_LOCK_TIMEOUT_DEL, self.lock_timeout)
            raise TimeoutError(ERR_COULD_NOT_ACQUIRE % self.lock_timeout)
        
        try:
            try:
                self.m_running_threads.remove(thread)
                self.m_logger.info("Removed thread '%s' from pool", thread_name)
                
                # Add to history (keep only last max_history threads)
                self.m_completed_threads.append(thread)
                if len(self.m_completed_threads) > self.max_history:
                    self.m_completed_threads.pop(0)
                self.m_logger.debug("Archived thread '%s' to history", thread_name)
            except ValueError:
                self.m_logger.debug("Thread '%s' not found in pool", thread_name)
        finally:
            self._lock.release()

    def get_all_threads(self) -> List:
        """Return all threads currently managed.
        
        Returns:
            List of all managed threads
        """
        if not self._lock.acquire(timeout=self.lock_timeout):
            self.m_logger.error(ERR_LOCK_TIMEOUT_GET_ALL, self.lock_timeout)
            return []
        
        try:
            return self.m_running_threads.copy()
        finally:
            self._lock.release()

    def get_completed_threads(self) -> List:
        """Return all completed threads from history.
        
        Returns:
            List of completed threads
        """
        if not self._lock.acquire(timeout=self.lock_timeout):
            self.m_logger.error(ERR_LOCK_TIMEOUT_GET_COMPLETED, self.lock_timeout)
            return []
        
        try:
            return self.m_completed_threads.copy()
        finally:
            self._lock.release()

    def get_all_threads_with_history(self) -> Tuple[List, List]:
        """Return both running and completed threads.
        
        Returns:
            Tuple of (running_threads, completed_threads)
        """
        if not self._lock.acquire(timeout=self.lock_timeout):
            self.m_logger.error(ERR_LOCK_TIMEOUT_GET_ALL_HISTORY, self.lock_timeout)
            return ([], [])
        
        try:
            return (self.m_running_threads.copy(), self.m_completed_threads.copy())
        finally:
            self._lock.release()

    def get_threads_by_name(self, name: str) -> List:
        """Return all threads matching a given name.
        
        Args:
            name: The thread name to search for
            
        Returns:
            List of threads with matching names
        """
        if not self._lock.acquire(timeout=self.lock_timeout):
            self.m_logger.error(ERR_LOCK_TIMEOUT_GET_BY_NAME, self.lock_timeout)
            return []
        
        try:
            return [t for t in self.m_running_threads 
                    if (hasattr(t, 'get_name') and t.get_name() == name) or 
                       t.m_default_name == name]
        finally:
            self._lock.release()

    def get_unique_names(self) -> List:
        """Return the list of unique thread names.
        
        Returns:
            List of unique thread names
        """
        if not self._lock.acquire(timeout=self.lock_timeout):
            self.m_logger.error(ERR_LOCK_TIMEOUT_GET_UNIQUE, self.lock_timeout)
            return []
        
        try:
            names = set()
            for t in self.m_running_threads:
                if hasattr(t, 'get_name'):
                    names.add(t.get_name())
                else:
                    names.add(t.m_default_name)
            return list(names)
        finally:
            self._lock.release()
    
    def get_names(self) -> List:
        """Return the list of all thread names.
        
        Returns:
            List of thread names (may contain duplicates)
        """
        if not self._lock.acquire(timeout=self.lock_timeout):
            self.m_logger.error(ERR_LOCK_TIMEOUT_GET_NAMES, self.lock_timeout)
            return []
        
        try:
            names = []
            for thread in self.m_running_threads:
                if hasattr(thread, 'get_name'):
                    names.append(thread.get_name())
                else:
                    names.append(thread.m_default_name)
            return names
        finally:
            self._lock.release()

    def get_thread(self, name: str):
        """Return a thread by its name.
        
        Args:
            name: The name of the desired thread
            
        Returns:
            The thread object, or None if not found
        """
        if not self._lock.acquire(timeout=self.lock_timeout):
            self.m_logger.error(ERR_LOCK_TIMEOUT_GET_THREAD, self.lock_timeout)
            return None
        
        try:
            for thread in self.m_running_threads:
                thread_name = thread.get_name() if hasattr(thread, 'get_name') else thread.m_default_name
                if name == thread_name:
                    return thread
            return None
        finally:
            self._lock.release()

    def remove_from_history(self, name: str) -> bool:
        """Remove a completed thread from history by name.
        
        Args:
            name: The name of the thread to remove from history
            
        Returns:
            True if removed, False if not found
        """
        if not self._lock.acquire(timeout=self.lock_timeout):
            self.m_logger.error(ERR_LOCK_TIMEOUT_REMOVE_HISTORY, self.lock_timeout)
            return False
        
        try:
            for thread in self.m_completed_threads:
                thread_name = thread.get_name() if hasattr(thread, 'get_name') else str(thread)
                if name == thread_name:
                    self.m_completed_threads.remove(thread)
                    self.m_logger.info("Removed thread '%s' from history", thread_name)
                    return True
            self.m_logger.debug("Thread '%s' not found in history", name)
            return False
        finally:
            self._lock.release()

    def kill_all_threads(self):
        """Kill all managed threads (useful for shutdown)"""
        if not self._lock.acquire(timeout=self.lock_timeout):
            self.m_logger.error(ERR_LOCK_TIMEOUT_KILL_ALL, self.lock_timeout)
            return
        
        try:
            threads_copy = self.m_running_threads.copy()
        finally:
            self._lock.release()
        
        self.m_logger.warning("Killing all %d threads", len(threads_copy))
        
        for thread in threads_copy:
            try:
                self.del_thread(thread)
            except Exception as e:
                self.m_logger.error("Failed to kill thread: %s", e)

    def get_thread_count(self) -> int:
        """Get the number of currently managed threads.
        
        Returns:
            Number of threads
        """
        if not self._lock.acquire(timeout=self.lock_timeout):
            self.m_logger.error(ERR_LOCK_TIMEOUT_COUNT, self.lock_timeout)
            return 0
        
        try:
            return len(self.m_running_threads)
        finally:
            self._lock.release()

    def get_thread_stats(self) -> dict:
        """Get statistics about managed threads.
        
        Returns:
            Dictionary with thread statistics
        """
        if not self._lock.acquire(timeout=self.lock_timeout):
            self.m_logger.error(ERR_LOCK_TIMEOUT_STATS, self.lock_timeout)
            return DEFAULT_STATS
        
        try:
            # Calculate unique names without calling get_unique_names() to avoid nested lock
            unique_names = set()
            for t in self.m_running_threads:
                if hasattr(t, 'get_name'):
                    unique_names.add(t.get_name())
                else:
                    unique_names.add(t.m_default_name)
            
            stats = {
                "total": len(self.m_running_threads),
                "running": sum(1 for t in self.m_running_threads if getattr(t, 'm_running', False)),
                "with_process": sum(1 for t in self.m_running_threads if getattr(t, 'm_process_running', False)),
                "with_error": sum(1 for t in self.m_running_threads if getattr(t, 'm_error', None)),
                "unique_names": len(unique_names)
            }
            return stats
        finally:
            self._lock.release()

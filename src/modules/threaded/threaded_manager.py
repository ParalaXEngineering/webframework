"""
Thread Manager - Manages all running threads in the framework.

This module provides centralized management of all threads created through
the Threaded_action base class.
"""

import threading

try:
    from ..logger_factory import get_logger
except ImportError:
    from logger_factory import get_logger

thread_manager_obj = None


class Threaded_manager:
    """Manage the different threads of the framework"""

    def __init__(self, lock_timeout=2.0):
        """Initialize the thread manager
        
        Args:
            lock_timeout: Default timeout in seconds for lock acquisition (default: 2.0)
        """
        self.m_running_threads = []
        self._lock = threading.Lock()  # Thread-safe operations
        self.lock_timeout = lock_timeout  # Configurable lock timeout
        
        # Initialize logger using centralized factory
        self.m_logger = get_logger("threaded_manager")
        self.m_logger.info("Thread Manager started")

    def add_thread(self, thread: threading.Thread):
        """Add a new thread to the pool.
        
        Args:
            thread: The thread to add
        """
        if not self._lock.acquire(timeout=self.lock_timeout):
            self.m_logger.error(f"Failed to acquire lock for add_thread (timeout={self.lock_timeout}s)")
            raise TimeoutError(f"Could not acquire lock within {self.lock_timeout}s")
        
        try:
            if thread in self.m_running_threads:
                self.m_logger.debug(f"Thread '{thread.get_name()}' already in pool")
                return
            self.m_running_threads.append(thread)
            self.m_logger.info(f"Added thread '{thread.get_name()}' to pool")
        finally:
            self._lock.release()

    def del_thread(self, thread: threading.Thread):
        """Delete a thread from the pool.
        
        Args:
            thread: The thread to delete
        """
        thread_name = thread.get_name() if hasattr(thread, 'get_name') else str(thread)
        
        # Try to close connections and processes
        try:
            if hasattr(thread, 'command_close'):
                thread.command_close()
        except Exception as e:
            self.m_logger.debug(f"Thread '{thread_name}' command_close failed: {e}")
            
        try:
            if hasattr(thread, 'process_close'):
                thread.process_close()
        except Exception as e:
            self.m_logger.debug(f"Thread '{thread_name}' process_close failed: {e}")

        # Remove from pool
        if not self._lock.acquire(timeout=self.lock_timeout):
            self.m_logger.error(f"Failed to acquire lock for del_thread (timeout={self.lock_timeout}s)")
            raise TimeoutError(f"Could not acquire lock within {self.lock_timeout}s")
        
        try:
            try:
                self.m_running_threads.remove(thread)
                self.m_logger.info(f"Removed thread '{thread_name}' from pool")
            except ValueError:
                self.m_logger.debug(f"Thread '{thread_name}' not found in pool")
        finally:
            self._lock.release()

    def get_all_threads(self) -> list:
        """Return all threads currently managed.
        
        Returns:
            List of all managed threads
        """
        if not self._lock.acquire(timeout=self.lock_timeout):
            self.m_logger.error(f"Failed to acquire lock for get_all_threads (timeout={self.lock_timeout}s)")
            return []
        
        try:
            return self.m_running_threads.copy()
        finally:
            self._lock.release()

    def get_threads_by_name(self, name: str) -> list:
        """Return all threads matching a given name.
        
        Args:
            name: The thread name to search for
            
        Returns:
            List of threads with matching names
        """
        if not self._lock.acquire(timeout=self.lock_timeout):
            self.m_logger.error(f"Failed to acquire lock for get_threads_by_name (timeout={self.lock_timeout}s)")
            return []
        
        try:
            return [t for t in self.m_running_threads 
                    if (hasattr(t, 'get_name') and t.get_name() == name) or 
                       t.m_default_name == name]
        finally:
            self._lock.release()

    def get_unique_names(self) -> list:
        """Return the list of unique thread names.
        
        Returns:
            List of unique thread names
        """
        if not self._lock.acquire(timeout=self.lock_timeout):
            self.m_logger.error(f"Failed to acquire lock for get_unique_names (timeout={self.lock_timeout}s)")
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
    
    def get_names(self) -> list:
        """Return the list of all thread names.
        
        Returns:
            List of thread names (may contain duplicates)
        """
        if not self._lock.acquire(timeout=self.lock_timeout):
            self.m_logger.error(f"Failed to acquire lock for get_names (timeout={self.lock_timeout}s)")
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
            self.m_logger.error(f"Failed to acquire lock for get_thread (timeout={self.lock_timeout}s)")
            return None
        
        try:
            for thread in self.m_running_threads:
                thread_name = thread.get_name() if hasattr(thread, 'get_name') else thread.m_default_name
                if name == thread_name:
                    return thread
            return None
        finally:
            self._lock.release()

    def kill_all_threads(self):
        """Kill all managed threads (useful for shutdown)"""
        if not self._lock.acquire(timeout=self.lock_timeout):
            self.m_logger.error(f"Failed to acquire lock for kill_all_threads (timeout={self.lock_timeout}s)")
            return
        
        try:
            threads_copy = self.m_running_threads.copy()
        finally:
            self._lock.release()
        
        self.m_logger.warning(f"Killing all {len(threads_copy)} threads")
        
        for thread in threads_copy:
            try:
                self.del_thread(thread)
            except Exception as e:
                self.m_logger.error(f"Failed to kill thread: {e}")

    def get_thread_count(self) -> int:
        """Get the number of currently managed threads.
        
        Returns:
            Number of threads
        """
        if not self._lock.acquire(timeout=self.lock_timeout):
            self.m_logger.error(f"Failed to acquire lock for get_thread_count (timeout={self.lock_timeout}s)")
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
            self.m_logger.error(f"Failed to acquire lock for get_thread_stats (timeout={self.lock_timeout}s)")
            return {"total": 0, "running": 0, "with_process": 0, "with_error": 0, "unique_names": 0}
        
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

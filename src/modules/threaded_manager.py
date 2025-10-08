import threading
import logging
import logging.config
import os

thread_manager_obj = None


class Threaded_manager:
    """Manage the different threads of the framework"""

    def __init__(self):
        self.m_running_threads = []  # ✅ déplacement ici : variable d'instance
        
        # Try to find log_config.ini in multiple locations
        log_config_paths = [
            "submodules/framework/log_config.ini",
            "log_config.ini",
            os.path.join(os.path.dirname(__file__), "..", "..", "log_config.ini")
        ]
        
        log_config_found = False
        for path in log_config_paths:
            if os.path.exists(path):
                try:
                    logging.config.fileConfig(path)
                    log_config_found = True
                    break
                except Exception:
                    continue
        
        if not log_config_found:
            # Fallback to basic config if no file found
            logging.basicConfig(level=logging.INFO)
        
        self.m_logger = logging.getLogger("website")
        self.m_logger.info("Thread Manager started")

    def add_thread(self, thread: threading.Thread):
        """Add a new thread to the pool

        :param thread: The thread to add
        :type thread: threading.Thread
        """
        if thread in self.m_running_threads:
            return
        self.m_running_threads.append(thread)

    def del_thread(self, thread: threading.Thread):
        """Delete a thread from the pool

        :param thread: The thread to delete
        :type thread: _type_
        """
        try:
            thread.command_close()
            thread.process_close()
        except Exception as e:
            self.m_logger.info("Thread deletion failed: " + str(e))
            pass

        try:
            self.m_running_threads.remove(thread)
        except Exception as e:
            self.m_logger.info("Thread removal failed: " + str(e))
            pass

    def get_all_threads(self) -> list:
        """Return all threads currently managed"""
        return self.m_running_threads.copy()

    def get_threads_by_name(self, name: str) -> list:
        """Return all threads matching a given name"""
        return [t for t in self.m_running_threads if t.m_default_name == name]

    def get_unique_names(self) -> list:
        """Return the list of unique thread names"""
        return list(set(t.m_default_name for t in self.m_running_threads))
    
    def get_names(self) -> list:
        """Return the list of all the threads, by name

        :return: A list of thread's names
        :rtype: list
        """
        names = []
        for thread in self.m_running_threads:
            names.append(thread.m_default_name)

        return names

    def get_thread(self, name: str) -> threading.Thread:
        """Return a thread by it's name

        :param name: The name of the desired thread
        :type name: str
        :return: The thread object, or None if the name is not found
        :rtype: threading.Thread
        """

        for thread in self.m_running_threads:
            if name == thread.m_default_name:
                return thread

        return None

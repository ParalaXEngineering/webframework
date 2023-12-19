import threading

thread_manager_obj = None


class Threaded_manager:
    """Manage the different threads of the framework"""

    m_running_threads = []
    """List of the currently running threads"""

    def add_thread(self, thread: threading.Thread):
        """Add a new thread to the pool

        :param thread: The thread to add
        :type thread: threading.Thread
        """
        if thread in self.m_running_threads:
            return
        else:
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

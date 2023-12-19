import threading
import socket
import time
import copy
import os
import tarfile
import platform
import subprocess
import logging


from submodules.framework.src import threaded_manager
from submodules.framework.src import utilities
from submodules.framework.src import scheduler

class Threaded_action:
    """Base class to execute long term action. It registeres itself on the thread manager and handle the creation and destruction of the python thread.

    Moreover, it provides a set of helper function to communication with the host (Windows, Linux or Macos) in order to call, for instance, scripts or programs.
    """


    m_scheduler = None
    """Link to the sceduler object"""

    m_default_name = "Default name"
    """The name of the module"""

    m_type = "threaded_action"
    """The type of the module"""

    def __init__(self):
        self.m_name = None

        """Constructor"""
        # Prepare the important variable
        self.m_thread_action = None
        self.m_thread_command = None
        self.m_thread_process_stdout = None
        self.m_thread_process_sterr = None

        self.m_running = False
        self.m_running_state = -1 #-1 indicate a task that just run, without any information about percentage or so

        self.m_process = None
        self.m_process_running = False
        self.m_process_results = []

        self.m_stderr = None
        self.m_stdout = None

        self.m_logger = None

        self.m_process_input = []

        self.m_background = False

        # Register the thread
        threaded_manager.thread_manager_obj.add_thread(self)

        logging.config.fileConfig("framework/log_config.ini")
        self.m_logger = logging.getLogger("ouFNis")
        self.m_logger.info("Scheduler started")

        self.m_scheduler = scheduler.scheduler_obj

    def get_name(self) -> str:
        """ Return the name of the instance

        :return: The name of the instance
        :rtype: str
        """
        if self.m_name:
            return self.m_name

        return self.m_default_name

    def change_name(self, name:str):
        """Change the name of the instance of the module

        :param name: The new name
        :type name: str
        """
        self.m_name = name


    def delete(self):
        """Delete the thread and unregister it from the thread manager"""
        
        threaded_manager.thread_manager_obj.del_thread(self)

    def process_exec(self, command: list, source_folder: str, shell=True, inputs=None):
        """Execute a local process command.  This function is not blocking, and will return immediately, even if the command is not over. Use command_wait() to detect the end of the command. 


        :param command: The command to execute
        :type command: list
        :param source_folder: The relative path of execution
        :type source_folder: str
        :param shell: The shell argument of subprocess, defaults to True
        :type shell: bool, optional
        :param inputs: a list with detection of a specific string and how to react, defaults to None
        :type inputs: _type_, optional
        """

        self.m_process = subprocess.Popen(command, cwd=source_folder, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, universal_newlines=True, shell=shell)
        self.m_process_running = True

        # Start a reading thread
        self.m_thread_process_stdout = threading.Thread(target=self.process_read_stdout, daemon=True)
        self.m_thread_process_stdout.start()
        self.m_thread_process_stderr = threading.Thread(target=self.process_read_stderr, daemon=True)
        self.m_thread_process_stderr.start()

    def process_close(self):
        """Kill and close the local process
        """
        if self.m_process:
            self.m_process.kill()
            self.m_process = None

    def process_format_results(self) -> list:
        """Format the results of the process, and reset them.
        By default, the formating does nothing and just send the raw data.

        Returns:
            list: The result of the last executed (or executing) process
        """
        result = copy.copy(self.m_process_results)
        self.m_process_results = []
        return result


    def process_delete_results(self):
        """Delete the results of the process
        """
        self.m_process_results = []

    def process_read_stderr(self):
        """Read thread for the error output of the currently executing local process
        """
        while self.m_process and self.m_process.poll() is None:
            try: 
                line = self.m_process.stderr.readline()
                self.m_process_results.append(line)
            except Exception as e:
                self.m_process_running = False
            time.sleep(0.1)

        # Process is done, read any line that might still be there
        try:
            lines = self.m_process.stderr.readlines()
            for line in lines:
                self.m_process_results.append(line)
            
            self.m_process_running = False
        except Exception as e:
                # If we kill the process there won't be anything left to read: it's ok.
                self.m_command_running = False
                return
        return

    def process_read_stdout(self):
        """Read thread for the standard output of the currently executing local process
        """
        while self.m_process_running and self.m_process.poll() is None:
            try: 
                line = self.m_process.stdout.readline()
                if self.m_process_input:
                    if self.m_process_input[0] in line:
                        self.m_process.communicate(input=self.m_process_input[1])
                self.m_process_results.append(line)
            except Exception as e:
                self.m_process_running = False
            time.sleep(0.1)
        
        # Process is done, read any line that might still be there
        try:
            lines = self.m_process.stdout.readlines()
            for line in lines:
                self.m_process_results.append(line)

            self.m_process_running = False
        except Exception as e:
                # If we kill the process there won't be anything left to read: it's ok.
                self.m_command_running = False
                return
        return

    def process_wait(self):
        """Wait for the currently executing local process to finish
        """
        #TODO: must be semaphored
        while(1):
            time.sleep(0.3)
            if self.m_process_running == False:
                return

    def process_read_results(self):
        """Read the raw results of the last executed (executing) process, and delete them
        """
        #TODO: must be semaphored
        result = copy.copy(self.m_process_results)
        self.m_process_results = []
        return result

    def action(self):
        """Main function of this thread
        """
        return

    def thread_process(self):
        """Thread function
        """
        self.m_running = True
        # Wait for the browser
        try:
            print("Trying to start action")
            self.action()
        except Exception as e:
            print("Thread has failed: " + str(e))
        self.m_running = False

        if not self.m_background:
            # Wait a bit to finish all the reading, we are not in a hurry anyway...
            self.delete()
        return

    def start(self):
        """Thread start
        """
        self.m_thread_action = threading.Thread(target=self.thread_process, daemon=True)
        self.m_thread_action.start()
        return

    def wait_finished(self):
        """Thread finish
        """
        self.m_thread_action.join()
        return
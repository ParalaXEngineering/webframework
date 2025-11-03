import time
import threading
import logging
import logging.config

from enum import Enum

from submodules.framework.src import threaded_manager
from submodules.framework.src import log_utils

scheduler_obj = None
scheduler_ltobj = None


class logLevel(Enum):
    success = 0
    info = 1
    warning = 2
    error = 3
    empty = 4


class Scheduler_LongTerm:
    def __init__(self):
        self.functions = []
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.running = False

        log_utils.setup_logging()
        self.m_logger = logging.getLogger("website")

    def register_function(self, function, period: int) -> None:
        """Register a nex function

        :param function: The function to register
        :type function: Function
        :param period: The period, in minutes, to execute this function
        :type period: int
        """
        self.functions.append((function, period, time.time()))

    def run(self):
        """
        Main execution loop
        """
        self.running = True
        while self.running:
            current_time = time.time()
            for func, period, last_run in self.functions:
                if current_time - last_run >= period * 60:
                    try:
                        func()
                    except Exception as e:
                        self.m_logger.error(f"Error executing function {func.__name__}: {e}")
                    
                    # Update last execution time
                    self.functions = [(f, p, (current_time if f is func else last_run)) for f, p, last_run in self.functions]

            time.sleep(10)

        self.m_logger.info("LT Scheduler stopped")

    def start(self):
        """"
        Start the scheduler in its thread
        """
        if not self.running:
            self.m_logger.info("LT Scheduler started")
            self.thread.start()

    def stop(self):
        """
        Stop the scheduler
        """
        self.running = False


class Scheduler:
    """Basic scheduler class, which has the responsability to handle periodic tasks.
    This is the base class, which generate the messages to the website and handle the special buttons, if any.

    """

    socket_obj = None
    """Main object to the client socketio instance"""

    m_status = []
    """List of the status information that has not been sent to the website yet"""

    m_reload = []
    """List of the reload information. A reload information concerns any item on the website that can be dinamicaly reloaded."""

    m_popups = []
    """List of the popups that has not been sent to the website yet"""

    m_contents = []
    """To remove"""

    m_buttons = []
    """List of the buttons information (for instance, in topbar) that has not been sent to the website yet"""

    m_results = []
    """List of the results (from the task actions field in the webengine) that has not been sent to the website yet"""

    m_modals = []
    """List of the modals dialogs that has not been sent to the website yet"""

    m_button_disable = []
    """List of the buttons that will be disabled"""

    m_button_enable = []
    """List of the buttons that will be enabled"""

    m_user_connected = False
    """Indicate if a user is connected. If not, the scheduler is halted"""

    def user_before(self):
        """Function to be overwritten by specific website, ut is executed at the begning of a scheduler cycle"""
        return

    def user_after(self):
        """Function to be overwritten by specific website, ut is executed at the end of a scheduler cycle"""
        return

    def emit_reload(self, content: str):
        """Send some information about a formulaire that needs to be refreshed on the page

        :param content: The content of the formulaire, in the form of a list of {id: "...", content: "..."}
        :type content: str
        """
        i = 0
        for item in content:
            self.m_reload.append([item["id"], item["content"]])
            i += 1

    def disable_button(self, id: str):
        """Disable a button by its id

        :param id: The id of the button
        :type id: str
        """
        self.m_button_disable.append(id)

    def enable_button(self, id: str):
        """Enable a button by its id

        :param id: The id of the button
        :type id: str
        """
        self.m_button_enable.append(id)

    def emit_status(
        self, category: str, string: str, status: int = 0, supplement: str = ""
    ):
        """Queue a message status to be sent to the web client

        :param category: The category that indicate where the status will be published in the main page
        :type category: str
        :param string: The information string to display to the user
        :type string: str
        :param status: The status, a number between 0 and 100% that indicate the progress.
        At 100% the task is considered as successfull. The status 101% can be used to indicate an error, defaults to 0
        :type status: int, optional
        :param supplement: A supplement status that can be used to add information on the main case, defaults to ""
        :type supplement: str, optional
        """
        self.m_status.append([category, string, status, supplement])

    def emit_popup(self, level: logLevel, string: str):
        """ "Emit a a popup that will be displayed to the user

        :param level: The log level of the popup (succes, info, warning or error)
        :type level: logLevel
        :param string: The content of the popup. Some html can be present in it.
        :type string: str
        """
        self.m_popups.append([level, string])
        return

    def emit_result(self, category: str, content):
        """Add a result information in the bottom of the "Action progress".
        The category is any category supported by bootstrap (success, danger, etc...)

        :param category: A category from bootstrap
        :type category: str
        :param content: The content to display. HTML is supported
        :type content: _type_
        """

        self.m_results.append([category, content])

    def emit_button(self, id: str, icon: str, text: str, style: str = "primary"):
        """Change the content of a topbar button

        :param id: The id of the button to
        :type id: str
        :param icon: The icon of the button to change, from the mdi icons
        :type icon: str
        :param text: The new text
        :type text: str
        :param style: The bootstrap style of the button. Defaults to "primary"., defaults to "primary"
        :type style: str, optional
        """
        self.m_buttons.append([id, icon, text, style])

    def emit_modal(self, id: str, content: str):
        """Change the content of a topbar modal

        :param id: The id of the button to
        :type id: str
        :param content: The new text
        :type content: str

        :notes: modal might be big, and having a lot of them can use a vast amount of memory if the user don't consume them. So only the last 5 ones are kept.
        """

        self.m_modals.append([id, content])
        self.m_modals = self.m_modals[-5:] 

    def start(self):
        """Start the scheduler"""
        log_utils.setup_logging()
        self.m_logger = logging.getLogger("website")
        self.m_logger.info("Scheduler started")

        while 1:
            if not self.m_user_connected:
                time.sleep(1)
                continue

            self.user_before()

            # Send buttons, if any
            for item in self.m_buttons:
                self.socket_obj.emit("button", {item[0]: [item[1], item[2], item[3]]})

            # Send popups if any
            for item in self.m_popups:
                level = item[0].name
                self.socket_obj.emit("popup", {level: item[1]})

            # Send content if any
            for item in self.m_contents:
                self.socket_obj.emit("content", {item[0]: item[1]})

            # Send the status if any. Start by filtering the status so we only keep the last important ones
            previous_status = ""
            filtered_status = []
            for item in reversed(self.m_status):
                if item[1] != previous_status:
                    filtered_status.append(item)
                    previous_status = item[1]
                else:
                    continue

            if len(filtered_status) > 0:
                for item in reversed(filtered_status):
                    self.socket_obj.emit(
                        "action_status", {item[0]: [item[1], item[2], item[3]]}
                    )

            # Send result if any
            for item in self.m_results:
                self.socket_obj.emit("result", {"category": item[0], "text": item[1]})

            for item in self.m_modals:
                self.socket_obj.emit("modal", {"id": item[0], "text": item[1]})

            # Send new formulaire information
            for item in self.m_reload:
                self.socket_obj.emit("reload", {"id": item[0], "content": item[1]})

            threads_names = threaded_manager.thread_manager_obj.get_unique_names()
            thread_info = []
            for name in threads_names:
                current_thread = threaded_manager.thread_manager_obj.get_threads_by_name(name)
                for i, thread in enumerate(current_thread):
                    thread_info.append({
                        "name": f"{name} #{i+1}" if len(current_thread) > 1 else name,
                        "state": thread.m_running_state
                    })

            self.socket_obj.emit("threads", thread_info)

            # Send the button disable / enable
            self.socket_obj.emit("disable_button", self.m_button_disable)
            self.socket_obj.emit("enable_button", self.m_button_enable)

            self.m_status = []
            self.m_popups = []
            self.m_contents = []
            self.m_results = []
            self.m_modals = []
            self.m_buttons = []
            self.m_reload = []
            self.m_button_disable = []
            self.m_button_enable = []

            self.user_after()
            time.sleep(0.1)

import time
import threading
from enum import Enum
from typing import Optional, cast

try:
    from ..threaded import threaded_manager
    from ..log.logger_factory import get_logger
    from .message_queue import MessageQueue, MessageType
    from .emitter import MessageEmitter
except ImportError:
    from threaded import threaded_manager
    from log.logger_factory import get_logger
    from message_queue import MessageQueue, MessageType
    from emitter import MessageEmitter


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
        self.m_logger = get_logger("scheduler_longterm")

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

    m_user_connected = False
    """Indicate if a user is connected. If not, the scheduler is halted"""

    def __init__(self, socket_obj=None, message_queue=None, message_emitter=None):
        """Initialize the scheduler with optional dependency injection.
        
        :param socket_obj: The socketio object for real-time communication
        :param message_queue: Optional MessageQueue instance (created if not provided)
        :param message_emitter: Optional MessageEmitter instance (created if not provided)
        """
        self.socket_obj = socket_obj
        self._queue = message_queue if message_queue is not None else MessageQueue()
        self._emitter = message_emitter if message_emitter is not None else (
            MessageEmitter(socket_obj) if socket_obj is not None else None
        )
        self.m_logger = None

    def user_before(self):
        """Function to be overwritten by specific website, ut is executed at the begning of a scheduler cycle"""
        return

    def user_after(self):
        """Function to be overwritten by specific website, ut is executed at the end of a scheduler cycle"""
        return

    def emit_reload(self, content: list):
        """Send some information about a formulaire that needs to be refreshed on the page

        :param content: The content of the formulaire, in the form of a list of {id: "...", content: "..."}
        :type content: list
        """
        for item in content:
            data = [item["id"], item["content"]]  # type: ignore
            self._queue.add(MessageType.RELOAD, data)

    def disable_button(self, id: str):
        """Disable a button by its id

        :param id: The id of the button
        :type id: str
        """
        self._queue.add(MessageType.BUTTON_DISABLE, id)

    def enable_button(self, id: str):
        """Enable a button by its id

        :param id: The id of the button
        :type id: str
        """
        self._queue.add(MessageType.BUTTON_ENABLE, id)

    def emit_status(
        self, category: str, string: str, status: int = 0, supplement: str = "", status_id: Optional[str] = None
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
        :param status_id: Optional ID to identify and update a specific status line. If provided, updates the existing
        line with this ID instead of creating a new one. Defaults to None (creates new line each time)
        :type status_id: str, optional
        """
        # If status_id provided, use it as the identifier; otherwise use the string
        identifier = status_id if status_id else string
        data = [category, identifier, status, supplement]
        self._queue.add(MessageType.STATUS, data)

    def emit_popup(self, level: logLevel, string: str):
        """ "Emit a a popup that will be displayed to the user

        :param level: The log level of the popup (succes, info, warning or error)
        :type level: logLevel
        :param string: The content of the popup. Some html can be present in it.
        :type string: str
        """
        data = [level, string]
        self._queue.add(MessageType.POPUP, data)

    def emit_result(self, category: str, content):
        """Add a result information in the bottom of the "Action progress".
        The category is any category supported by bootstrap (success, danger, etc...)

        :param category: A category from bootstrap
        :type category: str
        :param content: The content to display. HTML is supported
        :type content: _type_
        """
        data = [category, content]
        self._queue.add(MessageType.RESULT, data)

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
        data = [id, icon, text, style]
        self._queue.add(MessageType.BUTTON, data)

    def emit_modal(self, id: str, content: str):
        """Change the content of a topbar modal

        :param id: The id of the button to
        :type id: str
        :param content: The new text
        :type content: str

        :notes: modal might be big, and having a lot of them can use a vast amount of memory if the user don't consume them. So only the last 5 ones are kept.
        """
        data = [id, content]
        self._queue.add(MessageType.MODAL, data) 

    def start(self):
        """Start the scheduler"""
        self.m_logger = get_logger("scheduler")
        self.m_logger.info("Scheduler started")
        
        # Configure emitter logger if it exists
        if self._emitter is not None and hasattr(self._emitter, 'logger'):
            self._emitter.logger = self.m_logger

        while 1:
            if not self.m_user_connected:
                time.sleep(1)
                continue

            self.user_before()

            # Get all messages from queues
            buttons = self._queue.get_all(MessageType.BUTTON)
            popups = self._queue.get_all(MessageType.POPUP)
            status = self._queue.get_all(MessageType.STATUS)
            results = self._queue.get_all(MessageType.RESULT)
            modals = self._queue.get_all(MessageType.MODAL)
            reloads = self._queue.get_all(MessageType.RELOAD)
            button_disable = self._queue.get_all(MessageType.BUTTON_DISABLE)
            button_enable = self._queue.get_all(MessageType.BUTTON_ENABLE)

            # Debug: Log what we collected
            if any([buttons, popups, status, results, modals, reloads, button_disable, button_enable]):
                self.m_logger.info(f"[SCHEDULER] Collected messages - Status: {len(status)}, Popups: {len(popups)}, Results: {len(results)}, Buttons: {len(buttons)}, Reloads: {len(reloads)}")

            # Emit using emitter (handles filtering and errors)
            if self._emitter is not None:
                self._emitter.emit_buttons(buttons)
                self._emitter.emit_popups(popups)
                self._emitter.emit_status(status)
                self._emitter.emit_results(results)
                self._emitter.emit_modals(modals)
                self._emitter.emit_reloads(reloads)
                self._emitter.emit_button_states(button_disable, button_enable)

                # Thread information
                thread_info = []
                if threaded_manager.thread_manager_obj:
                    threads_names = cast(list, threaded_manager.thread_manager_obj.get_unique_names())
                    for name in threads_names:
                        current_thread = threaded_manager.thread_manager_obj.get_threads_by_name(name)
                        for i, thread in enumerate(current_thread):
                            thread_info.append({
                                "name": f"{name} #{i+1}" if len(current_thread) > 1 else name,
                            "state": thread.m_running_state
                        })
                self._emitter.emit_threads(thread_info)

            self.user_after()
            time.sleep(0.1)

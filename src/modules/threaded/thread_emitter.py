"""Thread status emitter for real-time UI updates.

Background thread that periodically emits thread status updates via SocketIO.
Uses Displayer framework for consistent UI rendering.

NOTE: Uses socketio_manager for user-specific rooms to prevent data leakage between users.
"""
import os
import threading
import time
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader

from src.modules.displayer import (
    BSalign, BSstyle, Displayer, DisplayerItemActionButtons,
    DisplayerItemAlert, DisplayerItemBadge, DisplayerItemConsole,
    DisplayerItemIconText, DisplayerItemText, DisplayerLayout, Layouts,
)
from src.modules.i18n.messages import (
    MSG_THREAD_COMPLETED_HEADER,
    MSG_THREAD_LAST_N,
    MSG_THREAD_NO_DATA,
    MSG_THREAD_NO_THREADS,
    MSG_THREAD_RUNNING_HEADER,
    STATUS_THREAD_ABORTED,
    STATUS_THREAD_COMPLETED,
    STATUS_THREAD_ERROR,
    STATUS_THREAD_RUNNING,
    TEXT_THREAD_INFO_NAME,
    TEXT_THREAD_INFO_PROGRESS,
    TEXT_THREAD_INFO_STATUS,
    TEXT_THREAD_TAB_CONSOLE,
    TEXT_THREAD_TAB_INFO,
    TEXT_THREAD_TAB_LOGS,
)
from src.modules.log.logger_factory import get_logger
from src.modules.socketio_manager import socketio_manager
from . import threaded_manager


# Constants for thread status display
DEFAULT_EMISSION_INTERVAL = 1.0
MAX_CONSOLE_LINES = 30
MAX_LOG_LINES = 20


class ThreadEmitter:
    """Emits thread status updates via SocketIO using Displayer framework."""

    def __init__(self, socket_io, interval: float = DEFAULT_EMISSION_INTERVAL):
        """Initialize thread emitter.

        Args:
            socket_io: SocketIO instance for emission
            interval: Update interval in seconds (default: 1.0)
        """
        self.socket = socket_io
        self.interval = interval
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self.logger = get_logger("threaded_emitter")

        # Set up Jinja2 environment for template rendering (no Flask context needed)
        # templates/ is three levels up from src/modules/threaded/
        template_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "templates",
        )
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))
        self.content_reloader_template = self.jinja_env.get_template("base_content_reloader.j2")
        
    def start(self):
        """Start the emitter background thread."""
        if self.running:
            self.logger.warning("Thread emitter already running")
            return

        self.running = True
        self._thread = threading.Thread(target=self._emit_loop, daemon=True)
        self._thread.start()
        self.logger.debug("Thread emitter started (interval=%ss)", self.interval)
    
    def stop(self):
        """Stop the emitter background thread."""
        self.running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        self.logger.info("Thread emitter stopped")
    
    def _emit_loop(self):
        """Main emission loop - runs in background thread."""
        while self.running:
            try:
                self._emit_thread_update()
            except Exception as e:
                self.logger.error("Error emitting thread update: %s", e)

            time.sleep(self.interval)
    
    def _emit_thread_update(self):
        """Collect and emit current thread status as HTML to each user's room."""
        manager = threaded_manager.thread_manager_obj
        if not manager:
            self.logger.debug("Thread manager not initialized")
            return

        try:
            # Get running and completed threads
            running_threads, completed_threads = manager.get_all_threads_with_history()  # type: ignore

            # Limit completed to last 10
            completed_threads = list(completed_threads)[-10:] if completed_threads else []

            # Group threads by owner (username)
            threads_by_user: Dict[str, Dict[str, List]] = {}

            # Organize running threads by user
            if running_threads:
                for thread in running_threads:
                    username = getattr(thread, 'username', 'anonymous')
                    if username not in threads_by_user:
                        threads_by_user[username] = {'running': [], 'completed': []}
                    threads_by_user[username]['running'].append(thread)

            # Organize completed threads by user
            if completed_threads:
                for thread in completed_threads:
                    username = getattr(thread, 'username', 'anonymous')
                    if username not in threads_by_user:
                        threads_by_user[username] = {'running': [], 'completed': []}
                    threads_by_user[username]['completed'].append(thread)

            # Emit thread updates to each user's room
            for username, user_threads in threads_by_user.items():
                try:
                    # Build HTML content for this specific user
                    html_content = self._render_threads_html(
                        user_threads['running'],
                        user_threads['completed']
                    )

                    # Emit to this specific user's room(s) only
                    socketio_manager.emit_to_user('reload', {
                        'id': 'threads_content',
                        'content': html_content
                    }, username=username)

                except Exception as e:
                    self.logger.error("Error emitting to user '%s': %s", username, e)

        except Exception as e:
            from ..log.logger_factory import format_exception_html
            self.logger.error("Failed to emit thread update: %s", format_exception_html(e))
    
    def _render_threads_html(self, running_threads: List, completed_threads: List) -> str:
        """Render HTML for all threads using Displayer framework.

        Args:
            running_threads: List of running threads
            completed_threads: List of completed threads

        Returns:
            HTML string rendered from Displayer object
        """
        disp = Displayer()
        disp.add_generic("ThreadList")  # Initialize module

        if not running_threads and not completed_threads:
            disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))
            disp.add_display_item(DisplayerItemAlert(
                id="no_threads",
                text=str(MSG_THREAD_NO_THREADS),
                highlightType=BSstyle.INFO,
                icon="information"
            ), 0)
            return self._render_displayer(disp)

        # Main vertical layout - one row per thread
        num_threads = len(running_threads) + len(completed_threads)
        # +2 for section headers if both exist, +1 if only one exists
        num_rows = num_threads
        if running_threads:
            num_rows += 1  # Header row
        if completed_threads:
            num_rows += 1  # Header row

        disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))

        row_index = 0

        # Running threads section
        if running_threads:
            # Section header
            disp.add_display_item(DisplayerItemText(
                f"<h4><i class='mdi mdi-play-circle'></i> {MSG_THREAD_RUNNING_HEADER} ({len(running_threads)})</h4>"
            ), row_index)
            row_index += 1

            # Add each running thread as a slave layout
            for thread in running_threads:
                self._add_thread_card_to_displayer(disp, thread, row_index, is_running=True)
                row_index += 1

        # Completed threads section
        if completed_threads:
            # Section header
            disp.add_display_item(DisplayerItemText(
                f"<h4 class='mt-4'><i class='mdi mdi-history'></i> {MSG_THREAD_COMPLETED_HEADER} ({len(completed_threads)}) - {MSG_THREAD_LAST_N}</h4>"
            ), row_index)
            row_index += 1

            # Add each completed thread as a slave layout
            for thread in reversed(completed_threads):  # Newest first
                self._add_thread_card_to_displayer(disp, thread, row_index, is_running=False)
                row_index += 1

        return self._render_displayer(disp)
    
    def _render_displayer(self, disp: Displayer) -> str:
        """Render a Displayer object to HTML string.

        Args:
            disp: Displayer object to render

        Returns:
            HTML string
        """
        try:
            displayer_dict = disp.display()
            html = self.content_reloader_template.render(content=displayer_dict)
            return html
        except Exception as e:
            from ..log.logger_factory import format_exception_html
            self.logger.error("Failed to render displayer: %s", format_exception_html(e))
            return f"<div class='alert alert-danger'>Error rendering thread display: {e}</div>"
    
    def _add_thread_card_to_displayer(self, disp: Displayer, thread: Any, row_index: int, is_running: bool):
        """Add a single thread card to the main displayer.

        Args:
            disp: Main Displayer object
            thread: Thread object
            row_index: Row index in main layout where this thread goes
            is_running: Whether thread is currently running
        """
        thread_name = thread.get_name()
        # Use thread object id to ensure uniqueness when multiple threads have the same name
        thread_unique_id = id(thread)
        thread_id = f"{thread_name.replace(' ', '_').replace(':', '_')}_{thread_unique_id}"

        # Get thread status using proper getters
        progress = thread.get_progress()
        error = thread.get_error()
        is_actually_running = thread.is_running()
        console_data = thread.get_console_data()

        master = disp.add_master_layout(DisplayerLayout(Layouts.VERTICAL, [12]))

        header_layout_id = disp.add_slave_layout(
            DisplayerLayout(Layouts.VERTICAL, [6, 4, 2], alignment=[BSalign.L, BSalign.L, BSalign.R]),
            column=0,
            layout_id=master  # Add to the last master layout (the main vertical one)
        )

        # Left: Thread name
        disp.add_display_item(DisplayerItemIconText(
            id=f"{thread_id}_name",
            icon="mdi-cog",
            text=f"<h5 class='mb-0'>{thread_name}</h5>",
            color=BSstyle.PRIMARY
        ), column=0, layout_id=header_layout_id)

        right_col = 1

        # Status badge
        if error:
            status_badge = str(STATUS_THREAD_ABORTED) if "Aborted" in error else str(STATUS_THREAD_ERROR)
            badge_style = BSstyle.WARNING if "Aborted" in error else BSstyle.ERROR
            disp.add_display_item(DisplayerItemBadge(status_badge, badge_style), column=right_col, layout_id=header_layout_id)
        elif is_actually_running:
            disp.add_display_item(DisplayerItemBadge(str(STATUS_THREAD_RUNNING), BSstyle.SUCCESS), column=right_col, layout_id=header_layout_id)
        else:
            disp.add_display_item(DisplayerItemBadge(str(STATUS_THREAD_COMPLETED), BSstyle.INFO), column=right_col, layout_id=header_layout_id)

        # Progress badge
        if progress > 0:
            disp.add_display_item(DisplayerItemBadge(f"{progress}%", BSstyle.PRIMARY), column=right_col, layout_id=header_layout_id)

        # Delete button - for running threads it stops them, for completed it removes from history
        right_col += 1
        disp.add_display_item(DisplayerItemActionButtons(
            id=f"{thread_id}_actions",
            delete_url=f"/threads/delete?thread_name={thread_name}",
            style="icons"
        ), column=right_col, layout_id=header_layout_id)

        # Row 1: Tabs or "No Data"
        if not console_data:
            disp.add_display_item(DisplayerItemAlert(
                id=f"{thread_id}_nodata",
                text=str(MSG_THREAD_NO_DATA),
                highlightType=BSstyle.LIGHT,
                icon="mdi-information-outline"
            ), column=0, layout_id=master)
            return
        
        console_output = console_data.get('console_output', [])
        logs = console_data.get('logs', [])

        # Build tab titles
        tab_titles = []
        if console_output:
            tab_titles.append(str(TEXT_THREAD_TAB_CONSOLE))
        if logs:
            tab_titles.append(str(TEXT_THREAD_TAB_LOGS))
        tab_titles.append(str(TEXT_THREAD_TAB_INFO))

        # Add TABS layout with unique ID for this thread
        tabs_layout_id = disp.add_master_layout(
            DisplayerLayout(Layouts.TABS, tab_titles, userid=f"{thread_id}_tabs")
        )

        tab_col = 0

        # Tab: Console
        if console_output:
            console_tab_id = disp.add_slave_layout(
                DisplayerLayout(Layouts.VERTICAL, [12]),
                column=tab_col,
                layout_id=tabs_layout_id
            )
            disp.add_display_item(DisplayerItemConsole(
                id=f"{thread_id}_console",
                lines=console_output[-MAX_CONSOLE_LINES:],
                max_height="300px"
            ), column=0, layout_id=console_tab_id)
            tab_col += 1

        # Tab: Logs
        if logs:
            # Create vertical layout for logs
            log_table = disp.add_slave_layout(
                DisplayerLayout(Layouts.TABLE, ["Level", "Message"]),
                column=tab_col,
                layout_id=tabs_layout_id
            )

            for log_row, log in enumerate(logs[-MAX_LOG_LINES:]):
                level = log.get('level', 'info').upper()
                level_style_map = {
                    'DEBUG': BSstyle.SECONDARY,
                    'INFO': BSstyle.INFO,
                    'WARNING': BSstyle.WARNING,
                    'ERROR': BSstyle.ERROR
                }
                level_style = level_style_map.get(level, BSstyle.SECONDARY)

                disp.add_display_item(DisplayerItemBadge(level, level_style), column=0, line=log_row, layout_id=log_table)
                disp.add_display_item(DisplayerItemText(log.get('message', '')), column=1, line=log_row, layout_id=log_table)
            tab_col += 1

        # Tab: Info
        master_info = disp.add_slave_layout(
            DisplayerLayout(Layouts.VERTICAL, [12]),
            column=tab_col,
            layout_id=tabs_layout_id
        )

        info_tab_id = disp.add_slave_layout(
            DisplayerLayout(Layouts.VERTICAL, [6, 6]),
            column=0,
            layout_id=master_info
        )

        disp.add_display_item(DisplayerItemText(f"<strong>{TEXT_THREAD_INFO_NAME}</strong>"), column=0, layout_id=info_tab_id)
        disp.add_display_item(DisplayerItemText(thread_name), column=1, layout_id=info_tab_id)

        # Info line 2: Status
        info_tab_id = disp.add_slave_layout(
            DisplayerLayout(Layouts.VERTICAL, [6, 6]),
            column=0,
            layout_id=master_info
        )
        disp.add_display_item(DisplayerItemText(f"<strong>{TEXT_THREAD_INFO_STATUS}</strong>"), column=0, layout_id=info_tab_id)

        # Determine status text
        if error:
            status_text = str(STATUS_THREAD_ABORTED) if "Aborted" in error else str(STATUS_THREAD_ERROR)
        elif is_actually_running:
            status_text = str(STATUS_THREAD_RUNNING)
        else:
            status_text = str(STATUS_THREAD_COMPLETED)
        disp.add_display_item(DisplayerItemText(status_text), column=1, layout_id=info_tab_id)

        # Info line 3: Progress
        info_tab_id = disp.add_slave_layout(
            DisplayerLayout(Layouts.VERTICAL, [6, 6]),
            column=0,
            layout_id=master_info
        )
        disp.add_display_item(DisplayerItemText(f"<strong>{TEXT_THREAD_INFO_PROGRESS}</strong>"), column=0, layout_id=info_tab_id)
        disp.add_display_item(DisplayerItemText(f"{progress}%"), column=1, layout_id=info_tab_id)

        # Row 2: Error (if present)
        if error:
            disp.add_display_item(DisplayerItemAlert(
                id=f"{thread_id}_error",
                text=f"<strong>Error:</strong> {error}",
                highlightType=BSstyle.ERROR,
                icon="mdi-alert-circle"
            ), column=2, layout_id=master)
        
        return disp


# Global emitter instance
thread_emitter_obj: Optional[ThreadEmitter] = None


def initialize_thread_emitter(socketio_obj, interval=2.0):
    """Initialize the thread emitter singleton.
    
    Args:
        socketio_obj: SocketIO instance
        interval: Emission interval in seconds
        
    Returns:
        ThreadEmitter instance
    """
    global thread_emitter_obj
    if thread_emitter_obj is None:
        thread_emitter_obj = ThreadEmitter(socketio_obj, interval)
    return thread_emitter_obj


def get_thread_emitter() -> Optional[ThreadEmitter]:
    """Get the thread emitter singleton.
    
    Returns:
        ThreadEmitter instance or None if not initialized
    """
    return thread_emitter_obj

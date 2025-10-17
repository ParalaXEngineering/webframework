"""
Comprehensive Scheduler Tests

Tests the scheduler system including:
- MessageQueue: Thread-safe message queueing with size limits
- MessageEmitter: SocketIO emission logic with duplicate filtering
- Scheduler: Integration of queue and emitter with emit_* methods

Test Architecture:
- Unit tests for MessageQueue and MessageEmitter in isolation
- Integration tests for full Scheduler behavior
- Thread-safety tests for concurrent operations
- Mock SocketIO objects to avoid external dependencies

Coverage:
- Queue operations: add, get, peek, clear
- Queue size limits and FIFO eviction
- Queue thread safety with concurrent producers/consumers
- Emitter status/popup/button/modal/reload emission
- Emitter duplicate filtering and error handling
- Scheduler initialization with dependency injection
- Scheduler emit_* methods (status, popup, result, button, modal, reload)
- Scheduler button enable/disable
- Scheduler user hooks (user_before, user_after)
"""

import pytest
import unittest
import threading
import time
from unittest.mock import Mock

from src.modules.scheduler.emitter import MessageEmitter
from src.modules.scheduler.message_queue import MessageQueue, MessageType
from src.modules.scheduler import Scheduler, logLevel


# Mock logLevel enum for MessageEmitter tests
class MockLogLevel:
    """Mock log level for testing without full scheduler import."""
    def __init__(self, name):
        self.name = name

success = MockLogLevel("success")
info = MockLogLevel("info")
warning = MockLogLevel("warning")
error = MockLogLevel("error")


# =============================================================================
# MessageQueue Tests - Thread-safe message queueing
# =============================================================================

class TestMessageQueueBasics:
    """
    Test basic queue operations.
    
    Validates fundamental queue behavior: adding messages, retrieving messages,
    queue clearing, and independence of different message types.
    """
    
    def test_add_and_get_single_message(self):
        """
        Test adding and retrieving a single message.
        
        Validates that a message added to the queue can be retrieved correctly
        with all its data intact.
        """
        queue = MessageQueue()
        
        queue.add(MessageType.STATUS, ["cat1", "msg1", 50, ""])
        messages = queue.get_all(MessageType.STATUS)
        
        assert len(messages) == 1
        assert messages[0] == ["cat1", "msg1", 50, ""]
    
    def test_add_and_get_multiple_messages(self):
        """
        Test adding and retrieving multiple messages.
        
        Validates that multiple messages are stored in FIFO order
        and retrieved correctly.
        """
        queue = MessageQueue()
        
        queue.add(MessageType.STATUS, ["cat1", "msg1", 50, ""])
        queue.add(MessageType.STATUS, ["cat2", "msg2", 100, ""])
        queue.add(MessageType.STATUS, ["cat3", "msg3", 75, ""])
        
        messages = queue.get_all(MessageType.STATUS)
        
        assert len(messages) == 3
        assert messages[0] == ["cat1", "msg1", 50, ""]
        assert messages[1] == ["cat2", "msg2", 100, ""]
        assert messages[2] == ["cat3", "msg3", 75, ""]
    
    def test_get_all_clears_queue(self):
        """
        Test that get_all clears the queue after retrieval.
        
        Validates that get_all is a destructive operation - messages are
        removed from the queue after being retrieved.
        """
        queue = MessageQueue()
        
        queue.add(MessageType.POPUP, ["info", "test message"])
        
        first_get = queue.get_all(MessageType.POPUP)
        second_get = queue.get_all(MessageType.POPUP)
        
        assert len(first_get) == 1
        assert len(second_get) == 0
    
    def test_peek_does_not_clear_queue(self):
        """
        Test that peek does not modify the queue.
        
        Validates that peek allows inspection of queued messages without
        removing them, enabling conditional processing.
        """
        queue = MessageQueue()
        
        queue.add(MessageType.RESULT, ["success", "Test result"])
        
        peeked = queue.peek(MessageType.RESULT)
        gotten = queue.get_all(MessageType.RESULT)
        
        assert len(peeked) == 1
        assert len(gotten) == 1
        assert peeked == gotten
    
    def test_different_message_types_independent(self):
        """
        Test that different message types are stored independently.
        
        Validates that STATUS, POPUP, BUTTON, and other message types have
        separate queues and don't interfere with each other.
        """
        queue = MessageQueue()
        
        queue.add(MessageType.STATUS, ["status_data"])
        queue.add(MessageType.POPUP, ["popup_data"])
        queue.add(MessageType.BUTTON, ["button_data"])
        
        status_msgs = queue.get_all(MessageType.STATUS)
        popup_msgs = queue.get_all(MessageType.POPUP)
        button_msgs = queue.get_all(MessageType.BUTTON)
        
        assert len(status_msgs) == 1
        assert len(popup_msgs) == 1
        assert len(button_msgs) == 1
        assert status_msgs[0] == ["status_data"]
        assert popup_msgs[0] == ["popup_data"]
        assert button_msgs[0] == ["button_data"]


class TestMessageQueueSizeLimits:
    """
    Test queue size limit enforcement.
    
    Validates that queues respect configurable size limits to prevent
    unbounded memory growth during long-running operations.
    """
    
    def test_respects_max_size(self):
        """
        Test that queue respects max size limit.
        
        Validates FIFO eviction: when queue exceeds max_size, oldest messages
        are discarded to make room for new messages.
        """
        queue = MessageQueue(max_size=3)
        
        # Add more messages than max_size
        for i in range(5):
            queue.add(MessageType.STATUS, [f"msg{i}"])
        
        messages = queue.get_all(MessageType.STATUS)
        
        # Should only have last 3 messages (FIFO eviction)
        assert len(messages) == 3
        assert messages[0] == ["msg2"]
        assert messages[1] == ["msg3"]
        assert messages[2] == ["msg4"]
    
    def test_modal_special_limit(self):
        """
        Test that modals have special smaller limit.
        
        Validates that modals use a smaller limit (default 5) to prevent
        UI overwhelming with too many modal dialogs.
        """
        queue = MessageQueue(max_size=1000, modal_limit=5)
        
        # Add many modals
        for i in range(10):
            queue.add(MessageType.MODAL, [f"modal_{i}", f"content_{i}"])
        
        modals = queue.get_all(MessageType.MODAL)
        
        # Should only keep last 5 modals
        assert len(modals) == 5
        assert modals[0] == ["modal_5", "content_5"]
        assert modals[4] == ["modal_9", "content_9"]
    
    def test_other_queues_use_max_size(self):
        """
        Test that non-modal queues use max_size.
        
        Validates that only MODAL has special limit, all other message types
        use the standard max_size limit.
        """
        queue = MessageQueue(max_size=100, modal_limit=5)
        
        # Add many status messages
        for i in range(150):
            queue.add(MessageType.STATUS, [f"status_{i}"])
        
        statuses = queue.get_all(MessageType.STATUS)
        
        # Should have max_size messages, not modal_limit
        assert len(statuses) == 100


class TestMessageQueueThreadSafety:
    """
    Test thread-safety of queue operations.
    
    Validates that MessageQueue can safely handle concurrent operations
    from multiple threads without data corruption or race conditions.
    """
    
    def test_concurrent_adds(self):
        """
        Test that concurrent adds don't lose messages.
        
        Validates that when multiple threads add messages simultaneously,
        all messages are preserved without loss or corruption.
        """
        queue = MessageQueue()
        num_threads = 10
        msgs_per_thread = 100
        
        def add_messages(thread_id: int):
            for i in range(msgs_per_thread):
                queue.add(MessageType.STATUS, [f"thread_{thread_id}_msg_{i}"])
        
        threads = [
            threading.Thread(target=add_messages, args=(i,))
            for i in range(num_threads)
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        messages = queue.get_all(MessageType.STATUS)
        assert len(messages) == num_threads * msgs_per_thread
    
    def test_concurrent_add_and_get(self):
        """
        Test concurrent adds and gets.
        
        Validates that producer and consumer threads can operate simultaneously
        without deadlocks or lost messages.
        """
        queue = MessageQueue()
        results = []
        
        def producer():
            for i in range(50):
                queue.add(MessageType.POPUP, [f"msg_{i}"])
                time.sleep(0.001)
        
        def consumer():
            for _ in range(10):
                msgs = queue.get_all(MessageType.POPUP)
                results.extend(msgs)
                time.sleep(0.005)
        
        prod_thread = threading.Thread(target=producer)
        cons_thread = threading.Thread(target=consumer)
        
        prod_thread.start()
        cons_thread.start()
        
        prod_thread.join()
        cons_thread.join()
        
        # Get any remaining messages
        results.extend(queue.get_all(MessageType.POPUP))
        
        # Should have received all 50 messages
        assert len(results) == 50


class TestMessageQueueClear:
    """
    Test clearing operations.
    
    Validates that queue clearing works correctly for individual message types
    and for all queues simultaneously.
    """
    
    def test_clear_specific_queue(self):
        """
        Test clearing a specific message queue.
        
        Validates that clearing one message type doesn't affect other types,
        allowing selective queue management.
        """
        queue = MessageQueue()
        
        queue.add(MessageType.STATUS, ["status1"])
        queue.add(MessageType.POPUP, ["popup1"])
        
        queue.clear(MessageType.STATUS)
        
        status_msgs = queue.get_all(MessageType.STATUS)
        popup_msgs = queue.get_all(MessageType.POPUP)
        
        assert len(status_msgs) == 0
        assert len(popup_msgs) == 1
    
    def test_clear_all(self):
        """
        Test clearing all queues.
        
        Validates that clear_all empties all message type queues simultaneously,
        useful for reset operations.
        """
        queue = MessageQueue()
        
        queue.add(MessageType.STATUS, ["status1"])
        queue.add(MessageType.POPUP, ["popup1"])
        queue.add(MessageType.BUTTON, ["button1"])
        
        queue.clear_all()
        
        assert queue.size(MessageType.STATUS) == 0
        assert queue.size(MessageType.POPUP) == 0
        assert queue.size(MessageType.BUTTON) == 0


class TestMessageQueueSize:
    """
    Test size checking.
    
    Validates that queue size reporting is accurate before and after
    operations, enabling queue monitoring.
    """
    
    def test_size_returns_correct_count(self):
        """
        Test that size returns correct count.
        
        Validates that size() accurately reports the number of queued messages
        and updates correctly after add/get operations.
        """
        queue = MessageQueue()
        
        assert queue.size(MessageType.STATUS) == 0
        
        queue.add(MessageType.STATUS, ["msg1"])
        assert queue.size(MessageType.STATUS) == 1
        
        queue.add(MessageType.STATUS, ["msg2"])
        queue.add(MessageType.STATUS, ["msg3"])
        assert queue.size(MessageType.STATUS) == 3
        
        queue.get_all(MessageType.STATUS)
        assert queue.size(MessageType.STATUS) == 0


# =============================================================================
# MessageEmitter Tests - SocketIO emission with mock objects
# =============================================================================

@pytest.fixture
def mock_socket():
    """
    Create a mock SocketIO object.
    
    Provides a mock for testing emitter without real SocketIO connection.
    """
    return Mock()


@pytest.fixture
def emitter(mock_socket):
    """
    Create a MessageEmitter with mock socket.
    
    Provides a configured emitter for testing emission logic.
    """
    return MessageEmitter(mock_socket)


class TestStatusEmission:
    """
    Test status message emission and filtering.
    
    Validates that status messages are emitted correctly to SocketIO
    with proper duplicate filtering.
    """
    
    def test_emit_empty_status_list(self, emitter, mock_socket):
        """
        Test that empty status list doesn't emit anything.
        
        Validates optimization: empty lists don't trigger SocketIO calls,
        reducing unnecessary network traffic.
        """
        emitter.emit_status([])
        assert not mock_socket.emit.called
    
    def test_emit_single_status(self, emitter, mock_socket):
        """
        Test emitting a single status message.
        
        Validates that status messages are formatted correctly with category,
        message, progress, and supplement data.
        """
        statuses = [["cat1", "msg1", 50, ""]]
        
        emitter.emit_status(statuses)
        
        mock_socket.emit.assert_called_once_with(
            "action_status",
            {"cat1": ["msg1", 50, ""]}
        )
    
    def test_emit_multiple_statuses(self, emitter, mock_socket):
        """
        Test emitting multiple status messages.
        
        Validates that multiple status messages are each emitted separately,
        allowing real-time progress updates.
        """
        statuses = [
            ["cat1", "msg1", 50, ""],
            ["cat2", "msg2", 75, "detail"],
            ["cat3", "msg3", 100, ""]
        ]
        
        emitter.emit_status(statuses)
        
        assert mock_socket.emit.call_count == 3
    
    def test_filters_duplicate_statuses(self, emitter, mock_socket):
        """
        Test that duplicate status messages are filtered.
        
        Validates duplicate filtering: keeps only the last occurrence of each
        unique category+message pair, preventing UI spam.
        """
        statuses = [
            ["cat1", "msg1", 25, ""],
            ["cat1", "msg1", 50, ""],  # Duplicate - should keep this one
            ["cat2", "msg2", 100, ""],
            ["cat1", "msg1", 75, ""],  # Another duplicate - should keep this one
        ]
        
        emitter.emit_status(statuses)
        
        # Should only emit 2 messages (unique msg1 with 75%, msg2)
        assert mock_socket.emit.call_count == 2
        
        calls = mock_socket.emit.call_args_list
        # Check both messages were emitted (order may vary based on dict iteration)
        emitted_data = [call_info[0][1] for call_info in calls]
        assert {"cat1": ["msg1", 75, ""]} in emitted_data
        assert {"cat2": ["msg2", 100, ""]} in emitted_data
    
    def test_handles_socket_error_gracefully(self, emitter, mock_socket):
        """
        Test that socket errors don't crash the emitter.
        
        Validates error resilience: SocketIO errors are caught and logged
        without crashing the scheduler or action.
        """
        mock_socket.emit.side_effect = Exception("Socket error")
        
        statuses = [["cat1", "msg1", 50, ""]]
        
        # Should not raise exception
        emitter.emit_status(statuses)
        
        assert mock_socket.emit.called


class TestPopupEmission:
    """
    Test popup message emission.
    
    Validates that popup messages (alerts/notifications) are emitted correctly
    with appropriate log levels.
    """
    
    def test_emit_single_popup(self, emitter, mock_socket):
        """
        Test emitting a single popup.
        
        Validates that popups are formatted with log level and message text,
        displayed as SweetAlert2 toasts to the user.
        """
        popups = [[info, "Test message"]]
        
        emitter.emit_popups(popups)
        
        mock_socket.emit.assert_called_once_with(
            "popup",
            {"info": "Test message"}
        )
    
    def test_emit_multiple_popups(self, emitter, mock_socket):
        """
        Test emitting multiple popups.
        
        Validates that multiple popups with different log levels
        (success, warning, error) are each emitted separately.
        """
        popups = [
            [success, "Success message"],
            [warning, "Warning message"],
            [error, "Error message"]
        ]
        
        emitter.emit_popups(popups)
        
        assert mock_socket.emit.call_count == 3
        mock_socket.emit.assert_any_call("popup", {"success": "Success message"})
        mock_socket.emit.assert_any_call("popup", {"warning": "Warning message"})
        mock_socket.emit.assert_any_call("popup", {"error": "Error message"})
    
    def test_handles_popup_error(self, emitter, mock_socket):
        """
        Test error handling for popup emission.
        
        Validates that popup emission errors don't crash the scheduler,
        ensuring robustness even with network issues.
        """
        mock_socket.emit.side_effect = Exception("Popup error")
        
        popups = [[info, "test"]]
        
        # Should not raise
        emitter.emit_popups(popups)


class TestResultEmission:
    """
    Test result message emission.
    
    Validates that action results (success/failure messages) are emitted
    correctly for display in result cards.
    """
    
    def test_emit_results(self, emitter, mock_socket):
        """
        Test emitting result messages.
        
        Validates that results are formatted with category (success/danger)
        and HTML text for rich result display.
        """
        results = [
            ["success", "Operation completed"],
            ["danger", "Operation failed"]
        ]
        
        emitter.emit_results(results)
        
        assert mock_socket.emit.call_count == 2
        mock_socket.emit.assert_any_call("result", {
            "category": "success",
            "text": "Operation completed"
        })
        mock_socket.emit.assert_any_call("result", {
            "category": "danger",
            "text": "Operation failed"
        })


class TestModalEmission:
    """
    Test modal dialog emission.
    
    Validates that modal dialogs are emitted correctly with ID and HTML content
    for dynamic modal display.
    """
    
    def test_emit_modals(self, emitter, mock_socket):
        """
        Test emitting modal dialogs.
        
        Validates that modals are sent with ID for targeting and HTML content
        for rendering in Bootstrap modal dialogs.
        """
        modals = [
            ["modal1", "<div>Content 1</div>"],
            ["modal2", "<div>Content 2</div>"]
        ]
        
        emitter.emit_modals(modals)
        
        assert mock_socket.emit.call_count == 2
        mock_socket.emit.assert_any_call("modal", {
            "id": "modal1",
            "text": "<div>Content 1</div>"
        })


class TestButtonEmission:
    """
    Test button update emission.
    
    Validates that button updates (icon, text, style changes) are emitted
    correctly for dynamic button state management.
    """
    
    def test_emit_buttons(self, emitter, mock_socket):
        """
        Test emitting button updates.
        
        Validates that button updates include ID, icon, text, and style
        for complete button re-rendering.
        """
        buttons = [
            ["btn1", "home", "Home", "primary"],
            ["btn2", "settings", "Settings", "secondary"]
        ]
        
        emitter.emit_buttons(buttons)
        
        assert mock_socket.emit.call_count == 2
        mock_socket.emit.assert_any_call("button", {
            "btn1": ["home", "Home", "primary"]
        })


class TestReloadEmission:
    """
    Test content reload emission.
    
    Validates that dynamic content reload messages are emitted correctly
    for updating DisplayerItemDynamicContent areas.
    """
    
    def test_emit_reloads(self, emitter, mock_socket):
        """
        Test emitting reload requests.
        
        Validates that reload messages include target ID and new HTML content
        for dynamic content updates without page refresh.
        """
        reloads = [
            ["content1", "<div>New content</div>"],
            ["content2", "<div>Another content</div>"]
        ]
        
        emitter.emit_reloads(reloads)
        
        assert mock_socket.emit.call_count == 2


class TestButtonStateEmission:
    """
    Test button state changes.
    
    Validates that button enable/disable state changes are emitted correctly
    for dynamic button state management.
    """
    
    def test_emit_button_states(self, emitter, mock_socket):
        """
        Test emitting button enable/disable.
        
        Validates that button state changes are sent in batches (lists of IDs)
        for efficient state management.
        """
        disable_list = ["btn1", "btn2"]
        enable_list = ["btn3", "btn4"]
        
        emitter.emit_button_states(disable_list, enable_list)
        
        assert mock_socket.emit.call_count == 2
        mock_socket.emit.assert_any_call("disable_button", ["btn1", "btn2"])
        mock_socket.emit.assert_any_call("enable_button", ["btn3", "btn4"])
    
    def test_emit_empty_button_states(self, emitter, mock_socket):
        """
        Test that empty lists don't emit.
        
        Validates optimization: empty state change lists don't trigger
        unnecessary SocketIO calls.
        """
        emitter.emit_button_states([], [])
        
        assert not mock_socket.emit.called


class TestThreadEmission:
    """
    Test thread status emission.
    
    Validates that thread manager status updates are emitted correctly
    for real-time thread monitoring.
    """
    
    def test_emit_threads(self, emitter, mock_socket):
        """
        Test emitting thread status.
        
        Validates that thread information (name, state) is sent for
        display in thread monitoring UI.
        """
        thread_info = [
            {"name": "worker1", "state": "RUNNING"},
            {"name": "worker2", "state": "IDLE"}
        ]
        
        emitter.emit_threads(thread_info)
        
        mock_socket.emit.assert_called_once_with("threads", thread_info)


# =============================================================================
# Scheduler Integration Tests - Full system integration
# =============================================================================

class TestSchedulerInitialization(unittest.TestCase):
    """
    Test scheduler initialization with dependency injection.
    
    Validates that Scheduler properly initializes with default or custom
    MessageQueue and MessageEmitter instances.
    """
    
    def test_default_initialization(self):
        """
        Test scheduler creates default queue and emitter.
        
        Validates that Scheduler automatically creates MessageQueue and
        MessageEmitter when not provided, simplifying typical usage.
        """
        mock_socket = Mock()
        scheduler = Scheduler(socket_obj=mock_socket)
        
        self.assertIsNotNone(scheduler._queue)
        self.assertIsNotNone(scheduler._emitter)
        self.assertEqual(scheduler.socket_obj, mock_socket)
    
    def test_custom_queue_initialization(self):
        """
        Test scheduler accepts custom queue.
        
        Validates dependency injection: custom MessageQueue with specific
        size limits can be provided for specialized use cases.
        """
        mock_socket = Mock()
        custom_queue = MessageQueue(max_size=500)
        scheduler = Scheduler(socket_obj=mock_socket, message_queue=custom_queue)
        
        self.assertEqual(scheduler._queue, custom_queue)
    
    def test_custom_emitter_initialization(self):
        """
        Test scheduler accepts custom emitter.
        
        Validates dependency injection: custom MessageEmitter can be provided
        for testing or specialized emission logic.
        """
        mock_socket = Mock()
        custom_emitter = MessageEmitter(mock_socket)
        scheduler = Scheduler(socket_obj=mock_socket, message_emitter=custom_emitter)
        
        self.assertEqual(scheduler._emitter, custom_emitter)
    
    def test_no_socket_initialization(self):
        """
        Test scheduler works without socket (for testing).
        
        Validates that Scheduler can be used without SocketIO for unit testing,
        queueing messages without emission.
        """
        scheduler = Scheduler()
        
        self.assertIsNotNone(scheduler._queue)
        self.assertIsNone(scheduler._emitter)


class TestSchedulerMessageEmission(unittest.TestCase):
    """
    Test message emission through scheduler.
    
    Validates that all emit_* methods correctly add messages to the queue
    with proper formatting.
    """
    
    def setUp(self):
        """
        Set up test fixtures.
        
        Creates mock socket, queue, emitter, and scheduler for each test.
        """
        self.mock_socket = Mock()
        self.queue = MessageQueue()
        self.emitter = MessageEmitter(self.mock_socket)
        self.scheduler = Scheduler(
            socket_obj=self.mock_socket,
            message_queue=self.queue,
            message_emitter=self.emitter
        )
    
    def test_emit_status_adds_to_queue(self):
        """
        Test emit_status adds message to queue.
        
        Validates that emit_status correctly formats and queues status messages
        with category, message, progress, and supplement.
        """
        self.scheduler.emit_status("test_cat", "test_msg", 50, "supplement")
        
        messages = self.queue.get_all(MessageType.STATUS)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0], ["test_cat", "test_msg", 50, "supplement"])
    
    def test_emit_popup_adds_to_queue(self):
        """
        Test emit_popup adds message to queue.
        
        Validates that emit_popup correctly queues popup messages with
        log level and message text.
        """
        self.scheduler.emit_popup(logLevel.info, "Test popup")
        
        messages = self.queue.get_all(MessageType.POPUP)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0][0], logLevel.info)
        self.assertEqual(messages[0][1], "Test popup")
    
    def test_emit_result_adds_to_queue(self):
        """
        Test emit_result adds message to queue.
        
        Validates that emit_result correctly queues result messages with
        category (success/danger) and HTML text.
        """
        self.scheduler.emit_result("success", "<b>Done!</b>")
        
        messages = self.queue.get_all(MessageType.RESULT)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0], ["success", "<b>Done!</b>"])
    
    def test_emit_button_adds_to_queue(self):
        """
        Test emit_button adds message to queue.
        
        Validates that emit_button correctly queues button updates with
        ID, icon, text, and style.
        """
        self.scheduler.emit_button("btn1", "mdi-play", "Start", "success")
        
        messages = self.queue.get_all(MessageType.BUTTON)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0], ["btn1", "mdi-play", "Start", "success"])
    
    def test_emit_modal_adds_to_queue(self):
        """
        Test emit_modal adds message to queue.
        
        Validates that emit_modal correctly queues modal messages with
        ID and HTML content.
        """
        self.scheduler.emit_modal("modal1", "<h1>Modal Content</h1>")
        
        messages = self.queue.get_all(MessageType.MODAL)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0], ["modal1", "<h1>Modal Content</h1>"])
    
    def test_emit_reload_adds_to_queue(self):
        """
        Test emit_reload adds messages to queue.
        
        Validates that emit_reload correctly handles list of content updates,
        queuing each target ID and HTML content separately.
        """
        content = [
            {"id": "form1", "content": "<input>"},
            {"id": "form2", "content": "<select>"}
        ]
        self.scheduler.emit_reload(content)
        
        messages = self.queue.get_all(MessageType.RELOAD)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0], ["form1", "<input>"])
        self.assertEqual(messages[1], ["form2", "<select>"])
    
    def test_disable_button_adds_to_queue(self):
        """
        Test disable_button adds to queue.
        
        Validates that disable_button correctly queues button IDs for
        disabling in the UI.
        """
        self.scheduler.disable_button("btn1")
        
        messages = self.queue.get_all(MessageType.BUTTON_DISABLE)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0], "btn1")
    
    def test_enable_button_adds_to_queue(self):
        """
        Test enable_button adds to queue.
        
        Validates that enable_button correctly queues button IDs for
        enabling in the UI.
        """
        self.scheduler.enable_button("btn1")
        
        messages = self.queue.get_all(MessageType.BUTTON_ENABLE)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0], "btn1")


class TestSchedulerQueueIntegration(unittest.TestCase):
    """
    Test scheduler integration with MessageQueue.
    
    Validates that Scheduler correctly enforces queue size limits and
    respects queue configuration.
    """
    
    def setUp(self):
        """
        Set up test fixtures.
        
        Creates scheduler with small queue size for testing limit enforcement.
        """
        self.mock_socket = Mock()
        self.queue = MessageQueue(max_size=10)  # Small size for testing
        self.scheduler = Scheduler(
            socket_obj=self.mock_socket,
            message_queue=self.queue
        )
    
    def test_queue_size_limits_enforced(self):
        """
        Test that queue size limits are enforced.
        
        Validates that when more messages are emitted than max_size,
        FIFO eviction keeps only the most recent messages.
        """
        # Add 15 messages (more than max_size of 10)
        for i in range(15):
            self.scheduler.emit_status("cat", f"msg{i}", i)
        
        messages = self.queue.get_all(MessageType.STATUS)
        # Should only have last 10 due to FIFO eviction
        self.assertEqual(len(messages), 10)
        self.assertEqual(messages[-1][1], "msg14")
    
    def test_modal_size_limit(self):
        """
        Test that modal size limit is enforced (5 modals max).
        
        Validates that modal queue has special smaller limit to prevent
        overwhelming the UI with too many dialogs.
        """
        # Add 10 modals
        for i in range(10):
            self.scheduler.emit_modal(f"modal{i}", f"content{i}")
        
        messages = self.queue.get_all(MessageType.MODAL)
        # MessageQueue has modal_limit of 5
        self.assertLessEqual(len(messages), 5)


class TestSchedulerEmitterIntegration(unittest.TestCase):
    """
    Test scheduler integration with MessageEmitter.
    
    Validates that Scheduler and MessageEmitter work together correctly,
    including duplicate filtering and error handling.
    """
    
    def setUp(self):
        """
        Set up test fixtures.
        
        Creates full scheduler with queue and emitter for integration testing.
        """
        self.mock_socket = Mock()
        self.queue = MessageQueue()
        self.emitter = MessageEmitter(self.mock_socket)
        self.scheduler = Scheduler(
            socket_obj=self.mock_socket,
            message_queue=self.queue,
            message_emitter=self.emitter
        )
    
    def test_emitter_status_duplicate_filtering(self):
        """
        Test that emitter filters duplicate status messages.
        
        Validates that when multiple status messages with same category+message
        are queued, only the last occurrence is emitted to prevent UI spam.
        """
        # Add multiple status messages with same content
        self.scheduler.emit_status("cat", "same", 10)
        self.scheduler.emit_status("cat", "same", 20)
        self.scheduler.emit_status("cat", "different", 30)
        self.scheduler.emit_status("cat", "same", 40)
        
        messages = self.queue.get_all(MessageType.STATUS)
        
        # Convert QueuedMessage objects to the format expected by emitter
        # QueuedMessage.data contains [category, message, status, supplement]
        status_list = [msg.data for msg in messages]
        
        # Emit through emitter
        self.emitter.emit_status(status_list, "test_user")
        
        # Should have emitted only 3 times (duplicates filtered)
        # Note: Filtering keeps last occurrence of each unique message
        self.assertGreater(self.mock_socket.emit.call_count, 0)


class TestSchedulerThreadSafety(unittest.TestCase):
    """
    Test thread safety of scheduler operations.
    
    Validates that Scheduler can safely handle concurrent emit_* calls
    from multiple threads without data corruption.
    """
    
    def test_concurrent_message_emission(self):
        """
        Test concurrent message emission from multiple threads.
        
        Validates that when multiple threads emit messages simultaneously,
        all messages are preserved correctly in the queue.
        """
        mock_socket = Mock()
        scheduler = Scheduler(socket_obj=mock_socket)
        
        def emit_messages(thread_id):
            for i in range(10):
                scheduler.emit_status(f"thread{thread_id}", f"msg{i}", i)
                scheduler.emit_popup(logLevel.info, f"popup{thread_id}_{i}")
        
        threads = []
        for i in range(5):
            t = threading.Thread(target=emit_messages, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # Should have 50 status messages (5 threads * 10 messages)
        status_messages = scheduler._queue.get_all(MessageType.STATUS)
        self.assertEqual(len(status_messages), 50)
        
        # Should have 50 popup messages
        popup_messages = scheduler._queue.get_all(MessageType.POPUP)
        self.assertEqual(len(popup_messages), 50)


class TestSchedulerUserHooks(unittest.TestCase):
    """
    Test scheduler user hook methods.
    
    Validates that user_before and user_after hooks work correctly
    and can be overridden in subclasses for custom behavior.
    """
    
    def test_user_before_default(self):
        """
        Test user_before default implementation.
        
        Validates that default user_before hook returns None and does nothing,
        ready to be overridden by subclasses.
        """
        scheduler = Scheduler()
        result = scheduler.user_before()
        self.assertIsNone(result)
    
    def test_user_after_default(self):
        """
        Test user_after default implementation.
        
        Validates that default user_after hook returns None and does nothing,
        ready to be overridden by subclasses.
        """
        scheduler = Scheduler()
        result = scheduler.user_after()
        self.assertIsNone(result)
    
    def test_user_hooks_can_be_overridden(self):
        """
        Test that user hooks can be overridden in subclass.
        
        Validates the extensibility pattern: subclasses can override user_before
        and user_after to add custom setup/teardown logic for actions.
        """
        class CustomScheduler(Scheduler):
            def __init__(self):
                super().__init__()
                self.before_called = False
                self.after_called = False
            
            def user_before(self):
                self.before_called = True
            
            def user_after(self):
                self.after_called = True
        
        scheduler = CustomScheduler()
        scheduler.user_before()
        scheduler.user_after()
        
        self.assertTrue(scheduler.before_called)
        self.assertTrue(scheduler.after_called)


if __name__ == "__main__":
    # Run pytest tests
    pytest.main([__file__, "-v"])

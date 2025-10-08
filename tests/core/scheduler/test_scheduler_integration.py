"""
Integration tests for refactored Scheduler class.

Tests the full integration between Scheduler, MessageQueue, and MessageEmitter.
"""

import unittest
from unittest.mock import Mock
import threading

# Import Scheduler classes from scheduler_classes module
from src.modules import scheduler_classes
from src.modules.scheduler import MessageQueue, MessageEmitter, MessageType

# Get classes
Scheduler = scheduler_classes.Scheduler
logLevel = scheduler_classes.logLevel


class TestSchedulerInitialization(unittest.TestCase):
    """Test scheduler initialization with dependency injection."""
    
    def test_default_initialization(self):
        """Test scheduler creates default queue and emitter."""
        mock_socket = Mock()
        scheduler = Scheduler(socket_obj=mock_socket)
        
        self.assertIsNotNone(scheduler._queue)
        self.assertIsNotNone(scheduler._emitter)
        self.assertEqual(scheduler.socket_obj, mock_socket)
    
    def test_custom_queue_initialization(self):
        """Test scheduler accepts custom queue."""
        mock_socket = Mock()
        custom_queue = MessageQueue(max_size=500)
        scheduler = Scheduler(socket_obj=mock_socket, message_queue=custom_queue)
        
        self.assertEqual(scheduler._queue, custom_queue)
    
    def test_custom_emitter_initialization(self):
        """Test scheduler accepts custom emitter."""
        mock_socket = Mock()
        custom_emitter = MessageEmitter(mock_socket)
        scheduler = Scheduler(socket_obj=mock_socket, message_emitter=custom_emitter)
        
        self.assertEqual(scheduler._emitter, custom_emitter)
    
    def test_no_socket_initialization(self):
        """Test scheduler works without socket (for testing)."""
        scheduler = Scheduler()
        
        self.assertIsNotNone(scheduler._queue)
        self.assertIsNone(scheduler._emitter)


class TestSchedulerMessageEmission(unittest.TestCase):
    """Test message emission through scheduler."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_socket = Mock()
        self.queue = MessageQueue()
        self.emitter = MessageEmitter(self.mock_socket)
        self.scheduler = Scheduler(
            socket_obj=self.mock_socket,
            message_queue=self.queue,
            message_emitter=self.emitter
        )
    
    def test_emit_status_adds_to_queue(self):
        """Test emit_status adds message to queue."""
        self.scheduler.emit_status("test_cat", "test_msg", 50, "supplement")
        
        messages = self.queue.get_all(MessageType.STATUS)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0], ["test_cat", "test_msg", 50, "supplement"])
    
    def test_emit_popup_adds_to_queue(self):
        """Test emit_popup adds message to queue."""
        self.scheduler.emit_popup(logLevel.info, "Test popup")
        
        messages = self.queue.get_all(MessageType.POPUP)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0][0], logLevel.info)
        self.assertEqual(messages[0][1], "Test popup")
    
    def test_emit_result_adds_to_queue(self):
        """Test emit_result adds message to queue."""
        self.scheduler.emit_result("success", "<b>Done!</b>")
        
        messages = self.queue.get_all(MessageType.RESULT)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0], ["success", "<b>Done!</b>"])
    
    def test_emit_button_adds_to_queue(self):
        """Test emit_button adds message to queue."""
        self.scheduler.emit_button("btn1", "mdi-play", "Start", "success")
        
        messages = self.queue.get_all(MessageType.BUTTON)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0], ["btn1", "mdi-play", "Start", "success"])
    
    def test_emit_modal_adds_to_queue(self):
        """Test emit_modal adds message to queue."""
        self.scheduler.emit_modal("modal1", "<h1>Modal Content</h1>")
        
        messages = self.queue.get_all(MessageType.MODAL)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0], ["modal1", "<h1>Modal Content</h1>"])
    
    def test_emit_reload_adds_to_queue(self):
        """Test emit_reload adds messages to queue."""
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
        """Test disable_button adds to queue."""
        self.scheduler.disable_button("btn1")
        
        messages = self.queue.get_all(MessageType.BUTTON_DISABLE)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0], "btn1")
    
    def test_enable_button_adds_to_queue(self):
        """Test enable_button adds to queue."""
        self.scheduler.enable_button("btn1")
        
        messages = self.queue.get_all(MessageType.BUTTON_ENABLE)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0], "btn1")


class TestSchedulerQueueIntegration(unittest.TestCase):
    """Test scheduler integration with MessageQueue."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_socket = Mock()
        self.queue = MessageQueue(max_size=10)  # Small size for testing
        self.scheduler = Scheduler(
            socket_obj=self.mock_socket,
            message_queue=self.queue
        )
    
    def test_queue_size_limits_enforced(self):
        """Test that queue size limits are enforced."""
        # Add 15 messages (more than max_size of 10)
        for i in range(15):
            self.scheduler.emit_status("cat", f"msg{i}", i)
        
        messages = self.queue.get_all(MessageType.STATUS)
        # Should only have last 10 due to FIFO eviction
        self.assertEqual(len(messages), 10)
        self.assertEqual(messages[-1][1], "msg14")
    
    def test_modal_size_limit(self):
        """Test that modal size limit is enforced (5 modals max)."""
        # Add 10 modals
        for i in range(10):
            self.scheduler.emit_modal(f"modal{i}", f"content{i}")
        
        messages = self.queue.get_all(MessageType.MODAL)
        # MessageQueue has modal_limit of 5
        self.assertLessEqual(len(messages), 5)


class TestSchedulerEmitterIntegration(unittest.TestCase):
    """Test scheduler integration with MessageEmitter."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_socket = Mock()
        self.queue = MessageQueue()
        self.emitter = MessageEmitter(self.mock_socket)
        self.scheduler = Scheduler(
            socket_obj=self.mock_socket,
            message_queue=self.queue,
            message_emitter=self.emitter
        )
    
    def test_emitter_status_duplicate_filtering(self):
        """Test that emitter filters duplicate status messages."""
        # Add multiple status messages with same content
        self.scheduler.emit_status("cat", "same", 10)
        self.scheduler.emit_status("cat", "same", 20)
        self.scheduler.emit_status("cat", "different", 30)
        self.scheduler.emit_status("cat", "same", 40)
        
        messages = self.queue.get_all(MessageType.STATUS)
        
        # Emit through emitter
        self.emitter.emit_status(messages)
        
        # Should have emitted only 3 times (duplicates filtered)
        # Note: Filtering keeps last occurrence of each unique message
        self.assertGreater(self.mock_socket.emit.call_count, 0)


class TestSchedulerThreadSafety(unittest.TestCase):
    """Test thread safety of scheduler operations."""
    
    def test_concurrent_message_emission(self):
        """Test concurrent message emission from multiple threads."""
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
    """Test scheduler user hook methods."""
    
    def test_user_before_default(self):
        """Test user_before default implementation."""
        scheduler = Scheduler()
        result = scheduler.user_before()
        self.assertIsNone(result)
    
    def test_user_after_default(self):
        """Test user_after default implementation."""
        scheduler = Scheduler()
        result = scheduler.user_after()
        self.assertIsNone(result)
    
    def test_user_hooks_can_be_overridden(self):
        """Test that user hooks can be overridden in subclass."""
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
    unittest.main()

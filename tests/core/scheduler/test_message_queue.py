"""
Unit tests for MessageQueue.

Tests the thread-safe message queueing system in isolation.
"""
import pytest
import threading
import time
from src.modules.scheduler.message_queue import MessageQueue, MessageType


class TestMessageQueueBasics:
    """Test basic queue operations."""
    
    def test_add_and_get_single_message(self):
        """Test adding and retrieving a single message."""
        queue = MessageQueue()
        
        queue.add(MessageType.STATUS, ["cat1", "msg1", 50, ""])
        messages = queue.get_all(MessageType.STATUS)
        
        assert len(messages) == 1
        assert messages[0] == ["cat1", "msg1", 50, ""]
    
    def test_add_and_get_multiple_messages(self):
        """Test adding and retrieving multiple messages."""
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
        """Test that get_all clears the queue after retrieval."""
        queue = MessageQueue()
        
        queue.add(MessageType.POPUP, ["info", "test message"])
        
        first_get = queue.get_all(MessageType.POPUP)
        second_get = queue.get_all(MessageType.POPUP)
        
        assert len(first_get) == 1
        assert len(second_get) == 0
    
    def test_peek_does_not_clear_queue(self):
        """Test that peek does not modify the queue."""
        queue = MessageQueue()
        
        queue.add(MessageType.RESULT, ["success", "Test result"])
        
        peeked = queue.peek(MessageType.RESULT)
        gotten = queue.get_all(MessageType.RESULT)
        
        assert len(peeked) == 1
        assert len(gotten) == 1
        assert peeked == gotten
    
    def test_different_message_types_independent(self):
        """Test that different message types are stored independently."""
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
    """Test queue size limit enforcement."""
    
    def test_respects_max_size(self):
        """Test that queue respects max size limit."""
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
        """Test that modals have special smaller limit."""
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
        """Test that non-modal queues use max_size."""
        queue = MessageQueue(max_size=100, modal_limit=5)
        
        # Add many status messages
        for i in range(150):
            queue.add(MessageType.STATUS, [f"status_{i}"])
        
        statuses = queue.get_all(MessageType.STATUS)
        
        # Should have max_size messages, not modal_limit
        assert len(statuses) == 100


class TestMessageQueueThreadSafety:
    """Test thread-safety of queue operations."""
    
    def test_concurrent_adds(self):
        """Test that concurrent adds don't lose messages."""
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
        """Test concurrent adds and gets."""
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
    """Test clearing operations."""
    
    def test_clear_specific_queue(self):
        """Test clearing a specific message queue."""
        queue = MessageQueue()
        
        queue.add(MessageType.STATUS, ["status1"])
        queue.add(MessageType.POPUP, ["popup1"])
        
        queue.clear(MessageType.STATUS)
        
        status_msgs = queue.get_all(MessageType.STATUS)
        popup_msgs = queue.get_all(MessageType.POPUP)
        
        assert len(status_msgs) == 0
        assert len(popup_msgs) == 1
    
    def test_clear_all(self):
        """Test clearing all queues."""
        queue = MessageQueue()
        
        queue.add(MessageType.STATUS, ["status1"])
        queue.add(MessageType.POPUP, ["popup1"])
        queue.add(MessageType.BUTTON, ["button1"])
        
        queue.clear_all()
        
        assert queue.size(MessageType.STATUS) == 0
        assert queue.size(MessageType.POPUP) == 0
        assert queue.size(MessageType.BUTTON) == 0


class TestMessageQueueSize:
    """Test size checking."""
    
    def test_size_returns_correct_count(self):
        """Test that size returns correct count."""
        queue = MessageQueue()
        
        assert queue.size(MessageType.STATUS) == 0
        
        queue.add(MessageType.STATUS, ["msg1"])
        assert queue.size(MessageType.STATUS) == 1
        
        queue.add(MessageType.STATUS, ["msg2"])
        queue.add(MessageType.STATUS, ["msg3"])
        assert queue.size(MessageType.STATUS) == 3
        
        queue.get_all(MessageType.STATUS)
        assert queue.size(MessageType.STATUS) == 0

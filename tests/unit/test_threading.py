"""
Unit Tests for Threading System - Comprehensive test suite.

Tests cover:
- Thread lifecycle management
- Console output capture
- Logging functionality
- Process communication
- Thread manager operations
"""

import pytest
import time
import sys
import os
from threading import Event

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.modules.threaded.threaded_action import Threaded_action
from src.modules.threaded.threaded_manager import Threaded_manager
from src.modules import scheduler


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(autouse=True)
def setup_thread_manager():
    """Initialize thread manager before each test"""
    import src.modules.threaded.threaded_manager as tm_module
    tm_module.thread_manager_obj = Threaded_manager()
    yield
    # Cleanup after test - kill all threads
    if tm_module.thread_manager_obj:
        tm_module.thread_manager_obj.kill_all_threads()
        time.sleep(0.2)  # Give threads time to stop


@pytest.fixture(autouse=True)
def setup_scheduler():
    """Initialize scheduler before each test"""
    if scheduler.scheduler_obj is None:
        from src.modules.scheduler.scheduler import Scheduler
        scheduler.scheduler_obj = Scheduler()
    yield


# ============================================================================
# TEST THREAD CLASSES
# ============================================================================

class SimpleThread(Threaded_action):
    """Simple thread for testing basic functionality"""
    m_default_name = "SimpleThread"
    
    def __init__(self):
        super().__init__()
        self.executed = False
        self.execution_count = 0
    
    def action(self):
        self.console_write("Starting simple action")
        self.executed = True
        self.execution_count += 1
        time.sleep(0.1)
        self.console_write("Simple action completed")


class ProgressThread(Threaded_action):
    """Thread with progress tracking"""
    m_default_name = "ProgressThread"
    
    def action(self):
        self.console_write("Starting progress action")
        for i in range(10):
            self.m_running_state = i * 10
            self.console_write(f"Progress: {self.m_running_state}%")
            time.sleep(0.05)
        self.m_running_state = 100
        self.console_write("Progress action completed")


class ErrorThread(Threaded_action):
    """Thread that raises an error"""
    m_default_name = "ErrorThread"
    
    def action(self):
        self.console_write("About to raise error")
        raise ValueError("Test error message")


class ProcessThread(Threaded_action):
    """Thread that runs a process"""
    m_default_name = "ProcessThread"
    
    def action(self):
        self.console_write("Starting process")
        
        # Run a simple command
        if sys.platform == "win32":
            self.process_exec(["echo", "Hello from process"], ".", shell=True)
        else:
            self.process_exec(["echo", "Hello from process"], ".")
        
        self.process_wait(timeout=5)
        
        results = self.process_read_results()
        self.console_write(f"Process output: {results}")


class LongRunningThread(Threaded_action):
    """Thread that runs for a long time"""
    m_default_name = "LongRunningThread"
    
    def __init__(self):
        super().__init__()
        self.stop_event = Event()
    
    def action(self):
        self.console_write("Long running task started")
        for i in range(100):
            if self.stop_event.is_set():
                self.console_write("Stopped by request")
                break
            time.sleep(0.1)
            if i % 10 == 0:
                self.console_write(f"Still running... {i}")
        self.console_write("Long running task finished")


# ============================================================================
# BASIC THREAD TESTS
# ============================================================================

def test_thread_creation():
    """Test that threads are created and registered"""
    thread = SimpleThread()
    
    assert thread is not None
    assert thread.get_name() == "SimpleThread"
    assert not thread.m_running
    assert thread.m_running_state == -1


def test_thread_start_and_execution():
    """Test thread starts and executes action"""
    thread = SimpleThread()
    thread.start()
    
    # Wait for thread to complete
    time.sleep(0.5)
    
    assert thread.executed
    assert thread.execution_count == 1


def test_thread_name_change():
    """Test changing thread name"""
    thread = SimpleThread()
    
    original_name = thread.get_name()
    thread.change_name("CustomName")
    
    assert thread.get_name() == "CustomName"
    assert thread.get_name() != original_name


def test_thread_deletion():
    """Test thread deletion and cleanup"""
    import src.modules.threaded.threaded_manager as tm_module
    manager = tm_module.thread_manager_obj
    
    thread = SimpleThread()
    thread_count_before = manager.get_thread_count()
    
    thread.delete()
    time.sleep(0.1)
    
    thread_count_after = manager.get_thread_count()
    assert thread_count_after < thread_count_before


# ============================================================================
# CONSOLE TESTS
# ============================================================================

def test_console_write():
    """Test writing to console"""
    thread = SimpleThread()
    
    thread.console_write("Test message 1")
    thread.console_write("Test message 2", "WARNING")
    thread.console_write("Test message 3", "ERROR")
    
    output = thread.console_get_output()
    
    assert len(output) >= 3
    assert any("Test message 1" in line for line in output)
    assert any("WARNING" in line for line in output)
    assert any("ERROR" in line for line in output)


def test_console_raw_write():
    """Test writing raw messages to console"""
    thread = SimpleThread()
    
    thread.console_write_raw("Raw message without timestamp")
    
    output = thread.console_get_output()
    
    assert "Raw message without timestamp" in output


def test_console_get_limited_output():
    """Test getting limited number of console lines"""
    thread = SimpleThread()
    
    for i in range(20):
        thread.console_write(f"Message {i}")
    
    last_5 = thread.console_get_output(lines=5)
    
    assert len(last_5) == 5
    assert "Message 19" in last_5[-1]


def test_console_clear():
    """Test clearing console output"""
    thread = SimpleThread()
    
    thread.console_write("Message 1")
    thread.console_write("Message 2")
    
    output_before = thread.console_get_output()
    assert len(output_before) > 0
    
    thread.console_clear()
    
    output_after = thread.console_get_output()
    assert len(output_after) == 0


def test_console_maxlen():
    """Test console output maximum length"""
    thread = SimpleThread()
    
    # Write more than maxlen (1000)
    for i in range(1500):
        thread.console_write(f"Message {i}")
    
    output = thread.console_get_output()
    
    # Should be capped at 1000
    assert len(output) <= 1000


# ============================================================================
# LOGGING TESTS
# ============================================================================

def test_log_write():
    """Test writing log entries"""
    thread = SimpleThread()
    
    thread.log_write("Log entry 1")
    thread.log_write("Log entry 2", "WARNING")
    thread.log_write("Log entry 3", "ERROR")
    
    logs = thread.log_get_entries()
    
    assert len(logs) >= 3
    assert logs[-3]["message"] == "Log entry 1"
    assert logs[-2]["level"] == "WARNING"
    assert logs[-1]["level"] == "ERROR"


def test_log_entries_structure():
    """Test log entry structure"""
    thread = SimpleThread()
    
    thread.log_write("Test log", "INFO")
    logs = thread.log_get_entries()
    
    assert len(logs) > 0
    last_log = logs[-1]
    
    assert "timestamp" in last_log
    assert "level" in last_log
    assert "message" in last_log
    assert last_log["message"] == "Test log"


def test_log_clear():
    """Test clearing log entries"""
    thread = SimpleThread()
    
    thread.log_write("Log 1")
    thread.log_write("Log 2")
    
    logs_before = thread.log_get_entries()
    assert len(logs_before) > 0
    
    thread.log_clear()
    
    logs_after = thread.log_get_entries()
    assert len(logs_after) == 0


def test_log_maxlen():
    """Test log entries maximum length"""
    thread = SimpleThread()
    
    # Write more than maxlen (500)
    for i in range(600):
        thread.log_write(f"Log {i}")
    
    logs = thread.log_get_entries()
    
    # Should be capped at 500
    assert len(logs) <= 500


# ============================================================================
# CONSOLE DATA TESTS
# ============================================================================

def test_get_console_data():
    """Test getting all console data"""
    thread = SimpleThread()
    
    thread.console_write("Console message")
    thread.log_write("Log message")
    
    data = thread.get_console_data()
    
    assert "console_output" in data
    assert "logs" in data
    assert "process_output" in data
    assert "running" in data
    assert "progress" in data
    assert "error" in data
    
    assert len(data["console_output"]) > 0
    assert len(data["logs"]) > 0


# ============================================================================
# PROGRESS TESTS
# ============================================================================

def test_progress_tracking():
    """Test thread progress tracking"""
    thread = ProgressThread()
    thread.start()
    
    # Wait a bit for progress
    time.sleep(0.3)
    
    # Progress should be updating
    assert thread.m_running_state >= 0
    
    # Wait for completion
    time.sleep(0.5)
    
    # Should reach 100%
    assert thread.m_running_state == 100


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

def test_error_handling():
    """Test thread error handling"""
    thread = ErrorThread()
    thread.start()
    
    # Wait for thread to complete
    time.sleep(0.5)
    
    # Error should be captured
    assert thread.m_error is not None
    assert "Test error message" in thread.m_error
    
    # Console should show error
    output = thread.console_get_output()
    assert any("Thread failed" in line for line in output)


# ============================================================================
# PROCESS COMMUNICATION TESTS
# ============================================================================

def test_process_execution():
    """Test process execution and communication"""
    thread = ProcessThread()
    thread.start()
    
    # Wait for process to complete
    time.sleep(2)
    
    # Console should contain process output
    output = thread.console_get_output()
    assert any("Starting process" in line for line in output)
    assert any("Process output" in line for line in output)


def test_process_close():
    """Test process termination"""
    thread = SimpleThread()
    
    # Start a long-running process that produces output
    if sys.platform == "win32":
        # ping produces continuous output
        thread.process_exec(["ping", "localhost", "-n", "10"], ".", shell=True)
    else:
        # Use a command that produces output to keep reading threads alive
        thread.process_exec(["sh", "-c", "while true; do echo test; sleep 1; done"], ".", shell=True)
    
    # Wait for process to start and reading threads to initialize
    time.sleep(0.3)
    
    # Verify process is running (check the process object, not the flag)
    assert thread.m_process is not None, "Process should be created"
    assert thread.m_process.poll() is None, "Process should still be running"
    
    # Close the process
    thread.process_close()
    time.sleep(0.2)
    
    # After close, process should be None
    assert thread.m_process is None, "Process should be None after close"
    assert not thread.m_process_running, "Flag should be False after close"


# ============================================================================
# THREAD MANAGER TESTS
# ============================================================================

def test_thread_manager_add():
    """Test adding threads to manager"""
    import src.modules.threaded.threaded_manager as tm_module
    manager = tm_module.thread_manager_obj
    
    initial_count = manager.get_thread_count()
    
    thread1 = SimpleThread()
    thread2 = SimpleThread()
    
    # Threads are auto-added in __init__
    assert manager.get_thread_count() == initial_count + 2


def test_thread_manager_get_all():
    """Test getting all threads"""
    import src.modules.threaded.threaded_manager as tm_module
    manager = tm_module.thread_manager_obj
    
    thread1 = SimpleThread()
    thread2 = SimpleThread()
    _ = (thread1, thread2)  # Suppress unused warning
    
    all_threads = manager.get_all_threads()
    
    assert thread1 in all_threads
    assert thread2 in all_threads


def test_thread_manager_get_by_name():
    """Test getting threads by name"""
    import src.modules.threaded.threaded_manager as tm_module
    manager = tm_module.thread_manager_obj
    
    thread1 = SimpleThread()
    thread1.change_name("Thread1")
    
    thread2 = SimpleThread()
    thread2.change_name("Thread2")
    
    found_threads = manager.get_threads_by_name("Thread1")
    
    assert len(found_threads) == 1
    assert found_threads[0].get_name() == "Thread1"


def test_thread_manager_unique_names():
    """Test getting unique thread names"""
    import src.modules.threaded.threaded_manager as tm_module
    manager = tm_module.thread_manager_obj
    
    thread1 = SimpleThread()
    thread2 = SimpleThread()
    thread3 = ProgressThread()
    _ = (thread1, thread2, thread3)  # Suppress unused warning
    
    unique_names = manager.get_unique_names()
    
    assert "SimpleThread" in unique_names
    assert "ProgressThread" in unique_names


def test_thread_manager_stats():
    """Test thread manager statistics"""
    import src.modules.threaded.threaded_manager as tm_module
    manager = tm_module.thread_manager_obj
    
    # Create threads but don't start them (avoid hanging)
    thread1 = SimpleThread()
    thread2 = SimpleThread()
    _ = (thread1, thread2)  # Suppress unused warning
    
    stats = manager.get_thread_stats()
    
    assert "total" in stats
    assert "running" in stats
    assert "with_process" in stats
    assert "with_error" in stats
    assert stats["total"] >= 2
    
    # Cleanup
    manager.del_thread(thread1)
    manager.del_thread(thread2)


def test_thread_manager_delete():
    """Test deleting threads from manager"""
    import src.modules.threaded.threaded_manager as tm_module
    manager = tm_module.thread_manager_obj
    
    thread = SimpleThread()
    count_before = manager.get_thread_count()
    
    manager.del_thread(thread)
    count_after = manager.get_thread_count()
    
    assert count_after == count_before - 1


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_multiple_threads_concurrent():
    """Test multiple threads running concurrently"""
    threads = []
    for i in range(5):
        thread = SimpleThread()
        thread.change_name(f"Thread_{i}")
        thread.start()
        threads.append(thread)
    
    # Wait for all to complete
    time.sleep(1)
    
    # All should have executed
    for thread in threads:
        assert thread.executed


def test_thread_lifecycle():
    """Test complete thread lifecycle"""
    import src.modules.threaded.threaded_manager as tm_module
    manager = tm_module.thread_manager_obj
    
    # Create
    thread = SimpleThread()
    assert not thread.m_running
    
    # Start
    thread.start()
    time.sleep(0.1)
    assert thread.m_running
    
    # Wait for completion
    time.sleep(0.5)
    assert not thread.m_running
    assert thread.executed
    
    # Should be auto-deleted from manager
    time.sleep(0.5)
    all_threads = manager.get_all_threads()
    assert thread not in all_threads


def test_console_during_execution():
    """Test console updates during thread execution"""
    thread = ProgressThread()
    thread.start()
    
    # Check console updates during execution
    time.sleep(0.2)
    output_mid = thread.console_get_output()
    assert len(output_mid) > 0
    
    # Wait for completion
    time.sleep(0.5)
    output_final = thread.console_get_output()
    
    # Should have more messages
    assert len(output_final) > len(output_mid)
    assert any("completed" in line.lower() for line in output_final)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

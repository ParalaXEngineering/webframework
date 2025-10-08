"""
Unit tests for MessageEmitter.

Tests the SocketIO emission logic with mock SocketIO objects.
"""
import pytest
from unittest.mock import Mock, call
from src.modules.scheduler.emitter import MessageEmitter


# Mock logLevel enum for testing
class MockLogLevel:
    def __init__(self, name):
        self.name = name

success = MockLogLevel("success")
info = MockLogLevel("info")
warning = MockLogLevel("warning")
error = MockLogLevel("error")


@pytest.fixture
def mock_socket():
    """Create a mock SocketIO object."""
    return Mock()


@pytest.fixture
def emitter(mock_socket):
    """Create a MessageEmitter with mock socket."""
    return MessageEmitter(mock_socket)


class TestStatusEmission:
    """Test status message emission and filtering."""
    
    def test_emit_empty_status_list(self, emitter, mock_socket):
        """Test that empty status list doesn't emit anything."""
        emitter.emit_status([])
        assert not mock_socket.emit.called
    
    def test_emit_single_status(self, emitter, mock_socket):
        """Test emitting a single status message."""
        statuses = [["cat1", "msg1", 50, ""]]
        
        emitter.emit_status(statuses)
        
        mock_socket.emit.assert_called_once_with(
            "action_status",
            {"cat1": ["msg1", 50, ""]}
        )
    
    def test_emit_multiple_statuses(self, emitter, mock_socket):
        """Test emitting multiple status messages."""
        statuses = [
            ["cat1", "msg1", 50, ""],
            ["cat2", "msg2", 75, "detail"],
            ["cat3", "msg3", 100, ""]
        ]
        
        emitter.emit_status(statuses)
        
        assert mock_socket.emit.call_count == 3
    
    def test_filters_duplicate_statuses(self, emitter, mock_socket):
        """Test that duplicate status messages are filtered."""
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
        """Test that socket errors don't crash the emitter."""
        mock_socket.emit.side_effect = Exception("Socket error")
        
        statuses = [["cat1", "msg1", 50, ""]]
        
        # Should not raise exception
        emitter.emit_status(statuses)
        
        assert mock_socket.emit.called


class TestPopupEmission:
    """Test popup message emission."""
    
    def test_emit_single_popup(self, emitter, mock_socket):
        """Test emitting a single popup."""
        popups = [[info, "Test message"]]
        
        emitter.emit_popups(popups)
        
        mock_socket.emit.assert_called_once_with(
            "popup",
            {"info": "Test message"}
        )
    
    def test_emit_multiple_popups(self, emitter, mock_socket):
        """Test emitting multiple popups."""
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
        """Test error handling for popup emission."""
        mock_socket.emit.side_effect = Exception("Popup error")
        
        popups = [[info, "test"]]
        
        # Should not raise
        emitter.emit_popups(popups)


class TestResultEmission:
    """Test result message emission."""
    
    def test_emit_results(self, emitter, mock_socket):
        """Test emitting result messages."""
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
    """Test modal dialog emission."""
    
    def test_emit_modals(self, emitter, mock_socket):
        """Test emitting modal dialogs."""
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
    """Test button update emission."""
    
    def test_emit_buttons(self, emitter, mock_socket):
        """Test emitting button updates."""
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
    """Test content reload emission."""
    
    def test_emit_reloads(self, emitter, mock_socket):
        """Test emitting reload requests."""
        reloads = [
            ["content1", "<div>New content</div>"],
            ["content2", "<div>Another content</div>"]
        ]
        
        emitter.emit_reloads(reloads)
        
        assert mock_socket.emit.call_count == 2


class TestButtonStateEmission:
    """Test button state changes."""
    
    def test_emit_button_states(self, emitter, mock_socket):
        """Test emitting button enable/disable."""
        disable_list = ["btn1", "btn2"]
        enable_list = ["btn3", "btn4"]
        
        emitter.emit_button_states(disable_list, enable_list)
        
        assert mock_socket.emit.call_count == 2
        mock_socket.emit.assert_any_call("disable_button", ["btn1", "btn2"])
        mock_socket.emit.assert_any_call("enable_button", ["btn3", "btn4"])
    
    def test_emit_empty_button_states(self, emitter, mock_socket):
        """Test that empty lists don't emit."""
        emitter.emit_button_states([], [])
        
        assert not mock_socket.emit.called


class TestThreadEmission:
    """Test thread status emission."""
    
    def test_emit_threads(self, emitter, mock_socket):
        """Test emitting thread status."""
        thread_info = [
            {"name": "worker1", "state": "RUNNING"},
            {"name": "worker2", "state": "IDLE"}
        ]
        
        emitter.emit_threads(thread_info)
        
        mock_socket.emit.assert_called_once_with("threads", thread_info)

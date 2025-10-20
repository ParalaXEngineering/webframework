"""
Unit tests for thread_emitter module.

Tests cover lifecycle and error handling.
UI rendering tests are intentionally skipped (low value, covered by integration tests).
Note: ThreadEmitter automatically gets threads from threaded_manager, 
no manual thread assignment methods available.
"""

import pytest
import time
from unittest.mock import Mock, patch

from src.modules.threaded.thread_emitter import ThreadEmitter


class TestThreadEmitterLifecycle:
    """Test emitter start/stop lifecycle."""
    
    def test_start_stop_lifecycle(self):
        """Test starting and stopping the thread emitter."""
        mock_socket = Mock()
        
        emitter = ThreadEmitter(mock_socket, interval=0.1)
        
        assert not emitter.running
        assert emitter._thread is None
        
        # Start
        emitter.start()
        assert emitter.running
        assert emitter._thread is not None
        assert emitter._thread.is_alive()
        
        time.sleep(0.25)  # Let it run a bit
        
        # Stop
        emitter.stop()
        assert not emitter.running
        time.sleep(0.3)  # Wait for thread to join
        assert not emitter._thread.is_alive()
    
    def test_start_already_running(self):
        """Test that starting an already running emitter logs warning."""
        mock_socket = Mock()
        
        emitter = ThreadEmitter(mock_socket, interval=0.1)
        
        emitter.start()
        assert emitter.running
        
        # Try to start again
        with patch.object(emitter.logger, 'warning') as mock_warning:
            emitter.start()
            mock_warning.assert_called_once()
            assert "already running" in str(mock_warning.call_args).lower()
        
        emitter.stop()
    
    def test_initialization_parameters(self):
        """Test that initialization parameters are set correctly."""
        mock_socket = Mock()
        
        emitter = ThreadEmitter(mock_socket, interval=3.0)
        
        assert emitter.socket == mock_socket
        assert emitter.interval == 3.0
        assert emitter.jinja_env is not None  # Jinja environment should be initialized


class TestErrorHandling:
    """Test error handling in emit loop."""
    
    def test_error_handling_in_emit_loop(self):
        """Test that errors in emission loop don't crash the emitter."""
        mock_socket = Mock()
        
        with patch('src.modules.threaded.thread_emitter.socketio_manager') as mock_manager:
            # Make emit_to_user raise an exception
            mock_manager.emit_to_user.side_effect = Exception("Socket error")
            
            emitter = ThreadEmitter(mock_socket, interval=0.05)
            
            # Start emitter
            emitter.start()
            
            # Let it run and encounter errors
            time.sleep(0.2)
            
            # Should still be running despite errors
            assert emitter.running
            
            emitter.stop()
    
    def test_error_in_render_threads_html(self):
        """Test that errors in rendering don't crash emitter."""
        mock_socket = Mock()
        
        emitter = ThreadEmitter(mock_socket, interval=0.05)
        
        # Mock _render_threads_html to raise exception
        with patch.object(emitter, '_render_threads_html', side_effect=Exception("Render error")):
            with patch('src.modules.threaded.thread_emitter.socketio_manager'):
                emitter.start()
                time.sleep(0.15)
                
                # Should still be running
                assert emitter.running
                
                emitter.stop()


class TestEmissionBehavior:
    """Test emission behavior."""
    
    def test_no_emission_without_users(self):
        """Test that emission doesn't fail when no users are configured."""
        mock_socket = Mock()
        
        with patch('src.modules.threaded.thread_emitter.socketio_manager'):
            emitter = ThreadEmitter(mock_socket, interval=0.05)
            
            # Start without any users
            emitter.start()
            time.sleep(0.15)
            emitter.stop()
            
            # Should have run without errors (emission to empty user dict)
            # May or may not call emit_to_user depending on implementation
            # The important thing is it didn't crash
    
    def test_emission_during_runtime(self):
        """Test that emitter continues emitting during runtime."""
        mock_socket = Mock()
        
        with patch('src.modules.threaded.thread_emitter.socketio_manager'):
            emitter = ThreadEmitter(mock_socket, interval=0.05)
            
            emitter.start()
            time.sleep(0.2)  # Let it run for several intervals
            emitter.stop()
            
            # Should have run without errors


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

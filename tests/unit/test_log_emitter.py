"""
Unit tests for log_emitter module.

Tests cover lifecycle, multi-user live mode, thread-safety, and error handling.
"""

import pytest
import tempfile
import os
import time
import threading
from unittest.mock import Mock, patch

from src.modules.log.log_emitter import LogEmitter


class TestLogEmitterLifecycle:
    """Test emitter start/stop lifecycle."""
    
    def test_start_stop_lifecycle(self):
        """Test starting and stopping the emitter."""
        mock_socket = Mock()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            emitter = LogEmitter(mock_socket, temp_dir, interval=0.1)
            
            assert not emitter.running
            assert emitter._thread is None
            
            # Start
            emitter.start()
            assert emitter.running
            assert emitter._thread is not None
            assert emitter._thread.is_alive()
            
            time.sleep(0.2)  # Let it run a bit
            
            # Stop
            emitter.stop()
            assert not emitter.running
            time.sleep(0.3)  # Wait for thread to join
            assert not emitter._thread.is_alive()
    
    def test_start_already_running(self):
        """Test that starting an already running emitter logs warning."""
        mock_socket = Mock()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            emitter = LogEmitter(mock_socket, temp_dir, interval=0.1)
            
            emitter.start()
            assert emitter.running
            
            # Try to start again
            with patch.object(emitter.logger, 'warning') as mock_warning:
                emitter.start()
                mock_warning.assert_called_once()
                assert "already running" in str(mock_warning.call_args)
            
            emitter.stop()
    
    def test_initialization_parameters(self):
        """Test that initialization parameters are set correctly."""
        mock_socket = Mock()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            emitter = LogEmitter(mock_socket, temp_dir, interval=5.0, max_lines=2000)
            
            assert emitter.socket == mock_socket
            assert emitter.logs_dir == temp_dir
            assert emitter.interval == 5.0
            assert emitter.max_lines == 2000
            assert isinstance(emitter.live_mode_users, set)
            assert len(emitter.live_mode_users) == 0


class TestLiveModeManagement:
    """Test multi-user live mode management."""
    
    def test_set_live_mode_enable(self):
        """Test enabling live mode for a user."""
        mock_socket = Mock()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            emitter = LogEmitter(mock_socket, temp_dir)
            
            emitter.set_live_mode("user1", enabled=True)
            
            assert "user1" in emitter.live_mode_users
            assert emitter.is_live_mode_enabled("user1")
    
    def test_set_live_mode_disable(self):
        """Test disabling live mode for a user."""
        mock_socket = Mock()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            emitter = LogEmitter(mock_socket, temp_dir)
            
            emitter.set_live_mode("user1", enabled=True)
            assert emitter.is_live_mode_enabled("user1")
            
            emitter.set_live_mode("user1", enabled=False)
            
            assert "user1" not in emitter.live_mode_users
            assert not emitter.is_live_mode_enabled("user1")
    
    def test_multiple_users_live_mode(self):
        """Test multiple users with live mode."""
        mock_socket = Mock()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            emitter = LogEmitter(mock_socket, temp_dir)
            
            emitter.set_live_mode("user1", enabled=True)
            emitter.set_live_mode("user2", enabled=True)
            emitter.set_live_mode("user3", enabled=True)
            
            assert len(emitter.live_mode_users) == 3
            assert emitter.is_live_mode_enabled("user1")
            assert emitter.is_live_mode_enabled("user2")
            assert emitter.is_live_mode_enabled("user3")
            
            emitter.set_live_mode("user2", enabled=False)
            
            assert len(emitter.live_mode_users) == 2
            assert not emitter.is_live_mode_enabled("user2")
    
    def test_is_live_mode_enabled_unknown_user(self):
        """Test checking live mode for user who hasn't enabled it."""
        mock_socket = Mock()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            emitter = LogEmitter(mock_socket, temp_dir)
            
            assert not emitter.is_live_mode_enabled("unknown_user")


class TestThreadSafety:
    """Test thread-safe operations on live_mode_users."""
    
    def test_concurrent_live_mode_access(self):
        """Test that multiple threads can safely access live_mode_users."""
        mock_socket = Mock()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            emitter = LogEmitter(mock_socket, temp_dir)
            
            def enable_for_users(start_idx, count):
                for i in range(start_idx, start_idx + count):
                    emitter.set_live_mode(f"user{i}", enabled=True)
            
            # Create multiple threads enabling live mode
            threads = []
            for i in range(5):
                thread = threading.Thread(target=enable_for_users, args=(i*10, 10))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads
            for thread in threads:
                thread.join()
            
            # Should have 50 users
            assert len(emitter.live_mode_users) == 50
    
    def test_thread_safe_emit_with_live_mode_changes(self):
        """Test that emission continues safely while live mode changes."""
        mock_socket = Mock()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test log file
            log_file = os.path.join(temp_dir, "test.log")
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write("2024-01-15 10:30:00,000 - INFO - test - test.py:1 - Test message\n")
            
            with patch('src.modules.log.log_emitter.socketio_manager') as mock_manager:
                emitter = LogEmitter(mock_socket, temp_dir, interval=0.05)
                
                # Enable live mode for user1
                emitter.set_live_mode("user1", enabled=True)
                
                # Start emitter
                emitter.start()
                
                time.sleep(0.15)  # Let it emit a few times
                
                # Disable and enable users while emitting
                emitter.set_live_mode("user1", enabled=False)
                emitter.set_live_mode("user2", enabled=True)
                
                time.sleep(0.15)
                
                emitter.stop()
                
                # Should have emitted without errors
                assert mock_manager.emit_to_user.called


class TestGetLogData:
    """Test getting structured log data."""
    
    def test_get_log_data_valid_logs(self):
        """Test getting log data from valid log files."""
        mock_socket = Mock()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test log files
            log1 = os.path.join(temp_dir, "app.log")
            with open(log1, 'w', encoding='utf-8') as f:
                f.write("2024-01-15 10:30:00,000 - INFO - test - test.py:1 - Message 1\n")
                f.write("2024-01-15 10:30:01,000 - ERROR - test - test.py:2 - Message 2\n")
            
            log2 = os.path.join(temp_dir, "debug.log")
            with open(log2, 'w', encoding='utf-8') as f:
                f.write("2024-01-15 10:30:02,000 - DEBUG - test - test.py:3 - Message 3\n")
            
            emitter = LogEmitter(mock_socket, temp_dir)
            
            data = emitter.get_log_data(max_lines_per_file=50)
            
            assert 'files' in data
            assert len(data['files']) == 2
            
            # Check files are sorted
            assert data['files'][0]['name'] == 'app.log'
            assert data['files'][1]['name'] == 'debug.log'
            
            # Check entries
            assert len(data['files'][0]['entries']) == 2
            assert len(data['files'][1]['entries']) == 1
    
    def test_get_log_data_nonexistent_directory(self):
        """Test getting log data when directory doesn't exist."""
        mock_socket = Mock()
        
        emitter = LogEmitter(mock_socket, "/nonexistent/directory")
        
        data = emitter.get_log_data()
        
        assert 'error' in data
        assert 'not found' in data['error'].lower()
    
    def test_get_log_data_no_log_files(self):
        """Test getting log data when no .log files exist."""
        mock_socket = Mock()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create non-log file
            txt_file = os.path.join(temp_dir, "readme.txt")
            with open(txt_file, 'w') as f:
                f.write("Not a log file")
            
            emitter = LogEmitter(mock_socket, temp_dir)
            
            data = emitter.get_log_data()
            
            assert 'files' in data
            assert len(data['files']) == 0


class TestLogFileParsing:
    """Test log file reading and parsing."""
    
    def test_parse_standard_log_line(self):
        """Test parsing standard log format."""
        mock_socket = Mock()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            emitter = LogEmitter(mock_socket, temp_dir)
            
            line = "2025-10-09 15:45:54,146 - INFO - log.emitter - log_emitter.py:53 - Log emitter started"
            
            parsed = emitter._parse_log_line(line)
            
            assert parsed['timestamp'] == '2025-10-09 15:45:54,146'
            assert parsed['level'] == 'INFO'
            assert parsed['file_line'] == 'log_emitter.py:53'
            assert parsed['message'] == 'Log emitter started'
    
    def test_parse_log_line_fallback_format(self):
        """Test parsing log line with fallback format (no file:line)."""
        mock_socket = Mock()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            emitter = LogEmitter(mock_socket, temp_dir)
            
            line = "2024-01-15 10:30:45,123 - ERROR - Something went wrong"
            
            parsed = emitter._parse_log_line(line)
            
            assert parsed['timestamp'] == '2024-01-15 10:30:45,123'
            assert parsed['level'] == 'ERROR'
            assert parsed['file_line'] == ''
            assert 'Something went wrong' in parsed['message']
    
    def test_parse_malformed_log_line(self):
        """Test parsing malformed log line."""
        mock_socket = Mock()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            emitter = LogEmitter(mock_socket, temp_dir)
            
            line = "Random text without proper format"
            
            parsed = emitter._parse_log_line(line)
            
            # Should still parse with defaults
            assert parsed['level'] == 'INFO'
            assert parsed['message'] == line.strip()
            assert parsed['timestamp'] == ''
    
    def test_read_and_parse_log_file(self):
        """Test reading and parsing a complete log file."""
        mock_socket = Mock()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "test.log")
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write("2024-01-15 10:30:00,000 - INFO - test - test.py:1 - Line 1\n")
                f.write("2024-01-15 10:30:01,000 - ERROR - test - test.py:2 - Line 2\n")
                f.write("2024-01-15 10:30:02,000 - DEBUG - test - test.py:3 - Line 3\n")
            
            emitter = LogEmitter(mock_socket, temp_dir)
            
            entries = emitter._read_and_parse_log_file(log_file, max_lines=10)
            
            assert len(entries) == 3
            assert entries[0]['level'] == 'INFO'
            assert entries[1]['level'] == 'ERROR'
            assert entries[2]['level'] == 'DEBUG'
    
    def test_read_and_parse_with_max_lines(self):
        """Test that max_lines parameter limits output."""
        mock_socket = Mock()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "test.log")
            with open(log_file, 'w', encoding='utf-8') as f:
                for i in range(100):
                    f.write(f"2024-01-15 10:30:{i:02d},000 - INFO - test - test.py:{i} - Line {i}\n")
            
            emitter = LogEmitter(mock_socket, temp_dir)
            
            entries = emitter._read_and_parse_log_file(log_file, max_lines=10)
            
            assert len(entries) == 10
            # Should get last 10 lines
            assert 'Line 90' in entries[0]['message']
            assert 'Line 99' in entries[-1]['message']


class TestEmissionBehavior:
    """Test emission behavior with live mode."""
    
    def test_no_emission_without_live_users(self):
        """Test that no emission occurs when no users have live mode enabled."""
        mock_socket = Mock()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test log file
            log_file = os.path.join(temp_dir, "test.log")
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write("2024-01-15 10:30:00,000 - INFO - test - test.py:1 - Test\n")
            
            with patch('src.modules.log.log_emitter.socketio_manager') as mock_manager:
                emitter = LogEmitter(mock_socket, temp_dir, interval=0.05)
                
                # Start without any live users
                emitter.start()
                time.sleep(0.15)  # Let it run for 3 intervals
                emitter.stop()
                
                # Should NOT have emitted (no live users)
                assert not mock_manager.emit_to_user.called
    
    def test_emission_to_live_users_only(self):
        """Test that emission only goes to users with live mode enabled."""
        mock_socket = Mock()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test log file
            log_file = os.path.join(temp_dir, "test.log")
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write("2024-01-15 10:30:00,000 - INFO - test - test.py:1 - Test\n")
            
            with patch('src.modules.log.log_emitter.socketio_manager') as mock_manager:
                emitter = LogEmitter(mock_socket, temp_dir, interval=0.05)
                
                # Enable live mode for user1 only
                emitter.set_live_mode("user1", enabled=True)
                
                emitter.start()
                time.sleep(0.15)  # Let it emit
                emitter.stop()
                
                # Should have emitted to user1
                assert mock_manager.emit_to_user.called
                
                # Check that it was called with user1
                call_args_list = mock_manager.emit_to_user.call_args_list
                assert len(call_args_list) > 0
                
                # Verify all calls were to user1
                for call in call_args_list:
                    args, kwargs = call
                    assert kwargs.get('username') == 'user1' or (len(args) >= 3 and args[2] == 'user1')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

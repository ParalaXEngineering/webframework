"""
Unit tests for log_parser module.

Tests cover log file reading, parsing, level extraction, and filtering.
Pure business logic with no external dependencies.
"""

import pytest
import tempfile
import os

from src.modules.log.log_parser import (
    read_log_file,
    parse_log_lines,
    filter_logs_by_level,
    _extract_log_level
)


class TestReadLogFile:
    """Test reading log files."""
    
    def test_read_valid_log_file(self):
        """Test reading a valid log file."""
        # Create temporary log file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False, encoding='utf-8') as f:
            f.write("2024-01-15 10:30:00 INFO Starting application\n")
            f.write("2024-01-15 10:30:01 DEBUG Initialization complete\n")
            f.write("2024-01-15 10:30:02 WARNING Low memory\n")
            temp_path = f.name
        
        try:
            lines = read_log_file(temp_path)
            
            assert len(lines) == 3
            assert "INFO Starting application" in lines[0]
            assert "DEBUG Initialization complete" in lines[1]
            assert "WARNING Low memory" in lines[2]
        finally:
            os.unlink(temp_path)
    
    def test_read_with_max_lines(self):
        """Test that max_lines parameter limits output."""
        # Create log file with many lines
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False, encoding='utf-8') as f:
            for i in range(100):
                f.write(f"2024-01-15 10:30:{i:02d} INFO Line {i}\n")
            temp_path = f.name
        
        try:
            lines = read_log_file(temp_path, max_lines=10)
            
            assert len(lines) == 10
            # Should get the LAST 10 lines
            assert "Line 90" in lines[0]
            assert "Line 99" in lines[-1]
        finally:
            os.unlink(temp_path)
    
    def test_read_small_file(self):
        """Test reading file smaller than max_lines."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False, encoding='utf-8') as f:
            f.write("2024-01-15 10:30:00 INFO Line 1\n")
            f.write("2024-01-15 10:30:01 INFO Line 2\n")
            temp_path = f.name
        
        try:
            lines = read_log_file(temp_path, max_lines=100)
            
            assert len(lines) == 2
        finally:
            os.unlink(temp_path)
    
    def test_read_nonexistent_file(self):
        """Test reading a file that doesn't exist."""
        lines = read_log_file("/nonexistent/path/file.log")
        
        assert len(lines) == 1
        assert "Log file not found" in lines[0]
    
    def test_read_empty_file(self):
        """Test reading an empty log file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False, encoding='utf-8') as f:
            temp_path = f.name
        
        try:
            lines = read_log_file(temp_path)
            assert len(lines) == 0
        finally:
            os.unlink(temp_path)


class TestParseLogLines:
    """Test parsing of log lines."""
    
    def test_parse_standard_format(self):
        """Test parsing standard log format."""
        lines = [
            "2024-01-15 10:30:00 INFO Starting application",
            "2024-01-15 10:30:01 ERROR Failed to connect",
            "2024-01-15 10:30:02 WARNING Low disk space"
        ]
        
        parsed = parse_log_lines(lines)
        
        assert len(parsed) == 3
        assert parsed[0]['level'] == 'INFO'
        assert parsed[0]['message'] == 'INFO Starting application'
        assert '2024-01-15' in parsed[0]['timestamp']
        
        assert parsed[1]['level'] == 'ERROR'
        assert 'Failed to connect' in parsed[1]['message']
        
        assert parsed[2]['level'] == 'WARNING'
        assert 'Low disk space' in parsed[2]['message']
    
    def test_parse_with_multiword_message(self):
        """Test parsing logs with complex messages."""
        lines = [
            "2024-01-15 10:30:00 INFO User admin logged in from 192.168.1.1"
        ]
        
        parsed = parse_log_lines(lines)
        
        assert len(parsed) == 1
        assert parsed[0]['level'] == 'INFO'
        assert 'User admin logged in from 192.168.1.1' in parsed[0]['message']
    
    def test_parse_empty_lines(self):
        """Test that empty lines are skipped."""
        lines = [
            "2024-01-15 10:30:00 INFO Test",
            "",
            "   ",
            "2024-01-15 10:30:01 DEBUG Another test"
        ]
        
        parsed = parse_log_lines(lines)
        
        # Should skip empty/whitespace lines
        assert len(parsed) == 2
        assert parsed[0]['level'] == 'INFO'
        assert parsed[1]['level'] == 'DEBUG'
    
    def test_parse_malformed_lines(self):
        """Test parsing malformed log lines."""
        lines = [
            "Random text without timestamp",
            "Just a message",
            "OK"
        ]
        
        parsed = parse_log_lines(lines)
        
        assert len(parsed) == 3
        # Should still parse but with UNKNOWN level
        assert parsed[0]['level'] == 'UNKNOWN'
        assert 'Random' in parsed[0]['message'] or 'without timestamp' in parsed[0]['message']
        assert parsed[0]['raw'] == 'Random text without timestamp'
    
    def test_parse_preserves_raw_line(self):
        """Test that raw line is preserved."""
        lines = ["2024-01-15 10:30:00 INFO Test message"]
        
        parsed = parse_log_lines(lines)
        
        assert parsed[0]['raw'] == lines[0]
    
    def test_parse_different_log_levels(self):
        """Test parsing all standard log levels."""
        lines = [
            "2024-01-15 10:30:00 DEBUG Debug message",
            "2024-01-15 10:30:01 INFO Info message",
            "2024-01-15 10:30:02 WARNING Warning message",
            "2024-01-15 10:30:03 ERROR Error message",
            "2024-01-15 10:30:04 CRITICAL Critical message",
            "2024-01-15 10:30:05 FATAL Fatal message"
        ]
        
        parsed = parse_log_lines(lines)
        
        assert parsed[0]['level'] == 'DEBUG'
        assert parsed[1]['level'] == 'INFO'
        assert parsed[2]['level'] == 'WARNING'
        assert parsed[3]['level'] == 'ERROR'
        assert parsed[4]['level'] == 'CRITICAL'
        assert parsed[5]['level'] == 'FATAL'


class TestExtractLogLevel:
    """Test log level extraction."""
    
    def test_extract_info(self):
        """Test extracting INFO level."""
        assert _extract_log_level("2024-01-15 10:30:00 INFO Message") == 'INFO'
        assert _extract_log_level("INFO: This is info") == 'INFO'
        assert _extract_log_level("info message") == 'INFO'  # Case insensitive
    
    def test_extract_warning(self):
        """Test extracting WARNING level."""
        assert _extract_log_level("2024-01-15 10:30:00 WARNING Message") == 'WARNING'
        assert _extract_log_level("WARN: Something") == 'WARN'
    
    def test_extract_error(self):
        """Test extracting ERROR level."""
        assert _extract_log_level("2024-01-15 10:30:00 ERROR Message") == 'ERROR'
        assert _extract_log_level("ERROR: Failed") == 'ERROR'
    
    def test_extract_debug(self):
        """Test extracting DEBUG level."""
        assert _extract_log_level("2024-01-15 10:30:00 DEBUG Message") == 'DEBUG'
    
    def test_extract_critical(self):
        """Test extracting CRITICAL level."""
        assert _extract_log_level("2024-01-15 10:30:00 CRITICAL Message") == 'CRITICAL'
    
    def test_extract_fatal(self):
        """Test extracting FATAL level."""
        assert _extract_log_level("2024-01-15 10:30:00 FATAL Message") == 'FATAL'
    
    def test_extract_unknown(self):
        """Test that lines without level return UNKNOWN."""
        assert _extract_log_level("Random text") == 'UNKNOWN'
        assert _extract_log_level("2024-01-15 10:30:00 Message") == 'UNKNOWN'
    
    def test_extract_case_insensitive(self):
        """Test that extraction is case insensitive."""
        assert _extract_log_level("error: something bad") == 'ERROR'
        assert _extract_log_level("Info: all good") == 'INFO'


class TestFilterLogsByLevel:
    """Test filtering logs by level."""
    
    def test_filter_by_error(self):
        """Test filtering ERROR logs."""
        parsed_logs = [
            {'level': 'INFO', 'message': 'Info 1'},
            {'level': 'ERROR', 'message': 'Error 1'},
            {'level': 'WARNING', 'message': 'Warning 1'},
            {'level': 'ERROR', 'message': 'Error 2'},
            {'level': 'INFO', 'message': 'Info 2'}
        ]
        
        errors = filter_logs_by_level(parsed_logs, 'ERROR')
        
        assert len(errors) == 2
        assert errors[0]['message'] == 'Error 1'
        assert errors[1]['message'] == 'Error 2'
    
    def test_filter_by_info(self):
        """Test filtering INFO logs."""
        parsed_logs = [
            {'level': 'INFO', 'message': 'Info 1'},
            {'level': 'ERROR', 'message': 'Error 1'},
            {'level': 'INFO', 'message': 'Info 2'}
        ]
        
        infos = filter_logs_by_level(parsed_logs, 'INFO')
        
        assert len(infos) == 2
    
    def test_filter_case_insensitive(self):
        """Test that filtering is case insensitive."""
        parsed_logs = [
            {'level': 'ERROR', 'message': 'Error 1'},
            {'level': 'INFO', 'message': 'Info 1'}
        ]
        
        errors = filter_logs_by_level(parsed_logs, 'error')  # lowercase
        
        assert len(errors) == 1
        assert errors[0]['message'] == 'Error 1'
    
    def test_filter_no_matches(self):
        """Test filtering with no matches."""
        parsed_logs = [
            {'level': 'INFO', 'message': 'Info 1'},
            {'level': 'WARNING', 'message': 'Warning 1'}
        ]
        
        errors = filter_logs_by_level(parsed_logs, 'ERROR')
        
        assert len(errors) == 0
    
    def test_filter_empty_list(self):
        """Test filtering empty list."""
        errors = filter_logs_by_level([], 'ERROR')
        
        assert len(errors) == 0


class TestIntegration:
    """Integration tests combining multiple functions."""
    
    def test_full_workflow(self):
        """Test complete workflow: read -> parse -> filter."""
        # Create temp log file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False, encoding='utf-8') as f:
            f.write("2024-01-15 10:30:00 INFO Application started\n")
            f.write("2024-01-15 10:30:01 ERROR Database connection failed\n")
            f.write("2024-01-15 10:30:02 WARNING Memory usage high\n")
            f.write("2024-01-15 10:30:03 ERROR File not found\n")
            f.write("2024-01-15 10:30:04 INFO Processing complete\n")
            temp_path = f.name
        
        try:
            # Read
            lines = read_log_file(temp_path)
            assert len(lines) == 5
            
            # Parse
            parsed = parse_log_lines(lines)
            assert len(parsed) == 5
            
            # Filter errors
            errors = filter_logs_by_level(parsed, 'ERROR')
            assert len(errors) == 2
            assert 'Database connection failed' in errors[0]['message']
            assert 'File not found' in errors[1]['message']
            
            # Filter info
            infos = filter_logs_by_level(parsed, 'INFO')
            assert len(infos) == 2
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

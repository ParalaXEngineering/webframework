"""Utility module for logging configuration"""
import logging
import logging.config
import os
import socket
import configparser
import tempfile


def setup_logging():
    """Configure logging with appropriate paths based on on_target status"""
    # Determine log path based on on_target status
    hostname = socket.gethostname()
    on_target = "al70x" in hostname
    
    if on_target:
        website_log = "/tmp/website.log"
        root_log = "/tmp/root.log"
    else:
        website_log = "website.log"
        root_log = "root.log"
    
    # Configure logging with dynamic log paths
    config = configparser.ConfigParser()
    config.read("submodules/framework/log_config.ini")
    
    # Update log file paths - need to escape backslashes for Windows paths
    config.set('handler_fileHandlerWebsite', 'args', f"(r'{website_log}', 'W0', 1)")
    config.set('handler_fileHandlerRoot', 'args', f"(r'{root_log}', 'W0', 1)")
    
    # Write temporary config
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.ini') as tmp_config:
        config.write(tmp_config)
        tmp_config_path = tmp_config.name
    
    # Load the modified config
    logging.config.fileConfig(tmp_config_path)
    
    # Clean up temporary file
    try:
        os.unlink(tmp_config_path)
    except:
        pass

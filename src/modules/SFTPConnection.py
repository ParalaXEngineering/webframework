"""SFTP connection manager for remote file operations.

Provides a client for establishing SFTP connections and performing operations
such as uploading, downloading, and managing remote directories.
"""

import logging
import os
import stat
import socket

import paramiko

try:
    from .log.logger_factory import get_logger
except ImportError:
    from log.logger_factory import get_logger

logger = get_logger(__name__)

# Suppress verbose paramiko logging
logging.getLogger("paramiko").setLevel(logging.WARNING)

class SFTPConnection:
    """SFTP connection client for remote file operations.
    
    Manages connection lifecycle and provides methods for uploading, downloading,
    and managing remote directories over SFTP protocol.
    """

    def __init__(self, host, username, password, port=22):
        """Initialize SFTP connection parameters.
        
        Args:
            host: Remote SFTP server hostname or IP address.
            username: Authentication username.
            password: Authentication password.
            port: SFTP port (default: 22).
        """
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.transport = None
        self.sftp = None

    def connect(self):
        """Establish SFTP connection if not already active."""
        if self.sftp is not None:
            return  # Already connected

        try:
            # Create socket with connection timeout
            sock = socket.create_connection((self.host, self.port), timeout=0.5)

            # Create transport and connect
            self.transport = paramiko.Transport(sock)
            self.transport.connect(username=self.username, password=self.password)

            # Create SFTP client from transport
            self.sftp = paramiko.SFTPClient.from_transport(self.transport)
        except Exception as e:
            logger.debug("SFTP connection failed for %s:%s - %s", self.host, self.port, e)
            self.sftp = None

    def listdir(self, remote_path):
        """List files in a remote directory.
        
        Args:
            remote_path: Path to remote directory.
        
        Returns:
            List of filenames, or empty list on error.
        """
        self.connect()
        if self.sftp:
            try:
                return self.sftp.listdir(remote_path)
            except FileNotFoundError:
                logger.debug("Remote directory not found: %s", remote_path)
                return []
        return []

    def download_file(self, remote_path, local_path):
        """Download a file from remote SFTP server.
        
        Args:
            remote_path: Path to remote file.
            local_path: Path to save file locally.
        """
        self.connect()
        if self.sftp:
            try:
                self.sftp.get(remote_path, local_path)
            except Exception as e:
                logger.error("Failed to download %s: %s", remote_path, e)

    def upload_file(self, local_path, remote_path):
        """Upload a file to remote SFTP server.
        
        Args:
            local_path: Path to local file to upload.
            remote_path: Destination path on remote server.
        """
        self.connect()
        if self.sftp:
            try:
                self.sftp.put(local_path, remote_path)
            except Exception as e:
                logger.error("Failed to upload %s to %s: %s", local_path, remote_path, e)

    def mkdir(self, remote_path):
        """Create a remote directory if it doesn't exist.
        
        Args:
            remote_path: Path to create on remote server.
        """
        self.connect()
        if self.sftp:
            try:
                self.sftp.mkdir(remote_path)
            except OSError:
                # Directory already exists or permission denied
                logger.debug("Cannot create directory (may already exist): %s", remote_path)

    def close(self):
        """Close SFTP connection cleanly."""
        if self.sftp:
            self.sftp.close()
            self.sftp = None
        if self.transport:
            self.transport.close()
            self.transport = None

    def exists(self, remote_path):
        """Check if a file or directory exists on remote server.
        
        Args:
            remote_path: Path to check on remote server.
        
        Returns:
            True if path exists, False otherwise.
        """
        self.connect()
        if self.sftp:
            try:
                self.sftp.stat(remote_path)
                return True
            except FileNotFoundError:
                return False
            except Exception as e:
                logger.error("Failed to check existence of %s: %s", remote_path, e)
                return False
        return False

    def download_dir(self, remote_dir, local_dir):
        """Recursively download a directory from remote SFTP server.
        
        Args:
            remote_dir: Path to remote directory.
            local_dir: Local destination directory.
        """
        self.connect()
        if self.sftp is None:
            return

        os.makedirs(local_dir, exist_ok=True)

        for item in self.sftp.listdir_attr(remote_dir):
            remote_path = f"{remote_dir}/{item.filename}"
            local_path = os.path.join(local_dir, item.filename)

            if item.st_mode and stat.S_ISDIR(item.st_mode):
                self.download_dir(remote_path, local_path)
            else:
                try:
                    self.sftp.get(remote_path, local_path)
                except Exception as e:
                    logger.error("Failed to download %s: %s", remote_path, e)
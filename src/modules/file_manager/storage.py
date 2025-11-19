"""
Content-Addressable File Storage - hashfs wrapper for deduplication.

This module provides a wrapper around hashfs library to enable content-addressable
storage with automatic deduplication. Files are stored by their SHA256 hash, so
identical files are only stored once regardless of how many times they're uploaded.
"""

from hashfs import HashFS
from pathlib import Path
from typing import Dict, BinaryIO
import hashlib
from io import BytesIO

try:
    from ..log.logger_factory import get_logger
except ImportError:
    from log.logger_factory import get_logger

logger = get_logger("file_manager.storage")


class ContentAddressableStorage:
    """Wrapper for hashfs library providing content-addressable file storage.
    
    This class implements deduplication by storing files based on their content hash.
    Multiple uploads of the same file will reference the same physical storage.
    
    Attributes:
        fs: HashFS instance managing the storage
        storage_path: Root path for hash-based storage
    """
    
    def __init__(self, storage_path: Path):
        """Initialize content-addressable storage.
        
        Args:
            storage_path: Root directory for hash-based file storage
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize HashFS with 2-level deep, 2-character wide directory structure
        # Example: abc123... -> ab/c1/abc123...
        self.fs = HashFS(
            str(self.storage_path),
            depth=2,       # Directory nesting depth
            width=2,       # Characters per directory level
            algorithm='sha256'  # Hash algorithm
        )
        
        logger.info(f"Initialized content-addressable storage at {storage_path}")
    
    def store(self, file_stream: BinaryIO, original_filename: str = None) -> Dict[str, str]:
        """Store file content and return storage metadata.
        
        Files are stored by their content hash. If the same content already exists,
        the existing file is reused (deduplication).
        
        Args:
            file_stream: Binary file stream to store
            original_filename: Original filename (for reference, not used in storage path)
            
        Returns:
            Dictionary with storage metadata::
            
                {
                    'checksum': SHA256 hash of content,
                    'storage_path': Relative path in hashfs (e.g., 'ab/c1/abc123...'),
                    'abspath': Absolute filesystem path,
                    'size': File size in bytes,
                    'is_duplicate': True if file already existed (deduplication occurred)
                }
        """
        # Read file content
        file_stream.seek(0)
        content = file_stream.read()
        
        # Calculate checksum
        checksum = hashlib.sha256(content).hexdigest()
        
        # Check if file already exists (deduplication check)
        is_duplicate = False
        address = None
        
        if self.fs.exists(checksum):
            # File already exists, get its address
            is_duplicate = True
            address = self.fs.get(checksum)
            logger.debug(f"File already exists (deduplication): {checksum[:16]}...")
        else:
            # File doesn't exist, store it
            address = self.fs.put(BytesIO(content))
            logger.debug(f"Stored new file: {checksum[:16]}...")
        
        return {
            'checksum': checksum,
            'storage_path': address.relpath,
            'abspath': address.abspath,
            'size': len(content),
            'is_duplicate': is_duplicate
        }
    
    def get(self, storage_path: str) -> Path:
        """Retrieve absolute path for a file by its storage path.
        
        Args:
            storage_path: Relative path in hashfs (from store() return value)
            
        Returns:
            Absolute Path object to the file
            
        Raises:
            IOError: File not found
        """
        # hashfs stores files by hash, but we can reconstruct the path
        abs_path = self.storage_path / storage_path
        
        if not abs_path.exists():
            raise IOError(f"File not found in storage: {storage_path}")
        
        return abs_path
    
    def get_by_checksum(self, checksum: str) -> Path:
        """Retrieve file by its content checksum.
        
        Args:
            checksum: SHA256 hash of file content
            
        Returns:
            Absolute Path object to the file
            
        Raises:
            IOError: File not found
        """
        address = self.fs.get(checksum)
        return Path(address.abspath)
    
    def exists(self, checksum: str) -> bool:
        """Check if a file with given checksum exists in storage.
        
        Args:
            checksum: SHA256 hash to check
            
        Returns:
            True if file exists, False otherwise
        """
        try:
            self.fs.get(checksum)
            return True
        except IOError:
            return False
    
    def delete(self, storage_path: str) -> bool:
        """Delete a file from storage.
        
        Note: This should be used carefully in a deduplicated system, as multiple
        database records may reference the same physical file. The FileManager
        should handle reference counting.
        
        Args:
            storage_path: Relative path in hashfs
            
        Returns:
            True if deleted, False if file didn't exist
        """
        try:
            abs_path = self.get(storage_path)
            abs_path.unlink()
            logger.debug(f"Deleted file: {storage_path}")
            return True
        except (IOError, FileNotFoundError):
            logger.warning(f"Attempted to delete non-existent file: {storage_path}")
            return False
    
    def calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum for a file.
        
        Args:
            file_path: Path to file
            
        Returns:
            SHA256 hash as hex string
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            # Read file in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

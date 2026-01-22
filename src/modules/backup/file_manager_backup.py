"""
File Manager Backup Module

Handles backup and restore operations for the File Manager component,
including the SQLite database and HashFS storage.
"""

import zipfile
from pathlib import Path
from typing import Dict, Optional, Tuple

from src.modules.log.logger_factory import get_logger

logger = get_logger(__name__)


def get_file_manager_info() -> Tuple[Optional[Path], Optional[Path]]:
    """Get file manager database and storage paths.
    
    Returns:
        Tuple: (db_path, hashfs_path) or (None, None) if not available
    """
    try:
        from src.pages import file_handler
        
        if file_handler.file_manager is None:
            logger.warning("File manager not initialized")
            return None, None
        
        fm = file_handler.file_manager
        db_path = Path(fm.db_path)
        hashfs_path = Path(fm.hashfs_path)
        
        if not db_path.exists():
            logger.warning(f"File manager DB not found: {db_path}")
            return None, None
            
        return db_path, hashfs_path
        
    except Exception as e:
        logger.warning(f"Could not access file manager: {e}")
        return None, None


def calculate_directory_size(path: Path) -> int:
    """Calculate total size of a directory recursively.
    
    Args:
        path: Directory path
        
    Returns:
        int: Total size in bytes
    """
    total = 0
    try:
        for entry in path.rglob('*'):
            if entry.is_file():
                total += entry.stat().st_size
    except Exception as e:
        logger.warning(f"Error calculating directory size {path}: {e}")
    return total


def calculate_file_manager_size() -> Tuple[int, int, int]:
    """Calculate file manager database and storage size.
    
    Returns:
        Tuple: (db_size, files_size, total_size) in bytes
    """
    db_path, hashfs_path = get_file_manager_info()
    
    if db_path is None:
        return 0, 0, 0
    
    db_size = db_path.stat().st_size if db_path.exists() else 0
    files_size = calculate_directory_size(hashfs_path) if hashfs_path and hashfs_path.exists() else 0
    
    return db_size, files_size, db_size + files_size


def count_uploaded_files() -> int:
    """Count number of uploaded files in file manager.
    
    Returns:
        int: Number of files
    """
    try:
        from src.pages import file_handler
        from src.modules.file_manager.models import FileVersion
        
        if file_handler.file_manager is None:
            return 0
        
        # Count current file versions in database using SQLAlchemy
        count = file_handler.file_manager.db_session.query(FileVersion).filter(
            FileVersion.is_current == True
        ).count()
        
        return count
        
    except Exception as e:
        logger.warning(f"Could not count files: {e}")
        return 0


def backup_file_manager(zipf: zipfile.ZipFile) -> Dict:
    """Add file manager to an open ZIP file.
    
    Args:
        zipf: Open ZipFile in write mode
        
    Returns:
        Dict: Metadata about backed up files (file_count, files_size_mb, etc.)
    """
    metadata = {
        "file_count": 0,
        "files_size_mb": 0.0,
    }
    
    db_path, hashfs_path = get_file_manager_info()
    
    if db_path and db_path.exists():
        logger.info("Including file manager in backup")
        
        # Add file manager database
        zipf.write(db_path, "file_manager/.file_metadata.db")
        
        # Add hashfs files
        if hashfs_path and hashfs_path.exists():
            for file_path in hashfs_path.rglob('*'):
                if file_path.is_file():
                    # Preserve directory structure within hashfs
                    rel_path = file_path.relative_to(hashfs_path.parent)
                    zipf.write(file_path, f"file_manager/{rel_path}")
        
        # Update metadata with file counts
        metadata["file_count"] = count_uploaded_files()
        db_size, files_size, total_size = calculate_file_manager_size()
        metadata["files_size_mb"] = round(total_size / (1024 * 1024), 2)
    else:
        logger.warning("File manager not available, skipping")
    
    return metadata


def restore_file_manager(temp_dir: Path) -> bool:
    """Restore file manager from extracted backup directory.
    
    Args:
        temp_dir: Directory containing extracted backup
        
    Returns:
        bool: True if successful, False otherwise
    """
    import shutil
    
    file_manager_dir = temp_dir / "file_manager"
    
    if not file_manager_dir.exists():
        logger.info("No file manager data in backup")
        return False
    
    logger.info("Restoring file manager")
    db_path_fm, hashfs_path = get_file_manager_info()
    
    if not db_path_fm or not hashfs_path:
        logger.warning("File manager not available, skipping file restore")
        return False
    
    # Restore file manager database
    fm_db_backup = file_manager_dir / ".file_metadata.db"
    if fm_db_backup.exists():
        # Backup current file manager DB
        if db_path_fm.exists():
            backup_fm_db = db_path_fm.with_suffix('.db.bak')
            shutil.copy2(db_path_fm, backup_fm_db)
            logger.info(f"Backed up current file manager DB to {backup_fm_db}")
        
        shutil.copy2(fm_db_backup, db_path_fm)
        logger.info("File manager database restored")
    
    # Restore hashfs files
    hashfs_backup = file_manager_dir / "hashfs"
    if hashfs_backup.exists():
        # Backup current hashfs
        if hashfs_path.exists():
            backup_hashfs = hashfs_path.parent / "hashfs.bak"
            if backup_hashfs.exists():
                shutil.rmtree(backup_hashfs)
            shutil.copytree(hashfs_path, backup_hashfs)
            logger.info(f"Backed up current hashfs to {backup_hashfs}")
            
            # Clear current hashfs
            shutil.rmtree(hashfs_path)
        
        # Restore from backup
        shutil.copytree(hashfs_backup, hashfs_path)
        logger.info("HashFS storage restored")
    
    return True

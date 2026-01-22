"""
Configuration Backup Module

Handles backup and restore operations for configuration files.
"""

import hashlib
import shutil
import zipfile
from pathlib import Path
from typing import Dict, Optional

from src.modules.log.logger_factory import get_logger

logger = get_logger(__name__)


def get_project_root() -> Path:
    """Get the project root directory.
    
    Returns:
        Path: Project root path (where main.py is)
    """
    return Path(__file__).parent.parent.parent.parent.parent.parent


def get_config_path() -> Path:
    """Get the website config.json path.
    
    Returns:
        Path: Config file path
    """
    return get_project_root() / "website" / "config.json"


def backup_config(zipf: zipfile.ZipFile) -> Dict:
    """Add configuration file to an open ZIP file.
    
    Args:
        zipf: Open ZipFile in write mode
        
    Returns:
        Dict: Metadata including config_hash for integrity verification
    """
    metadata = {}
    
    config_path = get_config_path()
    if config_path.exists():
        logger.info("Including config.json in backup")
        zipf.write(config_path, "config.json")
        # Calculate hash for integrity verification
        with open(config_path, 'rb') as f:
            config_hash = hashlib.sha256(f.read()).hexdigest()
        metadata["config_hash"] = config_hash
    else:
        logger.warning("Config file not found, skipping")
    
    return metadata


def restore_config(temp_dir: Path, verify_hash: Optional[str] = None) -> bool:
    """Restore configuration file from extracted backup directory.
    
    Args:
        temp_dir: Directory containing extracted backup
        verify_hash: Optional SHA256 hash to verify integrity
        
    Returns:
        bool: True if successful, False otherwise
    """
    config_path_backup = temp_dir / "config.json"
    
    if not config_path_backup.exists():
        logger.info("No config data in backup")
        return False
    
    logger.info("Restoring config.json")
    config_dest = get_config_path()
    
    # Verify hash if available
    if verify_hash:
        with open(config_path_backup, 'rb') as f:
            restored_hash = hashlib.sha256(f.read()).hexdigest()
        if restored_hash != verify_hash:
            logger.warning("Config hash mismatch, but continuing restore")
    
    # Backup current config before overwriting
    if config_dest.exists():
        backup_current = config_dest.with_suffix('.json.bak')
        shutil.copy2(config_dest, backup_current)
        logger.info(f"Backed up current config to {backup_current}")
    
    shutil.copy2(config_path_backup, config_dest)
    logger.info("Config restored successfully")
    return True

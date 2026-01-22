"""
Tooltip Manager Backup Module

Handles backup and restore operations for the Tooltip Manager database.
"""

import shutil
import zipfile
from pathlib import Path
from typing import Dict, Optional

from src.modules.log.logger_factory import get_logger

logger = get_logger(__name__)


def get_tooltip_manager_info() -> Optional[Path]:
    """Get tooltip manager database path.
    
    Returns:
        Path: Tooltip DB path or None if not available
    """
    try:
        from src.app_context import app_context
        
        if not hasattr(app_context, 'tooltip_manager') or app_context.tooltip_manager is None:
            logger.warning("Tooltip manager not initialized")
            return None
        
        tm = app_context.tooltip_manager
        # Get the db path from the engine URL
        db_url = str(tm.engine.url)
        # Extract path from sqlite:///path format
        if db_url.startswith('sqlite:///'):
            db_path = Path(db_url.replace('sqlite:///', ''))
            
            if not db_path.exists():
                logger.warning(f"Tooltip DB not found: {db_path}")
                return None
                
            return db_path
        
        return None
        
    except Exception as e:
        logger.warning(f"Could not access tooltip manager: {e}")
        return None


def backup_tooltip_manager(zipf: zipfile.ZipFile) -> Dict:
    """Add tooltip manager to an open ZIP file.
    
    Args:
        zipf: Open ZipFile in write mode
        
    Returns:
        Dict: Metadata (empty for tooltips, for consistency)
    """
    metadata = {}
    
    tooltip_db_path = get_tooltip_manager_info()
    
    if tooltip_db_path and tooltip_db_path.exists():
        logger.info("Including tooltip database in backup")
        zipf.write(tooltip_db_path, "tooltips/.tooltip_data.db")
    else:
        logger.warning("Tooltip database not available, skipping")
    
    return metadata


def restore_tooltip_manager(temp_dir: Path) -> bool:
    """Restore tooltip manager from extracted backup directory.
    
    Args:
        temp_dir: Directory containing extracted backup
        
    Returns:
        bool: True if successful, False otherwise
    """
    tooltips_dir = temp_dir / "tooltips"
    
    if not tooltips_dir.exists():
        logger.info("No tooltip data in backup")
        return False
    
    logger.info("Restoring tooltip database")
    tooltip_db_path = get_tooltip_manager_info()
    
    if not tooltip_db_path:
        logger.warning("Tooltip manager not available, skipping tooltip restore")
        return False
    
    tooltip_db_backup = tooltips_dir / ".tooltip_data.db"
    if tooltip_db_backup.exists():
        # Backup current tooltip DB
        if tooltip_db_path.exists():
            backup_tooltip_db = tooltip_db_path.with_suffix('.db.bak')
            shutil.copy2(tooltip_db_path, backup_tooltip_db)
            logger.info(f"Backed up current tooltip DB to {backup_tooltip_db}")
        
        shutil.copy2(tooltip_db_backup, tooltip_db_path)
        logger.info("Tooltip database restored")
        return True
    
    return False

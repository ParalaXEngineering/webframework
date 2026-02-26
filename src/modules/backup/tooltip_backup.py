"""
Tooltip Manager Backup Module

Provides backup and restore operations for the framework's Tooltip Manager
SQLite database.
"""

import shutil
import zipfile
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from src.modules.log.logger_factory import get_logger
except ImportError:
    import logging
    get_logger = logging.getLogger

from src.modules.app_context import app_context

logger = get_logger("backup.tooltip")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_tooltip_db_path() -> Optional[Path]:
    """Return the path to the tooltip SQLite database, or None."""
    tm = app_context.tooltip_manager
    if tm is None:
        return None
    # The engine URL has the form ``sqlite:///path/to/db``
    try:
        url_str = str(tm.engine.url)
        # strip "sqlite:///" prefix
        if url_str.startswith("sqlite:///"):
            return Path(url_str[len("sqlite:///"):])
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Info helper
# ---------------------------------------------------------------------------

def get_tooltip_manager_info() -> Optional[Path]:
    """Return the tooltip database path, or None if unavailable."""
    return _get_tooltip_db_path()


# ---------------------------------------------------------------------------
# Backup
# ---------------------------------------------------------------------------

def backup_tooltip_manager(zip_file: zipfile.ZipFile) -> Dict[str, Any]:
    """Add the tooltip database to *zip_file*.

    Returns metadata dict with ``tooltip_count``.
    """
    db_path = _get_tooltip_db_path()
    if db_path is None or not db_path.exists():
        logger.warning("Tooltip database not found – skipping")
        return {"tooltip_count": 0}

    zip_file.write(str(db_path), "tooltips/.tooltip_data.db")

    # Count tooltips for metadata
    tooltip_count = 0
    try:
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("SELECT COUNT(*) FROM tooltips")
        tooltip_count = cursor.fetchone()[0]
        conn.close()
    except Exception as exc:
        logger.warning("Could not count tooltips: %s", exc)

    logger.info("Backed up tooltip database (%d tooltips)", tooltip_count)
    return {"tooltip_count": tooltip_count}


# ---------------------------------------------------------------------------
# Restore
# ---------------------------------------------------------------------------

def restore_tooltip_manager(extract_dir: Path) -> bool:
    """Restore tooltip database from extracted backup.

    Expects ``tooltips/.tooltip_data.db`` inside *extract_dir*.
    """
    db_src = extract_dir / "tooltips" / ".tooltip_data.db"
    if not db_src.exists():
        logger.warning("No tooltip database in backup")
        return False

    db_dest = _get_tooltip_db_path()
    if db_dest is None:
        logger.error("Tooltip Manager not initialised – cannot restore")
        return False

    try:
        shutil.copy2(str(db_src), str(db_dest))
        logger.info("Restored tooltip database to %s", db_dest)
        return True
    except Exception as exc:
        logger.error("Failed to restore tooltip database: %s", exc, exc_info=True)
        return False

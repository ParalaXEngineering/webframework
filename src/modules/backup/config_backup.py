"""
Configuration Backup Module

Provides backup and restore operations for the application's config.json.
"""

import hashlib
import shutil
import zipfile
from pathlib import Path
from typing import Any, Dict

try:
    from src.modules.log.logger_factory import get_logger
except ImportError:
    import logging
    get_logger = logging.getLogger

from src.modules.app_context import app_context

logger = get_logger("backup.config")


# ---------------------------------------------------------------------------
# Info helpers
# ---------------------------------------------------------------------------

def get_config_path() -> Path:
    """Return the path to the application config.json.

    Falls back to ``Path("website/config.json")`` when the settings
    manager is not yet initialised.
    """
    sm = app_context.settings_manager
    if sm is not None and hasattr(sm, "storage") and hasattr(sm.storage, "config_path"):
        return Path(sm.storage.config_path)
    return Path("website/config.json")


# ---------------------------------------------------------------------------
# Backup
# ---------------------------------------------------------------------------

def backup_config(zip_file: zipfile.ZipFile) -> Dict[str, Any]:
    """Add config.json to *zip_file*.

    Returns metadata dict with ``config_hash``.
    """
    config_path = get_config_path()
    if not config_path.exists():
        logger.warning("Config file not found at %s", config_path)
        return {}

    zip_file.write(str(config_path), "config.json")
    config_hash = hashlib.sha256(config_path.read_bytes()).hexdigest()
    logger.info("Backed up config.json (%s)", config_hash[:12])
    return {"config_hash": config_hash}


# ---------------------------------------------------------------------------
# Restore
# ---------------------------------------------------------------------------

def restore_config(extract_dir: Path, expected_hash: str = None) -> bool:
    """Restore config.json from extracted backup.

    If *expected_hash* is provided, verifies integrity before overwriting.
    """
    src = extract_dir / "config.json"
    if not src.exists():
        logger.warning("No config.json in backup")
        return False

    if expected_hash:
        actual = hashlib.sha256(src.read_bytes()).hexdigest()
        if actual != expected_hash:
            logger.error(
                "Config hash mismatch: expected %s, got %s",
                expected_hash[:12],
                actual[:12],
            )
            return False

    dest = get_config_path()
    try:
        shutil.copy2(str(src), str(dest))
        logger.info("Restored config.json to %s", dest)
        return True
    except Exception as exc:
        logger.error("Failed to restore config: %s", exc, exc_info=True)
        return False

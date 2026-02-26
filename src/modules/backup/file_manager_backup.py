"""
File Manager Backup Module

Provides backup and restore operations for the framework's File Manager,
including its SQLite metadata database and the HashFS content-addressable
file store.

All public functions obtain the live FileManager instance from the
framework's ``file_handler`` page module so that no caller needs to
pass an explicit reference.
"""

import os
import shutil
import zipfile
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

try:
    from src.modules.log.logger_factory import get_logger
except ImportError:
    import logging
    get_logger = logging.getLogger

logger = get_logger("backup.file_manager")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_file_manager():
    """Retrieve the live FileManager instance from the framework page module.

    The instance is injected into ``src.pages.file_handler`` at startup by
    ``src.main.init_framework``.  We look it up via ``sys.modules`` first
    (fast path) and fall back to an explicit import.
    """
    import sys

    fh = sys.modules.get("src.pages.file_handler")
    if fh is not None and getattr(fh, "file_manager", None) is not None:
        return fh.file_manager

    try:
        from src.pages import file_handler
        return getattr(file_handler, "file_manager", None)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Info / sizing helpers (used by the backup-page UI)
# ---------------------------------------------------------------------------

def get_file_manager_info() -> Tuple[Optional[Path], Optional[Path]]:
    """Return ``(db_path, hashfs_path)`` for the active File Manager.

    Returns ``(None, None)`` when the File Manager is not initialised.
    """
    fm = _get_file_manager()
    if fm is None:
        return None, None
    return Path(fm.db_path), Path(fm.hashfs_path)


def calculate_file_manager_size() -> Tuple[int, int, int]:
    """Calculate storage consumed by the File Manager.

    Returns:
        ``(db_size, files_size, total_size)`` in bytes.
        All zeros when the File Manager is not available.
    """
    fm = _get_file_manager()
    if fm is None:
        return 0, 0, 0

    db_path = Path(fm.db_path)
    hashfs_path = Path(fm.hashfs_path)

    db_size = db_path.stat().st_size if db_path.exists() else 0

    files_size = 0
    if hashfs_path.exists():
        for dirpath, _dirnames, filenames in os.walk(hashfs_path):
            for fname in filenames:
                files_size += os.path.getsize(os.path.join(dirpath, fname))

    return db_size, files_size, db_size + files_size


def count_uploaded_files() -> int:
    """Return the number of file versions tracked by the File Manager.

    Falls back to 0 when the File Manager is not initialised or query fails.
    """
    fm = _get_file_manager()
    if fm is None:
        return 0

    try:
        from src.modules.file_manager.models import FileVersion
        count = fm.db_session.query(FileVersion).count()
        return count
    except Exception as exc:
        logger.warning("Failed to count uploaded files: %s", exc)
        return 0


# ---------------------------------------------------------------------------
# Backup
# ---------------------------------------------------------------------------

def backup_file_manager(zip_file: zipfile.ZipFile) -> Dict[str, Any]:
    """Add the File Manager database and HashFS store to *zip_file*.

    Returns a metadata dict with keys ``file_count`` and ``files_size_mb``
    suitable for merging into the backup's ``metadata.json``.
    """
    fm = _get_file_manager()
    if fm is None:
        logger.warning("File Manager not available – skipping file backup")
        return {"file_count": 0, "files_size_mb": 0.0}

    db_path = Path(fm.db_path)
    hashfs_path = Path(fm.hashfs_path)

    file_count = 0
    files_size = 0

    # 1. Database
    if db_path.exists():
        zip_file.write(str(db_path), "file_manager/.file_metadata.db")
        files_size += db_path.stat().st_size

    # 2. HashFS content store
    if hashfs_path.exists():
        for dirpath, _dirs, filenames in os.walk(hashfs_path):
            for fname in filenames:
                full_path = os.path.join(dirpath, fname)
                arc_name = os.path.join(
                    "file_manager/hashfs",
                    os.path.relpath(full_path, hashfs_path),
                )
                zip_file.write(full_path, arc_name)
                files_size += os.path.getsize(full_path)
                file_count += 1

    files_size_mb = round(files_size / (1024 * 1024), 2)
    logger.info(
        "Backed up file manager: %d files, %.2f MB", file_count, files_size_mb
    )
    return {"file_count": file_count, "files_size_mb": files_size_mb}


# ---------------------------------------------------------------------------
# Restore
# ---------------------------------------------------------------------------

def restore_file_manager(extract_dir: Path) -> bool:
    """Restore File Manager data from an extracted backup directory.

    Expects the directory to contain:
    - ``file_manager/.file_metadata.db``
    - ``file_manager/hashfs/`` (content store tree)

    Returns ``True`` on success, ``False`` otherwise.
    """
    fm = _get_file_manager()
    if fm is None:
        logger.error("File Manager not available – cannot restore")
        return False

    fm_dir = extract_dir / "file_manager"
    if not fm_dir.exists():
        logger.warning("No file_manager directory in backup – nothing to restore")
        return False

    db_src = fm_dir / ".file_metadata.db"
    hashfs_src = fm_dir / "hashfs"

    try:
        # Restore database
        if db_src.exists():
            dest = Path(fm.db_path)
            shutil.copy2(str(db_src), str(dest))
            logger.info("Restored file manager database to %s", dest)

        # Restore HashFS content store
        if hashfs_src.exists():
            dest_dir = Path(fm.hashfs_path)
            # Merge files (don't wipe existing store – content-addressable is safe)
            for dirpath, _dirs, filenames in os.walk(hashfs_src):
                for fname in filenames:
                    src_file = os.path.join(dirpath, fname)
                    rel = os.path.relpath(src_file, hashfs_src)
                    dst_file = dest_dir / rel
                    dst_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_file, str(dst_file))

            logger.info("Restored HashFS content to %s", dest_dir)

        return True

    except Exception as exc:
        logger.error("Failed to restore file manager: %s", exc, exc_info=True)
        return False

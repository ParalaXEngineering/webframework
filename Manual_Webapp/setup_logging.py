"""
Hierarchical Logging Configuration for Manual_Webapp

Loads logging configs from framework → Manual_Webapp in sequence.
Each layer can add/override its own loggers without disturbing others.

IMPORTANT: Logs are written to the CALLER'S root (manual_webapp_root),
not the framework root. This ensures log_viewer can find them.
"""

import logging
import logging.config
import os
from pathlib import Path


def setup_hierarchical_logging(framework_root: Path, manual_webapp_root: Path):
    """
    Load logging configurations in order: framework → Manual_Webapp.
    
    Each config is loaded with disable_existing_loggers=False so they
    are additive rather than replacing previous configurations.
    
    CRITICAL: Sets LOG_DIR environment variable so log_config.ini writes
    to the caller's root (manual_webapp_root/logs), not framework root.
    
    Args:
        framework_root: Path to the framework root directory
        manual_webapp_root: Path to the Manual_Webapp root directory (where logs should be)
    """
    # Ensure logs directory exists at the CALLER'S root
    logs_dir = manual_webapp_root / 'logs'
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Set environment variable for log_config.ini to use absolute paths
    os.environ['LOG_DIR'] = str(logs_dir)
    print(f"[Logging] Logs will be written to: {logs_dir}")
    
    config_files = [
        (framework_root / 'log_config.ini', 'framework'),
        (manual_webapp_root / 'log_config.ini', 'Manual_Webapp'),
    ]
    
    for config_path, layer_name in config_files:
        if config_path.exists():
            try:
                # Load with disable_existing_loggers=False to make configs additive
                logging.config.fileConfig(
                    str(config_path),
                    disable_existing_loggers=False
                )
                print(f"[Logging] Loaded {layer_name} logging config: {config_path}")
            except Exception as e:
                print(f"[Logging] Warning: Failed to load {layer_name} logging config: {e}")
        else:
            print(f"[Logging] Note: {layer_name} logging config not found: {config_path}")

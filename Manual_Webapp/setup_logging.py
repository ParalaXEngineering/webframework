"""
Hierarchical Logging Configuration for Manual_Webapp

Loads logging configs from framework → Manual_Webapp in sequence.
Each layer can add/override its own loggers without disturbing others.
"""

import logging
import logging.config
from pathlib import Path


def setup_hierarchical_logging(framework_root: Path, manual_webapp_root: Path):
    """
    Load logging configurations in order: framework → Manual_Webapp.
    
    Each config is loaded with disable_existing_loggers=False so they
    are additive rather than replacing previous configurations.
    
    Args:
        framework_root: Path to the framework root directory
        manual_webapp_root: Path to the Manual_Webapp root directory
    """
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
                print(f"Loaded {layer_name} logging config: {config_path}")
            except Exception as e:
                print(f"Warning: Failed to load {layer_name} logging config: {e}")
        else:
            print(f"Note: {layer_name} logging config not found: {config_path}")

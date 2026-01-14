"""Default configuration definitions for optional framework features.

Each configuration section can be enabled in site_conf.py and will be automatically
merged into the main config.json if the corresponding feature is enabled.

Configuration sections:
- FRAMEWORK_UI_CONFIG: UI settings for threads, logs, status displays
- REDMINE_CONFIG: Bug tracker integration with Redmine
- UPDATES_CONFIG: Update/maintenance server configuration (FTP or local)
- FILE_STORAGE_CONFIG: File manager storage, thumbnails, and metadata settings
- FEATURE_CONFIGS: Mapping of feature flags to their configuration dictionaries
"""

from .i18n.messages import (
    CONFIG_FRAMEWORK_UI,
    CONFIG_LANGUAGE,
    CONFIG_THREAD_STATUS_ENABLED,
    CONFIG_THREAD_STATUS_POSITION,
    CONFIG_THREAD_STATUS_ICON,
    CONFIG_LOG_VIEWER_MAX_LINES,
    CONFIG_LOG_VIEWER_REFRESH_INTERVAL,
    CONFIG_REDMINE,
    CONFIG_REDMINE_USER,
    CONFIG_REDMINE_PASSWORD,
    CONFIG_REDMINE_ADDRESS,
    CONFIG_REDMINE_PROJECT_ID,
    CONFIG_UPDATES,
    CONFIG_UPDATES_SOURCE,
    CONFIG_UPDATES_FOLDER,
    CONFIG_UPDATES_FTP_ADDRESS,
    CONFIG_UPDATES_FTP_PATH,
    CONFIG_UPDATES_FTP_USER,
    CONFIG_UPDATES_FTP_PASSWORD,
    CONFIG_FILE_STORAGE,
    CONFIG_HASHFS_PATH,
    CONFIG_MAX_FILE_SIZE_MB,
    CONFIG_ALLOWED_EXTENSIONS,
    CONFIG_CATEGORIES,
    CONFIG_GROUP_IDS,
    CONFIG_GENERATE_THUMBNAILS,
    CONFIG_THUMBNAIL_SIZES,
    CONFIG_IMAGE_QUALITY,
    CONFIG_STRIP_EXIF,
    CONFIG_TAGS,
)

# Default configuration for Framework UI settings
FRAMEWORK_UI_CONFIG = {
    "framework_ui": {
        "friendly": str(CONFIG_FRAMEWORK_UI),
        
        "language": {
            "friendly": str(CONFIG_LANGUAGE),
            "type": "select",
            "value": "en",
            "options": ["en", "fr"],
            "persistent": True,
            "overridable_by_user": True
        },
        
        "thread_status_enabled": {
            "friendly": str(CONFIG_THREAD_STATUS_ENABLED),
            "type": "bool",
            "value": True,
            "persistent": True,
            "overridable_by_user": True
        },
        
        "thread_status_position": {
            "friendly": str(CONFIG_THREAD_STATUS_POSITION),
            "type": "select",
            "value": "right",
            "options": ["left", "center", "right"],
            "persistent": True,
            "overridable_by_user": True
        },
        
        "thread_status_icon": {
            "friendly": str(CONFIG_THREAD_STATUS_ICON),
            "type": "icon",
            "value": "cog-sync",
            "persistent": True,
            "overridable_by_user": True
        },
        
        "log_viewer_max_lines": {
            "friendly": str(CONFIG_LOG_VIEWER_MAX_LINES),
            "type": "int",
            "value": 1000,
            "persistent": True,
            "overridable_by_user": True
        },
        
        "log_viewer_refresh_interval": {
            "friendly": str(CONFIG_LOG_VIEWER_REFRESH_INTERVAL),
            "type": "int",
            "value": 2,
            "persistent": True,
            "overridable_by_user": True
        }
    }
}

# Default configuration for Redmine integration
REDMINE_CONFIG = {
    "redmine": {
        "friendly": str(CONFIG_REDMINE),
        "user": {
            "type": "string",
            "friendly": str(CONFIG_REDMINE_USER),
            "value": "",
            "persistent": True
        },
        "password": {
            "type": "string",
            "friendly": str(CONFIG_REDMINE_PASSWORD),
            "value": "",
            "persistent": True
        },
        "address": {
            "type": "string",
            "friendly": str(CONFIG_REDMINE_ADDRESS),
            "value": "https://redmine.example.com/",
            "persistent": True
        },
        "project_id": {
            "type": "string",
            "friendly": str(CONFIG_REDMINE_PROJECT_ID),
            "value": "",
            "persistent": True
        }
    }
}

# Default configuration for updates/maintenance
UPDATES_CONFIG = {
    "updates": {
        "friendly": str(CONFIG_UPDATES),
        "source": {
            "type": "select",
            "friendly": str(CONFIG_UPDATES_SOURCE),
            "value": "FTP",
            "options": [
                "FTP",
                "Folder"
            ],
            "persistent": False
        },
        "folder": {
            "type": "string",
            "friendly": str(CONFIG_UPDATES_FOLDER),
            "value": "",
            "persistent": False
        },
        "address": {
            "type": "string",
            "friendly": str(CONFIG_UPDATES_FTP_ADDRESS),
            "value": "",
            "persistent": True
        },
        "path": {
            "type": "string",
            "friendly": str(CONFIG_UPDATES_FTP_PATH),
            "value": "",
            "persistent": True
        },
        "user": {
            "type": "string",
            "friendly": str(CONFIG_UPDATES_FTP_USER),
            "value": "",
            "persistent": True
        },
        "password": {
            "type": "string",
            "friendly": str(CONFIG_UPDATES_FTP_PASSWORD),
            "value": "",
            "persistent": True
        }
    }
}

# Default configuration for file storage/management
FILE_STORAGE_CONFIG = {
    "file_storage": {
        "friendly": str(CONFIG_FILE_STORAGE),
        
        "hashfs_path": {
            "type": "path",
            "friendly": str(CONFIG_HASHFS_PATH),
            "value": "resources/hashfs_storage",
            "persistent": True
        },
        
        "max_file_size_mb": {
            "type": "int",
            "friendly": str(CONFIG_MAX_FILE_SIZE_MB),
            "value": 50,
            "persistent": True
        },
        
        "allowed_extensions": {
            "type": "array",
            "friendly": str(CONFIG_ALLOWED_EXTENSIONS),
            "value": [
                ".pdf", ".txt", ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp",
                ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
                ".csv", ".zip", ".7z", ".rar"
            ],
            "persistent": True
        },
        
        "categories": {
            "type": "array",
            "friendly": str(CONFIG_CATEGORIES),
            "value": [
                "general",
                "documents",
                "images",
                "reports",
                "archives"
            ],
            "persistent": True
        },
        
        "group_ids": {
            "type": "array",
            "friendly": str(CONFIG_GROUP_IDS),
            "value": [
                "invoice_group",
                "contract_group",
                "photo_group",
                "report_group"
            ],
            "persistent": True
        },
        
        "generate_thumbnails": {
            "type": "bool",
            "friendly": str(CONFIG_GENERATE_THUMBNAILS),
            "value": True,
            "persistent": True
        },
        
        "thumbnail_sizes": {
            "type": "array",
            "friendly": str(CONFIG_THUMBNAIL_SIZES),
            "value": ["150x150", "300x300"],
            "persistent": True
        },
        
        "image_quality": {
            "type": "int",
            "friendly": str(CONFIG_IMAGE_QUALITY),
            "value": 85,
            "persistent": True
        },
        
        "strip_exif": {
            "type": "bool",
            "friendly": str(CONFIG_STRIP_EXIF),
            "value": True,
            "persistent": True
        },
        
        "tags": {
            "type": "array",
            "friendly": str(CONFIG_TAGS),
            "value": [
                "invoice",
                "contract",
                "photo",
                "diagram",
                "report",
                "archive",
                "important",
                "draft"
            ],
            "persistent": True
        }
    }
}

# Default configuration for tooltip system
TOOLTIP_CONFIG = {
    "tooltip_system": {
        "db_path": {
            "type": "string",
            "value": "resources/tooltip_data.db",
            "description": "Path to tooltip database",
            "persistent": True
        },
        "cache_ttl": {
            "type": "int",
            "value": 300,
            "description": "Cache TTL in seconds",
            "persistent": True
        },
        "image_max_width": {
            "type": "int",
            "value": 800,
            "description": "Max width for resized images",
            "persistent": True
        },
        "image_max_height": {
            "type": "int",
            "value": 600,
            "description": "Max height for resized images",
            "persistent": True
        },
        "image_quality": {
            "type": "int",
            "value": 85,
            "description": "JPEG quality (1-100)",
            "persistent": True
        },
        "allowed_elements": {
            "type": "list",
            "value": ["p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "td", "th", "label", "span", "div", "select"],
            "description": "HTML elements where tooltips are allowed to be displayed",
            "persistent": True
        }
    }
}

# Map of feature flags to their config sections
FEATURE_CONFIGS = {
    "framework_ui": FRAMEWORK_UI_CONFIG,  # Always enabled (includes language, thread status, log viewer settings)
    "bug_tracker": REDMINE_CONFIG,
    "updater": UPDATES_CONFIG,
    "packager": UPDATES_CONFIG,  # Packager uses same config as updater
    "file_manager": FILE_STORAGE_CONFIG,
    "tooltip_manager": TOOLTIP_CONFIG,
}

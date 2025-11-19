"""
Default configuration definitions for optional framework features.

Each configuration section can be enabled in site_conf and will be automatically
merged into the main config.json if enabled.
"""

# Default configuration for Framework UI settings
FRAMEWORK_UI_CONFIG = {
    "framework_ui": {
        "friendly": "Framework UI Configuration",
        
        "thread_status_enabled": {
            "friendly": "Show Thread Status in Topbar",
            "type": "bool",
            "value": True,
            "persistent": True,
            "overridable_by_user": True
        },
        
        "thread_status_position": {
            "friendly": "Thread Status Position in Topbar",
            "type": "select",
            "value": "right",
            "options": ["left", "center", "right"],
            "persistent": True,
            "overridable_by_user": True
        },
        
        "thread_status_icon": {
            "friendly": "Thread Status Icon",
            "type": "icon",
            "value": "cog-sync",
            "persistent": True,
            "overridable_by_user": True
        },
        
        "log_viewer_max_lines": {
            "friendly": "Log Viewer Max Lines to Display",
            "type": "int",
            "value": 1000,
            "persistent": True,
            "overridable_by_user": True
        },
        
        "log_viewer_refresh_interval": {
            "friendly": "Log Viewer Refresh Interval (seconds)",
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
        "friendly": "Redmine credentials",
        "user": {
            "type": "string",
            "friendly": "User",
            "value": "",
            "persistent": True
        },
        "password": {
            "type": "string",
            "friendly": "Password",
            "value": "",
            "persistent": True
        },
        "address": {
            "type": "string",
            "friendly": "Address",
            "value": "https://redmine.example.com/",
            "persistent": True
        }
    }
}

# Default configuration for updates/maintenance
UPDATES_CONFIG = {
    "updates": {
        "friendly": "Maintenance server configuration",
        "source": {
            "type": "select",
            "friendly": "Source",
            "value": "FTP",
            "options": [
                "FTP",
                "Folder"
            ],
            "persistent": False
        },
        "folder": {
            "type": "string",
            "friendly": "Local folder",
            "value": "",
            "persistent": False
        },
        "address": {
            "type": "string",
            "friendly": "FTP Address",
            "value": "",
            "persistent": True
        },
        "path": {
            "type": "string",
            "friendly": "FTP Remote path",
            "value": "",
            "persistent": True
        },
        "user": {
            "type": "string",
            "friendly": "FTP User",
            "value": "",
            "persistent": True
        },
        "password": {
            "type": "string",
            "friendly": "FTP Password",
            "value": "",
            "persistent": True
        }
    }
}

# Default configuration for file storage/management
FILE_STORAGE_CONFIG = {
    "file_storage": {
        "friendly": "File Storage Settings",
        
        "hashfs_path": {
            "type": "path",
            "friendly": "HashFS Storage Directory",
            "value": "resources/hashfs_storage",
            "persistent": True
        },
        
        "max_file_size_mb": {
            "type": "int",
            "friendly": "Max File Size (MB)",
            "value": 50,
            "persistent": True
        },
        
        "allowed_extensions": {
            "type": "array",
            "friendly": "Allowed Extensions",
            "value": [
                ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp",
                ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
                ".txt", ".csv", ".zip", ".7z", ".rar"
            ],
            "persistent": True
        },
        
        "categories": {
            "type": "array",
            "friendly": "File Categories",
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
            "friendly": "Available Group IDs",
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
            "friendly": "Generate Thumbnails",
            "value": True,
            "persistent": True
        },
        
        "thumbnail_sizes": {
            "type": "array",
            "friendly": "Thumbnail Sizes (WxH)",
            "value": ["150x150", "300x300"],
            "persistent": True
        },
        
        "image_quality": {
            "type": "int",
            "friendly": "Image Compression Quality (1-100)",
            "value": 85,
            "persistent": True
        },
        
        "strip_exif": {
            "type": "bool",
            "friendly": "Remove EXIF Metadata from Images",
            "value": True,
            "persistent": True
        },
        
        "tags": {
            "type": "array",
            "friendly": "Available File Tags",
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

# Map of feature flags to their config sections
FEATURE_CONFIGS = {
    "framework_ui": FRAMEWORK_UI_CONFIG,  # Added when threads or logs enabled
    "bug_tracker": REDMINE_CONFIG,
    "updater": UPDATES_CONFIG,
    "packager": UPDATES_CONFIG,  # Packager uses same config as updater
    "file_manager": FILE_STORAGE_CONFIG,
}

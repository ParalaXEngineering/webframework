"""
Default configuration definitions for optional framework features.

Each configuration section can be enabled in site_conf and will be automatically
merged into the main config.json if enabled.
"""

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

# Map of feature flags to their config sections
FEATURE_CONFIGS = {
    "bug_tracker": REDMINE_CONFIG,
    "updater": UPDATES_CONFIG,
    "packager": UPDATES_CONFIG,  # Packager uses same config as updater
}

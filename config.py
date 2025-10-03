# Development configuration
DEBUG = True
SECRET_KEY = 'dev-secret-key-change-in-production'
SESSION_TYPE = 'filesystem'
TEMPLATES_AUTO_RELOAD = True
PROPAGATE_EXCEPTIONS = False

# Framework-specific settings
FRAMEWORK_MODE = 'standalone'  # or 'submodule'
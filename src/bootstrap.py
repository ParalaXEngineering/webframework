"""
ParalaX Web Framework - Bootstrap Module

Provides a simple entry point for initializing ParalaX web applications.
This module handles all the complex path setup, logging configuration,
and framework initialization that was previously done in each site's main.py.

Usage:
    from paralax_bootstrap import bootstrap_app
    
    # In your site's main.py:
    app, socketio = bootstrap_app(
        site_conf_class=MySiteConf,
        port=5000
    )
    
    if __name__ == '__main__':
        socketio.run(app, debug=True, host='0.0.0.0', port=5000)
"""

import os
import sys
import secrets
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Type, Tuple, Any

if TYPE_CHECKING:
    from flask import Flask
    from flask_socketio import SocketIO
    from .modules.site_conf import Site_conf


def get_or_create_secret_key(app_root: Path) -> str:
    """
    Get secret key from file or create new one.
    
    Priority:
    1. PARALAX_SECRET_KEY environment variable
    2. .secret_key file in app root
    3. Generate new key and save to file
    
    Args:
        app_root: Application root directory
        
    Returns:
        Secret key string
    """
    # Check environment variable
    env_key = os.environ.get('PARALAX_SECRET_KEY')
    if env_key:
        return env_key
    
    # Check .secret_key file
    key_file = app_root / '.secret_key'
    if key_file.exists():
        return key_file.read_text(encoding='utf-8').strip()
    
    # Generate new key and save
    new_key = secrets.token_hex(32)
    try:
        key_file.write_text(new_key)
        try:
            key_file.chmod(0o600)  # Restrictive permissions
        except Exception:
            pass
        print(f"Generated new secret key in {key_file}")
    except OSError as e:
        print(f"Warning: Could not save secret key to file: {e}")
    
    return new_key


def bootstrap_app(
    site_conf_class: Type["Site_conf"],
    project_root: Optional[Path] = None,
    port: int = 5000,
    framework_submodule_path: str = "submodules/framework",
    log_dir: Optional[str] = None,
) -> Tuple["Flask", "SocketIO"]:
    """
    Bootstrap a ParalaX web application.
    
    This function handles:
    - Path setup (framework and project paths)
    - Working directory configuration
    - Logging initialization
    - Secret key management
    - Site configuration
    - App initialization via setup_app()
    
    Args:
        site_conf_class: Your site's Site_conf subclass
        project_root: Project root directory (default: caller's directory)
        port: Application port (for reference, not used directly)
        framework_submodule_path: Path to framework submodule relative to project_root
        log_dir: Custom log directory (default: project_root/logs)
        
    Returns:
        Tuple of (Flask app, SocketIO instance)
        
    Example:
        from src.bootstrap import bootstrap_app
        from website.site_conf import MySiteConf
        
        app, socketio = bootstrap_app(MySiteConf)
        
        if __name__ == '__main__':
            socketio.run(app, debug=True, host='0.0.0.0', port=5000)
    """
    # Determine project root from caller if not provided
    if project_root is None:
        # Get the caller's frame to find their directory
        import inspect
        frame = inspect.currentframe()
        if frame and frame.f_back:
            caller_file = frame.f_back.f_globals.get('__file__')
            if caller_file:
                project_root = Path(caller_file).parent.absolute()
            else:
                project_root = Path.cwd()
        else:
            project_root = Path.cwd()
    else:
        project_root = Path(project_root).absolute()
    
    framework_root = project_root / framework_submodule_path
    
    if not framework_root.exists():
        raise RuntimeError(
            f"Framework not found at {framework_root}\n"
            f"Make sure the framework submodule is initialized:\n"
            f"  git submodule update --init --recursive"
        )
    
    # === PATH SETUP ===
    # Framework root MUST be first for src.* imports to work
    if str(framework_root) not in sys.path:
        sys.path.insert(0, str(framework_root))
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # === WORKING DIRECTORY ===
    # Framework expects to run from its directory for relative template/static paths
    original_cwd = os.getcwd()
    os.chdir(str(framework_root))
    
    # === LOGGING SETUP ===
    # Set LOG_DIR before any framework imports that might use logging
    import src.modules.log.logger_factory as logger_factory
    logger_factory.LOG_DIR = log_dir or str(project_root / 'logs')
    
    # Initialize logging
    from src.modules.log.logger_factory import initialize_logging, get_logger
    initialize_logging(project_root)
    
    logger = get_logger("bootstrap")
    logger.info(f"Bootstrapping application from {project_root}")
    
    # === IMPORT FRAMEWORK ===
    from src.modules.app_context import app_context
    from src.modules import site_conf as site_conf_module
    from src.main import app, setup_app
    
    # === SECRET KEY ===
    secret_key = get_or_create_secret_key(project_root)
    app.config['SECRET_KEY'] = secret_key
    
    # === CONFIGURE SITE ===
    site_conf_instance = site_conf_class()
    app_context.site_conf = site_conf_instance
    app_context.app_path = str(project_root)
    site_conf_module.site_conf_app_path = str(project_root)
    
    # === SETUP APP ===
    socketio = setup_app(app)
    
    return app, socketio


def run_app(
    app: "Flask",
    socketio: "SocketIO",
    host: str = "0.0.0.0",
    port: int = 5000,
    debug: bool = True,
    use_reloader: bool = False,
) -> None:
    """
    Run the application with SocketIO.
    
    Args:
        app: Flask application instance
        socketio: SocketIO instance
        host: Host to bind to
        port: Port to listen on
        debug: Enable debug mode
        use_reloader: Enable auto-reloader (disabled by default due to chdir)
    """
    socketio.run(
        app,
        debug=debug,
        host=host,
        port=port,
        use_reloader=use_reloader,
        allow_unsafe_werkzeug=True
    )

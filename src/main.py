try:
    from flask import Flask, render_template, session, request, g
    from flask_session import Session
    from flask_socketio import SocketIO
    FLASK_AVAILABLE = True
except ImportError:
    # Flask not available - create dummy classes for import testing
    Flask = None  # type: ignore
    render_template = None  # type: ignore
    session = None  # type: ignore
    request = None  # type: ignore
    g = None  # type: ignore
    Session = None  # type: ignore
    SocketIO = None  # type: ignore
    FLASK_AVAILABLE = False

import time
import os
import webbrowser
import uuid

import importlib
import sys
import threading
import traceback

try:
    from .modules import scheduler
    from .modules.threaded import threaded_manager
    from .modules.auth.auth_manager import auth_manager
    from .modules import site_conf
    from .modules.log.logger_factory import get_logger
    from .modules.socketio_manager import initialize_socketio_manager
except ImportError:
    from modules import scheduler
    from modules.threaded import threaded_manager
    from modules.auth.auth_manager import auth_manager
    from modules import site_conf
    from modules.log.logger_factory import get_logger
    from modules.socketio_manager import initialize_socketio_manager

# Create Flask app only if Flask is available
if FLASK_AVAILABLE:
    app = Flask(  # type: ignore
            __name__,
            instance_relative_config=True,
            static_folder=os.path.join("..", "webengine", "assets"),
            template_folder=os.path.join("..", "templates")
        )
else:
    app = None  # Placeholder when Flask is not available

def authorize_refresh(f):
    f._disable_csrf = True  # Ajouter un attribut personnalisé
    return f


def setup_app(app):
    """Setup Flask app. Only call when FLASK_AVAILABLE is True."""
    if not FLASK_AVAILABLE:
        return None
    
    app.config["SESSION_TYPE"] = "filesystem"  # type: ignore
    app.config['TEMPLATES_AUTO_RELOAD'] = False  # type: ignore
    app.config["SECRET_KEY"] = "super secret key"  # type: ignore
    app.config["PROPAGATE_EXCEPTIONS"] = False  # type: ignore
    app.config.from_object(__name__)  # type: ignore
    Session(app)  # type: ignore

    socketio_obj = SocketIO(app)  # type: ignore
    
    # Initialize logger using centralized factory and log application start
    logger = get_logger("main")
    logger.info("Application starting up")
    
    # Initialize SocketIO manager for user isolation
    socketio_manager_obj = initialize_socketio_manager(socketio_obj)
    logger.info("SocketIO manager initialized for multi-user support")

    # Detect if we're running from exe
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        app_path = sys._MEIPASS  # type: ignore
    else:
        # Go up 2 levels from src/main.py to get framework root
        # src/main.py -> src/ -> webframework/
        app_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Get all Python files in the "pages" directory (if it exists)
    website_pages_path = os.path.join(app_path, "website", "pages")
    if os.path.exists(website_pages_path):
        files = [f for f in os.listdir(website_pages_path) if f.endswith(".py") and not f.startswith("__")]
        
        # Import each module and register its blueprint
        for file in files:
            module_name = file[:-3]  # Remove the ".py" extension
            
            try:
                # Import the module
                page_module = importlib.import_module(f"website.pages.{module_name}")
                
                # Register the blueprint if it exists
                if hasattr(page_module, 'bp'):
                    app.register_blueprint(page_module.bp)
                    logger.info(f"Registered website page blueprint: {module_name}")
            except ImportError as e:
                logger.warning(f"Failed to import website page {module_name}: {e}")
            except Exception as e:
                logger.warning(f"Failed to register blueprint for {module_name}: {e}")

    # Auto-discover and register framework internal pages
    try:
        from . import pages as pages_module
    except ImportError:
        import pages as pages_module
    
    # Get the pages directory path
    pages_dir = os.path.dirname(os.path.abspath(pages_module.__file__))
    
    # Get all Python files in the pages directory
    framework_pages = [f[:-3] for f in os.listdir(pages_dir) 
                       if f.endswith('.py') and f != '__init__.py']
    
    # Import and register each framework page blueprint
    for page_name in framework_pages:
        try:
            if '.' in __name__:  # Running as package
                page_module = importlib.import_module(f".pages.{page_name}", package='src')
            else:  # Running directly
                page_module = importlib.import_module(f"pages.{page_name}")
            
            # Register the blueprint if it exists
            if hasattr(page_module, 'bp'):
                app.register_blueprint(page_module.bp)
                logger.info(f"Registered framework page blueprint: {page_name}")
        except ImportError as e:
            logger.warning(f"Failed to import framework page {page_name}: {e}")
        except Exception as e:
            logger.warning(f"Failed to register blueprint for {page_name}: {e}")

    # Initialize auth manager with default configuration
    # The auth_manager variable is imported at the top of this file
    # We need to update the module-level singleton
    try:
        from .modules.auth import auth_manager as auth_manager_module
        from .modules.auth.auth_manager import AuthManager
    except ImportError:
        from modules.auth import auth_manager as auth_manager_module
        from modules.auth.auth_manager import AuthManager
    
    # Create and set the global auth_manager instance
    auth_manager_instance = AuthManager(auth_dir=os.path.join(app_path, "website", "auth"))
    auth_manager_module.auth_manager = auth_manager_instance
    
    # Also update the local module reference so the inject_endpoint function can access it
    globals()['auth_manager'] = auth_manager_instance
    
    logger.info("Auth manager initialized")

    # Start scheduler
    if os.path.isfile(os.path.join(app_path, "website", "scheduler.py")):
        scheduler_obj = importlib.import_module("website.scheduler").Scheduler(socket_obj=socketio_obj)
    else:
        scheduler_obj = scheduler.Scheduler(socket_obj=socketio_obj)

    scheduler_thread = threading.Thread(target=scheduler_obj.start, daemon=True)
    scheduler_thread.start()

    scheduler.scheduler_obj = scheduler_obj

    # Start long term scheduler
    scheduler_lt = scheduler.Scheduler_LongTerm()
    scheduler_lt.start()
    scheduler.scheduler_ltobj = scheduler_lt

    threaded_manager.thread_manager_obj = threaded_manager.Threaded_manager()

    # Initialize log emitter for real-time log viewing
    try:
        from .modules.log import log_emitter
    except ImportError:
        from modules.log import log_emitter
    
    logs_dir = os.path.join(app_path, 'logs')
    log_emitter.initialize_log_emitter(socketio_obj, logs_dir, interval=2.0)
    logger.info("Log emitter initialized")

    # Initialize thread emitter for real-time thread updates
    try:
        from .modules.threaded import thread_emitter
    except ImportError:
        from modules.threaded import thread_emitter
    
    thread_emitter.thread_emitter_obj = thread_emitter.ThreadEmitter(socketio_obj, interval=0.5)
    thread_emitter.thread_emitter_obj.start()
    logger.info("Thread emitter initialized")

    # Register SocketIO connection handlers for user rooms
    @socketio_obj.on("connect")  # type: ignore
    def handle_connect():
        """Handle client connection - join user-specific room"""
        try:
            room = socketio_manager_obj.join_user_room()
            username = session.get('user', 'anonymous')  # type: ignore
            logger.info(f"Client connected: {username} in room {room}")
        except Exception as e:
            logger.error(f"Error in handle_connect: {e}")
    
    @socketio_obj.on("disconnect")  # type: ignore
    def handle_disconnect():
        """Handle client disconnection - leave user room"""
        try:
            username = session.get('user', 'anonymous')  # type: ignore
            socketio_manager_obj.leave_user_room()
            logger.info(f"Client disconnected: {username}")
        except Exception as e:
            logger.error(f"Error in handle_disconnect: {e}")

    # Register user_connected handler (ALWAYS needed for thread progress)
    @socketio_obj.on("user_connected")  # type: ignore
    def connect():
        scheduler.scheduler_obj.m_user_connected = True  # type: ignore

    # Import site_conf (if website module exists)
    try:
        site_conf.site_conf_obj = importlib.import_module("website.site_conf").Site_conf()
        site_conf.site_conf_obj.m_scheduler_obj = scheduler_obj
        site_conf.site_conf_app_path = app_path

        # Register long term functions from the site confi
        site_conf.site_conf_obj.register_scheduler_lt_functions()

        @socketio_obj.server.on("*")  # type: ignore
        def catch_all(event, sid, *args):
            site_conf.site_conf_obj.socketio_event(event, args)  # type: ignore
    except ModuleNotFoundError:
        logger.info("No website.site_conf found - running in test/framework-only mode")

    @app.context_processor  # type: ignore
    def inject_bar():
        custom_context = site_conf.site_conf_obj.context_processor()  # type: ignore
        base_context = dict(
            sidebarItems=site_conf.site_conf_obj.m_sidebar,  # type: ignore
            topbarItems=site_conf.site_conf_obj.m_topbar,  # type: ignore
            app=site_conf.site_conf_obj.m_app,  # type: ignore
            javascript=site_conf.site_conf_obj.m_javascripts,  # type: ignore
            filename=None,
            title=site_conf.site_conf_obj.m_app["name"],  # type: ignore
            footer=site_conf.site_conf_obj.m_app["footer"]  # type: ignore
        )
        # Merge custom context from site_conf (like enable_easter_eggs) with base context
        if custom_context:
            base_context.update(custom_context)
        return base_context

    @app.context_processor  # type: ignore
    def inject_endpoint():
        if "page_info" not in session:  # type: ignore
            session["page_info"] = ""  # type: ignore

        # Get current user from session
        # Use auth_manager only if it's initialized
        user = session.get('user') or session.get('username')  # type: ignore
        if not user and auth_manager is not None:
            user = auth_manager.get_current_user()
        
        return dict(
            endpoint=request.endpoint, page_info=session["page_info"], user=user  # type: ignore
        )

    
    @app.context_processor  # type: ignore
    def inject_csrf_token():
        # Fonction pour générer un jeton unique
        def generate_csrf_token():
            session['csrf_token'] = str(uuid.uuid4())  # type: ignore
            return session['csrf_token']  # type: ignore
        
        return dict(csrf_token=generate_csrf_token())

    @app.context_processor
    def inject_resources():
        from .modules.displayer import ResourceRegistry
        return dict(
            required_css=ResourceRegistry.get_required_css(),
            required_js=ResourceRegistry.get_required_js(),
            required_cdn=ResourceRegistry.get_required_js_cdn()
        )

    # Custom Jinja2 filter for url_for with dict parameters
    @app.template_filter('url_for_with_params')
    def url_for_with_params_filter(endpoint, params=None):
        """
        Generate a URL for an endpoint with optional parameters.
        
        Args:
            endpoint: Flask endpoint name (e.g., 'logging.api_log_data')
            params: Dictionary of URL parameters (e.g., {'log_file': 'test.log'})
        
        Returns:
            Generated URL string
        """
        from flask import url_for
        if params:
            return url_for(endpoint, **params)
        return url_for(endpoint)

    # Index page
    @app.route("/")  # type: ignore
    def index():
        session["page_info"] = "index"  # type: ignore
        return render_template("index.j2", title=site_conf.site_conf_obj.m_app["name"], content=site_conf.site_conf_obj.m_index)  # type: ignore

    # Error handling to log errors
    @app.errorhandler(Exception)  # type: ignore
    def handle_exception(e):
        
        if hasattr(e, 'code') and e.code == 404:    
            requested_url = request.path  # type: ignore
            query_parameters = request.args.to_dict()  # type: ignore
            app.logger.error(f"A 404 was generated at the following path: {requested_url}. Get arguments: {query_parameters}")  # type: ignore
            return render_template("404.j2", requested=requested_url)  # type: ignore

        app.logger.error("An error occurred", exc_info=e)  # type: ignore
        return render_template("error.j2", error=str(e), traceback=str(traceback.format_exc()))  # type: ignore

    @app.before_request  # type: ignore
    def before_request():            
        g.start_time = time.time()  # type: ignore

        scheduler.scheduler_obj.m_user_connected = False  # type: ignore
        if request.endpoint == "static":  # type: ignore
            return

        # Note: config reading migrated to settings engine in src/modules/settings
        
        inject_bar()

    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        webbrowser.open("http://127.0.0.1:5000/common/login")
    
    return socketio_obj


# Only setup the app if we're running as main, not during import for testing
if __name__ == "__main__":
    setup_app(app)

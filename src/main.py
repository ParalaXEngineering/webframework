try:
    from flask import Flask, render_template, session, request, g
    from flask_session import Session
    from flask_socketio import SocketIO
    FLASK_AVAILABLE = True
except ImportError:
    # Flask not available - create dummy classes for import testing
    Flask = None
    render_template = None
    session = None
    request = None
    g = None
    Session = None
    SocketIO = None
    FLASK_AVAILABLE = False

try:
    from .modules import utilities
except ImportError:
    import utilities

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
except ImportError:
    import scheduler
    from threaded import threaded_manager
    from auth.auth_manager import auth_manager
    import site_conf
    from log.logger_factory import get_logger

# Create Flask app only if Flask is available
if FLASK_AVAILABLE:
    app = Flask(
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
    app.config["SESSION_TYPE"] = "filesystem"
    app.config['TEMPLATES_AUTO_RELOAD'] = False
    app.config["SECRET_KEY"] = "super secret key"
    app.config["PROPAGATE_EXCEPTIONS"] = False
    app.config.from_object(__name__)
    Session(app)

    socketio_obj = SocketIO(app)
    
    # Initialize logger using centralized factory and log application start
    logger = get_logger("main")
    logger.info("Application starting up")

    # Detect if we're running from exe
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        app_path = sys._MEIPASS
    else:
        app_path = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        )

    # Get all Python files in the "pages" directory (if it exists)
    website_pages_path = os.path.join(app_path, "website", "pages")
    if os.path.exists(website_pages_path):
        files = [f for f in os.listdir(website_pages_path) if f.endswith(".py")]
        
        # Dictionary to store the modules that need to be imported first
        modules_to_load_first = {}

        # Identify files with the same base name (e.g., "xxx" and "xxx_abcdef")
        for file in files:
            module_name = file[:-3]  # Remove the ".py" extension
            base_name = module_name.split('_')[0]  # Get the base name (before the first "_")

            # Organize the modules with the same base name
            if base_name not in modules_to_load_first:
                modules_to_load_first[base_name] = []
            if module_name != base_name:
                modules_to_load_first[base_name].append(module_name)

        # Import all modules and register the blueprint from the main module (e.g., "xxx.py")
        for base_name, module_names in modules_to_load_first.items():
            # Import all related modules first (e.g., "xxx_abcdef.py")
            for module_name in sorted(module_names):
                importlib.import_module(f"website.pages.{module_name}")

            # Finally, import and register the blueprint from the main module (e.g., "xxx.py")
            main_module = importlib.import_module(f"website.pages.{base_name}")

            # Register the blueprint if it exists in the main module
            if hasattr(main_module, 'bp'):
                app.register_blueprint(main_module.bp)

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

    # Auth manager is already initialized as a module-level singleton
    # No need to create instance here

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
        from threaded import thread_emitter
    
    thread_emitter.thread_emitter_obj = thread_emitter.ThreadEmitter(socketio_obj, interval=0.5)
    thread_emitter.thread_emitter_obj.start()
    logger.info("Thread emitter initialized")

    # Register user_connected handler (ALWAYS needed for thread progress)
    @socketio_obj.on("user_connected")
    def connect():
        scheduler.scheduler_obj.m_user_connected = True

    # Import site_conf (if website module exists)
    try:
        site_conf.site_conf_obj = importlib.import_module("website.site_conf").Site_conf()
        site_conf.site_conf_obj.m_scheduler_obj = scheduler_obj
        site_conf.site_conf_app_path = app_path

        # Register long term functions from the site confi
        site_conf.site_conf_obj.register_scheduler_lt_functions()

        @socketio_obj.server.on("*")
        def catch_all(event, sid, *args):
            site_conf.site_conf_obj.socketio_event(event, args)
    except ModuleNotFoundError:
        logger.info("No website.site_conf found - running in test/framework-only mode")

    @app.context_processor
    def inject_bar():
        custom_context = site_conf.site_conf_obj.context_processor()
        base_context = dict(
            sidebarItems=site_conf.site_conf_obj.m_sidebar,
            topbarItems=site_conf.site_conf_obj.m_topbar,
            app=site_conf.site_conf_obj.m_app,
            javascript=site_conf.site_conf_obj.m_javascripts,
            filename=None,
            title=site_conf.site_conf_obj.m_app["name"],
            footer=site_conf.site_conf_obj.m_app["footer"]
        )
        # Merge custom context from site_conf (like enable_easter_eggs) with base context
        if custom_context:
            base_context.update(custom_context)
        return base_context

    @app.context_processor
    def inject_endpoint():
        if "page_info" not in session:
            session["page_info"] = ""

        # Get current user from session
        user = session.get('user') or session.get('username') or auth_manager.get_current_user()
        
        return dict(
            endpoint=request.endpoint, page_info=session["page_info"], user=user
        )

    
    @app.context_processor
    def inject_csrf_token():
        # Fonction pour générer un jeton unique
        def generate_csrf_token():
            session['csrf_token'] = str(uuid.uuid4())
            return session['csrf_token']
        
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
    @app.route("/")
    def index():
        session["page_info"] = "index"
        return render_template("index.j2", title=site_conf.site_conf_obj.m_app["name"], content=site_conf.site_conf_obj.m_index)

    # Error handling to log errors
    @app.errorhandler(Exception)
    def handle_exception(e):
        
        if hasattr(e, 'code') and e.code == 404:    
            requested_url = request.path
            query_parameters = request.args.to_dict()
            app.logger.error(f"A 404 was generated at the following path: {requested_url}. Get arguments: {query_parameters}")
            return render_template("404.j2", requested=requested_url)

        app.logger.error("An error occurred", exc_info=e)
        return render_template("error.j2", error=str(e), traceback=str(traceback.format_exc()))

    @app.before_request
    def before_request():            
        g.start_time = time.time()

        scheduler.scheduler_obj.m_user_connected = False
        if request.endpoint == "static":
            return

        # Note: config reading migrated to settings engine in src/modules/settings
        
        inject_bar()

    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        webbrowser.open("http://127.0.0.1:5000/common/login")
    
    return socketio_obj


# Only setup the app if we're running as main, not during import for testing
if __name__ == "__main__":
    setup_app(app)

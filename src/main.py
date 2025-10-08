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
import logging
import logging.config
import uuid

import importlib
import sys
import threading
import traceback

from functools import wraps

try:
    from .modules import scheduler_classes as scheduler
    from .modules import threaded_manager
    from .modules import access_manager
    from .modules import site_conf
except ImportError:
    import scheduler_classes as scheduler
    import threaded_manager
    import access_manager
    import site_conf

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
    
    # Try to find log config file in different possible locations
    log_config_paths = [
        "log_config.ini",  # For standalone usage
        "../log_config.ini",  # For when running from src directory
        "submodules/framework/log_config.ini"  # For submodule usage
    ]
    
    for log_path in log_config_paths:
        if os.path.exists(log_path):
            logging.config.fileConfig(log_path)
            break
    else:
        # Fallback to basic logging if no config file found
        logging.basicConfig(level=logging.INFO)

    # Detect if we're running from exe
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        app_path = sys._MEIPASS
    else:
        app_path = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        )

    # Get all Python files in the "pages" directory
    files = [f for f in os.listdir(os.path.join(app_path, "website", "pages")) if f.endswith(".py")]
    
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

    # Register other common blueprints
    try:
        from .pages import settings, common, updater, packager, bug_tracker
    except ImportError:
        from pages import settings, common, updater, packager, bug_tracker
    app.register_blueprint(settings.bp)
    app.register_blueprint(common.bp)
    app.register_blueprint(updater.bp)
    app.register_blueprint(packager.bp)
    app.register_blueprint(bug_tracker.bp)

    # Register access manager
    access_manager.auth_object = access_manager.Access_manager()

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

    # Import site_conf
    site_conf.site_conf_obj = importlib.import_module("website.site_conf").Site_conf()
    site_conf.site_conf_obj.m_scheduler_obj = scheduler_obj
    site_conf.site_conf_app_path = app_path

    # Register long term functions from the site confi
    site_conf.site_conf_obj.register_scheduler_lt_functions()

    @socketio_obj.on("user_connected")
    def connect():
        scheduler.scheduler_obj.m_user_connected = True

    @socketio_obj.server.on("*")
    def catch_all(event, sid, *args):
        site_conf.site_conf_obj.socketio_event(event, args)

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

        if access_manager.auth_object.get_login():
            user = access_manager.auth_object.get_user()
        else:
            user = None
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

        # Read the parameters
        session["config"] = utilities.util_read_parameters()

        inject_bar()

    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        webbrowser.open("http://127.0.0.1:5000/common/login")


# Only setup the app if we're running as main, not during import for testing
if __name__ == "__main__" or (FLASK_AVAILABLE and app is not None and not os.environ.get('PYTEST_CURRENT_TEST')):
    setup_app(app)

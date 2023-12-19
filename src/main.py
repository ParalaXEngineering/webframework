from flask import Flask, render_template, session, request
from flask_session import Session

from submodules.framework.src.framework import utilities

import os
import logging

from flask_socketio import SocketIO
import importlib
import sys
import threading
from submodules.framework.src.framework import scheduler
from submodules.framework.src.framework import threaded_manager
from submodules.framework.src.framework import access_manager
from submodules.framework.src.framework import site_conf


def main():
    if len(sys.argv) == 1:
        try:
            file = open("site", "r")
            read_content = file.read()
            sys.argv.append(read_content)
        except Exception:
            print('''The software must be started with either an argument
                  specifying the site, or a 'site' file with this
                  information''')

    app = Flask(__name__, instance_relative_config=True,
                static_folder=os.path.join("..", "webengine", "assets"))

    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SECRET_KEY'] = 'super secret key'
    app.config.from_object(__name__)
    Session(app)

    socketio_obj = SocketIO(app)

    log = logging.getLogger('werkzeug')
    log.setLevel(logging.WARNING)

    # Detect if we're running from exe
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        app_path = sys._MEIPASS
    else:
        app_path = os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

    # Automatically import all pages
    for item in os.listdir(os.path.join(app_path, "website", "pages")):
        if ".py" in item:
            print("website.pages." + item[0:-3])
            module = importlib.import_module("website.pages." + item[0:-3])
            app.register_blueprint(module.bp)

    # Some pages are present in all websites
    from submodules.framework.src.framework import settings
    app.register_blueprint(settings.bp)
    from submodules.framework.src.framework import common
    app.register_blueprint(common.bp)
    from submodules.framework.src.framework import updater
    app.register_blueprint(updater.bp)

    # Register access manager
    access_manager.auth_object = access_manager.Access_manager()

    # Start scheduler
    if os.path.isfile(os.path.join(app_path, "website", "scheduler.py")):
        scheduler_obj = importlib.import_module(
            "website.scheduler").Scheduler()
    else:
        scheduler_obj = scheduler.Scheduler()

    scheduler_obj.socket_obj = socketio_obj
    scheduler_thread = threading.Thread(
        target=scheduler_obj.start, daemon=True)
    scheduler_thread.start()

    #
    scheduler.scheduler_obj = scheduler_obj

    threaded_manager.thread_manager_obj = threaded_manager.Threaded_manager()

    # Import site_conf
    site_conf.site_conf_obj = importlib.import_module(
        "website.site_conf").Site_conf()
    site_conf.site_conf_obj.m_scheduler_obj = scheduler_obj

    @socketio_obj.on("user_connected")
    def connect():
        scheduler.scheduler_obj.m_user_connected = True

    @socketio_obj.server.on('*')
    def catch_all(event, sid, *args):
        site_conf.site_conf_obj.socketio_event(event)

    @app.context_processor
    def inject_bar():
        site_conf.site_conf_obj.context_processor()
        return dict(sidebarItems=site_conf.site_conf_obj.m_sidebar,
                    topbarItems=site_conf.site_conf_obj.m_topbar,
                    app=site_conf.site_conf_obj.m_app,
                    javascript=site_conf.site_conf_obj.m_javascripts,
                    filename=None)

    @app.context_processor
    def inject_endpoint():
        if "page_info" not in session:
            session["page_info"] = ""

        if access_manager.auth_object.get_login():
            user = access_manager.auth_object.get_user()
        else:
            user = None
        return dict(endpoint=request.endpoint,
                    page_info=session["page_info"],
                    user=user)

    # Index page
    @app.route('/')
    def index():
        session["page_info"] = "index"
        return (render_template('index.j2'))

    @app.before_request
    def before_request():
        scheduler.scheduler_obj.m_user_connected = False
        if request.endpoint == "static":
            return

        # Read the parameters
        session['config'] = utilities.util_read_parameters()

        inject_bar()

    app.run(debug=True, host="0.0.0.0", use_reloader=False)

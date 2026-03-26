"""
Separate authentication server for OnTarget mode.
Runs on port 8080 and handles only the /auth route.
"""
from flask import Flask, render_template, request, redirect, session
import os
import sys
import socket
from datetime import datetime, timedelta

def create_auth_app():
    """Create a minimal Flask app for authentication only"""
    auth_app = Flask(
        __name__,
        instance_relative_config=True,
        static_folder=os.path.join("..", "webengine", "assets"),
        template_folder=os.path.join("..", "templates")
    )
    
    from jinja2 import ChoiceLoader, FileSystemLoader
    from flask import Blueprint
    
    # Configure multiple template folders
    auth_app.jinja_loader = ChoiceLoader([
        FileSystemLoader(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "..", "website", "templates")),
        FileSystemLoader(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "templates"))
    ])
    
    hostname = socket.gethostname()
    on_target = "al70x" in hostname
    
    auth_app.config["SESSION_TYPE"] = "filesystem"
    # Use /tmp for session files on target (read-only filesystem)
    # IMPORTANT: Must use the same session directory as main app for session sharing
    if on_target:
        auth_app.config["SESSION_FILE_DIR"] = "/tmp/flask_session"
    auth_app.config['TEMPLATES_AUTO_RELOAD'] = False
    auth_app.config["SECRET_KEY"] = "super secret key"
    auth_app.config["PROPAGATE_EXCEPTIONS"] = False
    auth_app.config.from_object(__name__)
    
    from flask_session import Session
    Session(auth_app)
    
    from submodules.framework.src import utilities
    from submodules.framework.src import access_manager
    from submodules.framework.src import site_conf
    from submodules.framework.src.security_utils import ATTEMPTS_BEFORE_LOCKOUT, LOCKOUT_DURATION
    
    # Initialize access manager
    if not access_manager.auth_object:
        access_manager.auth_object = access_manager.Access_manager()
    
    # Create a common blueprint for assets (to match the template expectations)
    common_bp = Blueprint("common", __name__, url_prefix="/common")
    
    @auth_app.route("/auth", methods=["GET", "POST"])
    def auth():
        """Authentication page for OnTarget mode"""
        access_manager.auth_object.unlog()
        config = utilities.util_read_parameters()
        users = config["access"]["users"]["value"]

        error_message = None
        cooldown_remaining = 0
        attempts_remaining = ATTEMPTS_BEFORE_LOCKOUT

        # Sort users and remove GUEST if present
        users.sort()
        if "GUEST" in users:
            users.remove("GUEST")

        # Check if there's an active cooldown (OnTarget only - 20 seconds between attempts)
        if 'auth_cooldown_until' in session:
            cooldown_until = session['auth_cooldown_until']
            now = datetime.now()
            if now < cooldown_until:
                # Still in cooldown
                cooldown_remaining = int((cooldown_until - now).total_seconds())
                # Get the last attempted user to show remaining attempts
                last_user = session.get('last_attempted_user', users[0] if users else 'unknown')
                attempts_remaining = access_manager.auth_object.get_remaining_attempts(last_user)
                error_message = f"Please wait {cooldown_remaining} seconds before next attempt. ({attempts_remaining} attempts remaining)"
            else:
                # Cooldown expired, clear it
                session.pop('auth_cooldown_until', None)
                cooldown_remaining = 0

        if request.method == "POST" and cooldown_remaining == 0:
            data_in = utilities.util_post_to_json(request.form.to_dict())

            username = data_in["user"]
            password = data_in["password"]
            
            # Store the attempted username for displaying attempts remaining during cooldown
            session['last_attempted_user'] = username

            if username in users:
                # Use access_manager to check login attempt (handles lockout)
                success, error_message = access_manager.auth_object.check_login_attempt(username, password)
                
                if success:
                    access_manager.auth_object.set_user(username, True)
                    # Clear any cooldown on successful login
                    session.pop('auth_cooldown_until', None)
                    session.pop('last_attempted_user', None)
                    # Redirect to main app on port 80
                    redirect_path = config["core"]["redirect"]["value"] if "core" in config else "/"
                    return redirect(f"http://{request.host.split(':')[0]}:80{redirect_path}")
                else:
                    # Failed login - get remaining attempts and set 20 second cooldown
                    attempts_remaining = access_manager.auth_object.get_remaining_attempts(username)
                    
                    # Only add 20s cooldown if not already locked for LOCKOUT_DURATION
                    if "locked" not in error_message.lower():
                        session['auth_cooldown_until'] = datetime.now() + timedelta(seconds=20)
                        cooldown_remaining = 20
                        if attempts_remaining > 0:
                            error_message = f"{error_message} Please wait {cooldown_remaining} seconds. ({attempts_remaining} attempts remaining)"
                        else:
                            error_message = f"{error_message} Please wait {cooldown_remaining} seconds."
                    else:
                        # Already locked for LOCKOUT_DURATION, don't add 20s cooldown
                        attempts_remaining = 0
            else:
                error_message = "User does not exist"
                # Also set cooldown for non-existent user
                session['auth_cooldown_until'] = datetime.now() + timedelta(seconds=20)
                cooldown_remaining = 20
                attempts_remaining = ATTEMPTS_BEFORE_LOCKOUT

        # Get app info for display
        # Always on_target when using auth server on port 8080
        on_target = True
        app_name = "Web MNT App" if on_target else "OuFNis DFDIG"
        
        app_info = {
            "name": app_name,
            "version": site_conf.Site_conf.m_globals.get("version", "1.0.0.0"),
            "icon": "ufo-outline"
        }
        
        return render_template("login.j2", target="auth", users=users, message=error_message, 
                             app=app_info, on_target=on_target, cooldown_remaining=cooldown_remaining,
                             attempts_remaining=attempts_remaining, max_attempts=ATTEMPTS_BEFORE_LOCKOUT,
                             title=app_name, web_title="Auth")
    
    @common_bp.route("/assets/<asset_type>/", methods=["GET"])
    def assets(asset_type):
        """Serve static assets for the login page"""
        from flask import send_file
        
        # Detect if we're running from exe
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            app_path = sys._MEIPASS
        else:
            app_path = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            )
        
        try:
            if asset_type == "images":
                folder_path = os.path.join(app_path, "website", "assets", "images")
            else:
                folder_path = os.path.join(app_path, "submodules", "framework", "webengine", "assets", asset_type)
            
            file_name = request.args.get("filename")
            if file_name and file_name[0] == ".":
                file_name = file_name[2:]
            file_path = os.path.join(folder_path, file_name)
            
            if not os.path.exists(file_path):
                return "", 200
            
            return send_file(file_path, as_attachment=True)
        except Exception:
            return "", 200
    
    # Register the common blueprint
    auth_app.register_blueprint(common_bp)
    
    return auth_app

def start_auth_server(port=8080):
    """Start the authentication server on the specified port"""
    auth_app = create_auth_app()
    auth_app.run(debug=False, host='0.0.0.0', port=port, threaded=True)

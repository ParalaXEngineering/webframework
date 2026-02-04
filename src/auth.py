"""
Authentication blueprint for OnTarget mode.
This module provides the /auth route instead of /common/login when running on target.
Runs on the same port as the main app (single Flask session).
"""
from flask import Blueprint, render_template, request, redirect, session
from datetime import datetime, timedelta
import socket

from submodules.framework.src import utilities
from submodules.framework.src import access_manager
from submodules.framework.src import site_conf

bp = Blueprint("auth", __name__, url_prefix="")


@bp.route("/auth", methods=["GET", "POST"])
def auth():
    """Authentication page for OnTarget mode"""
    access_manager.auth_object.unlog()
    config = utilities.util_read_parameters()
    users = config["access"]["users"]["value"]

    error_message = None
    cooldown_remaining = 0
    attempts_remaining = 5

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

        redirect_path = config["core"]["redirect"]["value"] if "core" in config else "/"

        if username in users:
            # Use access_manager to check login attempt (handles 5 attempts + 5min lock)
            success, error_message = access_manager.auth_object.check_login_attempt(username, password)
            
            if success:
                access_manager.auth_object.set_user(username, True)
                # Clear any cooldown on successful login
                session.pop('auth_cooldown_until', None)
                session.pop('last_attempted_user', None)
                # Redirect to configured path (same port now)
                return redirect(redirect_path)
            else:
                # Failed login - get remaining attempts and set 20 second cooldown
                attempts_remaining = access_manager.auth_object.get_remaining_attempts(username)
                
                # Only add 20s cooldown if not already locked for 5 minutes
                if "locked" not in error_message.lower():
                    session['auth_cooldown_until'] = datetime.now() + timedelta(seconds=20)
                    cooldown_remaining = 20
                    if attempts_remaining > 0:
                        error_message = f"{error_message} Please wait {cooldown_remaining} seconds. ({attempts_remaining} attempts remaining)"
                    else:
                        error_message = f"{error_message} Please wait {cooldown_remaining} seconds."
                else:
                    # Already locked for 5 minutes, don't add 20s cooldown
                    attempts_remaining = 0
        else:
            error_message = "User does not exist"
            # Also set cooldown for non-existent user
            session['auth_cooldown_until'] = datetime.now() + timedelta(seconds=20)
            cooldown_remaining = 20
            attempts_remaining = 5

    # Get app info for display
    hostname = socket.gethostname()
    on_target = "al70x" in hostname
    app_name = "Web MNT App" if on_target else "OuFNis DFDIG"
    
    app_info = {
        "name": app_name,
        "version": site_conf.Site_conf.m_globals.get("version", "1.0.0.0"),
        "icon": "ufo-outline"
    }
    
    return render_template("login.j2", target="auth.auth", users=users, message=error_message, 
                         app=app_info, on_target=on_target, cooldown_remaining=cooldown_remaining,
                         attempts_remaining=attempts_remaining, title=app_name, web_title="Auth")

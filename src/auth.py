"""
Authentication blueprint for OnTarget mode.
This module provides the /auth route instead of /common/login when running on target.
Runs on the same port as the main app (single Flask session).

Includes 2FA support via OTP (One-Time Password) when running on target.
"""
from flask import Blueprint, render_template, request, redirect, session, jsonify
from datetime import datetime, timedelta
import socket
import logging
import time
from pathlib import Path

from submodules.framework.src import utilities
from submodules.framework.src import access_manager
from submodules.framework.src import site_conf
from submodules.framework.src.otp_manager import get_otp_manager, is_otp_enabled
from submodules.framework.src.security_utils import failed_login_manager

logger = logging.getLogger("website")
bp = Blueprint("auth", __name__, url_prefix="")

# Auth activity signal file configuration
AUTH_SIGNAL_BASE_PATH = "/var/lib/dfnet"
AUTH_SIGNAL_SUBDIR = "oufnis"
AUTH_SIGNAL_FILENAME = "auth_active"


def _get_auth_signal_path() -> Path:
    """Get the path to the auth activity signal file."""
    target_type = 'hmi'
    return Path(AUTH_SIGNAL_BASE_PATH) / target_type / AUTH_SIGNAL_SUBDIR / AUTH_SIGNAL_FILENAME


def _update_auth_signal():
    """Update the auth activity signal file with current timestamp."""
    if not is_otp_enabled():
        return  # Only on target
    
    signal_path = _get_auth_signal_path()
    try:
        signal_path.parent.mkdir(parents=True, exist_ok=True)
        signal_path.write_text(str(time.time()))
    except Exception as e:
        logger.warning(f"Failed to update auth signal: {e}")


@bp.route("/auth", methods=["GET", "POST"])
def auth():
    """Authentication page for OnTarget mode"""
    # Signal that someone is on the auth page (for OTP overlay)
    _update_auth_signal()
    
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
        otp_code = data_in.get("otp_code", "").strip()
        
        # Store the attempted username for displaying attempts remaining during cooldown
        session['last_attempted_user'] = username

        redirect_path = config["core"]["redirect"]["value"] if "core" in config else "/"

        # Check if 2FA/OTP is required (only on target)
        otp_required = is_otp_enabled()

        if username in users:
            # Use access_manager to check login attempt (handles 5 attempts + 5min lock)
            success, error_message = access_manager.auth_object.check_login_attempt(username, password)
            
            if success:
                # Password verified - now check OTP if required
                if otp_required:
                    if not otp_code:
                        error_message = "2FA code required"
                        logger.warning(f"Login attempt for '{username}' missing 2FA code")
                    else:
                        otp_manager = get_otp_manager()
                        otp_valid, otp_msg = otp_manager.validate(otp_code)
                        
                        if otp_valid:
                            # Full authentication successful
                            access_manager.auth_object.set_user(username, True)
                            session.pop('auth_cooldown_until', None)
                            session.pop('last_attempted_user', None)
                            logger.info(f"User '{username}' authenticated with 2FA")
                            return redirect(redirect_path)
                        else:
                            # Failed 2FA - record as failed login attempt
                            count = failed_login_manager.increment_attempts(username)
                            attempts_remaining = failed_login_manager.get_remaining_attempts(username)
                            
                            if count >= 5:
                                error_message = "Too many failed attempts. Account locked for 5 minutes."
                                logger.warning(f"Account '{username}' LOCKED after failed 2FA attempts")
                            else:
                                error_message = f"Invalid 2FA code: {otp_msg} ({attempts_remaining} attempts remaining)"
                                logger.warning(f"Invalid 2FA attempt for user '{username}' ({attempts_remaining} attempts remaining)")
                            
                            # Set cooldown for failed 2FA
                            session['auth_cooldown_until'] = datetime.now() + timedelta(seconds=20)
                            cooldown_remaining = 20
                else:
                    # No 2FA required - direct login
                    access_manager.auth_object.set_user(username, True)
                    session.pop('auth_cooldown_until', None)
                    session.pop('last_attempted_user', None)
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
    
    # Check if 2FA is required for this environment
    otp_required = is_otp_enabled()
    
    # Ensure OTP is initialized/valid (auto-regenerates if expired)
    if otp_required:
        otp_manager = get_otp_manager()
        otp_manager.get_current_otp()
    
    app_info = {
        "name": app_name,
        "version": site_conf.Site_conf.m_globals.get("version", "1.0.0.0"),
        "icon": "ufo-outline"
    }
    
    return render_template("login.j2", target="auth.auth", users=users, message=error_message, 
                         app=app_info, on_target=on_target, cooldown_remaining=cooldown_remaining,
                         attempts_remaining=attempts_remaining, title=app_name, web_title="Auth",
                         otp_required=otp_required)


@bp.route("/auth/heartbeat", methods=["POST"])
def auth_heartbeat():
    """
    Heartbeat endpoint to signal that a user is actively on the auth page.
    
    The frontend calls this every 2 seconds to keep the auth_active signal fresh.
    The OTP overlay displays the code only when this signal is recent.
    """
    _update_auth_signal()
    
    # Ensure OTP is valid/regenerated
    if is_otp_enabled():
        otp_manager = get_otp_manager()
        otp_manager.get_current_otp()
    
    return jsonify({"status": "ok", "timestamp": time.time()})


@bp.route("/auth/close", methods=["POST"])
def auth_close():
    """
    Called when user leaves the auth page (beforeunload event).
    Clears the auth signal to hide the OTP overlay immediately.
    """
    if not is_otp_enabled():
        return jsonify({"status": "ok"})
    
    signal_path = _get_auth_signal_path()
    try:
        if signal_path.exists():
            signal_path.write_text("0")  # Set to 0 to indicate closed
    except Exception as e:
        logger.warning(f"Failed to clear auth signal: {e}")
    
    return jsonify({"status": "ok"})

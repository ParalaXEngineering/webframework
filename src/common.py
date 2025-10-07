from flask import Blueprint, render_template, request, send_file, redirect

from submodules.framework.src import utilities
from submodules.framework.src import access_manager
from submodules.framework.src import displayer
from submodules.framework.src import site_conf
from submodules.framework.src import User_defined_module

import os
import sys
import markdown
import bcrypt
import logging
from datetime import datetime, timedelta

bp = Blueprint("common", __name__, url_prefix="/common")
logger = logging.getLogger("website")

# Dictionary to track failed login attempts: {username: {'count': int, 'locked_until': datetime}}
failed_login_attempts = {}


@bp.route("/download", methods=["GET"])
def download():
    """Page that handle a download request by serving the file through flask"""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base_path = os.path.join(
            os.path.dirname(sys.executable),
            "ressources",
            "downloads",
            request.args.to_dict()["file"],
        )
        send_path = base_path
    else:
        send_path = os.path.join("..", "..", "..", "ressources", "downloads", request.args.to_dict()["file"])
        base_path = os.path.join("ressources", "downloads", request.args.to_dict()["file"])

    if not os.path.exists(base_path):
        return render_template("404.j2")

    return send_file(send_path, as_attachment=True)


@bp.route("/assets/<asset_type>/", methods=["GET"])
def assets(asset_type):
    try:
        asset_paths = site_conf.site_conf_obj.get_statics(site_conf.site_conf_app_path)

        folder_path = None
        for path_info in asset_paths:
            if asset_type in path_info:
                folder_path = asset_paths[asset_type]
                break

        if folder_path is None:
            return "Invalid folder type", 404

        file_name = request.args.get("filename")
        if file_name[0] == ".":
            file_name = file_name[2:]
        file_path = os.path.join(folder_path, file_name)

        if not os.path.exists(file_path):
            return "", 200  # Return a blank page with status 200

        return send_file(file_path, as_attachment=True)
    except Exception:
        return render_template("base.j2")


@bp.route("/login", methods=["GET", "POST"])
def login():
    """Login page"""
    access_manager.auth_object.unlog()
    config = utilities.util_read_parameters()
    users = config["access"]["users"]["value"]
    users_password = config["access"]["users_password"]["value"]

    error_message = None

    # Sort users
    users.sort()
    if "GUEST" not in users:
        users = ["GUEST"] + users

    if request.method == "POST":
        data_in = utilities.util_post_to_json(request.form.to_dict())

        username = data_in["user"]
        password_attempt = data_in["password"].encode('utf-8')

        redirect_path = config["core"]["redirect"]["value"] if "core" in config else "/"

        # Check if user is currently locked - BLOCK EVERYTHING
        if username in failed_login_attempts:
            locked_until = failed_login_attempts[username].get('locked_until')
            if locked_until and datetime.now() < locked_until:
                remaining_time = (locked_until - datetime.now()).total_seconds()
                minutes = int(remaining_time // 60)
                seconds = int(remaining_time % 60)
                error_message = f"Account locked. Try again in {minutes}m {seconds}s"
                logger.warning(f"Blocked login attempt for locked user '{username}' (locked until {locked_until.strftime('%H:%M:%S')})")
                return render_template("login.j2", target="common.login", users=users, message=error_message)
            elif locked_until and datetime.now() >= locked_until:
                # Lock expired, reset attempts
                failed_login_attempts[username] = {'count': 0, 'locked_until': None}

        if username in users:
            if username not in users_password:
                # No password is always allowed for now
                # Reset failed attempts on successful login
                if username in failed_login_attempts:
                    failed_login_attempts[username] = {'count': 0, 'locked_until': None}
                access_manager.auth_object.set_user(username, True)
                logger.info(f"Successful login for user '{username}' (no password required)")
                return redirect(redirect_path)
            else:
                stored_password = users_password[username][0]
                stored_hash = stored_password.encode('utf-8')

                # Vérifier le mot de passe avec bcrypt
                try:
                    if bcrypt.checkpw(password_attempt, stored_hash):
                        # Connexion réussie - reset failed attempts
                        if username in failed_login_attempts:
                            failed_login_attempts[username] = {'count': 0, 'locked_until': None}
                        access_manager.auth_object.set_user(username, True)
                        logger.info(f"Successful login for user '{username}'")
                        return redirect(redirect_path)
                    else:
                        # Failed login attempt
                        if username not in failed_login_attempts:
                            failed_login_attempts[username] = {'count': 0, 'locked_until': None}
                        
                        failed_login_attempts[username]['count'] += 1
                        attempts_left = 5 - failed_login_attempts[username]['count']
                        
                        if failed_login_attempts[username]['count'] >= 5:
                            # Lock the account for 5 minutes
                            failed_login_attempts[username]['locked_until'] = datetime.now() + timedelta(minutes=5)
                            error_message = "Too many failed attempts. Account locked for 5 minutes."
                            logger.warning(f"Account '{username}' LOCKED for 5 minutes (until {failed_login_attempts[username]['locked_until'].strftime('%H:%M:%S')})")
                        else:
                            error_message = f"Bad Password for this user ({attempts_left} attempts remaining)"
                            logger.warning(f"Failed login attempt for user '{username}' ({attempts_left} attempts remaining)")
                except Exception as e:
                    logger.error(f"CRITICAL: Exception during password verification for user '{username}': {e}")
                    error_message = "Authentication error. Please contact administrator."
                    # Do NOT allow access on exception - security critical
                    return render_template("login.j2", target="common.login", users=users, message=error_message)
        else:
            error_message = "User does not exist"
            logger.warning(f"Failed login attempt for non-existent user '{username}'")

    return render_template("login.j2", target="common.login", users=users, message=error_message)


@bp.route("/help", methods=["GET"])
def help():
    data_in = request.args.to_dict()
    try:
        topic = data_in["topic"]

        # Open md file
        md_file_path = os.path.join("website", "help", topic + ".md")
        # Vérifiez si le fichier existe pour éviter FileNotFoundError
        if not os.path.exists(md_file_path):
            return "Fichier Markdown non trouvé.", 404
        with open(md_file_path, "r", encoding="utf-8") as text:
            text_data = text.read()

        content = markdown.markdown(text_data, extensions=["sane_lists", "toc", "tables"])
        disp = displayer.Displayer()
        # disp.add_generic("Changelog", display=False)
        User_defined_module.User_defined_module.m_default_name = "Help"
        disp.add_module(User_defined_module.User_defined_module, display=False)
        disp.set_title(f"Documentation: {topic.capitalize().replace('_', ' ').upper()}")
        disp.add_master_layout(
            displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12], subtitle="")
        )

        disp.add_display_item(
            displayer.DisplayerItemAlert(content, displayer.BSstyle.NONE), 0
        )
        return render_template("base_content.j2", content=disp.display(), target="")
    except Exception:
        return render_template("base.j2")

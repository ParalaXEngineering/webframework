"""
Authentication blueprint for OnTarget mode.
This module provides the /auth route instead of /common/login when running on target.
"""
from flask import Blueprint, render_template, request, redirect

from submodules.framework.src import utilities
from submodules.framework.src import access_manager

bp = Blueprint("auth", __name__, url_prefix="")


@bp.route("/auth", methods=["GET", "POST"])
def auth():
    """Authentication page for OnTarget mode"""
    access_manager.auth_object.unlog()
    config = utilities.util_read_parameters()
    users = config["access"]["users"]["value"]

    error_message = None

    # Sort users and remove GUEST if present
    users.sort()
    if "GUEST" in users:
        users.remove("GUEST")

    if request.method == "POST":
        data_in = utilities.util_post_to_json(request.form.to_dict())

        username = data_in["user"]
        password = data_in["password"]

        redirect_path = config["core"]["redirect"]["value"] if "core" in config else "/"

        if username in users:
            # Use access_manager to check login attempt
            success, error_message = access_manager.auth_object.check_login_attempt(username, password)
            
            if success:
                access_manager.auth_object.set_user(username, True)
                return redirect(redirect_path)
            # else: error_message is already set
        else:
            error_message = "User does not exist"

    return render_template("login.j2", target="auth.auth", users=users, message=error_message)

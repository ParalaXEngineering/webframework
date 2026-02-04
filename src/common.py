from flask import Blueprint, render_template, request, send_file, redirect

from submodules.framework.src import utilities
from submodules.framework.src import access_manager
from submodules.framework.src import displayer
from submodules.framework.src import site_conf
from submodules.framework.src import User_defined_module

import os
import sys

bp = Blueprint("common", __name__, url_prefix="/common")


@bp.route("/download", methods=["GET"])
def download():
    """Page that handle a download request by serving the file through flask"""
    filename = request.args.to_dict()["file"]
    
    # Use get_writable_path to find the file in the correct location
    # (redirects to /tmp on target)
    base_path = utilities.get_writable_path(
        os.path.join("ressources", "downloads", filename),
        create_dirs=False
    )

    if not os.path.exists(base_path):
        return render_template("404.j2")

    return send_file(base_path, as_attachment=True)


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

    return render_template("login.j2", target="common.login", users=users, message=error_message)


@bp.route("/help", methods=["GET"])
def help():
    # Help is not available on target (no markdown files and no markdown module)
    if site_conf.Site_conf.m_globals.get("on_target", False):
        return "Help not available on target", 404
    
    import markdown
    
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

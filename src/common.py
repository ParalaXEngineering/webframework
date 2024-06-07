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

bp = Blueprint("common", __name__, url_prefix="/common")


@bp.route("/download", methods=["GET"])
def download():
    """Page that handle a download request by serving the file through flask"""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        path = os.path.join(
            os.path.dirname(sys.executable),
            "..",
            "downloads",
            request.args.to_dict()["file"],
        )
    else:
        path = os.path.join(os.path.join("..", "..", "..", "ressources", "downloads"), request.args.to_dict()["file"])

    if not os.path.exists(path):
        return "", 200  # Return a blank page with status 200
    
    return send_file(path, as_attachment=True)


@bp.route("/assets/<asset_type>/", methods=["GET"])
def assets(asset_type):
    asset_paths = site_conf.site_conf_obj.get_statics(site_conf.site_conf_app_path)

    folder_path = None
    for path_info in asset_paths:
        if asset_type in path_info:
            folder_path = asset_paths[asset_type]
            break

    if folder_path is None:
        return "Invalid folder type", 404

    file_name = request.args.get("filename")
    file_path = os.path.join(folder_path, file_name)

    if not os.path.exists(file_path):
        return "", 200  # Return a blank page with status 200

    return send_file(file_path, as_attachment=True)


@bp.route("/login", methods=["GET", "POST"])
def login():
    """Login page"""
    access_manager.auth_object.unlog()
    config = utilities.util_read_parameters()
    users = config["access"]["users"]["value"]
    users_password = config["access"]["users_password"]["value"]

    error_message = None

    if request.method == "POST":
        data_in = utilities.util_post_to_json(request.form.to_dict())

        username = data_in["user"]
        password_attempt = data_in["password"].encode('utf-8')

        if username in users:
            if username not in users_password:
                # No password is always allowed for now
                access_manager.auth_object.set_user(username, True)
                return redirect('/')
            else:
                stored_password = users_password[username][0]
                stored_hash = stored_password.encode('utf-8')
                # Vérifier le mot de passe avec bcrypt
                if bcrypt.checkpw(password_attempt, stored_hash):
                    # Connexion réussie
                    access_manager.auth_object.set_user(username, True)
                    return redirect('/')
                else:
                    error_message = "Bad Password for this user"
        else:
            error_message = "User does not exist"
    
    # Sort users
    users.sort()
    if "GUEST" in users:
        users.remove("GUEST")
    users = ["GUEST"] + users

    return render_template("login.j2", target="common.login", users=users, message=error_message)


@bp.route("/help", methods=["GET"])
def help():
    data_in = request.args.to_dict()
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
    disp.add_module(User_defined_module.User_defined_module)
    disp.add_master_layout(
        displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12], subtitle="")
    )

    disp.add_display_item(
        displayer.DisplayerItemAlert(content, displayer.BSstyle.NONE), 0
    )

    return render_template("base_content.j2", content=disp.display(), target="")

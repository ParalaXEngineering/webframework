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

import re
from datetime import datetime

from redminelib import Redmine

bp = Blueprint("common", __name__, url_prefix="/common")

@bp.route("/bugtracker", methods=["GET", "POST"])
def bugtracker():
    param = utilities.util_read_parameters()
        
        
    disp = displayer.Displayer()
    # disp.add_generic("Changelog", display=False)
    User_defined_module.User_defined_module.m_default_name = "Bug Tracker"
    disp.add_module(User_defined_module.User_defined_module)

    redmine = Redmine(param["redmine"]["address"]["value"], username=param["redmine"]["user"]["value"], password=param["redmine"]["password"]["value"], requests={"verify": False})
    project_id=site_conf.site_conf_obj.m_app["name"].lower().replace('_', '-')
    issues = redmine.issue.filter(project_id=project_id)
    versions = redmine.version.filter(project_id=project_id)
    version_name = site_conf.site_conf_obj.m_app["version"].lower().replace('_', '-')

    if request.method == "POST":
        data_in = utilities.util_post_to_json(request.form.to_dict())["Bug Tracker"]
        if len(data_in["description"]) < 5:
            return render_template("failure.j2", message="Please provide a meaningfull description of the issue")
        if len(data_in["subject"]) < 5:
            return render_template("failure.j2", message="Please provide a meaningfull subject of the issue")

        version_redmine = 0
        for version in versions:
            if version.name == version_name:
                version_redmine = version.id

        try:
            new_issue = redmine.issue.create(
                subject=data_in["subject"],
                description=data_in["description"] + '\r\n' + "Added by OuFNis User " + access_manager.auth_object.get_user(),
                project_id=project_id,
                custom_fields=[{"id": 10, "value": version_redmine}, {"id": 11, "value": "-"}, {"id": 16, "value": "-"}, {"id": 20, "value": "-"}, {"id": 20, "value": "-"}],
                uploads=[{'path': 'website.log', 'description': 'Website log'}, {'path': 'root.log', 'description': 'Root log'}]
            )
        except Exception as e:
            return render_template("failure.j2", message=f"Issue creation failed with the following message: {e}")

        disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [4, 7, 1], subtitle="Current issues"))

    

    
    disp.add_master_layout(
        displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [4, 7, 1], subtitle="Current issues")
    )

    for issue in issues:
        disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [4, 7, 1], subtitle=""))
        disp.add_display_item(displayer.DisplayerItemText(str(issue.subject)), 0)
        disp.add_display_item(displayer.DisplayerItemText(str(issue.description)), 1)
        disp.add_display_item(displayer.DisplayerItemIconLink("", "", "eye", issue.url, color=displayer.BSstyle.SUCCESS), 2)
        print(issue.description)

    disp.add_master_layout(
        displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [4, 8], subtitle="Create a new issue")
    )
    disp.add_display_item(displayer.DisplayerItemText("Enter subject"), 0)
    disp.add_display_item(displayer.DisplayerItemInputString("subject"), 1)
    disp.add_master_layout(
        displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [4, 8], subtitle="")
    )
    disp.add_display_item(displayer.DisplayerItemText("Enter Description"), 0)
    disp.add_display_item(displayer.DisplayerItemInputString("description"), 1)
    
    disp.add_master_layout(
        displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12], subtitle="")
    )
    disp.add_display_item(displayer.DisplayerItemButton("create", "Submit"))

    return render_template("base_content.j2", content=disp.display(), target="common.bugtracker")


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

    content = markdown.markdown(text_data, extensions=["sane_lists", "toc"])
    disp = displayer.Displayer()
    # disp.add_generic("Changelog", display=False)
    User_defined_module.User_defined_module.m_default_name = " "
    disp.add_module(User_defined_module.User_defined_module)
    disp.add_master_layout(
        displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12], subtitle="")
    )

    disp.add_display_item(
        displayer.DisplayerItemAlert(content, displayer.BSstyle.NONE), 0
    )

    return render_template("base_content.j2", content=disp.display(), target="")


def parse_log_file(log_file):
    log_entries = []

    log_pattern = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) \| (\w+) +\| (\w+\.\w+) +\| (\w+) +\| (\d+) +\| (.*)"

    with open(log_file, "r") as file:
        lines = file.readlines()

    full_line = ""
    previous_entry = {
        "time": 0,
        "level": 0,
        "file": "",
        "function": "",
        "line": 0,
        "message": "",
    }
    current_entry = {
        "time": 0,
        "level": 0,
        "file": "",
        "function": "",
        "line": 0,
        "message": "",
    }
    for line in reversed(lines):
        full_line = line + full_line
        if "|" not in line:
            continue
        else:
            match = re.match(log_pattern, full_line, re.DOTALL)
            if match:
                timestamp_str, level, file, function, line_num, message = match.groups()

                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f")
                timestamp = timestamp.replace(microsecond=0)

                current_entry = {
                    "time": timestamp,
                    "level": level,
                    "file": file,
                    "function": function,
                    "line": int(line_num),
                    "message": message.strip(),
                }

                if current_entry["message"] == "Scheduler started":
                    log_entries.append(current_entry)
                    break

                are_equal = all(previous_entry[key] == current_entry[key] for key in previous_entry if key != "message")
                if are_equal:
                    current_entry["message"] = previous_entry["message"] + '<br>' + current_entry["message"]
                    previous_entry = current_entry
                    break

                if previous_entry["time"] != 0:
                    log_entries.append(previous_entry)
                previous_entry = current_entry
                full_line = ""

    # Don't forget the last one...
    if current_entry["time"] != 0:
        log_entries.append(current_entry)
    log_entries.reverse()

    return log_entries


@bp.route("/logs", methods=["GET"])
def logs():
    """Log pages"""
    disp = displayer.Displayer()
    disp.add_generic("Log", display=False)

    log_files = ["website.log", "root.log"]
    for log_file in log_files:
        log_entries = parse_log_file(log_file)

        disp.add_master_layout(
            displayer.DisplayerLayout(
                displayer.Layouts.TABLE,
                ["Time", "Level", "File", "Function", "Line", "Message"],
                log_file[:-4].upper(),
            )
        )

        i = 0
        for log in reversed(log_entries):
            disp.add_display_item(
                displayer.DisplayerItemText(log["time"].strftime("%H:%M:%S")), 0, line=i
            )
            if log["level"] == "DEBUG":
                disp.add_display_item(
                    displayer.DisplayerItemBadge(
                        log["level"], displayer.BSstyle.PRIMARY
                    ),
                    1,
                    line=i,
                )
            elif log["level"] == "INFO":
                disp.add_display_item(
                    displayer.DisplayerItemBadge(log["level"], displayer.BSstyle.INFO),
                    1,
                    line=i,
                )
            elif log["level"] == "WARNING":
                disp.add_display_item(
                    displayer.DisplayerItemBadge(
                        log["level"], displayer.BSstyle.WARNING
                    ),
                    1,
                    line=i,
                )
            else:
                disp.add_display_item(
                    displayer.DisplayerItemBadge(log["level"], displayer.BSstyle.ERROR),
                    1,
                    line=i,
                )
            disp.add_display_item(displayer.DisplayerItemText(log["file"]), 2, line=i)
            disp.add_display_item(
                displayer.DisplayerItemText(log["function"]), 3, line=i
            )
            disp.add_display_item(displayer.DisplayerItemText(log["line"]), 4, line=i)
            disp.add_display_item(
                displayer.DisplayerItemText(log["message"].replace("\n", "<br>")), 5, line=i
            )

            i += 1

    return render_template("base_content.j2", content=disp.display(), target="")

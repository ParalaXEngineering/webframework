from flask import Blueprint, render_template, request, send_file

from submodules.framework.src import utilities
from submodules.framework.src import access_manager
from submodules.framework.src import displayer
from submodules.framework.src import site_conf

import os
import sys
import markdown

import re
from datetime import datetime

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

    if request.method == "POST":
        data_in = utilities.util_post_to_json(request.form.to_dict())
        authorized = access_manager.auth_object.set_user(
            data_in["user"], data_in["password"]
        )

        if authorized:
            return render_template("index.j2")
        else:
            return render_template("failure.j2", message="Bad password")

    return render_template("login.j2", target="common.login", users=users)


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

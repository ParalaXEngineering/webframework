from flask import Blueprint, render_template, request, send_file

from submodules.framework.src import utilities
from submodules.framework.src import access_manager
from submodules.framework.src import displayer

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
        path = os.path.join(os.path.join("downloads"), request.args.to_dict()["file"])
    return send_file(path, as_attachment=True)


@bp.route("/login", methods=["GET", "POST"])
def login():
    """Login page"""
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
    text = open(os.path.join("website", "help", topic + ".md"), "r")
    text_data = text.read()
    text.close()
    content = markdown.markdown(text_data, extensions=["sane_lists"])

    disp = displayer.Displayer()
    disp.add_generic("Changelog", display=False)
    disp.add_master_layout(
        displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12], subtitle="")
    )

    disp.add_display_item(
        displayer.DisplayerItemAlert(content, displayer.BSstyle.NONE), 0
    )

    return render_template("base_content.j2", content=disp.display(), target="")


def parse_log_file(log_file):
    log_entries = []

    log_pattern = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) \| (\w+) +\| (\w+\.\w+) +\| (\w+) +\| (\d+) +\| (.+)"

    with open(log_file, "r") as file:
        lines = file.readlines()

    for line in reversed(lines):
        match = re.match(log_pattern, line)
        if match:
            timestamp_str, level, file, function, line_num, message = match.groups()

            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f")

            entry = {
                "time": timestamp,
                "level": level,
                "file": file,
                "function": function,
                "line": int(line_num),
                "message": message.strip(),
            }

            if entry["message"] == "Scheduler started":
                log_entries.append(entry)
                break

            log_entries.append(entry)

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
                displayer.DisplayerItemText(log["message"]), 5, line=i
            )

            i += 1

    return render_template("base_content.j2", content=disp.display(), target="")

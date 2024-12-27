from flask import Blueprint, render_template, request, session

from submodules.framework.src import utilities
from submodules.framework.src import access_manager
from submodules.framework.src import displayer
from submodules.framework.src import User_defined_module

import json
import subprocess
import psutil
import importlib
import os
import sys
import re
import platform

from datetime import datetime


bp = Blueprint("settings", __name__, url_prefix="/settings")


@bp.route("/ip_config", methods=["GET"])
def ip_config():
    interfaces = psutil.net_if_addrs()
    # Configuration des adresses IP et des masques de sous-réseau
    # And now, display!
    disp = displayer.Displayer()
    User_defined_module.User_defined_module.m_default_name = "IP Configuration"
    disp.add_module(User_defined_module.User_defined_module)
    disp.add_master_layout(
        displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12], subtitle="")
    )
    disp.add_display_item(displayer.DisplayerItemText('<a href="http://127.0.0.1:5000/common/help?topic=usage#configuration-de-la-carte-reseau-pour-utiliser-les-oufnis">Documentation</a>'), 0)
    disp.add_master_layout(
        displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12], subtitle="")
    )
    disp.add_display_item(displayer.DisplayerItemAlert("You need admin privileges to change IP Configuration on your PC, please run OuFNis_DFDIG.exe as admin", displayer.BSstyle.INFO), 0)
    disp.add_master_layout(
        displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL,
            [3, 3, 3, 2, 1],
            subtitle="",
            alignment=[displayer.BSalign.L, displayer.BSalign.L, displayer.BSalign.R, displayer.BSalign.L, displayer.BSalign.R],
        )
    )
    disp.add_display_item(displayer.DisplayerItemText("Select Network Interface"), 0)
    disp.add_display_item(displayer.DisplayerItemInputSelect("network_interface", None, None, sorted(interfaces)), 1)
    disp.add_display_item(displayer.DisplayerItemText("Static or DHCP"), 2)
    disp.add_display_item(displayer.DisplayerItemInputSelect("ip_type", None, "Static", ["Static", "DHCP"]), 3)
    disp.add_display_item(displayer.DisplayerItemButton("start_ip_config", "Run"), 4)

    return render_template("base_content.j2", content=disp.display(), target="settings.ip_config_apply")


@bp.route("/ip_config_apply", methods=["GET", "POST"])
def ip_config_apply():
    if request.method == "POST":
        ip_configs = [
            {"ip": "10.0.0.10", "mask": "255.255.255.0"},
            {"ip": "10.0.1.10", "mask": "255.255.255.0"},
            {"ip": "192.168.1.10", "mask": "255.255.255.0"}
        ]
        data_in = utilities.util_post_to_json(request.form.to_dict())
        data_in = data_in["IP Configuration"]

        if "start_ip_config" in data_in:
            try:
                if platform.system().lower() != "windows":
                    cmd_clear = f"sudo ip addr flush dev {data_in['network_interface']}"
                    subprocess.run(cmd_clear, shell=True, check=True)

                if data_in["ip_type"] == "Static":
                    first_ip = ip_configs.pop(0)
                    if platform.system().lower() == "windows":
                        cmd_ip = f"netsh interface ip set address name=\"{data_in['network_interface']}\" static {first_ip['ip']} {first_ip['mask']}"
                    else:  # Linux
                        cmd_ip = f"sudo ip addr add {first_ip['ip']}/{first_ip['mask']} dev {data_in['network_interface']}"
                    subprocess.run(cmd_ip, shell=True, check=True)
                    for ip_config in ip_configs:
                        if platform.system().lower() == "windows":
                            command = f"netsh interface ip add address name=\"{data_in['network_interface']}\" addr={ip_config['ip']} mask={ip_config['mask']}"
                        else:  # Linux
                            command = f"sudo ip addr add {ip_config['ip']}/{ip_config['mask']} dev {data_in['network_interface']}"
                        subprocess.run(command, shell=True, check=True)
                else:
                    if platform.system().lower() == "windows":
                        cmd_ip = f"netsh interface ip set address name=\"{data_in['network_interface']}\" dhcp"
                    else:  # Linux
                        cmd_ip = f"sudo dhclient {data_in['network_interface']}"
                    subprocess.run(cmd_ip, shell=True, check=True)
            except Exception:
                return render_template("failure.j2", message="You need admin authorization !!! Run OuFNis_DFDIG.exe with admin privileges")

        # Reload authorization
        access_manager.auth_object.load_authorizations()
        return render_template("success.j2", message="Paramètre modifiés")
    return render_template("base.j2")


@bp.route("/config_edit", methods=["GET"])
def config_edit():
    """Standard page to edit the config file"""

    if not access_manager.auth_object.authorize_group("admin"):
        return render_template("unauthorized.j2")

    # Load configuration
    session["page_info"] = "Configuration"
    serial = []
    for item in session["config"]:
        for subitem in session["config"][item]:
            if (
                "type" in session["config"][item][subitem]
                and session["config"][item][subitem]["type"] == "serial_select"
            ):
                serial = utilities.util_list_serial()

    # Detect if we're running from exe
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        app_path = sys._MEIPASS
    else:
        app_path = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        )

    # Load all the modules by names
    modules = []

    for item in os.listdir(os.path.join(app_path, "website", "modules")):
        if ".py" in item:
            try:
                module = importlib.import_module("website.modules." + item[0:-3])
                module_class = getattr(module, item[0:-3])
                modules.append(module_class.m_default_name)
            except Exception as e:
                # For big modules, there is multiple files, but they won't have any class. Support that
                continue

    # Update modules
    if "access" in session["config"]:
        for module in modules:
            if module not in session["config"]["access"]["modules"]["value"]:
                session["config"]["access"]["modules"]["value"][module] = ["admin"]
        session["config"]["access"]["modules"]["constrains"] = session["config"]["access"]["groups"]["value"]

        # Also add system modules:
        session["config"]["access"]["modules"]["value"]["Website engine update creation"] = ["admin", "user", "quality", "technicians"]
        session["config"]["access"]["modules"]["value"]["Website engine update"] = ["admin", "user", "quality", "technicians"]

        # Update user groups
        for user in session["config"]["access"]["users"]["value"]:
            if user not in session["config"]["access"]["users_groups"]["value"]:
                session["config"]["access"]["users_groups"]["value"][user] = ["admin"]
        session["config"]["access"]["users_groups"]["constrains"] = session["config"]["access"]["groups"]["value"]
        to_remove = []
        for user in session["config"]["access"]["users_groups"]["value"]:
            if user not in session["config"]["access"]["users"]["value"]:
                to_remove.append(user)

        for removal in to_remove:
            session["config"]["access"]["users_groups"]["value"].pop(removal)

        # Update user passwords
        for user in session["config"]["access"]["users"]["value"]:
            if user not in session["config"]["access"]["users_password"]["value"]:
                session["config"]["access"]["users_password"]["value"][user] = [""]

        to_remove = []
        for user in session["config"]["access"]["users_password"]["value"]:
            if user not in session["config"]["access"]["users"]["value"]:
                to_remove.append(user)

        for removal in to_remove:
            session["config"]["access"]["users_password"]["value"].pop(removal)

    # And now, display!
    disp = displayer.Displayer()
    disp.add_generic("Configuration")
    config = session["config"]

    for group in config:
        disp.add_master_layout(
            displayer.DisplayerLayout(
                displayer.Layouts.VERTICAL, [12], subtitle=config[group]["friendly"], spacing=2
            )
        )
        for item in config[group]:
            if "friendly" in config[group][item] and item != "friendly":
                if config[group][item]["type"] == "string":
                    disp.add_master_layout(
                        displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [3, 8, 1], spacing=2)
                    )
                    disp.add_display_item(
                        displayer.DisplayerItemText(config[group][item]["friendly"]), 0
                    )
                    disp.add_display_item(
                        displayer.DisplayerItemInputString(
                            group + "." + item, None, config[group][item]["value"]
                        ),
                        1,
                    )
                elif config[group][item]["type"] == "int":
                    disp.add_master_layout(
                        displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [3, 8, 1], spacing=2)
                    )
                    disp.add_display_item(
                        displayer.DisplayerItemText(config[group][item]["friendly"]), 0
                    )
                    disp.add_display_item(
                        displayer.DisplayerItemInputNumeric(
                            group + "." + item, None, config[group][item]["value"]
                        ),
                        1,
                    )
                elif config[group][item]["type"] == "select":
                    disp.add_master_layout(
                        displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [3, 8, 1], spacing=2)
                    )
                    disp.add_display_item(
                        displayer.DisplayerItemText(config[group][item]["friendly"]), 0
                    )
                    disp.add_display_item(
                        displayer.DisplayerItemInputSelect(
                            group + "." + item,
                            None,
                            config[group][item]["value"],
                            config[group][item]["options"],
                        ),
                        1,
                    )
                elif config[group][item]["type"] == "serial_select":
                    disp.add_master_layout(
                        displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [3, 8, 1], spacing=2)
                    )
                    disp.add_display_item(
                        displayer.DisplayerItemText(config[group][item]["friendly"]), 0
                    )
                    disp.add_display_item(
                        displayer.DisplayerItemInputSelect(
                            group + "." + item,
                            None,
                            config[group][item]["value"],
                            serial,
                        ),
                        1,
                    )
                elif config[group][item]["type"] == "cat_icon":
                    disp.add_master_layout(
                        displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [3, 8, 1], spacing=2)
                    )
                    disp.add_display_item(
                        displayer.DisplayerItemText(config[group][item]["friendly"]), 0
                    )
                    disp.add_display_item(
                        displayer.DisplayerItemInputStringIcon(
                            group + "." + item, config[group][item]["value"]
                        ),
                        1,
                    )
                elif config[group][item]["type"] == "multistring":
                    disp.add_master_layout(
                        displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [3, 3, 5, 1], spacing=2)
                    )
                    disp.add_display_item(
                        displayer.DisplayerItemText(config[group][item]["friendly"]), 0
                    )
                    for line in config[group][item]:
                        if line != "type" and line != "friendly" and line != "persistent":
                            disp.add_display_item(
                                displayer.DisplayerItemText(
                                    config[group][item][line]["friendly"]
                                ),
                                1,
                            )
                            disp.add_display_item(
                                displayer.DisplayerItemInputString(
                                    group + "." + item + "." + line,
                                    None,
                                    config[group][item][line]["value"],
                                ),
                                2,
                            )
                            disp.add_master_layout(
                                displayer.DisplayerLayout(
                                    displayer.Layouts.VERTICAL, [3, 3, 6]
                                )
                            )
                elif config[group][item]["type"] == "constrained_list":
                    disp.add_master_layout(
                        displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [3, 8, 1], spacing=2)
                    )
                    disp.add_display_item(
                        displayer.DisplayerItemText(config[group][item]["friendly"]), 0
                    )
                    disp.add_display_item(
                        displayer.DisplayerItemInputMultiSelect(
                            group + "." + item,
                            None,
                            config[group][item]["value"],
                            config[group][item]["options"],
                        ),
                        1,
                    )
                elif config[group][item]["type"] == "free_list":
                    disp.add_master_layout(
                        displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [3, 8, 1], spacing=2)
                    )
                    disp.add_display_item(
                        displayer.DisplayerItemText(config[group][item]["friendly"]), 0
                    )
                    disp.add_display_item(
                        displayer.DisplayerItemInputMultiText(
                            group + "." + item, None, config[group][item]["value"]
                        ),
                        1,
                    )
                elif config[group][item]["type"] == "constrained_mapping":
                    disp.add_master_layout(
                        displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [3, 8, 1], spacing=2)
                    )
                    disp.add_display_item(
                        displayer.DisplayerItemText(config[group][item]["friendly"]), 0
                    )
                    disp.add_display_item(
                        displayer.DisplayerItemInputMapping(
                            group + "." + item,
                            None,
                            config[group][item]["value"],
                            config[group][item]["constrains"],
                        ),
                        1,
                    )
                elif config[group][item]["type"] == "mapping":
                    disp.add_master_layout(
                        displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [3, 8, 1], spacing=2)
                    )
                    disp.add_display_item(
                        displayer.DisplayerItemText(config[group][item]["friendly"]), 0
                    )
                    disp.add_display_item(
                        displayer.DisplayerItemInputMapping(
                            group + "." + item, None, config[group][item]["value"]
                        ),
                        1,
                    )

                if "persistent" in config[group][item]:
                    disp.add_display_item(
                        displayer.DisplayerItemInputBox("persistent." + group + "." + item, None, config[group][item]["persistent"]), 2
                    )
                else:
                    disp.add_display_item(
                        displayer.DisplayerItemInputBox("persistent." + group + "." + item, None, False), 2
                    )

    disp.add_master_layout(
        displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL, [12], alignment=[displayer.BSalign.R], spacing=2
        )
    )
    disp.add_display_item(
        displayer.DisplayerItemButton("update", "Update"),
    )
    return render_template(
        "base_content.j2", content=disp.display(), target="settings.config_apply"
    )
    # return render_template('settings/config_edit.j2', config=session['config'], serial_ports=serial)


@bp.route("/config_apply", methods=["GET", "POST"])
def config_apply():
    """Standard page apply the new configuration"""
    if request.method == "POST":
        data_post = request.form.to_dict()

        # Jsonify the input data
        data_json = utilities.util_post_to_json(data_post)["Configuration"]

        for group in data_json:
            for item in data_json[group]:
                if "_list" not in item and "mapleft" not in item and "mapright" not in item and "persistent" not in group:
                    if (
                        session["config"][group][item]["type"] == "string"
                        or session["config"][group][item]["type"] == "int"
                        or session["config"][group][item]["type"] == "select"
                        or session["config"][group][item]["type"] == "serial_select"
                    ):
                        session["config"][group][item]["value"] = data_json[group][item]
                    elif (
                        session["config"][group][item]["type"] == "free_list"
                        or session["config"][group][item]["type"] == "constrained_list"
                        or session["config"][group][item]["type"] == "s"
                    ):
                        session["config"][group][item]["value"] = data_json[group][
                            item
                        ].split("#")
                    elif session["config"][group][item]["type"] == "modules":
                        session["config"][group][item]["value"] = json.loads(
                            data_json[group][item].replace("'", '"')
                        )
                    elif "mapping" in session["config"][group][item]["type"]:
                        mapping_info = {}
                        for map_item in data_json[group][item]:
                            if "_list" not in map_item and data_json[group][item][map_item]:
                                mapping_info[map_item] = data_json[group][item][
                                    map_item
                                ].split("#")
                        session["config"][group][item]["value"] = mapping_info

                    if "persistent" in data_json and group in data_json["persistent"] and item in data_json["persistent"][group]:
                        session["config"][group][item]["persistent"] = True
                    else:
                        session["config"][group][item]["persistent"] = False

        utilities.util_write_parameters(session["config"])

        # Reload authorization
        access_manager.auth_object.load_authorizations()
        return render_template("success.j2", message="Paramètre modifiés")
    return render_template("base.j2")


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

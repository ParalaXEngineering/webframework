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


@bp.route("/ip_config_apply", methods=["POST"])
def ip_config_apply():
    ip_configs = [
        {"ip": "10.0.0.10", "mask": "255.255.255.0"},
        {"ip": "10.0.1.10", "mask": "255.255.255.0"},
        {"ip": "192.168.1.10", "mask": "255.255.255.0"}
    ]
    data_in = utilities.util_post_to_json(request.form.to_dict())
    data_in = data_in["IP Configuration"]
    if "start_ip_config" in data_in:
        try:
            if data_in["ip_type"] == "Static":
                first_ip = ip_configs.pop(0)
                cmd_ip = f"netsh interface ip set address name=\"{data_in['network_interface']}\" static {first_ip['ip']} {first_ip['mask']}"
                subprocess.run(cmd_ip, shell=True, check=True)
                for ip_config in ip_configs:
                    command = f"netsh interface ip add address name=\"{data_in['network_interface']}\" addr={ip_config['ip']} mask={ip_config['mask']}"
                    subprocess.run(command, shell=True, check=True)
            else:
                cmd_ip = f"netsh interface ip set address name=\"{data_in['network_interface']}\" dhcp"
                subprocess.run(cmd_ip, shell=True, check=True)
        except Exception:
            return render_template("failure.j2", message="You need admin authorization !!! Run OuFNis_DFDIG.exe with admin privileges")

    # Reload authorization
    access_manager.auth_object.load_authorizations()
    return render_template("success.j2", message="Paramètre modifiés")


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
            module = importlib.import_module("website.modules." + item[0:-3])
            module_class = getattr(module, item[0:-3])
            modules.append(module_class.m_default_name)

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
                        if line != "type" and line != "friendly":
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


@bp.route("/config_apply", methods=["POST"])
def config_apply():
    """Standard page apply the new configuration"""
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


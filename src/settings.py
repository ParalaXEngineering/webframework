from flask import Blueprint, render_template, request, session

from submodules.framework.src import utilities
from submodules.framework.src import access_manager
from submodules.framework.src import displayer

import json
import importlib
import os
import sys

bp = Blueprint("settings", __name__, url_prefix="/settings")


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
        session["config"]["access"]["modules"]["constrains"] = session["config"][
            "access"
        ]["groups"]["value"]

        # Also add system modules:
        session["config"]["access"]["modules"]["value"][
            "Website engine update creation"
        ] = ["admin"]
        session["config"]["access"]["modules"]["value"]["Website engine update"] = [
            "admin",
            "user",
        ]

        # Update user groups
        for user in session["config"]["access"]["users"]["value"]:
            if user not in session["config"]["access"]["users_groups"]["value"]:
                session["config"]["access"]["users_groups"]["value"][user] = ["admin"]
        session["config"]["access"]["users_groups"]["constrains"] = session["config"][
            "access"
        ]["groups"]["value"]
        to_remove = []
        for user in session["config"]["access"]["users_groups"]["value"]:
            if user not in session["config"]["access"]["users"]["value"]:
                to_remove.append(user)

        for removal in to_remove:
            session["config"]["access"]["users_groups"]["value"].pop(removal)

    # And now, display!
    disp = displayer.Displayer()
    disp.add_generic("Configuration")
    config = session["config"]

    for group in config:
        disp.add_master_layout(
            displayer.DisplayerLayout(
                displayer.Layouts.VERTICAL, [12], subtitle=config[group]["friendly"]
            )
        )
        for item in config[group]:
            if "friendly" in config[group][item] and item != "friendly":
                if config[group][item]["type"] == "string":
                    disp.add_master_layout(
                        displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [3, 9])
                    )
                    disp.add_display_item(
                        displayer.DisplayerItemText(config[group][item]["friendly"]), 0
                    )
                    disp.add_display_item(
                        displayer.DisplayerItemInputText(
                            group + "." + item, None, config[group][item]["value"]
                        ),
                        1,
                    )
                elif config[group][item]["type"] == "int":
                    disp.add_master_layout(
                        displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [3, 9])
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
                        displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [3, 9])
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
                        displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [3, 9])
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
                        displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [3, 9])
                    )
                    disp.add_display_item(
                        displayer.DisplayerItemText(config[group][item]["friendly"]), 0
                    )
                    disp.add_display_item(
                        displayer.DisplayerItemInputTextIcon(
                            group + "." + item, config[group][item]["value"]
                        ),
                        1,
                    )
                elif config[group][item]["type"] == "multistring":
                    disp.add_master_layout(
                        displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [3, 3, 6])
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
                                displayer.DisplayerItemInputText(
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
                        displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [3, 9])
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
                        displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [3, 9])
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
                        displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [3, 9])
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
                        displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [3, 9])
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

    disp.add_master_layout(
        displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL, [12], alignment=[displayer.BSalign.R]
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
            if "_list" not in item and "mapleft" not in item and "mapright" not in item:
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
                    ].split(",")
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
                            ].split(",")
                    session["config"][group][item]["value"] = mapping_info

    utilities.util_write_parameters(session["config"])

    # Reload authorization
    access_manager.auth_object.load_authorizations()
    return render_template("success.j2", message="Paramètre modifiés")

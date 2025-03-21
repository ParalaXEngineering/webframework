import json
import os
import sys
import glob
import math
import serial
import zlib
import tarfile
import time
import re

from jinja2 import Environment, FileSystemLoader
from submodules.framework.src import displayer

CONFIG_GLOBAL = {}
LAST_ACCESS_CONFIG = None

def utils_remove_letter(text: str) -> int:
    """
    Extracts and returns the first integer (including negative numbers) found in a given text.
    
    Parameters:
        text (str): The input string containing numbers and letters.
        
    Returns:
        int: The extracted integer. If no number is found, returns 0.
    
    Example:
        >>> utils_remove_letter("-55°C")
        -55
        >>> utils_remove_letter("Temperature: +42 degrees")
        42
        >>> utils_remove_letter("No numbers here")
        0
    """
    match = re.search(r'-?\d+', text)  # Looks for a number, including negatives
    return int(match.group()) if match else 0

def util_drill_dict(input: dict) -> str:
    """
    Drills into a dictionary in order to get the ultimate string value. If a dictionary has multiple keys, only the value of the first key is drilled into.

    :param input: The dictionary to drill into
    :type input: dict
    :return: The ultimate string value found
    :rtype: str
    """
    current = input
    while isinstance(current, dict):
        key = next(iter(current))
        current = current[key]
    return current

def util_list_to_html(input_list):
    """
    Transforms a Python list into an HTML unordered list.
    
    :param input_list: List of strings or nested lists to convert.
    :return: A string containing the HTML unordered list.
    """
    if not isinstance(input_list, list):
        raise ValueError("Input must be a list.")
    
    def create_list(items):
        html = '<ul class="list-group list-group-flush">'
        for item in items:
            if isinstance(item, list):
                # Recursively create nested lists
                html += f'<li class="list-group-item">{create_list(item)}</li>'
            else:
                html += f'<li class="list-group-item">{item}</li>'
        html += "</ul>"
        return html
    
    return create_list(input_list)

def util_list_serial() -> list:
    """Return the list of the serial ports on the machine

    :raises EnvironmentError: Unsupported platform
    :return: The serial ports on the machine
    :rtype: list
    """
    if sys.platform.startswith("win"):
        ports = [f"COM{i + 1}" for i in range(256)]
    elif sys.platform.startswith("linux") or sys.platform.startswith("cygwin"):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob("/dev/tty[A-Za-z]*")
    elif sys.platform.startswith("darwin"):
        ports = glob.glob("/dev/tty.*")
    else:
        raise EnvironmentError("Unsupported platform")

    result = []
    for port in ports:
        if "usb" in port.lower():
            try:
                s = serial.Serial(port)
                s.close()
                result.append(port)
            except (OSError, serial.SerialException):
                pass

    return result


def util_post_unmap(data: dict) -> dict:
    """Parse the mapping fields in order to transform them in a more user friendly structure.
    As a result, a simple map will transform from:
    {"mapright0": "val0", "mapleft0": "val1", ...}
    to
    {"val0": "val1"}

    and a dualmap will transform from:
    {"mapAright0": "val0", "mapAleft0": "val1", "mapBright0": "val2", "mapBleft0": "val3"}
    to
    [{"val0": "val1", "val2": "val3"}]

    :param data: The json data to parse
    :type data: dict
    :return: A dictionnary with the mapping correctly transformed
    :rtype: dict
    """
    # Take care of the mappings
    for module in data:
        if isinstance(data[module], str):
            continue
        for item in data[module]:
            for cat in data[module][item]:
                if isinstance(data[module][item][cat], (list, dict)):
                    # We need enough levels
                    if not isinstance(data[module][item][cat], dict):
                        continue

                    # Simple map
                    if "mapleft0" in data[module][item][cat]:
                        i = 0
                        map_to_find = "mapleft" + str(i)
                        new_map = {}
                        while map_to_find in data[module][item][cat]:
                            new_map[data[module][item][cat]["mapleft" + str(i)]] = data[
                                module
                            ][item][cat]["mapright" + str(i)]
                            i += 1
                            map_to_find = "mapleft" + str(i)
                        data[module][item][cat] = new_map

                    # Dual map
                    if "mapAleft0" in data[module][item][cat]:
                        i = 0
                        map_to_find = "mapAleft" + str(i)
                        new_map = []
                        while map_to_find in data[module][item][cat]:
                            new_map.append(
                                {
                                    data[module][item][cat]["mapAleft" + str(i)]: data[
                                        module
                                    ][item][cat]["mapAright" + str(i)],
                                    data[module][item][cat]["mapBleft" + str(i)]: data[
                                        module
                                    ][item][cat]["mapBright" + str(i)],
                                }
                            )
                            i += 1
                            map_to_find = "mapAleft" + str(i)

                        data[module][item][cat] = new_map

    return data


def util_post_to_json(data: dict) -> dict:
    """Transform an html datastructure into a easy to manipulate json.
    The html datastructure should be in the following form:
    {
    level0a.level1a = a
    level0a.level1b = b
    level0b.levelx = x
    }
    for the following result:
    {
    level0a = {
    level1a = a
    level1b = b
    };
    level0b = {
    levelx = x
    }
    }

    :param data:  The html post data
    :type data: dict
    :return: A json representation of the data
    :rtype: dict
    """
    formated = {}
    list_pattern = re.compile(r'^[a-zA-Z]*list\d+$')

    # For each item given, we will parse level by level
    for item in data:
        current = formated

        # First, we split the data in order to have an array with each level
        item_split = item.split(".")
        if item[-1] == ".":
            item_split = [item_split[0]]
        if item[0] == ".":
            item_split = [item_split[1]]

        # For each level
        while len(item_split) > 0:
            # Adding new level
            if item_split[0] not in current:
                # Final element
                if len(item_split) == 1:
                    # Multichoice will be in the format item_choice: on
                    if data[item] == "on":
                        multichoice = item_split[0].split("_")

                        # We see this choice for the first time
                        if multichoice[0] not in current:
                            current[multichoice[0]] = [multichoice[1]]
                        else:
                            current[multichoice[0]].append(multichoice[1])
                    else:
                        if "#" in item_split[0]:
                            item_split[0] = item_split[0].split("#")[1]

                        if not list_pattern.match(item_split[0]):
                            current[item_split[0]] = data[item]
                        elif isinstance(current, list):
                            current.append(data[item])

                # Prepare for next level
                else:
                    # Next item is a list, we need to add it.
                    # This is implemented in list-select.j2.
                    # However, lists are alwayis acompagned with a prefix and a number after, so filter with that.
                    # We don't want to misinterpret user input.

                    # Regular expression pattern to match strings like "xxxxlistnn" where "xxxx" is any characters and "nn" is a number.
                    
                    if list_pattern.match(item_split[1]):
                        if not item_split[0] in current:
                            current[item_split[0]] = []
                        # Create only the list, the "final element" par will add the next items
                        # else:
                        # current[item_split[0]].append(data[item])
                    else:
                        current[item_split[0]] = {}
            # Father already exists
            else:
                # Final element
                if len(item_split) == 1 or item_split[1] == "":
                    # Multichoice will be in the format item_choice: on
                    if data[item] == "on":
                        multichoice = item_split[0].split("_")

                        # We see this choice for the first time
                        if multichoice[0] not in current:
                            current[multichoice[0]] = [multichoice[1]]
                        else:
                            current[multichoice[0]].append(multichoice[1])
                    else:
                        if "#" in item_split[0]:
                            item_split[0] = item_split[0].split("#")[1]

                        if not list_pattern.match(item_split[0]):
                            current[item_split[0]] = data[item]
                        elif isinstance(current, list):
                            current.append(data[item])

            # Now that we have added the element, go to the next level
            if data[item] == "on":
                current = current[item_split[0].split("_")[0]]
            else:
                if not list_pattern.match(item_split[0]):
                    current = current[item_split[0]]
                else:
                    current = [data[item]]
            item_split.pop(0)

    return formated


def util_read_parameters() -> dict:
    """Read the parameters of the application, and reload the configuration
    if it hasn't been accessed in the last 10 seconds.

    :return: The parameters of the application
    :rtype: dict
    """
    global CONFIG_GLOBAL
    global LAST_ACCESS_CONFIG
    config_file_path = "website/config.json"
    reload_interval = 10  # seconds

    # If it's the first access or more than 10 seconds have passed, reload the config
    if not LAST_ACCESS_CONFIG or time.time() - LAST_ACCESS_CONFIG > reload_interval:
        try:
            with open(config_file_path, 'r', encoding="utf-8") as f:
                config_data = json.load(f)
            CONFIG_GLOBAL = config_data
        except Exception as e:
            # If there's an error, fall back to the last known configuration
            config_data = CONFIG_GLOBAL
    else:
        # If accessed recently, use the cached config
        config_data = CONFIG_GLOBAL

    # Update the last access time
    LAST_ACCESS_CONFIG = time.time()

    return config_data


def util_write_parameters(data: dict):
    """Write the parameters of the application

    :param data: The new parameters to write
    :type data: dict
    """
    f = open("website/config.json", "w", encoding="utf-8")
    json.dump(data, f, indent=4)
    f.close()


def util_view_reload_displayer(id: str, disp: displayer) -> dict:
    """Reload a multi-user input with new data while using a displayer as input

    :param id: The id of the div text
    :type id: str
    :param input: The new text to display
    :type input: str
    :return: The object that can be passed for rendering
    :rtype: dict
    """
    # And update display
    env = Environment(loader=FileSystemLoader("submodules/framework/templates/"))
    template = env.get_template("base_content_reloader.j2")
    reloader = template.render(content=disp.display(True))  # Bypass authentification here

    to_render = [{"id": id, "content": reloader}]
    return to_render


def util_view_reload_text(index: str, content: str) -> dict:
    """Reload a multi-user input with new data

    :param index: The id of the div text
    :type index: str
    :param content: The new text to display
    :type content: str
    :return: The object that can be passed for rendering
    :rtype: dict
    """
    to_render = [{"id": index, "content": content}]
    return to_render


def util_view_create_modal(index: str, modal_displayer: displayer, base_displayer: displayer, header: str = None) -> str:
    """Add the content of a displayer as a modal in a second displayer. Return the link to use to access the modal

    :param index: The id of the modal to use
    :type index: str
    :param modal_displaer: The displayer that contains the information to show in the modal
    :type modal_displayer: displayer
    :param base_displayer: The displayer where the modal is inserted
    :type base_displayer: displayer
    :param header: A string for the header text
    :type header: str
    :return: The link to access the modal
    :rtype: dict
    """
    index = index.replace(" ", "_").replace(".", "_").replace('/', '_')
    base_displayer.add_modal("modal_" + index, modal_displayer, header)

    return index


def util_view_reload_multi_input(index: str, inputs: dict) -> dict:
    """Reload a multi-user input with new data

    :param index: The id of the form
    :type index: str
    :param inputs: a list of dictionnary representing the inputs in the form
    :param [{id: index, type: "text, number, select", value: "", label: ""}]
    :type inputs: dict
    :return: The rendered form to be displayed
    :rtype: dict
    """

    env = Environment(loader=FileSystemLoader("submodules/framework/templates/"))
    to_render = []
    for processing in inputs:
        if processing["type"] == "select":
            template = env.get_template("reload/select.j2")
            to_render.append(
                {
                    "id": index + "." + processing["id"],
                    "content": template.render(
                        name=processing["id"] + "." + index,
                        options=processing["data"],
                        selected=processing["value"],
                    ),
                }
            )

        elif processing["type"] == "text":
            template = env.get_template("reload/text.j2")
            to_render.append(
                {
                    "id": index + "." + processing["id"],
                    "content": template.render(
                        name=processing["id"] + "." + index, default=processing["value"]
                    ),
                }
            )

        elif processing["type"] == "slider":
            template = env.get_template("reload/slider.j2")
            to_render.append(
                {
                    "id": index + "." + processing["id"],
                    "content": template.render(
                        name=processing["id"] + "." + index,
                        default=processing["value"],
                        min=processing["range"][0],
                        max=processing["range"][1],
                    ),
                }
            )

        elif processing["type"] == "int":
            template = env.get_template("reload/int.j2")
            to_render.append(
                {
                    "id": index + "." + processing["id"],
                    "content": template.render(
                        name=processing["id"] + "." + index, default=processing["value"]
                    ),
                }
            )

        elif processing["type"] == "select-text":
            template = env.get_template("reload/select-text.j2")
            to_render.append(
                {
                    "id": index + "." + processing["id"] + ".div",
                    "content": template.render(
                        item={"id": index},
                        current={
                            "id": processing["id"],
                            "value": processing["value"],
                            "select": processing["select"],
                        },
                    ),
                }
            )

        elif processing["type"] == "text-text":
            template = env.get_template("reload/text-text.j2")
            to_render.append(
                {
                    "id": index + "." + processing["id"] + ".div",
                    "content": template.render(
                        item={"id": index},
                        current={"id": processing["id"], "value": processing["value"]},
                    ),
                }
            )

        elif processing["type"] == "list-select":
            template = env.get_template("reload/list-select.j2")
            to_render.append(
                {
                    "id": index + "." + processing["id"] + ".div",
                    "content": template.render(
                        item={"id": index},
                        current={
                            "id": processing["id"],
                            "value": processing["value"],
                            "select": processing["select"],
                        },
                    ),
                }
            )

        elif processing["type"] == "list-text":
            template = env.get_template("reload/list-text.j2")
            to_render.append(
                {
                    "id": index + "." + processing["id"] + ".div",
                    "content": template.render(
                        item={"id": index},
                        current={"id": processing["id"], "value": processing["value"]},
                    ),
                }
            )

    return to_render


def util_view_reload_input_file_manager(
    name: str,
    index: str,
    files: list = [],
    title: list = [],
    icons: list = [],
    classes: list = [],
    hiddens: list = [],
) -> dict:
    """Create the content necessary to reload a given input file manager

    :param name: The name of the calling module
    :type name: str
    :param index: The id of the form
    :type index: str
    :param files: A list of the files that should be already in the file manager, defaults to []
    :type files: list, optional
    :param title: A list of the titles of the file explorers, defaults to []
    :type title: list, optional
    :param icons: A list of the icons (the mdi project names) of the file explorers, defaults to []
    :type icons: list, optional
    :param classes: A list of the classes (the bootsrap classes such as danger, success or primary) used in the file explorers, defaults to []
    :type classes: list, optional
    :param hiddens: A list of true / false to indicate if a file explorer has a button to collapse the content, defaults to []
    :type hiddens: list, optional
    :return: The rendered html code to display
    :rtype: dict

    """
    env = Environment(loader=FileSystemLoader("submodules/framework/templates/"))
    template = env.get_template("reload/files.j2")
    to_render = []
    for i, file in enumerate(files):
        to_render.append(
            {
                "id": f"{name.replace(' ', '_')}_{index}_files{i}",
                "content": template.render(
                    file_id=f"{index}_files{i}",
                    name=index,
                    files=file,
                    title=title[i],
                    icon=icons[i],
                    classes=classes[i],
                    hidden=hiddens[i],
                ),
            }
        )
    return to_render


def util_dir_list(root: str, inclusion: list = None, modifier: str = None) -> list:
    """Scan a directory, without it's children and return a list of the file that have the inclusion information given by the user

    :param root: The root folder
    :type root: str
    :param inclusion: A list of inclusion, that is part of the file name or extension that must be present in the files listed, defaults to None
    :type inclusion: list, optional
    :param modifier: A function that change the name (parsing for instance), defaults to None
    :type modifier: str, optional
    :return: A list of the corresponding files
    :rtype: list

    """
    results = []
    try:
        current_files = os.listdir(root)
    except Exception:
        return results
    for item in current_files:
        if inclusion:
            for inclu in inclusion:
                if inclu in item:
                    if modifier:
                        results.append(modifier(item))
                    else:
                        results.append(item)

    return results


def util_find_files(root: str, inclusion: list = None) -> list:
    """Find all the files in a directory structure that fit the inclusion description, and return a list of the files with respect to the root path

    :param root: The root folder
    :type root: str
    :param inclusion: A list of inclusion, that is part of the file name or extension that must be present in the files listed, defaults to None
    :type inclusion: list, optional
    :return: A list of the found files
    :rtype: list

    """
    # return current_results
    if isinstance(inclusion, str):
        inclusion = [inclusion]
    found_files = []
    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            # If inclusion criteria is provided, check if any criteria is in the filename.
            if inclusion and not any(inc in filename for inc in inclusion):
                continue
            found_files.append(os.path.join(dirpath, filename))
    return found_files


def util_dir_structure(
    root: str, inclusion: list = None, modifier=None, clean=True
) -> dict:
    """Create the directory structure (all the directories and subfiles) recursively from a root folder

    :param root: The root folder
    :type root: str
    :param inclusion: A list of inclusion, that is part of the file name or extension that must be present in the files listed, defaults to None
    :type inclusion: list, optional
    :param modifier:  A function that change the name (parsing for instance), defaults to None
    :type modifier: _type_, optional
    :param clean: Clean all empty folder from the results, defaults to True
    :type clean: bool, optional
    :return: A dictionnary with the file structure in the form:

    code-block::

        {
        dir:
            { dir: {...}, file, file}, file
        }

    :rtype: dict

    """
    current_dir = {}
    try:
        items = os.listdir(root)
    except FileNotFoundError:
        return current_dir

    for item in items:
        if os.path.isfile(os.path.join(root, item)):
            if inclusion:
                for inclu in inclusion:
                    if inclu in item:
                        if modifier:
                            current_dir[modifier(item)] = os.path.join(root, item)
                        else:
                            current_dir[item] = os.path.join(root, item)
        else:
            directory = util_dir_structure(
                os.path.join(root, item), inclusion=inclusion, modifier=modifier
            )
            if clean:
                if len(directory) > 0:
                    current_dir[item] = directory
            else:
                current_dir[item] = directory

    return current_dir


def utils_keep_number(number: str) -> float:
    """Transform a string in a float, support "," and "." as decimal indicator

    :param number: The string to convert
    :type number: str
    :return: The float number
    :rtype: float
    """
    number_string = ""
    number = number.replace(",", ".")
    for s in number:
        if s.isnumeric() or s == ".":
            number_string += s

    try:
        if not number:
            return 0
        if number[0] == "-":
            return -float(number_string)
        else:
            return float(number_string)
    except Exception:
        return math.nan


def utils_format_unit(cpnt: dict) -> dict:
    """Takes a list of strings that represent a unit and format them, by puting them all at the same decimal, etc.

    Args:
        cpnt (dict): A list of component units

    Returns:
        dict: The formated units
    """
    unit_order = ["f", "p", "n", "µ", "m", "default", "K", "M", "G"]

    for item in cpnt:
        try:
            if "["  in item:        
                unit = item.split("[")[1][:-1]
            else:
                unit = item
                
            value = cpnt[item]
            new_unit = "default"

            if not value:
                continue

            # We might have stuff in () after the value, for instance (x4 channels)
            if "(" in value:
                value = value.split("(")[0]
            # Sometimes there is also @ and we don't want that either
            if '@' in value:
                value = value.split('@')[0]

            # Start by recovering the unit
            if unit == "R":
                unwanted = ["ohm", "Ohm", "ohms", "Ohms", "Ω", " "]
                expected_units = {
                    "m": "m",
                    "k": "K",
                    "K": "K",
                    "G": "G",
                    "M": "M",
                    "default": "R",
                }

            elif unit == "F":
                unwanted = [" "]
                expected_units = {
                    "f": "f",
                    "p": "p",
                    "n": "n",
                    "u": "µ",
                    "µ": "µ",
                    "m": "m",
                    "default": "",
                }

            elif unit == "V/µs":
                unwanted = [" "]
                expected_units = {"default": ""}

            else:
                unwanted = [" "]
                expected_units = {
                    "f": "f",
                    "p": "p",
                    "n": "n",
                    "u": "µ",
                    "µ": "µ",
                    "m": "m",
                    "M": "M",
                    "default": "",
                }

            if new_unit == "default":
                new_unit = expected_units["default"]

            unit_order[5] = expected_units["default"]

            # Remove unwanted bits
            for current_unwanted in unwanted:
                if current_unwanted in value:
                    value = value.replace(current_unwanted, "")

            # Set the unit
            new_unit = expected_units["default"]
            for eu, new_unit in expected_units.items():
                if eu in value:
                    break

            # We have the number and unit, see if we can change the unit
            value_float = utils_keep_number(value)
            if math.isnan(value_float):
                continue
            unit_index = unit_order.index(new_unit)

            negative = False
            if value_float < 0:
                negative = True
                value_float = -value_float

            if value_float < 1:
                value_float = value_float * 1000
                new_unit = unit_order[unit_index - 1]
            elif value_float >= 1000:
                value_float = value_float / 1000
                new_unit = unit_order[unit_index + 1]

            if round(value_float) - value_float == 0:
                value_float = int(value_float)

            value_float = round(value_float, 2)

            if negative:
                value_float = -value_float

            cpnt[item] = str(value_float) + new_unit
        except Exception:
            # Don't change it
            continue

    return cpnt


def utils_calculate_crc32(filepath):
    """Calcule le CRC32 d'un fichier donné."""
    with open(filepath, 'rb') as file:
        content = file.read()
        return zlib.crc32(content)


def utils_get_directory_crc32(directory_path):
    """Génère un dictionnaire des CRC32 pour tous les fichiers dans un répertoire."""
    crc32_dict = {}
    for root, _, files in os.walk(directory_path):
        for file in files:
            filepath = os.path.join(root, file)
            crc32_dict[filepath] = utils_calculate_crc32(filepath)
    return crc32_dict


def utils_create_backup(backup_folders, backup_name):
    """Crée un fichier .tar.gz contenant les dossiers spécifiés."""
    with tarfile.open(backup_name, "w:gz") as tar:
        for folder in backup_folders:
            tar.add(folder, arcname=os.path.basename(folder))

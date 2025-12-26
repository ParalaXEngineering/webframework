"""Utility functions for ParalaX web framework.

Provides common helpers for form data processing, file management, serialization,
breadcrumb navigation, and template rendering.
"""
import glob
import hmac
import os
import re
import sys
import tarfile
import zlib
from typing import TYPE_CHECKING, Callable, Optional

# Framework modules - i18n
from .i18n.messages import ERROR_CONFIG_KEY_NOT_FOUND
from .log.logger_factory import get_logger

logger = get_logger(__name__)

if TYPE_CHECKING:
    from . import displayer

# Optional dependencies - only import what's available
try:
    import serial
except ImportError:
    serial = None  # type: ignore

try:
    from jinja2 import Environment, FileSystemLoader
except ImportError:
    Environment = None  # type: ignore
    FileSystemLoader = None  # type: ignore

try:
    from flask import session
except ImportError:
    session = None  # type: ignore

# displayer is only imported at runtime, not for type checking
if not TYPE_CHECKING:
    try:
        from src.modules import displayer
    except ImportError:
        displayer = None  # type: ignore

# Constants for HTML rendering
HTML_LIST_CLASS = "list-group list-group-flush"
HTML_LIST_ITEM_CLASS = "list-group-item"

# Constants for platform detection
PLATFORM_WINDOWS = "win"
PLATFORM_LINUX = "linux"
PLATFORM_CYGWIN = "cygwin"
PLATFORM_DARWIN = "darwin"

# Constants for mapping field patterns
MAP_LEFT_PREFIX = "mapleft"
MAP_RIGHT_PREFIX = "mapright"
MAP_A_LEFT_PREFIX = "mapAleft"
MAP_A_RIGHT_PREFIX = "mapAright"
MAP_B_LEFT_PREFIX = "mapBleft"
MAP_B_RIGHT_PREFIX = "mapBright"

# Constants for form data processing
FORM_VALUE_ON = "on"
FORM_FIELD_SEPARATOR = "."
FORM_ID_SEPARATOR = "#"
LIST_PATTERN = re.compile(r'^[a-zA-Z]*list\d+$')
UNDERSCORE = "_"

# Constants for file size formatting
FILE_SIZE_UNITS = ['B', 'KB', 'MB', 'GB', 'TB']
FILE_SIZE_THRESHOLD = 1024.0

# Template type constants
TEMPLATE_TYPE_SELECT = "select"
TEMPLATE_TYPE_TEXT = "text"
TEMPLATE_TYPE_SLIDER = "slider"
TEMPLATE_TYPE_INT = "int"
TEMPLATE_TYPE_SELECT_TEXT = "select-text"
TEMPLATE_TYPE_TEXT_TEXT = "text-text"
TEMPLATE_TYPE_LIST_SELECT = "list-select"
TEMPLATE_TYPE_LIST_TEXT = "list-text"



def get_breadcrumbs():
    """Return the breadcrumbs from session.
    
    Returns:
        List of breadcrumb dictionaries or empty list if session unavailable.
    """
    if not session:
        return []
    return session.get('breadcrumbs', [])

def update_breadcrumbs(disp, level, title, endpoint, params=None, style=None):
    """Manage the breadcrumb trail in session and render via displayer.
    
    Args:
        disp: Displayer instance to render breadcrumbs.
        level: Integer breadcrumb depth (0-based), or -1 to append to end.
        title: Label for the breadcrumb.
        endpoint: Flask endpoint name for URL generation.
        params: List of query-string fragments like 'key=value', defaults to None.
        style: Bootstrap style class, defaults to None.
    """
    if not session:
        return
    
    breadcrumbs = session.get('breadcrumbs', [])
    new = {'title': title, 'endpoint': endpoint, 'params': params, 'style': style}

    if level == -1:
        level = len(breadcrumbs)
    
    # Maintain or truncate trail
    if len(breadcrumbs) > level:
        breadcrumbs = breadcrumbs[:level + 1] if breadcrumbs[level] == new else breadcrumbs[:level] + [new]
    else:
        breadcrumbs.append(new)
    
    session['breadcrumbs'] = breadcrumbs
    
    # Render breadcrumbs
    for crumb in breadcrumbs:
        disp.add_breadcrumb(crumb['title'], crumb['endpoint'], crumb['params'], crumb['style'])

def utils_remove_letter(text: str) -> int:
    """
    Extracts and returns the first integer (including negative numbers) found in a given text.
    
    Args:
        text: The input string containing numbers and letters
        
    Returns:
        The extracted integer. If no number is found, returns 0
    
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
    """Transform a Python list into an HTML unordered list.
    
    Args:
        input_list: List of strings or nested lists to convert.
        
    Returns:
        HTML string containing the unordered list.
        
    Raises:
        ValueError: If input_list is not a list.
    """
    if not isinstance(input_list, list):
        raise ValueError("Input must be a list.")
    
    def create_list(items):
        html = f'<ul class="{HTML_LIST_CLASS}">'
        for item in items:
            if isinstance(item, list):
                html += f'<li class="{HTML_LIST_ITEM_CLASS}">{create_list(item)}</li>'
            else:
                html += f'<li class="{HTML_LIST_ITEM_CLASS}">{item}</li>'
        html += "</ul>"
        return html
    
    return create_list(input_list)

def util_list_serial() -> list:
    """Return the list of available serial ports on the machine.
    
    Returns:
        List of serial port names available on the system.
        
    Raises:
        EnvironmentError: If platform is unsupported.
    """
    if not serial:
        return []
    
    if sys.platform.startswith(PLATFORM_WINDOWS):
        ports = [f"COM{i + 1}" for i in range(256)]
    elif sys.platform.startswith(PLATFORM_LINUX) or sys.platform.startswith(PLATFORM_CYGWIN):
        ports = glob.glob("/dev/tty[A-Za-z]*")
    elif sys.platform.startswith(PLATFORM_DARWIN):
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
            except (OSError, serial.SerialException):  # type: ignore
                pass

    return result


def util_post_unmap(data: dict) -> dict:
    """Parse mapping fields to transform into a more user-friendly structure.
    
    Transforms simple maps from {"mapright0": "val0", "mapleft0": "val1", ...}
    to {"val0": "val1"}.
    
    Transforms dual maps from {"mapAright0": "val0", "mapAleft0": "val1", ...}
    to [{"val0": "val1", "val2": "val3"}].
    
    Args:
        data: The JSON data to parse containing map fields.
        
    Returns:
        Dictionary with mapping fields correctly transformed.
    """
    for module in data:
        if isinstance(data[module], str):
            continue
        for item in data[module]:
            for cat in data[module][item]:
                if not isinstance(data[module][item][cat], dict):
                    continue

                # Simple map
                if f"{MAP_LEFT_PREFIX}0" in data[module][item][cat]:
                    i = 0
                    map_to_find = f"{MAP_LEFT_PREFIX}{i}"
                    new_map = {}
                    while map_to_find in data[module][item][cat]:
                        new_map[data[module][item][cat][f"{MAP_LEFT_PREFIX}{i}"]] = data[module][item][cat][f"{MAP_RIGHT_PREFIX}{i}"]
                        i += 1
                        map_to_find = f"{MAP_LEFT_PREFIX}{i}"
                    data[module][item][cat] = new_map

                # Dual map
                if f"{MAP_A_LEFT_PREFIX}0" in data[module][item][cat]:
                    i = 0
                    map_to_find = f"{MAP_A_LEFT_PREFIX}{i}"
                    new_map = []
                    while map_to_find in data[module][item][cat]:
                        new_map.append({
                            data[module][item][cat][f"{MAP_A_LEFT_PREFIX}{i}"]: data[module][item][cat][f"{MAP_A_RIGHT_PREFIX}{i}"],
                            data[module][item][cat][f"{MAP_B_LEFT_PREFIX}{i}"]: data[module][item][cat][f"{MAP_B_RIGHT_PREFIX}{i}"],
                        })
                        i += 1
                        map_to_find = f"{MAP_A_LEFT_PREFIX}{i}"

                    data[module][item][cat] = new_map

    return data


def util_post_to_json(data: dict, debug: bool = False) -> dict:
    """Transform HTML form data into nested JSON using ParalaX field conventions.
    
    This is the **core form processing function** for the framework. All Displayer
    form inputs use naming conventions that this function parses.
    
    CRITICAL: Always use this instead of request.form.get() for form processing.
    
    Args:
        data: Flat form data from request.form.to_dict()
        debug: If True, prints transformation steps for troubleshooting
        
    Returns:
        Nested dictionary structure matching the form hierarchy
    
    Field Naming Conventions:
        Dot Notation (nesting):
            "module.section.field" -> {"module": {"section": {"field": value}}}
            
        Checkbox/Multi-select (value="on"):
            "colors_red": "on", "colors_blue": "on" -> {"colors": ["red", "blue"]}
            
        ID Separator (#):
            "prefix#actualfield" -> {"actualfield": value}  (prefix stripped)
            
        List Pattern (fieldlist0, fieldlist1, ...):
            "items.namelist0": "a", "items.namelist1": "b" -> {"items": {"name": ["a", "b"]}}
    
    Examples:
        >>> # Simple nesting
        >>> util_post_to_json({"user.name": "John", "user.age": "30"})
        {'user': {'name': 'John', 'age': '30'}}
        
        >>> # Checkboxes (multiple selection)
        >>> util_post_to_json({"options_email": "on", "options_sms": "on"})
        {'options': ['email', 'sms']}
        
        >>> # Mixed
        >>> util_post_to_json({
        ...     "config.server.host": "localhost",
        ...     "config.server.port": "8080",
        ...     "config.features_logging": "on",
        ...     "config.features_debug": "on"
        ... })
        {'config': {'server': {'host': 'localhost', 'port': '8080'}, 'features': ['logging', 'debug']}}
    
    Warning:
        - Field names cannot start or end with "."
        - The "on" value is reserved for checkbox handling
        - List patterns must match: [a-zA-Z]*list[0-9]+
    
    See Also:
        - util_post_unmap(): For key-value mapping fields
        - DisplayerItemInputChoice: Generates checkbox fields
        - DisplayerItemInputSelect: Generates select fields
    """
    if debug:
        logger.debug(f"[util_post_to_json] Input: {data}")
    formated = {}

    # For each item given, we will parse level by level
    for item in data:
        current = formated

        # First, we split the data in order to have an array with each level
        item_split = item.split(FORM_FIELD_SEPARATOR)
        if item_split and item[-1] == FORM_FIELD_SEPARATOR:
            item_split = [item_split[0]]
        if item_split and item[0] == FORM_FIELD_SEPARATOR:
            item_split = [item_split[1]]

        # For each level
        while item_split:
            # Adding new level
            if item_split[0] not in current:
                # Final element
                if len(item_split) == 1:
                    if data[item] == FORM_VALUE_ON:
                        multichoice = item_split[0].split(UNDERSCORE)
                        if multichoice[0] not in current:
                            current[multichoice[0]] = [multichoice[1]]
                        else:
                            current[multichoice[0]].append(multichoice[1])
                    else:
                        if FORM_ID_SEPARATOR in item_split[0]:
                            item_split[0] = item_split[0].split(FORM_ID_SEPARATOR)[1]
                        if not LIST_PATTERN.match(item_split[0]):
                            current[item_split[0]] = data[item]
                        elif isinstance(current, list):
                            current.append(data[item])
                # Prepare for next level
                else:
                    if LIST_PATTERN.match(item_split[1]):
                        if item_split[0] not in current:
                            current[item_split[0]] = []
                    else:
                        current[item_split[0]] = {}
            # Father already exists
            else:
                # Final element
                if len(item_split) == 1 or item_split[1] == "":
                    if data[item] == FORM_VALUE_ON:
                        multichoice = item_split[0].split(UNDERSCORE)
                        if multichoice[0] not in current:
                            current[multichoice[0]] = [multichoice[1]]
                        else:
                            current[multichoice[0]].append(multichoice[1])
                    else:
                        if FORM_ID_SEPARATOR in item_split[0]:
                            item_split[0] = item_split[0].split(FORM_ID_SEPARATOR)[1]
                        if not LIST_PATTERN.match(item_split[0]):
                            current[item_split[0]] = data[item]
                        elif isinstance(current, list):
                            current.append(data[item])

            # Now that we have added the element, go to the next level
            if data[item] == FORM_VALUE_ON:
                current = current[item_split[0].split(UNDERSCORE)[0]]
            else:
                if not LIST_PATTERN.match(item_split[0]):
                    current = current[item_split[0]]
                else:
                    current = [data[item]]
            item_split.pop(0)

    if debug:
        logger.debug(f"[util_post_to_json] Output: {formated}")
    return formated


def form_to_nested_dict(data: dict[str, str], separator: str = ".") -> dict:
    """Simple form-to-dict conversion using only dot notation.
    
    A simpler alternative to util_post_to_json for new code that doesn't need
    the legacy checkbox/list patterns. Only handles dot-separated nesting.
    
    Args:
        data: Flat form data dictionary
        separator: Separator character for nesting (default: ".")
        
    Returns:
        Nested dictionary
        
    Example:
        >>> form_to_nested_dict({"a.b.c": "value", "a.b.d": "other"})
        {'a': {'b': {'c': 'value', 'd': 'other'}}}
    """
    result: dict = {}
    
    for key, value in data.items():
        parts = key.split(separator)
        current = result
        
        for i, part in enumerate(parts[:-1]):
            if part not in current:
                current[part] = {}
            current = current[part]
        
        current[parts[-1]] = value
    
    return result


def util_view_reload_displayer(id: str, disp: "displayer.Displayer") -> list:
    """Reload a multi-user input with new data while using a displayer as input.
    
    Args:
        id: The id of the div element to reload.
        disp: The displayer containing content to render.
        
    Returns:
        List with reload object for rendering, or empty list on error.
    """
    try:
        from flask import render_template
        reloader = render_template("base_content_reloader.j2", content=disp.display(True))
        return [{"id": id, "content": reloader}]
    except Exception:
        return []


def util_view_reload_text(index: str, content: str) -> list:
    """Reload a multi-user input with new text content.
    
    Args:
        index: The id of the div element to reload.
        content: The new text to display.
        
    Returns:
        List with reload object for rendering.
    """
    return [{"id": index, "content": content}]


def util_view_create_modal(index: str, modal_displayer: "displayer.Displayer", base_displayer: "displayer.Displayer", header: Optional[str] = None) -> str:
    """Add content from a displayer as a modal in another displayer.
    
    Args:
        index: The id of the modal to use.
        modal_displayer: The displayer containing information to show in modal.
        base_displayer: The displayer where the modal is inserted.
        header: Header text for modal, defaults to None.
        
    Returns:
        Sanitized index string for modal access.
    """
    index = index.replace(" ", UNDERSCORE).replace(".", UNDERSCORE).replace('/', UNDERSCORE)
    base_displayer.add_modal(f"modal_{index}", modal_displayer.display(True), header or "")  # type: ignore
    return index


def util_view_reload_multi_input(index: str, inputs: dict) -> list:
    """Reload a multi-user input with new data.
    
    Args:
        index: The id of the form.
        inputs: List of dictionaries representing form inputs.
        
    Returns:
        List of rendered input elements for display.
    """
    try:
        from flask import render_template
    except ImportError:
        return []
    
    to_render = []
    for processing in inputs:
        if processing["type"] == TEMPLATE_TYPE_SELECT:
            content = render_template("reload/select.j2",
                name=processing["id"] + FORM_FIELD_SEPARATOR + index,
                options=processing["data"],
                selected=processing["value"]
            )
            to_render.append({
                "id": index + FORM_FIELD_SEPARATOR + processing["id"],
                "content": content
            })

        elif processing["type"] == TEMPLATE_TYPE_TEXT:
            content = render_template("reload/text.j2",
                name=processing["id"] + FORM_FIELD_SEPARATOR + index,
                default=processing["value"]
            )
            to_render.append({"id": index + FORM_FIELD_SEPARATOR + processing["id"], "content": content})

        elif processing["type"] == TEMPLATE_TYPE_SLIDER:
            content = render_template("reload/slider.j2",
                name=processing["id"] + FORM_FIELD_SEPARATOR + index,
                default=processing["value"],
                min=processing["range"][0],
                max=processing["range"][1]
            )
            to_render.append({"id": index + FORM_FIELD_SEPARATOR + processing["id"], "content": content})

        elif processing["type"] == TEMPLATE_TYPE_INT:
            content = render_template("reload/int.j2",
                name=processing["id"] + FORM_FIELD_SEPARATOR + index,
                default=processing["value"]
            )
            to_render.append({"id": index + FORM_FIELD_SEPARATOR + processing["id"], "content": content})

        elif processing["type"] == TEMPLATE_TYPE_SELECT_TEXT:
            content = render_template("reload/select-text.j2",
                item={"id": index},
                current={
                    "id": processing["id"],
                    "value": processing["value"],
                    "select": processing["select"]
                }
            )
            to_render.append({"id": index + FORM_FIELD_SEPARATOR + processing["id"] + ".div", "content": content})

        elif processing["type"] == TEMPLATE_TYPE_TEXT_TEXT:
            content = render_template("reload/text-text.j2",
                item={"id": index},
                current={"id": processing["id"], "value": processing["value"]}
            )
            to_render.append({"id": index + FORM_FIELD_SEPARATOR + processing["id"] + ".div", "content": content})

        elif processing["type"] == TEMPLATE_TYPE_LIST_SELECT:
            content = render_template("reload/list-select.j2",
                item={"id": index},
                current={
                    "id": processing["id"],
                    "value": processing["value"],
                    "select": processing["select"]
                }
            )
            to_render.append({"id": index + FORM_FIELD_SEPARATOR + processing["id"] + ".div", "content": content})

        elif processing["type"] == TEMPLATE_TYPE_LIST_TEXT:
            content = render_template("reload/list-text.j2",
                item={"id": index},
                current={"id": processing["id"], "value": processing["value"]}
            )
            to_render.append({"id": index + FORM_FIELD_SEPARATOR + processing["id"] + ".div", "content": content})

    return to_render


def util_view_reload_input_file_manager(
    name: str,
    index: str,
    files: Optional[list] = None,
    title: Optional[list] = None,
    icons: Optional[list] = None,
    classes: Optional[list] = None,
    hiddens: Optional[list] = None,
) -> list:
    """Create the content necessary to reload a given input file manager.
    
    Args:
        name: The name of the calling module.
        index: The id of the form.
        files: List of files that should be in the file manager, defaults to None.
        title: List of titles for file explorers, defaults to None.
        icons: List of MDI icon names for file explorers, defaults to None.
        classes: List of Bootstrap classes for file explorers, defaults to None.
        hiddens: List of booleans for file explorer collapse buttons, defaults to None.
        
    Returns:
        List of rendered file manager HTML elements.
    """
    try:
        from flask import render_template
    except ImportError:
        return []
    
    # Use empty lists as defaults if None provided
    files = files or []
    title = title or []
    icons = icons or []
    classes = classes or []
    hiddens = hiddens or []
    
    to_render = []
    for i, file in enumerate(files):
        content = render_template("reload/files.j2",
            file_id=f"{index}_files{i}",
            name=index,
            files=file,
            title=title[i],
            icon=icons[i],
            classes=classes[i],
            hidden=hiddens[i]
        )
        to_render.append({
            "id": f"{name.replace(' ', UNDERSCORE)}_{index}_files{i}",
            "content": content
        })
    return to_render


def util_dir_list(root: str, inclusion: Optional[list] = None, modifier: Optional[Callable] = None) -> list:
    """Scan a directory (without children) and return files matching inclusion criteria.
    
    Args:
        root: The root folder to scan.
        inclusion: List of strings that must be present in filenames, defaults to None.
        modifier: Function to transform filenames, defaults to None.
        
    Returns:
        List of filenames matching the criteria.
    """
    results = []
    try:
        current_files = os.listdir(root)
    except Exception:
        return results
    
    for item in current_files:
        if inclusion and not any(inclu in item for inclu in inclusion):
            continue
        if modifier:
            results.append(modifier(item))
        else:
            results.append(item)

    return results


def util_find_files(root: str, inclusion: Optional[list] = None) -> list:
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
    root: str, inclusion: Optional[list] = None, modifier: Optional[Callable] = None, clean: bool = True
) -> dict:
    """Create the directory structure (all directories and subfiles) recursively from a root folder.
    
    Args:
        root: The root folder to scan.
        inclusion: List of strings that must be present in filenames to include, defaults to None.
        modifier: Function to transform filenames, defaults to None.
        clean: Clean all empty folders from results, defaults to True.
        
    Returns:
        Dictionary with nested structure: {"dir": {"file": path, ...}, ...}
    """
    current_dir = {}
    try:
        items = os.listdir(root)
    except FileNotFoundError:
        return current_dir

    for item in items:
        if os.path.isfile(os.path.join(root, item)):
            if inclusion and not any(inclu in item for inclu in inclusion):
                continue
            if modifier:
                current_dir[modifier(item)] = os.path.join(root, item)
            else:
                current_dir[item] = os.path.join(root, item)
        else:
            directory = util_dir_structure(
                os.path.join(root, item), inclusion=inclusion, modifier=modifier
            )
            if not clean or directory:
                current_dir[item] = directory

    return current_dir

def utils_calculate_crc32(filepath):
    """
    Calculate the CRC32 checksum of a file.
    
    Args:
        filepath: Path to the file to checksum
        
    Returns:
        CRC32 checksum as integer
    """
    with open(filepath, 'rb') as file:
        content = file.read()
        return zlib.crc32(content)


def utils_get_directory_crc32(directory_path):
    """
    Generate a dictionary of CRC32 checksums for all files in a directory.
    
    Args:
        directory_path: Path to the directory to scan
        
    Returns:
        Dictionary mapping file paths to their CRC32 checksums
    """
    crc32_dict = {}
    for root, _, files in os.walk(directory_path):
        for file in files:
            filepath = os.path.join(root, file)
            crc32_dict[filepath] = utils_calculate_crc32(filepath)
    return crc32_dict


def utils_create_backup(backup_folders, backup_name):
    """
    Create a .tar.gz backup file containing the specified folders.
    
    Args:
        backup_folders: List of folder paths to include in backup
        backup_name: Name of the backup file to create (should end in .tar.gz)
    """
    with tarfile.open(backup_name, "w:gz") as tar:
        for folder in backup_folders:
            tar.add(folder, arcname=os.path.basename(folder))


def get_config_or_error(settings_manager, *config_paths):
    """
    Safely retrieve one or more configuration values from nested dictionary structure.
    
    This function provides safe access to configuration settings by handling
    KeyError exceptions that may occur when accessing nested dictionary keys.
    Supports retrieving multiple config values in a single call for cleaner code.
    
    Args:
        settings_manager: The SettingsManager instance containing configuration
        *config_paths: One or more dot-separated paths to config values 
                      (e.g., "updates.source.value", "updates.folder.value")
    
    Returns:
        tuple: (config_values, error_response)
            - If successful with single path: (config_value, None)
            - If successful with multiple paths: (dict_of_values, None)
            - If error: (None, error_response_dict) containing error details
    
    Examples:
        >>> # Single value
        >>> source, error = get_config_or_error(settings_mgr, "updates.source.value")
        >>> if error:
        ...     return error
        
        >>> # Multiple values
        >>> configs, error = get_config_or_error(settings_mgr, 
        ...                                       "updates.address.value",
        ...                                       "updates.user.value", 
        ...                                       "updates.password.value")
        >>> if error:
        ...     return error
        >>> address = configs["updates.address.value"]
        >>> user = configs["updates.user.value"]
        >>> password = configs["updates.password.value"]
    """
    try:
        config = settings_manager.get_all_settings()
        results = {}
        
        for config_path in config_paths:
            # Navigate through the nested dictionary
            keys = config_path.split('.')
            value = config
            for key in keys:
                value = value[key]
            results[config_path] = value
        
        # Return single value if only one path was requested
        if len(config_paths) == 1:
            return results[config_paths[0]], None
        
        return results, None
        
    except KeyError as e:
        from flask import render_template
        error_message = ERROR_CONFIG_KEY_NOT_FOUND.format(key=str(e))
        return None, render_template("error.j2", traceback=error_message)


def validate_csrf_token(form_token):
    """Validate CSRF token from form against session token.
    
    Uses constant-time comparison to prevent timing attacks.
    
    Args:
        form_token: Token submitted with form (string)
        
    Returns:
        bool: True if valid, False otherwise
        
    Example:
        >>> from flask import request
        >>> if not validate_csrf_token(request.form.get('csrf_token')):
        ...     return "Invalid CSRF token", 403
    """
    if session is None:
        return False  # Session not available
        
    session_token = session.get('csrf_token')
    
    # Both tokens must exist
    if not session_token or not form_token:
        return False
    
    # Use constant-time comparison to prevent timing attacks
    return hmac.compare_digest(str(session_token), str(form_token))


def util_format_file_size(bytes_size: int) -> str:
    """Format file size from bytes to human-readable format.
    
    Converts byte values to appropriate units (B, KB, MB, GB, TB) with 2 decimal places.
    
    Args:
        bytes_size: File size in bytes.
        
    Returns:
        Formatted string with size and unit (e.g., "1.50 MB").
        
    Examples:
        >>> util_format_file_size(0)
        '0.00 B'
        >>> util_format_file_size(1024)
        '1.00 KB'
        >>> util_format_file_size(1536)
        '1.50 KB'
        >>> util_format_file_size(1048576)
        '1.00 MB'
        >>> util_format_file_size(1073741824)
        '1.00 GB'
    """
    size_float = float(bytes_size)
    for unit in FILE_SIZE_UNITS:
        if size_float < FILE_SIZE_THRESHOLD:
            return f"{size_float:.2f} {unit}"
        size_float /= FILE_SIZE_THRESHOLD
    return f"{size_float:.2f} PB"


def util_format_date(iso_date: str) -> str:
    """Format ISO 8601 date string to human-readable format.
    
    Converts datetime strings from ISO format to 'YYYY-MM-DD HH:MM' format.
    Handles various ISO 8601 formats including timezone info and microseconds.
    
    Args:
        iso_date: Date string in ISO 8601 format (e.g., "2024-03-15T14:30:45.123456")
        
    Returns:
        Formatted string in 'YYYY-MM-DD HH:MM' format, or original string if parsing fails
        
    Examples:
        >>> util_format_date('2024-03-15T14:30:45')
        '2024-03-15 14:30'
        >>> util_format_date('2024-03-15T14:30:45.123456')
        '2024-03-15 14:30'
        >>> util_format_date('2024-03-15T14:30:45+00:00')
        '2024-03-15 14:30'
        >>> util_format_date('invalid')
        'invalid'
    """
    from datetime import datetime
    try:
        # Handle both with and without timezone/microseconds
        dt = datetime.fromisoformat(iso_date.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M')
    except (ValueError, AttributeError):
        return iso_date


def util_get_file_icon(filename: str) -> str:
    """Get Bootstrap icon class for file based on extension.
    
    Maps file extensions to appropriate Bootstrap Icons classes for visual representation.
    Supports common document, media, archive, and code file types.
    
    Args:
        filename: Name of the file (with or without path).
        
    Returns:
        MDI icon class name (e.g., "mdi-file-pdf-box").
        
    Examples:
        >>> util_get_file_icon('document.pdf')
        'mdi-file-pdf-box'
        >>> util_get_file_icon('image.jpg')
        'mdi-file-image'
        >>> util_get_file_icon('archive.zip')
        'mdi-zip-box'
        >>> util_get_file_icon('script.py')
        'mdi-file-code'
        >>> util_get_file_icon('unknown.xyz')
        'mdi-file-document-outline'
    """
    ext = os.path.splitext(filename)[1].lower()
    
    icon_map = {
        '.pdf': 'mdi-file-pdf-box',
        '.doc': 'mdi-file-word', '.docx': 'mdi-file-word',
        '.xls': 'mdi-file-excel', '.xlsx': 'mdi-file-excel',
        '.ppt': 'mdi-file-powerpoint', '.pptx': 'mdi-file-powerpoint',
        '.jpg': 'mdi-file-image', '.jpeg': 'mdi-file-image', '.png': 'mdi-file-image',
        '.gif': 'mdi-file-image', '.bmp': 'mdi-file-image', '.svg': 'mdi-file-image',
        '.mp4': 'mdi-file-video', '.avi': 'mdi-file-video', '.mov': 'mdi-file-video',
        '.mp3': 'mdi-file-music', '.wav': 'mdi-file-music', '.flac': 'mdi-file-music',
        '.zip': 'mdi-zip-box', '.rar': 'mdi-zip-box', '.7z': 'mdi-zip-box',
        '.tar': 'mdi-zip-box', '.gz': 'mdi-zip-box',
        '.txt': 'mdi-file-document', '.md': 'mdi-file-document', '.log': 'mdi-file-document',
        '.py': 'mdi-file-code', '.js': 'mdi-file-code', '.html': 'mdi-file-code',
        '.css': 'mdi-file-code', '.json': 'mdi-file-code', '.xml': 'mdi-file-code',
    }
    
    return icon_map.get(ext, 'mdi-file-document-outline')


def util_generate_preview_html(file_meta: dict, size: str = "60px", with_modal: bool = True) -> str:
    """Generate preview HTML for a file (thumbnail or icon) with optional modal.
    
    Creates an HTML img tag for files with thumbnails, or an MDI icon
    for files without thumbnails. Gracefully falls back to icon if thumbnail
    URL generation fails. When with_modal=True, clicking the thumbnail opens
    a Bootstrap modal with a larger preview.
    
    Args:
        file_meta: File metadata dictionary containing:
            - 'id': File ID (required for modal)
            - 'name': Filename for extension detection
            - 'thumb_150x150' (optional): Relative path to 150x150 thumbnail
            - 'thumb_300x300' (optional): Relative path to 300x300 thumbnail (for modal)
        size: CSS size value for preview (default "60px")
        with_modal: If True, add click-to-enlarge modal (default True)
        
    Returns:
        HTML string containing either <img> tag or <i> icon tag, plus modal HTML if applicable
        
    Examples:
        >>> util_generate_preview_html({'id': 1, 'name': 'photo.jpg', 'thumb_150x150': '.thumbs/...'})
        '<img src="/files/download/..." class="img-thumbnail" ...> + modal HTML'
        
        >>> util_generate_preview_html({'name': 'document.pdf'})
        '<i class="mdi mdi-file-pdf-box text-danger" style="font-size: 2rem;"></i>'
    """
    # Check if thumbnail exists
    if 'thumb_150x150' in file_meta:
        thumb_path = file_meta['thumb_150x150']
        try:
            from flask import url_for
            thumb_url = url_for('file_handler.download', filepath=thumb_path, inline='true')
            
            file_id = file_meta.get('id', 0)
            filename = file_meta.get('name', 'file')
            
            if with_modal and file_id:
                modal_id = f'previewModal_{file_id}'
                
                # Check for larger thumbnail
                large_thumb_path = file_meta.get('thumb_300x300', thumb_path)
                large_url = url_for('file_handler.download', filepath=large_thumb_path, inline='true')
                download_url = url_for('file_handler.download_by_id', file_id=file_id)
                
                # Clickable thumbnail + modal
                html = f'''<img src="{thumb_url}" alt="Preview" class="img-thumbnail" 
                     style="max-width: {size}; max-height: {size}; cursor: pointer;"
                     data-bs-toggle="modal" data-bs-target="#{modal_id}" title="Click to enlarge">
                <div class="modal fade" id="{modal_id}" tabindex="-1" aria-hidden="true">
                    <div class="modal-dialog modal-dialog-centered modal-lg">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title"><i class="mdi mdi-file-image"></i> {filename}</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                            </div>
                            <div class="modal-body text-center">
                                <img src="{large_url}" alt="{filename}" class="img-fluid" style="max-height: 70vh;">
                            </div>
                            <div class="modal-footer">
                                <a href="{download_url}" class="btn btn-primary">
                                    <i class="mdi mdi-download"></i> Download Original
                                </a>
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            </div>
                        </div>
                    </div>
                </div>'''
                return html
            else:
                return f'<img src="{thumb_url}" alt="Preview" class="img-thumbnail" style="max-width: {size}; max-height: {size};">'
        except Exception:
            # Fall back to icon if url_for fails
            pass
    
    # No thumbnail - show file type icon
    icon_class = util_get_file_icon(file_meta['name'])
    return f'<i class="mdi {icon_class}" style="font-size: 2rem;"></i>'

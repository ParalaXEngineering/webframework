# Standard library
import copy
import os
import pathlib
import platform
import shutil
import subprocess
import sys
import tarfile
import traceback
import zipfile

# Third-party
from flask import Blueprint, render_template, request

# Local modules
from ..modules import displayer, site_conf, utilities
from ..modules import SFTPConnection
from ..modules.auth import auth_manager
from ..modules.log.logger_factory import get_logger
from ..modules.threaded.threaded_action import Threaded_action
from ..modules.utilities import get_config_or_error
from ..modules.i18n.messages import (
    ERROR_UPDATER_SETTINGS_NOT_INIT,
    ERROR_UPDATER_SETTINGS_RELOAD,
    ERROR_UPDATER_INVALID_SETTINGS,
    ERROR_UPDATER_UPLOAD_CONFIG,
    ERROR_UPDATER_CONFIG,
    ERROR_UPDATER_SFTP_CONFIG,
    STATUS_UPDATER_APPLYING,
    STATUS_UPDATER_UPLOADING,
    STATUS_UPDATER_DOWNLOADING,
    TEXT_UPDATER_CREATE_UPDATE,
    TEXT_UPDATER_UPLOAD_UPDATE,
    TEXT_UPDATER_SELECT_DOWNLOAD,
    TEXT_UPDATER_APPLY_UPDATE,
    TEXT_UPDATER_LOAD_UPDATE,
    SUBTITLE_UPDATER_CREATION,
    SUBTITLE_UPDATER_DEPLOYMENT,
    BUTTON_UPDATER_CREATE,
    BUTTON_UPDATER_UPLOAD,
    BUTTON_UPDATER_DOWNLOAD,
    BUTTON_UPDATER_APPLY,
    DISTRIB_UPDATER_WINDOWS,
    DISTRIB_UPDATER_LINUX,
    LABEL_UPDATER_FILE_UPLOAD,
    INFO_UPDATER_FOLDER_NOT_EXISTS,
    INFO_UPDATER_FTP_ERROR,
    MSG_UPDATER_APP_RESTART,
    MSG_UPDATER_PLEASE_RESTART,
)

logger = get_logger(__name__)

# Constants - Configuration keys
CONFIG_UPDATES_ADDRESS = "updates.address.value"
CONFIG_UPDATES_USER = "updates.user.value"
CONFIG_UPDATES_PASSWORD = "updates.password.value"
CONFIG_UPDATES_SOURCE = "updates.source.value"
CONFIG_UPDATES_FOLDER = "updates.folder.value"
CONFIG_UPDATES_PATH = "updates.path.value"

# Constants - Directory and file paths
DIR_UPDATES = "updates"
DIR_DOWNLOADS = "downloads"
PARENT_DIR = "../"
FILE_BOOTLOADER_WIN = "BTL.bat"
FILE_BOOTLOADER_LINUX = "BTL.sh"

# Constants - Archive formats
ARCHIVE_FORMAT_TAR_GZ = "r:gz"
PLATFORM_WINDOWS = "windows"

# Constants - Progress percentages
PROGRESS_START = 103
PROGRESS_SUCCESS = 100
PROGRESS_ERROR = 101
PROGRESS_PROCESSING = 103

# Constants - Source modes
SOURCE_FOLDER = "Folder"
SOURCE_FTP = "FTP"

# Constants - File types
ACCEPT_TYPES = [".zip", ".7z", ".rar"]

# Constants - Form button IDs
BTN_ACTION_CREATE = "create"
BTN_ACTION_UPLOAD = "upload"
BTN_ACTION_APPLY = "apply"
BTN_ACTION_DOWNLOAD = "download"
BTN_ACTION_UNPACK = "unpack"


def get_settings_manager():
    """Get the global settings manager instance (initialized at startup)."""
    from ..modules.settings import settings_manager
    return settings_manager


class SETUP_Updater(Threaded_action):
    """Module to create and upload the update packages.

    Update package can be uploaded to FTP servers, provided that the correct credentials are given in the settings
    """

    m_action = None

    m_default_name = "Website engine update creation"

    def __init__(self):
        super().__init__()

    def set_file(self, file: str) -> None:
        """Set the target file for update

        :param package: The target file for update
        :type package: str
        """
        self.m_file = file

    def set_distribution(self, distribution: str) -> None:
        self.m_distribution = distribution

    def set_action(self, action: str) -> None:
        """Set the action to perform

        :param action: Can be the following values:

            * create (to create a new package)
            * upload (to upload a previously created package to the FTP server)
        :type action: str
        """
        self.m_action = action

    def action(self):
        """Execute the module"""
        settings_mgr = get_settings_manager()
        
        # Get SFTP connection parameters with error handling
        configs, error = get_config_or_error(settings_mgr, 
                                             CONFIG_UPDATES_ADDRESS,
                                             CONFIG_UPDATES_USER,
                                             CONFIG_UPDATES_PASSWORD)
        if error:
            if self.m_logger:
                self.m_logger.error(str(ERROR_UPDATER_SFTP_CONFIG))
            return
        
        # Type guard: configs is dict when error is None
        assert isinstance(configs, dict), "Config should be dict when no error"
        
        sftp_conn = SFTPConnection.SFTPConnection(
            configs[CONFIG_UPDATES_ADDRESS],
            configs[CONFIG_UPDATES_USER],
            configs[CONFIG_UPDATES_PASSWORD]
        )

        site_conf_obj = site_conf.site_conf_obj

        if self.m_action in ("update", "load_update_file"):
            if self.m_scheduler:
                self.m_scheduler.emit_status(self.get_name(), STATUS_UPDATER_APPLYING, PROGRESS_START)
            settings_manager_inst = get_settings_manager()
            if not settings_manager_inst:
                if self.m_logger:
                    self.m_logger.error(ERROR_UPDATER_SETTINGS_NOT_INIT)
                return
            current_param = settings_manager_inst.get_all_settings()

            # --- Unzip / Untar ---
            if platform.system().lower() == PLATFORM_WINDOWS:
                with zipfile.ZipFile(os.path.join(self.m_file), mode="r") as zf:
                    zf.extractall(path=PARENT_DIR)
            else:
                # Safe extraction for tar.gz
                def is_within_directory(directory, target):
                    abs_directory = os.path.abspath(directory)
                    abs_target = os.path.abspath(target)
                    return os.path.commonprefix([abs_directory, abs_target]) == abs_directory

                dest = PARENT_DIR
                with tarfile.open(os.path.join(self.m_file), mode=ARCHIVE_FORMAT_TAR_GZ) as tf:
                    for member in tf.getmembers():
                        target_path = os.path.join(dest, member.name)
                        if not is_within_directory(dest, target_path):
                            raise Exception(f"Blocked path traversal in tar member: {member.name}")
                    tf.extractall(path=dest)

            # Recharger le nouveau config.json (qui vient d'être écrasé par l'archive)
            # Force reload from disk
            settings_mgr = get_settings_manager()
            if not settings_mgr:
                if self.m_logger:
                    self.m_logger.error(ERROR_UPDATER_SETTINGS_RELOAD)
                return
            settings_mgr.load()
            new_param = settings_mgr.get_all_settings()
            
            # Type guard: ensure new_param is dict
            if not isinstance(new_param, dict):
                if self.m_logger:
                    self.m_logger.error(ERROR_UPDATER_INVALID_SETTINGS)
                return

            # --- MERGE new_param -> current_param ---
            for topic, topic_data in new_param.items():  # type: ignore
                # Nouveau topic ? Copie complète (deepcopy)
                if topic not in current_param or not isinstance(topic_data, dict):
                    current_param[topic] = copy.deepcopy(topic_data)
                    continue

                cur_topic = current_param[topic]

                # Parcours des clés du topic (ppu, hmi, friendly, etc.)
                for key, new_item in topic_data.items():
                    # Clé absente côté courant ? Création (deepcopy)
                    if key not in cur_topic:
                        cur_topic[key] = copy.deepcopy(new_item)
                        continue

                    cur_item = cur_topic[key]

                    # Paramètre "persistable" (dict avec persistent)
                    if isinstance(new_item, dict) and 'persistent' in new_item:
                        if new_item.get('persistent'):
                            # persistent == true -> on remplace TOUT le bloc
                            cur_topic[key] = copy.deepcopy(new_item)
                        else:
                            # persistent == false -> garder la value, maj des métadonnées
                            if isinstance(cur_item, dict):
                                for meta in ('type', 'friendly', 'persistent'):
                                    if meta in new_item:
                                        cur_item[meta] = new_item[meta]
                                # NE PAS toucher à cur_item['value']
                            else:
                                # Structure incohérente : fallback copie complète
                                cur_topic[key] = copy.deepcopy(new_item)
                    else:
                        # Pas un paramètre persistable (ex: friendly d'un topic)
                        cur_topic[key] = copy.deepcopy(new_item)

                # Supprimer les anciennes clés absentes du nouveau topic
                for key in list(cur_topic.keys()):
                    if key not in topic_data:
                        cur_topic.pop(key)

            # Supprimer les anciens topics absents du nouveau fichier
            for topic in list(current_param.keys()):
                if topic not in new_param:
                    current_param.pop(topic)

            # Save merged parameters
            if settings_mgr:
                settings_mgr.storage.save(current_param)

            # Configuration pour le lancement du bootloader
            if site_conf_obj and platform.system().lower() == PLATFORM_WINDOWS:
                path_to_bootloader = os.path.join(FILE_BOOTLOADER_WIN)
                path_to_new_executable = os.path.join(site_conf_obj.m_app["name"] + "_update.exe")
                original_executable_path = os.path.join(site_conf_obj.m_app["name"] + ".exe")
            elif site_conf_obj:  # Assuming Linux for other platforms
                current_directory = os.path.dirname(os.path.abspath(__file__))
                path_to_bootloader = os.path.join(current_directory, FILE_BOOTLOADER_LINUX)
                path_to_new_executable = os.path.join(site_conf_obj.m_app["name"] + "_update")
                original_executable_path = os.path.join(site_conf_obj.m_app["name"])
            else:
                self.console_write("site_conf_obj not initialized", "ERROR")
                return
                
            # Lancer le bootloader dans un nouveau processus

            # Vérifier si le script BTL.sh existe
            if not os.path.isfile(path_to_bootloader):
                logger.error(f"Le script {path_to_bootloader} n'existe pas.")
                return
            if not os.path.isfile(path_to_new_executable):
                logger.error(f"Le script {path_to_new_executable} n'existe pas.")
                return
            if not os.path.isfile(original_executable_path):
                logger.error(f"Le script {original_executable_path} n'existe pas.")
                return

            try:
                if platform.system().lower() == PLATFORM_WINDOWS:
                    subprocess.Popen([path_to_bootloader, path_to_new_executable, original_executable_path])
                else:  # Assuming Linux for other platforms
                    subprocess.Popen(["bash", path_to_bootloader, path_to_new_executable, original_executable_path])
            except Exception as e:
                logger.exception(f"Error launching bootloader: {e}")

            if self.m_scheduler:
                self.m_scheduler.emit_status(self.get_name(), STATUS_UPDATER_APPLYING, PROGRESS_SUCCESS)
            if "distribution" in self.m_file:
                if self.m_scheduler:
                    self.m_scheduler.emit_status(
                        self.get_name(),
                        MSG_UPDATER_APP_RESTART,
                        102,
                    )
            else:
                if self.m_scheduler:
                    self.m_scheduler.emit_status(
                        self.get_name(), MSG_UPDATER_PLEASE_RESTART, 102
                    )

        elif self.m_action == "download":
            # Get source configuration with error handling
            source, error = get_config_or_error(get_settings_manager(), CONFIG_UPDATES_SOURCE)
            if error:
                if self.m_logger:
                    self.m_logger.error(f"Failed to get {CONFIG_UPDATES_SOURCE} from config")
                if self.m_scheduler:
                    self.m_scheduler.emit_status(
                        self.get_name(), f"Configuration error: {CONFIG_UPDATES_SOURCE} not found", PROGRESS_ERROR
                    )
                return

            try:
                os.mkdir(os.path.join(DIR_UPDATES))
            except FileExistsError:
                pass

            # Folder mode
            if self.m_scheduler:
                self.m_scheduler.emit_status(
                    self.get_name(), STATUS_UPDATER_DOWNLOADING, PROGRESS_PROCESSING
                )
            if source == SOURCE_FOLDER:
                folder_value, error = get_config_or_error(get_settings_manager(), CONFIG_UPDATES_FOLDER)
                if error:
                    if self.m_logger:
                        self.m_logger.error(f"Failed to get {CONFIG_UPDATES_FOLDER} from config")
                    if self.m_scheduler:
                        self.m_scheduler.emit_status(
                            self.get_name(), f"Configuration error: {CONFIG_UPDATES_FOLDER} not found", PROGRESS_ERROR
                        )
                    return
                
                if site_conf_obj and isinstance(folder_value, str):
                    shutil.copyfile(
                        os.path.join(
                            folder_value,
                            DIR_UPDATES,
                            site_conf_obj.m_app["name"],
                            self.m_file,
                        ),
                        os.path.join(DIR_DOWNLOADS, self.m_file),
                    )

            # FTP mode
            elif source == SOURCE_FTP:
                try:
                    if site_conf_obj:
                        # Get FTP path configuration
                        path_value, error = get_config_or_error(get_settings_manager(), CONFIG_UPDATES_PATH)
                        if error:
                            if self.m_logger:
                                self.m_logger.error(f"Failed to get {CONFIG_UPDATES_PATH} from config")
                            if self.m_scheduler:
                                self.m_scheduler.emit_status(
                                    self.get_name(), f"Configuration error: {CONFIG_UPDATES_PATH} not found", PROGRESS_ERROR
                                )
                            return
                        
                        # Définition des chemins
                        if isinstance(path_value, str):
                            remote_file_path = os.path.join(
                                path_value,
                                DIR_UPDATES,
                                site_conf_obj.m_app["name"],
                                self.m_file
                            ).replace("\\", "/")  # Assure la compatibilité Windows/Linux

                            local_file_path = os.path.join(DIR_UPDATES, self.m_file)

                            # Téléchargement du fichier
                            sftp_conn.download_file(remote_file_path, local_file_path)

                except Exception as e:
                    if self.m_logger:
                        self.m_logger.info(f"Update download failed: {e}")
                    if self.m_scheduler:
                        self.m_scheduler.emit_status(
                            self.get_name(),
                            STATUS_UPDATER_DOWNLOADING,
                            PROGRESS_ERROR,
                        )

            if self.m_scheduler:
                self.m_scheduler.emit_status(
                    self.get_name(), STATUS_UPDATER_DOWNLOADING, PROGRESS_SUCCESS
                )

            # Relist the package availables
            try:
                packages_total = os.listdir(os.path.join(DIR_UPDATES))
                packages = []
                for pack in packages_total:
                    if (
                        "distribution" in pack
                        and platform.system() in pack
                        and sys.argv[1] in pack
                    ):
                        packages.append(pack)
                    if "sources" in pack and sys.argv[1] in pack:
                        packages.append(pack)
            except Exception:
                packages = []

            # Update the list of package since it has been changed
            inputs = {
                "update_package": {
                    "label": "Select",
                    "id": "update_package",
                    "value": "",
                    "type": "select",
                    "data": packages,
                }
            }
            reloader = utilities.util_view_reload_multi_input("update_package", inputs)
            if self.m_scheduler:
                self.m_scheduler.emit_reload(reloader)

        elif self.m_action == "create":
            pass

            # Create the udpate folder if needed
            try:
                os.makedirs(os.path.join(DIR_UPDATES))
            except FileExistsError:
                # Alread exists, no big deal
                pass

            if self.m_scheduler:
                self.m_scheduler.emit_status(
                    self.get_name(), f"Creation of the update package for {self.m_distribution}", PROGRESS_PROCESSING
                )
            # Create the package with pyinstaller
            try:
                if site_conf_obj:
                    site_conf_obj.create_distribuate(self.m_distribution)
            except Exception as e:
                traceback_str = traceback.format_exc()
                if self.m_logger:
                    self.m_logger.warning("Update creation failed: " + str(e))
                    self.m_logger.info("Traceback was: " + traceback_str)
                if self.m_scheduler:
                    self.m_scheduler.emit_status(
                        self.get_name(),
                        f"Creation of the update package for {self.m_distribution}",
                        PROGRESS_ERROR,
                        supplement=str(e),
                    )
                return
            directories = [os.path.join("updater", self.m_distribution, "dist")]
            if site_conf_obj:
                version = site_conf_obj.m_app["version"].split("_")[0]
                if (self.m_distribution == DISTRIB_UPDATER_WINDOWS):
                    with zipfile.ZipFile(
                        os.path.join(
                            DIR_UPDATES,
                            site_conf_obj.m_app["name"]
                            + "_"
                            + version
                            + "_"
                            + platform.system()
                            + ".zip",
                        ),
                        mode="w",
                    ) as archive:
                        for dir in directories:
                            directory = pathlib.Path(dir)
                            for file_path in directory.rglob("*"):
                                archive.write(
                                    file_path, arcname=file_path.relative_to(directory)
                                )
            if self.m_scheduler:
                self.m_scheduler.emit_status(
                    self.get_name(), f"Creation of the update package for {self.m_distribution}", PROGRESS_SUCCESS
                )

        elif self.m_action == "upload":
            updates_folder = DIR_UPDATES
            files_to_upload = []

            # Vérifiez les fichiers présents dans le dossier updates
            for file in os.listdir(updates_folder):
                if file.endswith(".zip") or file.endswith(".tar.gz"):
                    files_to_upload.append(os.path.join(updates_folder, file))

            if not files_to_upload:
                if self.m_scheduler:
                    self.m_scheduler.emit_status(self.get_name(), STATUS_UPDATER_UPLOADING, PROGRESS_ERROR)
                return

            if self.m_scheduler:
                self.m_scheduler.emit_status(self.get_name(), STATUS_UPDATER_UPLOADING, PROGRESS_PROCESSING)

            # Get configuration for upload
            configs, error = get_config_or_error(get_settings_manager(),
                                                 CONFIG_UPDATES_SOURCE,
                                                 CONFIG_UPDATES_FOLDER,
                                                 CONFIG_UPDATES_PATH)
            if error:
                if self.m_logger:
                    self.m_logger.error(ERROR_UPDATER_UPLOAD_CONFIG)
                if self.m_scheduler:
                    self.m_scheduler.emit_status(self.get_name(), ERROR_UPDATER_CONFIG, PROGRESS_ERROR)
                return
            
            # Type guard: configs is dict when error is None
            assert isinstance(configs, dict), "Config should be dict when no error"

            # Folder mode
            if configs[CONFIG_UPDATES_SOURCE] == SOURCE_FOLDER:
                try:
                    if site_conf_obj:
                        os.makedirs(os.path.join(configs[CONFIG_UPDATES_FOLDER], DIR_UPDATES, site_conf_obj.m_app["name"]), exist_ok=True)
                except Exception as e:
                    if self.m_scheduler:
                        self.m_scheduler.emit_status(self.get_name(), f"Failed to create directories: {str(e)}", PROGRESS_ERROR)
                    return

                for file in files_to_upload:
                    try:
                        if site_conf_obj:
                            shutil.copyfile(
                                file,
                                os.path.join(
                                    configs[CONFIG_UPDATES_FOLDER],
                                    DIR_UPDATES,
                                    site_conf_obj.m_app["name"],
                                    os.path.basename(file),
                                ),
                            )
                    except Exception as e:
                        if self.m_scheduler:
                            self.m_scheduler.emit_status(self.get_name(), f"Failed to copy file {file}: {str(e)}", PROGRESS_ERROR)
                        return

            # FTP mode
            elif configs[CONFIG_UPDATES_SOURCE] == SOURCE_FTP:
                try:
                    if site_conf_obj:
                        # Définition du dossier distant
                        remote_dir = os.path.join(
                            configs[CONFIG_UPDATES_PATH],
                            DIR_UPDATES,
                            site_conf_obj.m_app["name"]
                        ).replace("\\", "/")  # Compatibilité Windows/Linux

                        # Vérification et création du dossier distant si nécessaire
                        try:
                            sftp_conn.listdir(remote_dir)
                        except FileNotFoundError:
                            sftp_conn.mkdir(remote_dir)

                        # Envoi des fichiers
                        for file in files_to_upload:
                            remote_file_path = os.path.join(remote_dir, os.path.basename(file)).replace("\\", "/")
                            sftp_conn.upload_file(file, remote_file_path)  # Upload du fichier

                except Exception as e:
                    if self.m_logger:
                        self.m_logger.info(f"Update upload failed: {e}")
                    if self.m_scheduler:
                        self.m_scheduler.emit_status(
                            self.get_name(),
                            STATUS_UPDATER_UPLOADING,
                            PROGRESS_ERROR, str(e)
                        )

            if self.m_scheduler:
                self.m_scheduler.emit_status(
                    self.get_name(), STATUS_UPDATER_UPLOADING, PROGRESS_SUCCESS
                )


bp = Blueprint("updater", __name__, url_prefix="/updater")


@bp.route("/update", methods=["GET", "POST"])
def update():
    """Update page to handle update package creation (if credential authorize it) or update package download and application"""
    site_conf_obj = site_conf.site_conf_obj
    data_in = None
    if request.method == "POST":
        data_in = utilities.util_post_to_json(request.form.to_dict())
        data_in = data_in[SETUP_Updater.m_default_name]

        if BTN_ACTION_CREATE in data_in:
            packager = SETUP_Updater()
            packager.set_action("create")
            packager.set_distribution(data_in["distrib"])
            packager.start()
        elif BTN_ACTION_UPLOAD in data_in:
            packager = SETUP_Updater()
            packager.set_action("upload")
            packager.start()
        elif BTN_ACTION_APPLY in data_in:
            packager = SETUP_Updater()
            packager.set_action("update")
            packager.set_file(data_in["update_package"])
            packager.start()
        elif BTN_ACTION_DOWNLOAD in data_in:
            packager = SETUP_Updater()
            packager.set_action("download")
            packager.set_file(data_in["download_package"])
            packager.start()
        elif BTN_ACTION_UNPACK in data_in:
            try:
                f = request.files[".load_update_file"]
                try:
                    os.mkdir(DIR_DOWNLOADS)
                except FileExistsError:
                    pass
                if f.filename:
                    f.save(os.path.join(DIR_DOWNLOADS, f.filename))
                packager = SETUP_Updater()
                packager.set_action("load_update_file")
                if f.filename:
                    packager.set_file(f.filename)
                packager.start()
            except Exception:
                pass

    disp = displayer.Displayer()
    disp.add_module(SETUP_Updater, display=False)
    disp.set_title(SETUP_Updater.m_default_name)
    
    # Load configuration with error handling
    configs, error = get_config_or_error(get_settings_manager(),
                                         CONFIG_UPDATES_SOURCE,
                                         CONFIG_UPDATES_FOLDER,
                                         CONFIG_UPDATES_PATH,
                                         CONFIG_UPDATES_ADDRESS,
                                         CONFIG_UPDATES_USER,
                                         CONFIG_UPDATES_PASSWORD)
    if error:
        return error
    
    # Type guard: configs is dict[str, Any] when error is None
    assert isinstance(configs, dict), "Config should be dict when no error"

    # Check if user is admin
    current_user_name = None
    if auth_manager:
        current_user_name = auth_manager.get_current_user()
    user = None
    if auth_manager and current_user_name:
        user = auth_manager.get_user(current_user_name)
    is_admin = user and "admin" in user.groups if user else False
    
    if is_admin and not ((getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"))):
        disp.add_master_layout(
            displayer.DisplayerLayout(
                displayer.Layouts.VERTICAL,
                [3, 6, 3],
                subtitle=SUBTITLE_UPDATER_CREATION,
                alignment=[
                    displayer.BSalign.L,
                    displayer.BSalign.L,
                    displayer.BSalign.R,
                ],
            )
        )

        disp.add_display_item(displayer.DisplayerItemText(TEXT_UPDATER_CREATE_UPDATE), 0)
        disp.add_display_item(displayer.DisplayerItemInputSelect("distrib", None, None, [DISTRIB_UPDATER_WINDOWS, DISTRIB_UPDATER_LINUX]), 1)
        disp.add_display_item(displayer.DisplayerItemButton(BTN_ACTION_CREATE, BUTTON_UPDATER_CREATE), 2)

        disp.add_master_layout(
            displayer.DisplayerLayout(
                displayer.Layouts.VERTICAL,
                [3, 6, 3],
                subtitle="",
                alignment=[
                    displayer.BSalign.L,
                    displayer.BSalign.L,
                    displayer.BSalign.R,
                ],
            )
        )
        disp.add_display_item(
            displayer.DisplayerItemText(TEXT_UPDATER_UPLOAD_UPDATE), 0
        )
        disp.add_display_item(displayer.DisplayerItemButton(BTN_ACTION_UPLOAD, BUTTON_UPDATER_UPLOAD), 2)

    to_apply = utilities.util_dir_structure(os.path.join(DIR_UPDATES), [".zip"])
    disp.add_master_layout(
        displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL,
            [3, 6, 3],
            subtitle=SUBTITLE_UPDATER_DEPLOYMENT,
            alignment=[displayer.BSalign.L, displayer.BSalign.L, displayer.BSalign.R],
        )
    )

    content = to_apply.values()
    content = [item for item in content if platform.system() in item]

    disp.add_display_item(displayer.DisplayerItemText(TEXT_UPDATER_APPLY_UPDATE), 0)
    disp.add_display_item(
        displayer.DisplayerItemInputSelect("update_package", None, None, list(content)), 1
    )
    disp.add_display_item(displayer.DisplayerItemButton(BTN_ACTION_APPLY, BUTTON_UPDATER_APPLY), 2)

    # Folder mode
    if configs[CONFIG_UPDATES_SOURCE] == SOURCE_FOLDER:
        if not os.path.exists(os.path.join(configs[CONFIG_UPDATES_FOLDER])):
            disp.add_master_layout(
                displayer.DisplayerLayout(
                    displayer.Layouts.VERTICAL,
                    [12],
                    subtitle="",
                    alignment=[displayer.BSalign.C],
                )
            )
            disp.add_display_item(
                displayer.DisplayerItemAlert(INFO_UPDATER_FOLDER_NOT_EXISTS, displayer.BSstyle.INFO), 0
            )
        else:
            if site_conf_obj:
                content = utilities.util_dir_structure(
                    os.path.join(
                        configs[CONFIG_UPDATES_FOLDER],
                        DIR_UPDATES,
                        site_conf_obj.m_app["name"],
                    ),
                    inclusion=[".zip"],
                )
            else:
                content = {}
            disp.add_master_layout(
                displayer.DisplayerLayout(
                    displayer.Layouts.VERTICAL,
                    [3, 6, 3],
                    subtitle="",
                    alignment=[
                        displayer.BSalign.L,
                        displayer.BSalign.L,
                        displayer.BSalign.R,
                    ],
                )
            )
            disp.add_display_item(
                displayer.DisplayerItemText(TEXT_UPDATER_SELECT_DOWNLOAD), 0
            )
            disp.add_display_item(
                displayer.DisplayerItemInputSelect(
                    "download_package", None, None, list(content.values()) if isinstance(content, dict) else []
                ),
                1,
            )
            disp.add_display_item(
                displayer.DisplayerItemButton(BTN_ACTION_DOWNLOAD, BUTTON_UPDATER_DOWNLOAD), 2
            )

    # FTP mode
    elif configs[CONFIG_UPDATES_SOURCE] == SOURCE_FTP:
        try:
            sftp_conn = SFTPConnection.SFTPConnection(
                configs[CONFIG_UPDATES_ADDRESS],
                configs[CONFIG_UPDATES_USER],
                configs[CONFIG_UPDATES_PASSWORD]
            )

            # Définition du chemin distant
            remote_path = ""
            if site_conf_obj:
                remote_path = os.path.join(
                    configs[CONFIG_UPDATES_PATH],
                    DIR_UPDATES,
                    site_conf_obj.m_app["name"]
                ).replace("\\", "/")  # Assure la compatibilité Windows/Linux

            # Liste des fichiers dans le dossier distant
            try:
                if remote_path:
                    content = sftp_conn.listdir(remote_path)
                    content = [item for item in content if platform.system() in item]
                else:
                    content = []
            except FileNotFoundError:
                content = []

            # Fermeture de la connexion SFTP
            sftp_conn.close()

        except Exception:
            disp.add_master_layout(
                displayer.DisplayerLayout(
                    displayer.Layouts.VERTICAL,
                    [12],
                    subtitle="",
                    alignment=[displayer.BSalign.C],
                )
            )
            disp.add_display_item(
                displayer.DisplayerItemAlert(INFO_UPDATER_FTP_ERROR, displayer.BSstyle.INFO), 0
            )

        disp.add_master_layout(
            displayer.DisplayerLayout(
                displayer.Layouts.VERTICAL,
                [3, 6, 3],
                subtitle="",
                alignment=[
                    displayer.BSalign.L,
                    displayer.BSalign.L,
                    displayer.BSalign.R,
                ],
            )
        )
        disp.add_display_item(
            displayer.DisplayerItemText(TEXT_UPDATER_SELECT_DOWNLOAD), 0
        )
        disp.add_display_item(
            displayer.DisplayerItemInputSelect(
                "download_package", None, None, content
            ),
            1,
        )
        disp.add_display_item(
            displayer.DisplayerItemButton(BTN_ACTION_DOWNLOAD, BUTTON_UPDATER_DOWNLOAD), 2
        )

    disp.add_master_layout(
        displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL,
            [3, 6, 3],
            subtitle="",
            alignment=[displayer.BSalign.L, displayer.BSalign.L, displayer.BSalign.R],
        )
    )
    disp.add_display_item(displayer.DisplayerItemText(TEXT_UPDATER_LOAD_UPDATE), 0)
    disp.add_display_item(displayer.DisplayerItemFileUpload(
        "load_update_file",
        LABEL_UPDATER_FILE_UPLOAD,
        category="updates",
        accept_types=ACCEPT_TYPES
    ), 1)

    return render_template(
        "base_content.j2", content=disp.display(), target="updater.update"
    )


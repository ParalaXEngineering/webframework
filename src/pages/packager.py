# Standard library
import datetime
import errno
import os
import shutil
import socket
import sys
import tempfile
import time

# Third-party
from flask import Blueprint, render_template, request

# Local modules
from ..modules import displayer, scheduler, site_conf, utilities
from ..modules import SFTPConnection
from ..modules.auth import auth_manager
from ..modules.threaded.threaded_action import Threaded_action
from ..modules.utilities import get_config_or_error

# Constants - Configuration keys
CONFIG_UPDATES_ADDRESS = "updates.address.value"
CONFIG_UPDATES_USER = "updates.user.value"
CONFIG_UPDATES_PASSWORD = "updates.password.value"
CONFIG_UPDATES_SOURCE = "updates.source.value"
CONFIG_UPDATES_FOLDER = "updates.folder.value"
CONFIG_UPDATES_PATH = "updates.path.value"

# Constants - Directory and file paths
DIR_PACKAGES = "packages"
DIR_DOWNLOADS = "downloads"
DIR_RESOURCES = "ressources"
FILE_VERSION = "version.txt"
VERSION_FILE_PATH = os.path.join(DIR_RESOURCES, FILE_VERSION)
ARCHIVE_DATE_FORMAT = "%y%m%d_"

# Constants - Status messages
STATUS_CREATING_ARCHIVE = "Creating archive, this might take a while"
STATUS_UPLOADING_PACKAGE = "Uploading package, this might take a while"
STATUS_DOWNLOADING_PACKAGE = "Downloading package, this might take a while"
STATUS_DELETING_TAR_GZ = "Deleting old tar.gz content"
STATUS_UNPACKING_ARCHIVE = "Unpacking archive, this might take a while"
STATUS_UNPACKING_SUCCESS = "Unpacking archive success"
ERROR_SFTP_CONFIG = "Failed to get SFTP config from settings"
ERROR_UPLOAD_CONFIG = "Failed to get upload config from settings"
ERROR_DOWNLOAD_CONFIG = "Failed to get download config from settings"
ERROR_PACKAGE_MUST_ZIP = "Package must be a .zip"
ERROR_CONFIG = "Configuration error"
ERROR_UNPACKING_FAILED = "Unpacking failed: "
ERROR_PACKAGE_UPLOAD_FAILED = "Package uploading failed: "
ERROR_PACKAGE_DOWNLOAD_FAILED = "Download package failed: "
ERROR_LONG_PATH = "Skipping file with too long path: "

# Constants - Source modes
SOURCE_FOLDER = "Folder"
SOURCE_FTP = "FTP"

# Constants - Progress percentages
PROGRESS_START = 103
PROGRESS_SUCCESS = 100
PROGRESS_ERROR = 101
PROGRESS_WARNING = 50

# Constants - Error handling
ERROR_LONG_PATH_CODE = errno.ENAMETOOLONG
REFRESH_DELAY = 7
REFRESH_CONTENT = "<meta http-equiv='refresh' content='5'><p>Unpacking completed successfully. The page will reload shortly.</p>"

# Constants - UI/Display
SUBTITLE_PACKAGE_CREATION = "Package creation"
SUBTITLE_PACKAGE_RESTORATION = "Package restoration"
TEXT_CREATE_PACKAGE = "Create a new package"
TEXT_UPLOAD_PACKAGE = "Upload package"
TEXT_SELECT_PACKAGE = "Select a package to download"
TEXT_PACKAGE_AVAILABLE = "Package available localy"
BUTTON_PACKAGE_CREATION = "Package creation"
BUTTON_PACKAGE_UPLOAD = "Package upload"
BUTTON_PACKAGE_INSTALL = "Install Package"
BUTTON_INSTALL_PACKAGE_ALT = "Install package"
BUTTON_UNPACK = "Unpack"
LABEL_FILES_TO_UPLOAD = "Files to upload"
LABEL_PACKAGE_TO_UNPACK = "Package to unpack"
ICON_FILE_UPLOAD = "file-upload"
ICON_FILE_PACKAGE = "file-package"
STYLE_PRIMARY = "primary"
INFO_FOLDER_NOT_EXISTS = "Configured package folder doesn't exists"
INFO_FTP_NOT_ACCESSIBLE = "FTP server not accessible, please check your connection, use a zip file or use a local folder"
INFO_FTP_UNKNOWN_ERROR = "Unkown FTP error: "


def get_settings_manager():
    """Get the global settings manager instance (initialized at startup)."""
    from ..modules.settings import settings_manager
    return settings_manager


class SETUP_Packager(Threaded_action):
    m_default_name = "Binaries Package Manager"
    m_action = ""

    def set_file(self, file):
        self.m_file = file

    def set_action(self, action):
        self.m_action = action

    def action(self):
        # Get SFTP connection parameters with error handling
        configs, error = get_config_or_error(get_settings_manager(),
                                             CONFIG_UPDATES_ADDRESS,
                                             CONFIG_UPDATES_USER,
                                             CONFIG_UPDATES_PASSWORD)
        if error:
            if self.m_logger:
                self.m_logger.error(ERROR_SFTP_CONFIG)
            return
        
        # Type guard: configs is dict when error is None
        assert isinstance(configs, dict), "Config should be dict when no error"
        
        sftp_conn = SFTPConnection.SFTPConnection(
            configs[CONFIG_UPDATES_ADDRESS],
            configs[CONFIG_UPDATES_USER],
            configs[CONFIG_UPDATES_PASSWORD]
        )

        site_conf_obj = site_conf.site_conf_obj

        if self.m_action == "create_package":
            try:
                os.mkdir(os.path.join(DIR_PACKAGES))
            except FileExistsError:
                pass

            # Sleep as it looks like shutil doesn't support concurrent access
            if self.m_scheduler:
                self.m_scheduler.emit_status(
                    self.get_name(), STATUS_CREATING_ARCHIVE, PROGRESS_START
                )
            today = datetime.datetime.now()

            try:
                with open(VERSION_FILE_PATH, 'r') as file:
                    package_version = file.read()
                if site_conf_obj and site_conf_obj.m_app["version"].split("_")[0] != package_version:
                    with open(VERSION_FILE_PATH, 'w') as file:
                        file.write(site_conf_obj.m_app["version"].split("_")[0])

                # Create a temporary directory to hold the archive content
                with tempfile.TemporaryDirectory() as temp_dir:
                    # Liste des dossiers spécifiques pour inclure tous les fichiers, y compris les .tar.gz
                    include_tar_gz_dirs = site_conf_obj.m_include_tar_gz_dirs if site_conf_obj else []

                    # Parcourir les fichiers dans DIR_RESOURCES
                    for root, dirs, files in os.walk(DIR_RESOURCES):
                        relative_path = os.path.relpath(root, DIR_RESOURCES)
                        dest_dir = os.path.join(temp_dir, relative_path)
                        os.makedirs(dest_dir, exist_ok=True)

                        for file in files:
                            source_path = os.path.join(root, file)
                            dest_path = os.path.join(dest_dir, file)

                            abs_root = os.path.abspath(root)
                            abs_tools_root = os.path.abspath(os.path.join(DIR_RESOURCES, "binaries", "tools"))

                            # Vérifier si le dossier actuel est un dossier spécifique
                            if any(os.path.abspath(root).startswith(os.path.abspath(include_dir)) for include_dir in include_tar_gz_dirs):
                                # Copier tous les fichiers des dossiers spécifiques
                                shutil.copy(source_path, dest_path)
                            elif not file.endswith(".tar.gz"):
                                # Copier uniquement les fichiers non .tar.gz pour les autres dossiers
                                shutil.copy(source_path, dest_path)
                            elif (
                                file.endswith(".tar.gz")
                                and not abs_root == abs_tools_root  # <- exclut ceux à la racine de tools
                                and abs_root.startswith(abs_tools_root)  # <- mais garde ceux dans ses sous-dossiers
                            ):
                                shutil.copy(source_path, dest_path)

                    # Créer l'archive à partir du répertoire temporaire
                    archive_path = os.path.join(DIR_PACKAGES, today.strftime(ARCHIVE_DATE_FORMAT + self.m_file))
                    shutil.make_archive(archive_path, "zip", temp_dir)

                if self.m_scheduler:
                    self.m_scheduler.emit_status(
                        self.get_name(), STATUS_CREATING_ARCHIVE, PROGRESS_SUCCESS
                    )
            except Exception as e:
                if self.m_logger:
                    self.m_logger.info("Package creation failed: " + str(e))
                if self.m_scheduler:
                    self.m_scheduler.emit_status(
                        self.get_name(), "Error in creating the archive: " + str(e), PROGRESS_ERROR
                    )

            to_upload_files = utilities.util_dir_structure(
                os.path.join(DIR_PACKAGES), inclusion=[".zip"]
            )
            reloader = utilities.util_view_reload_input_file_manager(
                self.m_default_name,
                "upload_package",
                [to_upload_files],
                [LABEL_FILES_TO_UPLOAD],
                [ICON_FILE_UPLOAD],
                [STYLE_PRIMARY],
                [False],
            )
            if self.m_scheduler:
                self.m_scheduler.emit_reload(reloader)

        elif self.m_action == "upload_package":
            if self.m_scheduler:
                self.m_scheduler.emit_status(
                    self.get_name(), STATUS_UPLOADING_PACKAGE, PROGRESS_START
                )

            # Get configuration for upload
            upload_configs, error = get_config_or_error(get_settings_manager(),
                                                        CONFIG_UPDATES_SOURCE,
                                                        CONFIG_UPDATES_FOLDER,
                                                        CONFIG_UPDATES_PATH)
            if error:
                if self.m_logger:
                    self.m_logger.error(ERROR_UPLOAD_CONFIG)
                if self.m_scheduler:
                    self.m_scheduler.emit_status(self.get_name(), ERROR_CONFIG, PROGRESS_ERROR)
                return
            
            # Type guard: upload_configs is dict when error is None
            assert isinstance(upload_configs, dict), "Config should be dict when no error"

            # Folder mode
            if upload_configs[CONFIG_UPDATES_SOURCE] == SOURCE_FOLDER:
                try:
                    os.mkdir(
                        os.path.join(upload_configs[CONFIG_UPDATES_FOLDER], DIR_PACKAGES)
                    )
                except FileExistsError:
                    pass

                try:
                    os.mkdir(
                        os.path.join(
                            upload_configs[CONFIG_UPDATES_FOLDER],
                            DIR_PACKAGES,
                            site_conf_obj.m_app["name"] if site_conf_obj else "unknown",
                        )
                    )
                except FileExistsError:
                    pass

                shutil.copyfile(
                    self.m_file,
                    os.path.join(
                        upload_configs[CONFIG_UPDATES_FOLDER],
                        DIR_PACKAGES,
                        site_conf_obj.m_app["name"] if site_conf_obj else "unknown",
                        self.m_file.split(os.path.sep)[-1],
                    ),
                )

            # FTP mode
            elif upload_configs[CONFIG_UPDATES_SOURCE] == SOURCE_FTP:
                try:
                    # Définition du dossier distant
                    remote_dir = os.path.join(
                        upload_configs[CONFIG_UPDATES_PATH],
                        DIR_PACKAGES,
                        site_conf_obj.m_app["name"] if site_conf_obj else "unknown"
                    ).replace("\\", "/")  # Compatibilité Windows/Linux
                    # Vérification et création du dossier distant si nécessaire
                    try:
                        sftp_conn.listdir(remote_dir)
                    except FileNotFoundError:
                        sftp_conn.mkdir(remote_dir)

                    # Définition du chemin distant du fichier
                    remote_file_path = os.path.join(remote_dir, os.path.basename(self.m_file)).replace("\\", "/")
                    # Envoi du fichier
                    sftp_conn.upload_file(self.m_file, remote_file_path)

                except Exception as e:
                    if self.m_logger:
                        self.m_logger.info(f"{ERROR_PACKAGE_UPLOAD_FAILED}{e}")
                    if self.m_scheduler:
                        self.m_scheduler.emit_status(
                            self.get_name(),
                            STATUS_UPLOADING_PACKAGE,
                            PROGRESS_ERROR,
                        )
            if self.m_scheduler:
                self.m_scheduler.emit_status(
                    self.get_name(), STATUS_UPLOADING_PACKAGE, PROGRESS_SUCCESS
                )

        elif (
            self.m_action == "download_package" or self.m_action == "load_package_file"
        ):
            path_to_file = self.m_file
            if self.m_action == "download_package":
                if self.m_scheduler:
                    self.m_scheduler.emit_status(
                        self.get_name(), STATUS_DOWNLOADING_PACKAGE, PROGRESS_START
                    )

                try:
                    os.mkdir(os.path.join(DIR_DOWNLOADS))
                except FileExistsError:
                    pass

                try:
                    os.mkdir(os.path.join(DIR_RESOURCES))
                except FileExistsError:
                    pass

                # Get configuration for download
                download_configs, error = get_config_or_error(get_settings_manager(),
                                                              CONFIG_UPDATES_SOURCE,
                                                              CONFIG_UPDATES_FOLDER,
                                                              CONFIG_UPDATES_PATH)
                if error:
                    if self.m_logger:
                        self.m_logger.error(ERROR_DOWNLOAD_CONFIG)
                    if self.m_scheduler:
                        self.m_scheduler.emit_status(self.get_name(), ERROR_CONFIG, PROGRESS_ERROR)
                    return
                
                # Type guard: download_configs is dict when error is None
                assert isinstance(download_configs, dict), "Config should be dict when no error"

                # Folder mode
                if download_configs[CONFIG_UPDATES_SOURCE] == SOURCE_FOLDER:
                    shutil.copyfile(
                        os.path.join(
                            download_configs[CONFIG_UPDATES_FOLDER],
                            DIR_PACKAGES,
                            site_conf_obj.m_app["name"] if site_conf_obj else "unknown",
                            self.m_file,
                        ),
                        os.path.join(DIR_DOWNLOADS, self.m_file),
                    )

                # FTP mode
                elif download_configs[CONFIG_UPDATES_SOURCE] == SOURCE_FTP:
                    path_to_file = os.path.join(DIR_DOWNLOADS, self.m_file).replace("\\", "/")  # Assure la compatibilité Windows/Linux

                    try:
                        # Définition du chemin distant
                        remote_file_path = os.path.join(
                            download_configs[CONFIG_UPDATES_PATH],
                            DIR_PACKAGES,
                            site_conf_obj.m_app["name"] if site_conf_obj else "unknown",
                            self.m_file
                        ).replace("\\", "/")  # Compatibilité Windows/Linux

                        # Création du dossier local DIR_DOWNLOADS s'il n'existe pas
                        os.makedirs(os.path.dirname(path_to_file), exist_ok=True)

                        # Téléchargement du fichier
                        sftp_conn.download_file(remote_file_path, path_to_file)

                    except Exception as e:
                        if self.m_logger:
                            self.m_logger.info(f"{ERROR_PACKAGE_DOWNLOAD_FAILED}{e}")
                        if self.m_scheduler:
                            self.m_scheduler.emit_status(
                                self.get_name(),
                                STATUS_DOWNLOADING_PACKAGE,
                                PROGRESS_ERROR,
                            )

                if self.m_scheduler:
                    self.m_scheduler.emit_status(
                        self.get_name(), STATUS_DOWNLOADING_PACKAGE, PROGRESS_SUCCESS
                    )
            else:
                if ".zip" not in self.m_file:
                    if self.m_scheduler:
                        self.m_scheduler.emit_popup(
                            scheduler.logLevel.error, ERROR_PACKAGE_MUST_ZIP
                        )
                    return

            # Remove only .tar.gz files in the DIR_RESOURCES folder and its subfolders, excluding specific directories
            if self.m_scheduler:
                self.m_scheduler.emit_status(self.get_name(), STATUS_DELETING_TAR_GZ, PROGRESS_START)

            ressources_path = os.path.join(DIR_RESOURCES)

            # Dossiers spécifiques où les .tar.gz ne doivent pas être supprimés
            if site_conf_obj and hasattr(site_conf_obj, 'm_include_tar_gz_dirs'):
                exclude_dirs_abs = [os.path.abspath(p) for p in site_conf_obj.m_include_tar_gz_dirs]  # type: ignore
            else:
                exclude_dirs_abs = []

            if os.path.exists(ressources_path):
                for root, dirs, files in os.walk(ressources_path):
                    root_abs = os.path.abspath(root)
                    # Vérifie si root est dans un des dossiers exclus
                    if any(root_abs.startswith(exclude_dir) for exclude_dir in exclude_dirs_abs):
                        if self.m_logger:
                            self.m_logger.info(f"Skipping excluded dir for .tar.gz deletion: {root_abs}")
                        continue

                    for file in files:
                        if file.endswith(".tar.gz"):
                            file_path = os.path.join(root, file)
                            try:
                                os.remove(file_path)
                                if self.m_logger:
                                    self.m_logger.info(f"Deleted .tar.gz: {file_path}")
                            except Exception as e:
                                if self.m_logger:
                                    self.m_logger.warning(f"Failed to delete {file_path}: {str(e)}")
                                if self.m_scheduler:
                                    self.m_scheduler.emit_status(self.get_name(), f"Failed to delete {file_path}: {str(e)}", PROGRESS_WARNING)
            else:
                os.mkdir(ressources_path)

            if self.m_scheduler:
                self.m_scheduler.emit_status(self.get_name(), STATUS_DELETING_TAR_GZ, PROGRESS_SUCCESS)

            try:
                if self.m_scheduler:
                    self.m_scheduler.emit_status(
                        self.get_name(), STATUS_UNPACKING_ARCHIVE, PROGRESS_START
                    )
                try:
                    shutil.unpack_archive(
                        path_to_file,
                        os.path.join(DIR_RESOURCES),
                        "zip",
                    )
                except FileNotFoundError as e:
                    if self.m_logger:
                        self.m_logger.warning(f"Skipping missing file: {e}")
                    pass
                except OSError as e:
                    if e.errno == ERROR_LONG_PATH_CODE:
                        if self.m_logger:
                            self.m_logger.error(f"{ERROR_LONG_PATH}{e}")
                    else:
                        raise

                if self.m_scheduler:
                    self.m_scheduler.emit_status(
                        self.get_name(), STATUS_UNPACKING_ARCHIVE, PROGRESS_SUCCESS
                    )

                # Émettre un statut avec une balise meta pour rafraîchir la page
                if self.m_scheduler:
                    self.m_scheduler.emit_status(self.get_name(), REFRESH_CONTENT, PROGRESS_START)

                time.sleep(REFRESH_DELAY)
                if self.m_scheduler:
                    self.m_scheduler.emit_status(
                        self.get_name(), STATUS_UNPACKING_SUCCESS, PROGRESS_SUCCESS
                    )

            except Exception as e:
                if self.m_logger:
                    self.m_logger.info(f"{ERROR_UNPACKING_FAILED}{str(e)}")
                if self.m_scheduler:
                    self.m_scheduler.emit_status(
                        self.get_name(),
                        STATUS_UNPACKING_ARCHIVE,
                        PROGRESS_ERROR,
                        str(e),
                    )
        return


bp = Blueprint("packager", __name__, url_prefix="/packager")


@bp.route("/packager", methods=["GET", "POST"])
def packager():
    data_in = None
    site_conf_obj = site_conf.site_conf_obj

    if request.method == "POST":
        data_raw = request.form.to_dict()
        data_in = utilities.util_post_to_json(data_raw)
        if SETUP_Packager.m_default_name in data_in:
            data_in = data_in[SETUP_Packager.m_default_name]
            packager = SETUP_Packager()

            if "pack" in data_in:
                packager.set_file(data_in["create_package"])
                packager.set_action("create_package")

            elif "upload" in data_in:
                for item in data_raw:
                    if data_raw[item] == STYLE_PRIMARY:
                        packager.set_file(item)
                packager.set_action("upload_package")

            elif "download" in data_in:
                packager.set_file(data_in["download_package"])
                packager.set_action("download_package")
            else:
                try:
                    for item in data_raw:
                        if data_raw[item] == STYLE_PRIMARY:
                            packager.set_file(item)
                    try:
                        os.mkdir(os.path.join(DIR_DOWNLOADS))
                    except FileExistsError:
                        pass

                    packager.set_action("load_package_file")
                except Exception:
                    pass

            packager.start()

    disp = displayer.Displayer()
    disp.add_module(SETUP_Packager, display=False)
    disp.set_title("Binaries Package Manager")

    # Check if user is admin
    current_user_name = auth_manager.get_current_user() if auth_manager else None
    user = auth_manager.get_user(current_user_name) if (auth_manager and current_user_name) else None
    is_admin = user and "admin" in user.groups if user else False

    # Packager
    if is_admin and not ((getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"))):
        disp.add_master_layout(
            displayer.DisplayerLayout(
                displayer.Layouts.VERTICAL,
                [3, 6, 3],
                subtitle=SUBTITLE_PACKAGE_CREATION,
                alignment=[
                    displayer.BSalign.L,
                    displayer.BSalign.L,
                    displayer.BSalign.R,
                ],
            )
        )
        disp.add_display_item(displayer.DisplayerItemText(TEXT_CREATE_PACKAGE), 0)
        disp.add_display_item(displayer.DisplayerItemInputString("create_package"), 1)
        disp.add_display_item(
            displayer.DisplayerItemButton("pack", BUTTON_PACKAGE_CREATION), 2
        )

        to_upload_files = utilities.util_dir_structure(
            os.path.join(DIR_PACKAGES), inclusion=[".zip"]
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
        disp.add_display_item(displayer.DisplayerItemText(TEXT_UPLOAD_PACKAGE), 0)
        disp.add_display_item(
            displayer.DisplayerItemInputFileExplorer(
                "upload_package",
                None,
                [to_upload_files],
                [LABEL_FILES_TO_UPLOAD],
                [ICON_FILE_UPLOAD],
                [STYLE_PRIMARY],
                [False],
            ),
            1,
        )
        disp.add_display_item(
            displayer.DisplayerItemButton("upload", BUTTON_PACKAGE_UPLOAD), 2
        )

    disp.add_master_layout(
        displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL,
            [3, 6, 3],
            subtitle=SUBTITLE_PACKAGE_RESTORATION,
            alignment=[
                displayer.BSalign.L,
                displayer.BSalign.L,
                displayer.BSalign.R,
            ],
        )
    )

    package_file = utilities.util_dir_structure(
        os.path.join(DIR_DOWNLOADS), inclusion=[".zip"]
    )
    disp.add_display_item(displayer.DisplayerItemText(TEXT_PACKAGE_AVAILABLE), 0)
    disp.add_display_item(
        displayer.DisplayerItemInputFileExplorer(
            "load_package_file",
            None,
            [package_file],
            [LABEL_PACKAGE_TO_UNPACK],
            [ICON_FILE_PACKAGE],
            [STYLE_PRIMARY],
            [False],
        ),
        1,
    )
    disp.add_display_item(displayer.DisplayerItemButton("unpack", BUTTON_UNPACK), 2)

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
    
    # Type guard: configs is dict when error is None
    assert isinstance(configs, dict), "Config should be dict when no error"

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
                displayer.DisplayerItemAlert(INFO_FOLDER_NOT_EXISTS, displayer.BSstyle.INFO), 0
            )
        else:
            content = utilities.util_dir_structure(
                os.path.join(
                    configs[CONFIG_UPDATES_FOLDER],
                    DIR_PACKAGES,
                    site_conf_obj.m_app["name"] if site_conf_obj else "unknown",
                ),
                inclusion=[".zip"],
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
                displayer.DisplayerItemText(TEXT_SELECT_PACKAGE), 0
            )
            disp.add_display_item(
                displayer.DisplayerItemInputSelect(
                    "download_package", None, None, list(content.values()) if isinstance(content, dict) else []
                ),
                1,
            )
            disp.add_display_item(
                displayer.DisplayerItemButton("download", BUTTON_PACKAGE_INSTALL), 2
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
            remote_dir = os.path.join(
                configs[CONFIG_UPDATES_PATH],
                DIR_PACKAGES,
                site_conf_obj.m_app["name"] if site_conf_obj else "unknown"
            ).replace("\\", "/")  # Compatibilité Windows/Linux

            # Récupération de la liste des fichiers
            try:
                content = sftp_conn.listdir(remote_dir)
            except FileNotFoundError:
                content = []

            # Fermeture de la connexion SFTP
            sftp_conn.close()

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
                displayer.DisplayerItemText(TEXT_SELECT_PACKAGE), 0
            )
            disp.add_display_item(
                displayer.DisplayerItemInputSelect(
                    "download_package", None, None, content
                ),
                1,
            )
            disp.add_display_item(
                displayer.DisplayerItemButton("download", BUTTON_INSTALL_PACKAGE_ALT), 2
            )

        except socket.gaierror:
            disp.add_master_layout(
                displayer.DisplayerLayout(
                    displayer.Layouts.VERTICAL,
                    [12],
                    subtitle="",
                    alignment=[displayer.BSalign.C],
                )
            )
            disp.add_display_item(
                displayer.DisplayerItemAlert(INFO_FTP_NOT_ACCESSIBLE, displayer.BSstyle.INFO), 0
            )
        except Exception as e:
            disp.add_master_layout(
                displayer.DisplayerLayout(
                    displayer.Layouts.VERTICAL,
                    [12],
                    subtitle="",
                    alignment=[displayer.BSalign.C],
                )
            )
            disp.add_display_item(
                displayer.DisplayerItemAlert(f"{INFO_FTP_UNKNOWN_ERROR}{str(e)}", displayer.BSstyle.WARNING), 0
            )

    return render_template(
        "base_content.j2", content=disp.display(), target="packager.packager"
    )

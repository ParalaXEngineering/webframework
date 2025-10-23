from flask import Blueprint, render_template, request

from ..modules import utilities
from ..modules.auth.auth_manager import auth_manager
from ..modules import site_conf
from ..modules import displayer
from ..modules import SFTPConnection
from ..modules.settings import SettingsManager
from ..modules.utilities import get_config_or_error

from ..modules.threaded.threaded_action import Threaded_action

import os
import zipfile
import tarfile
import pathlib
import sys
import platform
import shutil
import traceback
import subprocess
import copy
import logging

logger = logging.getLogger(__name__)


# Global settings manager
_settings_manager = None


def get_settings_manager():
    """Get or create settings manager instance and merge optional configs based on site_conf."""
    global _settings_manager
    if _settings_manager is None:
        from ..modules import site_conf
        
        config_path = os.path.join(os.getcwd(), "config.json")
        _settings_manager = SettingsManager(config_path)
        _settings_manager.load()
        
        # Merge optional configurations based on enabled features
        if site_conf.site_conf_obj:
            _settings_manager.merge_optional_configs(site_conf.site_conf_obj)
    return _settings_manager


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
                                             "updates.address.value",
                                             "updates.user.value",
                                             "updates.password.value")
        if error:
            if self.m_logger:
                self.m_logger.error("Failed to get SFTP config from settings")
            return
        
        sftp_conn = SFTPConnection.SFTPConnection(
            configs["updates.address.value"],
            configs["updates.user.value"],
            configs["updates.password.value"]
        )

        site_conf_obj = site_conf.site_conf_obj

        if self.m_action in ("update", "load_update_file"):
            if self.m_scheduler:
                self.m_scheduler.emit_status(self.get_name(), "Applying update", 103)
            current_param = get_settings_manager().get_all_settings()

            # --- Unzip / Untar ---
            if platform.system().lower() == "windows":
                with zipfile.ZipFile(os.path.join(self.m_file), mode="r") as zf:
                    zf.extractall(path="../")
            else:
                # Safe extraction for tar.gz
                def is_within_directory(directory, target):
                    abs_directory = os.path.abspath(directory)
                    abs_target = os.path.abspath(target)
                    return os.path.commonprefix([abs_directory, abs_target]) == abs_directory

                dest = "../"
                with tarfile.open(os.path.join(self.m_file), mode="r:gz") as tf:
                    for member in tf.getmembers():
                        target_path = os.path.join(dest, member.name)
                        if not is_within_directory(dest, target_path):
                            raise Exception(f"Blocked path traversal in tar member: {member.name}")
                    tf.extractall(path=dest)

            # Recharger le nouveau config.json (qui vient d'être écrasé par l'archive)
            # Force reload from disk
            settings_mgr = get_settings_manager()
            settings_mgr.load()
            new_param = settings_mgr.get_all_settings()

            # --- MERGE new_param -> current_param ---
            for topic, topic_data in new_param.items():
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
            settings_mgr.storage.save(current_param)

            # Configuration pour le lancement du bootloader
            if site_conf_obj and platform.system().lower() == "windows":
                path_to_bootloader = os.path.join("BTL.bat")
                path_to_new_executable = os.path.join(site_conf_obj.m_app["name"] + "_update.exe")
                original_executable_path = os.path.join(site_conf_obj.m_app["name"] + ".exe")
            elif site_conf_obj:  # Assuming Linux for other platforms
                current_directory = os.path.dirname(os.path.abspath(__file__))
                path_to_bootloader = os.path.join(current_directory, "BTL.sh")
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
                if platform.system().lower() == "windows":
                    subprocess.Popen([path_to_bootloader, path_to_new_executable, original_executable_path])
                else:  # Assuming Linux for other platforms
                    subprocess.Popen(["bash", path_to_bootloader, path_to_new_executable, original_executable_path])
            except Exception as e:
                logger.exception(f"Error launching bootloader: {e}")

            if self.m_scheduler:
                self.m_scheduler.emit_status(self.get_name(), "Applying update", 100)
            if "distribution" in self.m_file:
                if self.m_scheduler:
                    self.m_scheduler.emit_status(
                        self.get_name(),
                        "Application will restart, you can close this tab",
                        102,
                    )
            else:
                if self.m_scheduler:
                    self.m_scheduler.emit_status(
                        self.get_name(), "Please restart application", 102
                    )

        elif self.m_action == "download":
            # Get source configuration with error handling
            source, error = get_config_or_error(get_settings_manager(), "updates.source.value")
            if error:
                if self.m_logger:
                    self.m_logger.error("Failed to get updates.source.value from config")
                if self.m_scheduler:
                    self.m_scheduler.emit_status(
                        self.get_name(), "Configuration error: updates.source.value not found", 101
                    )
                return

            try:
                os.mkdir(os.path.join("updates"))
            except FileExistsError:
                pass

            # Folder mode
            if self.m_scheduler:
                self.m_scheduler.emit_status(
                    self.get_name(), "Downloading archive, this might take a while", 103
                )
            if source == "Folder":
                folder_value, error = get_config_or_error(get_settings_manager(), "updates.folder.value")
                if error:
                    if self.m_logger:
                        self.m_logger.error("Failed to get updates.folder.value from config")
                    if self.m_scheduler:
                        self.m_scheduler.emit_status(
                            self.get_name(), "Configuration error: updates.folder.value not found", 101
                        )
                    return
                
                if site_conf_obj:
                    shutil.copyfile(
                        os.path.join(
                            folder_value,
                            "updates",
                            site_conf_obj.m_app["name"],
                            self.m_file,
                        ),
                        os.path.join("downloads", self.m_file),
                    )

            # FTP mode
            elif source == "FTP":
                try:
                    if site_conf_obj:
                        # Get FTP path configuration
                        path_value, error = get_config_or_error(get_settings_manager(), "updates.path.value")
                        if error:
                            if self.m_logger:
                                self.m_logger.error("Failed to get updates.path.value from config")
                            if self.m_scheduler:
                                self.m_scheduler.emit_status(
                                    self.get_name(), "Configuration error: updates.path.value not found", 101
                                )
                            return
                        
                        # Définition des chemins
                        remote_file_path = os.path.join(
                            path_value,
                            "updates",
                            site_conf_obj.m_app["name"],
                            self.m_file
                        ).replace("\\", "/")  # Assure la compatibilité Windows/Linux

                        local_file_path = os.path.join("updates", self.m_file)

                        # Téléchargement du fichier
                        sftp_conn.download_file(remote_file_path, local_file_path)

                except Exception as e:
                    if self.m_logger:
                        self.m_logger.info(f"Update download failed: {e}")
                    if self.m_scheduler:
                        self.m_scheduler.emit_status(
                            self.get_name(),
                            "Downloading archive, this might take a while",
                            101,
                        )

            if self.m_scheduler:
                self.m_scheduler.emit_status(
                    self.get_name(), "Downloading archive, this might take a while", 100
                )

            # Relist the package availables
            try:
                packages_total = os.listdir(os.path.join("updates"))
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
                os.makedirs(os.path.join("updates"))
            except FileExistsError:
                # Alread exists, no big deal
                pass

            if self.m_scheduler:
                self.m_scheduler.emit_status(
                    self.get_name(), f"Creation of the update package for {self.m_distribution}", 103
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
                        101,
                        supplement=str(e),
                    )
                return
            directories = [os.path.join("updater", self.m_distribution, "dist")]
            if site_conf_obj:
                version = site_conf_obj.m_app["version"].split("_")[0]
                if (self.m_distribution == "Windows"):
                    with zipfile.ZipFile(
                        os.path.join(
                            "updates",
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
                    self.get_name(), f"Creation of the update package for {self.m_distribution}", 100
                )

        elif self.m_action == "upload":
            updates_folder = "updates"
            files_to_upload = []

            # Vérifiez les fichiers présents dans le dossier updates
            for file in os.listdir(updates_folder):
                if file.endswith(".zip") or file.endswith(".tar.gz"):
                    files_to_upload.append(os.path.join(updates_folder, file))

            if not files_to_upload:
                if self.m_scheduler:
                    self.m_scheduler.emit_status(self.get_name(), "Uploading updates, this might take a while", 101)
                return

            if self.m_scheduler:
                self.m_scheduler.emit_status(self.get_name(), "Uploading updates, this might take a while", 103)

            # Get configuration for upload
            configs, error = get_config_or_error(get_settings_manager(),
                                                 "updates.source.value",
                                                 "updates.folder.value",
                                                 "updates.path.value")
            if error:
                if self.m_logger:
                    self.m_logger.error("Failed to get upload config from settings")
                if self.m_scheduler:
                    self.m_scheduler.emit_status(self.get_name(), "Configuration error", 101)
                return

            # Folder mode
            if configs["updates.source.value"] == "Folder":
                try:
                    if site_conf_obj:
                        os.makedirs(os.path.join(configs["updates.folder.value"], "updates", site_conf_obj.m_app["name"]), exist_ok=True)
                except Exception as e:
                    if self.m_scheduler:
                        self.m_scheduler.emit_status(self.get_name(), f"Failed to create directories: {str(e)}", 101)
                    return

                for file in files_to_upload:
                    try:
                        if site_conf_obj:
                            shutil.copyfile(
                                file,
                                os.path.join(
                                    configs["updates.folder.value"],
                                    "updates",
                                    site_conf_obj.m_app["name"],
                                    os.path.basename(file),
                                ),
                            )
                    except Exception as e:
                        if self.m_scheduler:
                            self.m_scheduler.emit_status(self.get_name(), f"Failed to copy file {file}: {str(e)}", 101)
                        return

            # FTP mode
            elif configs["updates.source.value"] == "FTP":
                try:
                    if site_conf_obj:
                        # Définition du dossier distant
                        remote_dir = os.path.join(
                            configs["updates.path.value"],
                            "updates",
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
                            "Uploading updates, this might take a while",
                            101, str(e)
                        )

            if self.m_scheduler:
                self.m_scheduler.emit_status(
                    self.get_name(), "Uploading updates, this might take a while", 100
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

        if "create" in data_in:
            packager = SETUP_Updater()
            packager.set_action("create")
            packager.set_distribution(data_in["distrib"])
            packager.start()
        elif "upload" in data_in:
            packager = SETUP_Updater()
            packager.set_action("upload")
            packager.start()
        elif "apply" in data_in:
            packager = SETUP_Updater()
            packager.set_action("update")
            packager.set_file(data_in["update_package"])
            packager.start()
        elif "download" in data_in:
            packager = SETUP_Updater()
            packager.set_action("download")
            packager.set_file(data_in["download_package"])
            packager.start()
        elif "unpack" in data_in:
            try:
                f = request.files[".load_update_file"]
                try:
                    os.mkdir("downloads")
                except FileExistsError:
                    pass
                if f.filename:
                    f.save(os.path.join("downloads", f.filename))
                packager = SETUP_Updater()
                packager.set_action("load_update_file")
                if f.filename:
                    packager.set_file(f.filename)
                packager.start()
            except Exception:
                pass

    disp = displayer.Displayer()
    disp.add_module(SETUP_Updater, display=False)
    disp.set_title("Website engine update creation")
    
    # Load configuration with error handling
    configs, error = get_config_or_error(get_settings_manager(),
                                         "updates.source.value",
                                         "updates.folder.value",
                                         "updates.path.value",
                                         "updates.address.value",
                                         "updates.user.value",
                                         "updates.password.value")
    if error:
        return error

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
                subtitle="Update Creation",
                alignment=[
                    displayer.BSalign.L,
                    displayer.BSalign.L,
                    displayer.BSalign.R,
                ],
            )
        )

        disp.add_display_item(displayer.DisplayerItemText("Create a new update with installer"), 0)
        disp.add_display_item(displayer.DisplayerItemInputSelect("distrib", None, None, ["Windows", "Linux"]), 1)
        disp.add_display_item(displayer.DisplayerItemButton("create", "Create"), 2)

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
            displayer.DisplayerItemText("Upload the latested update"), 0
        )
        disp.add_display_item(displayer.DisplayerItemButton("upload", "Upload"), 2)

    to_apply = utilities.util_dir_structure(os.path.join("updates"), [".zip"])
    disp.add_master_layout(
        displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL,
            [3, 6, 3],
            subtitle="Update Deployment",
            alignment=[displayer.BSalign.L, displayer.BSalign.L, displayer.BSalign.R],
        )
    )

    content = to_apply.values()
    content = [item for item in content if platform.system() in item]

    disp.add_display_item(displayer.DisplayerItemText("Apply update"), 0)
    disp.add_display_item(
        displayer.DisplayerItemInputSelect("update_package", None, None, list(content)), 1
    )
    disp.add_display_item(displayer.DisplayerItemButton("apply", "Apply"), 2)

    # Folder mode
    if configs["updates.source.value"] == "Folder":
        if not os.path.exists(os.path.join(configs["updates.folder.value"])):
            info = "Configured update folder doesn't exists"
            disp.add_master_layout(
                displayer.DisplayerLayout(
                    displayer.Layouts.VERTICAL,
                    [12],
                    subtitle="",
                    alignment=[displayer.BSalign.C],
                )
            )
            disp.add_display_item(
                displayer.DisplayerItemAlert(info, displayer.BSstyle.INFO), 0
            )
        else:
            if site_conf_obj:
                content = utilities.util_dir_structure(
                    os.path.join(
                        configs["updates.folder.value"],
                        "updates",
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
                displayer.DisplayerItemText("Select a package to download"), 0
            )
            disp.add_display_item(
                displayer.DisplayerItemInputSelect(
                    "download_package", None, None, list(content.values()) if isinstance(content, dict) else []
                ),
                1,
            )
            disp.add_display_item(
                displayer.DisplayerItemButton("download", "Download"), 2
            )

    # FTP mode
    elif configs["updates.source.value"] == "FTP":
        try:
            sftp_conn = SFTPConnection.SFTPConnection(
                configs["updates.address.value"],
                configs["updates.user.value"],
                configs["updates.password.value"]
            )

            # Définition du chemin distant
            remote_path = ""
            if site_conf_obj:
                remote_path = os.path.join(
                    configs["updates.path.value"],
                    "updates",
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
            info = "FTP server not accessible, please check your connection, use a zip file or use a local folder"
            disp.add_master_layout(
                displayer.DisplayerLayout(
                    displayer.Layouts.VERTICAL,
                    [12],
                    subtitle="",
                    alignment=[displayer.BSalign.C],
                )
            )
            disp.add_display_item(
                displayer.DisplayerItemAlert(info, displayer.BSstyle.INFO), 0
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
            displayer.DisplayerItemText("Select a package to download"), 0
        )
        disp.add_display_item(
            displayer.DisplayerItemInputSelect(
                "download_package", None, None, content
            ),
            1,
        )
        disp.add_display_item(
            displayer.DisplayerItemButton("download", "Download"), 2
        )

    disp.add_master_layout(
        displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL,
            [3, 6, 3],
            subtitle="",
            alignment=[displayer.BSalign.L, displayer.BSalign.L, displayer.BSalign.R],
        )
    )
    disp.add_display_item(displayer.DisplayerItemText("Load package from file"), 0)
    disp.add_display_item(displayer.DisplayerItemInputFile("load_update_file"), 1)
    disp.add_display_item(displayer.DisplayerItemButton("unpack", "Unpack"), 2)

    return render_template(
        "base_content.j2", content=disp.display(), target="updater.update"
    )

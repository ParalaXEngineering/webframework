from flask import Blueprint, render_template, request

from submodules.framework.src import utilities
from submodules.framework.src import access_manager
from submodules.framework.src import site_conf
from submodules.framework.src import displayer
from submodules.framework.src import SFTPConnection

from submodules.framework.src import threaded_action

import os
import zipfile
import tarfile
import pathlib
import sys
import platform
import shutil
import traceback
import subprocess


class SETUP_Updater(threaded_action.Threaded_action):
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
        config = utilities.util_read_parameters()
        sftp_conn = SFTPConnection.SFTPConnection(
            config["updates"]["address"]["value"],
            config["updates"]["user"]["value"],
            config["updates"]["password"]["value"]
        )
        # Recover the site information
        site_conf_obj = site_conf.site_conf_obj

        """Execute the module
        """
        if self.m_action == "update" or self.m_action == "load_update_file":
            self.m_scheduler.emit_status(self.get_name(), "Applying update", 103)
            current_param = utilities.util_read_parameters()

            # Unzip or untar archive
            if platform.system().lower() == "windows":
                with zipfile.ZipFile(os.path.join(self.m_file), mode="r") as zip:
                    zip.extractall(path="../")
            else:  # Assuming Linux for other platforms
                with tarfile.open(os.path.join(self.m_file), mode="r:gz") as tar:
                    tar.extractall(path="../")

            # config file has been overwritten, we need to reapply current configuration
            new_param = utilities.util_read_parameters()

            # Add new topics
            for topic in new_param:
                if topic not in current_param:
                    current_param[topic] = new_param[topic]
                else:
                    for key in new_param[topic]:
                        if isinstance(new_param[topic][key], dict) and 'persistent' in new_param[topic][key]:
                            if new_param[topic][key]['persistent']:
                                current_param[topic][key]['value'] = new_param[topic][key]['value']

            # Remove old ones
            to_remove = [topic for topic in current_param if topic not in new_param]
            for topic in to_remove:
                current_param.pop(topic)

            # and save
            utilities.util_write_parameters(current_param)

            # Configuration pour le lancement du bootloader
            if platform.system().lower() == "windows":
                path_to_bootloader = os.path.join("BTL.bat")
                path_to_new_executable = os.path.join(site_conf_obj.m_app["name"] + "_update.exe")
                original_executable_path = os.path.join(site_conf_obj.m_app["name"] + ".exe")
            else:  # Assuming Linux for other platforms
                current_directory = os.path.dirname(os.path.abspath(__file__))
                path_to_bootloader = os.path.join(current_directory, "BTL.sh")
                path_to_new_executable = os.path.join(site_conf_obj.m_app["name"] + "_update")
                original_executable_path = os.path.join(site_conf_obj.m_app["name"])
            # Lancer le bootloader dans un nouveau processus

            # Vérifier si le script BTL.sh existe
            if not os.path.isfile(path_to_bootloader):
                print(f"Erreur: Le script {path_to_bootloader} n'existe pas.")
                return
            if not os.path.isfile(path_to_bootloader):
                print(f"Erreur: Le script {path_to_new_executable} n'existe pas.")
                return
            if not os.path.isfile(path_to_bootloader):
                print(f"Erreur: Le script {original_executable_path} n'existe pas.")
                return

            try:
                if platform.system().lower() == "windows":
                    subprocess.Popen([path_to_bootloader, path_to_new_executable, original_executable_path])
                else:  # Assuming Linux for other platforms
                    subprocess.Popen(["bash", path_to_bootloader, path_to_new_executable, original_executable_path])
            except Exception as e:
                print(e)

            self.m_scheduler.emit_status(self.get_name(), "Applying update", 100)
            if "distribution" in self.m_file:
                self.m_scheduler.emit_status(
                    self.get_name(),
                    "Application will restart, you can close this tab",
                    102,
                )
            else:
                self.m_scheduler.emit_status(
                    self.get_name(), "Please restart application", 102
                )

        elif self.m_action == "download":
            config = utilities.util_read_parameters()

            try:
                os.mkdir(os.path.join("updates"))
            except FileExistsError:
                pass

            # Folder mode
            self.m_scheduler.emit_status(
                self.get_name(), "Downloading archive, this might take a while", 103
            )
            config = utilities.util_read_parameters()
            if config["updates"]["source"]["value"] == "Folder":
                shutil.copyfile(
                    os.path.join(
                        config["updates"]["folder"]["value"],
                        "updates",
                        site_conf_obj.m_app["name"],
                        self.m_file,
                    ),
                    os.path.join("downloads", self.m_file),
                )

            # FTP mode
            elif config["updates"]["source"]["value"] == "FTP":
                try:
                    # Définition des chemins
                    remote_file_path = os.path.join(
                        config["updates"]["path"]["value"],
                        "updates",
                        site_conf_obj.m_app["name"],
                        self.m_file
                    ).replace("\\", "/")  # Assure la compatibilité Windows/Linux

                    local_file_path = os.path.join("updates", self.m_file)

                    # Téléchargement du fichier
                    sftp_conn.download_file(remote_file_path, local_file_path)

                except Exception as e:
                    self.m_logger.info(f"Update download failed: {e}")
                    self.m_scheduler.emit_status(
                        self.get_name(),
                        "Downloading archive, this might take a while",
                        101,
                    )

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
            inputs = []
            inputs.append(
                {
                    "label": "Select",
                    "id": "update_package",
                    "value": "",
                    "type": "select",
                    "data": packages,
                }
            )
            reloader = utilities.util_view_reload_multi_input("update_package", inputs)
            self.m_scheduler.emit_reload(reloader)

        elif self.m_action == "create":
            pass

            # Create the udpate folder if needed
            try:
                os.makedirs(os.path.join("updates"))
            except FileExistsError:
                # Alread exists, no big deal
                pass

            self.m_scheduler.emit_status(
                self.get_name(), f"Creation of the update package for {self.m_distribution}", 103
            )
            # Create the package with pyinstaller
            try:
                site_conf_obj.create_distribuate(self.m_distribution)
            except Exception as e:
                traceback_str = traceback.format_exc()
                self.m_logger.warning("Update creation failed: " + str(e))
                self.m_logger.info("Traceback was: " + traceback_str)
                self.m_scheduler.emit_status(
                    self.get_name(),
                    f"Creation of the update package for {self.m_distribution}",
                    101,
                    supplement=str(e),
                )
                return
            directories = [os.path.join("updater", self.m_distribution, "dist")]

            if (self.m_distribution == "Windows"):
                with zipfile.ZipFile(
                    os.path.join(
                        "updates",
                        site_conf_obj.m_app["name"]
                        + "_"
                        + site_conf_obj.m_app["version"]
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
                self.m_scheduler.emit_status(self.get_name(), "Uploading updates, this might take a while", 101)
                return

            self.m_scheduler.emit_status(self.get_name(), "Uploading updates, this might take a while", 103)

            # Folder mode
            config = utilities.util_read_parameters()

            if config["updates"]["source"]["value"] == "Folder":
                try:
                    os.makedirs(os.path.join(config["updates"]["folder"]["value"], "updates", site_conf_obj.m_app["name"]), exist_ok=True)
                except Exception as e:
                    self.m_scheduler.emit_status(self.get_name(), f"Failed to create directories: {str(e)}", 101)
                    return

                for file in files_to_upload:
                    try:
                        shutil.copyfile(
                            file,
                            os.path.join(
                                config["updates"]["folder"]["value"],
                                "updates",
                                site_conf_obj.m_app["name"],
                                os.path.basename(file),
                            ),
                        )
                    except Exception as e:
                        self.m_scheduler.emit_status(self.get_name(), f"Failed to copy file {file}: {str(e)}", 101)
                        return

            # FTP mode
            elif config["updates"]["source"]["value"] == "FTP":
                try:
                    # Définition du dossier distant
                    remote_dir = os.path.join(
                        config["updates"]["path"]["value"],
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
                    self.m_logger.info(f"Update upload failed: {e}")
                    self.emit_status(
                        self.get_name(),
                        "Uploading updates, this might take a while",
                        101, e
                    )

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
                f.save(os.path.join("downloads", f.filename))
                packager = SETUP_Updater()
                packager.set_action("load_update_file")
                packager.set_file(f.filename)
                packager.start()
            except Exception:
                pass

    disp = displayer.Displayer()
    disp.add_module(SETUP_Updater)
    config = utilities.util_read_parameters()

    if access_manager.auth_object.authorize_group("admin") and not ((getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"))):
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

    to_apply = utilities.util_dir_structure(os.path.join("updates"), ".zip")
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
    if config["updates"]["source"]["value"] == "Folder":
        if not os.path.exists(os.path.join(config["updates"]["folder"]["value"])):
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
            content = utilities.util_dir_structure(
                os.path.join(
                    config["updates"]["folder"]["value"],
                    "updates",
                    site_conf_obj.m_app["name"],
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

    # FTP mode
    elif config["updates"]["source"]["value"] == "FTP":
        try:
            sftp_conn = SFTPConnection.SFTPConnection(
                config["updates"]["address"]["value"],
                config["updates"]["user"]["value"],
                config["updates"]["password"]["value"]
            )

            # Définition du chemin distant
            remote_path = os.path.join(
                config["updates"]["path"]["value"],
                "updates",
                site_conf_obj.m_app["name"]
            ).replace("\\", "/")  # Assure la compatibilité Windows/Linux

            # Liste des fichiers dans le dossier distant
            try:
                content = sftp_conn.listdir(remote_path)
                content = [item for item in content if platform.system() in item]
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

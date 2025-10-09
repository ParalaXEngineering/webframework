from flask import Blueprint, render_template, request

from ..modules import utilities
from ..modules import access_manager
from ..modules import site_conf
from ..modules import displayer
from ..modules import scheduler
from ..modules import SFTPConnection

import shutil
import socket
import datetime
import sys
import time
import errno
from ..modules.threaded import Threaded_action

import os
import tempfile


class SETUP_Packager(Threaded_action):
    m_default_name = "Binaries Package Manager"
    m_action = ""

    def set_file(self, file):
        self.m_file = file

    def set_action(self, action):
        self.m_action = action

    def action(self):
        # Création d'une seule instance de connexion
        config = utilities.util_read_parameters()
        sftp_conn = SFTPConnection.SFTPConnection(
            config["updates"]["address"]["value"],
            config["updates"]["user"]["value"],
            config["updates"]["password"]["value"]
        )

        site_conf_obj = site_conf.site_conf_obj

        if self.m_action == "create_package":
            try:
                os.mkdir(os.path.join("packages"))
            except FileExistsError:
                pass

            # Sleep as it looks like shutil doesn't support concurrent access
            self.m_scheduler.emit_status(
                self.get_name(), "Creating archive, this might take a while", 103
            )
            today = datetime.datetime.now()

            try:
                with open(os.path.join("ressources", "version.txt"), 'r') as file:
                    package_version = file.read()
                if site_conf_obj.m_app["version"].split("_")[0] != package_version:
                    with open(os.path.join("ressources", "version.txt"), 'w') as file:
                        file.write(site_conf_obj.m_app["version"].split("_")[0])

                # Create a temporary directory to hold the archive content
                with tempfile.TemporaryDirectory() as temp_dir:
                    # Liste des dossiers spécifiques pour inclure tous les fichiers, y compris les .tar.gz
                    include_tar_gz_dirs = site_conf_obj.m_include_tar_gz_dirs

                    # Parcourir les fichiers dans 'ressources'
                    for root, dirs, files in os.walk("ressources"):
                        relative_path = os.path.relpath(root, "ressources")
                        dest_dir = os.path.join(temp_dir, relative_path)
                        os.makedirs(dest_dir, exist_ok=True)

                        for file in files:
                            source_path = os.path.join(root, file)
                            dest_path = os.path.join(dest_dir, file)

                            abs_root = os.path.abspath(root)
                            abs_tools_root = os.path.abspath("ressources/binaries/tools")

                            # Vérifier si le dossier actuel est un dossier spécifique
                            # if any(os.path.commonpath([root, include_dir]) == include_dir for include_dir in include_tar_gz_dirs):
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
                    archive_path = os.path.join("packages", today.strftime("%y%m%d_" + self.m_file))
                    shutil.make_archive(archive_path, "zip", temp_dir)

                self.m_scheduler.emit_status(
                    self.get_name(), "Creating archive, this might take a while", 100
                )
            except Exception as e:
                self.m_logger.info("Package creation failed: " + str(e))
                self.m_scheduler.emit_status(
                    self.get_name(), "Error in creating the archive: " + str(e), 101
                )

            to_upload_files = utilities.util_dir_structure(
                os.path.join("packages"), inclusion=[".zip"]
            )
            reloader = utilities.util_view_reload_input_file_manager(
                self.m_default_name,
                "upload_package",
                [to_upload_files],
                ["Files to upload"],
                ["file-upload"],
                ["primary"],
                [False],
            )
            self.m_scheduler.emit_reload(reloader)

        elif self.m_action == "upload_package":
            self.m_scheduler.emit_status(
                self.get_name(), "Uploading package, this might take a while", 103
            )

            # Folder mode
            if config["updates"]["source"]["value"] == "Folder":
                try:
                    os.mkdir(
                        os.path.join(config["updates"]["folder"]["value"], "packages")
                    )
                except FileExistsError:
                    pass

                try:
                    os.mkdir(
                        os.path.join(
                            config["updates"]["folder"]["value"],
                            "packages",
                            site_conf_obj.m_app["name"],
                        )
                    )
                except FileExistsError:
                    pass

                shutil.copyfile(
                    self.m_file,
                    os.path.join(
                        config["updates"]["folder"]["value"],
                        "packages",
                        site_conf_obj.m_app["name"],
                        self.m_file.split(os.path.sep)[-1],
                    ),
                )

            # FTP mode
            elif config["updates"]["source"]["value"] == "FTP":
                try:
                    # Définition du dossier distant
                    remote_dir = os.path.join(
                        config["updates"]["path"]["value"],
                        "packages",
                        site_conf_obj.m_app["name"]
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
                    self.m_logger.info(f"Package uploading failed: {e}")
                    self.m_scheduler.emit_status(
                        self.get_name(),
                        "Uploading package, this might take a while",
                        101,
                    )
            self.m_scheduler.emit_status(
                self.get_name(), "Uploading package, this might take a while", 100
            )

        elif (
            self.m_action == "download_package" or self.m_action == "load_package_file"
        ):
            path_to_file = self.m_file
            if self.m_action == "download_package":
                self.m_scheduler.emit_status(
                    self.get_name(), "Downloading package, this might take a while", 103
                )

                try:
                    os.mkdir(os.path.join("downloads"))
                except FileExistsError:
                    pass

                try:
                    os.mkdir(os.path.join("ressources"))
                except FileExistsError:
                    pass

                # Folder mode
                config = utilities.util_read_parameters()
                # path_to_file = self.m_file
                if config["updates"]["source"]["value"] == "Folder":
                    shutil.copyfile(
                        os.path.join(
                            config["updates"]["folder"]["value"],
                            "packages",
                            site_conf_obj.m_app["name"],
                            self.m_file,
                        ),
                        os.path.join("downloads", self.m_file),
                    )

                # FTP mode
                elif config["updates"]["source"]["value"] == "FTP":
                    path_to_file = os.path.join("downloads", self.m_file).replace("\\", "/")  # Assure la compatibilité Windows/Linux

                    try:
                        # Définition du chemin distant
                        remote_file_path = os.path.join(
                            config["updates"]["path"]["value"],
                            "packages",
                            site_conf_obj.m_app["name"],
                            self.m_file
                        ).replace("\\", "/")  # Compatibilité Windows/Linux

                        # Création du dossier local "downloads" s'il n'existe pas
                        os.makedirs(os.path.dirname(path_to_file), exist_ok=True)

                        # Téléchargement du fichier
                        sftp_conn.download_file(remote_file_path, path_to_file)

                    except Exception as e:
                        self.m_logger.info(f"Download package failed: {e}")
                        self.m_scheduler.emit_status(
                            self.get_name(),
                            "Downloading package, this might take a while",
                            101,
                        )

                self.m_scheduler.emit_status(
                    self.get_name(), "Downloading package, this might take a while", 100
                )
            else:
                if ".zip" not in self.m_file:
                    self.m_scheduler.emit_popup(
                        scheduler.logLevel.error, "Package must be a .zip"
                    )
                    return

            # Remove only .tar.gz files in the "ressources" folder and its subfolders, excluding specific directories
            self.m_scheduler.emit_status(self.get_name(), "Deleting old tar.gz content", 103)

            ressources_path = os.path.join("ressources")

            # Dossiers spécifiques où les .tar.gz ne doivent pas être supprimés
            exclude_dirs_abs = [os.path.abspath(p) for p in site_conf_obj.m_include_tar_gz_dirs]
            # exclude_tar_gz_dirs = site_conf_obj.m_include_tar_gz_dirs

            if os.path.exists(ressources_path):
                for root, dirs, files in os.walk(ressources_path):
                    root_abs = os.path.abspath(root)
                    # Vérifie si root est dans un des dossiers exclus
                    if any(root_abs.startswith(exclude_dir) for exclude_dir in exclude_dirs_abs):
                        self.m_logger.info(f"Skipping excluded dir for .tar.gz deletion: {root_abs}")
                        continue

                    for file in files:
                        if file.endswith(".tar.gz"):
                            file_path = os.path.join(root, file)
                            try:
                                os.remove(file_path)
                                self.m_logger.info(f"Deleted .tar.gz: {file_path}")
                            except Exception as e:
                                self.m_logger.warning(f"Failed to delete {file_path}: {str(e)}")
                                self.m_scheduler.emit_status(self.get_name(), f"Failed to delete {file_path}: {str(e)}", 50)
            else:
                os.mkdir(ressources_path)

            self.m_scheduler.emit_status(self.get_name(), "Deleting old tar.gz content", 100)

            try:
                self.m_scheduler.emit_status(
                    self.get_name(), "Unpacking archive, this might take a while", 103
                )
                try:
                    shutil.unpack_archive(
                        path_to_file,
                        os.path.join("ressources"),
                        "zip",
                    )
                except FileNotFoundError as e:
                    self.m_logger.warning(f"Skipping missing file: {e}")
                    pass
                except OSError as e:
                    if e.errno == errno.ENAMETOOLONG:
                        self.m_logger.error(f"Skipping file with too long path: {e}")
                    else:
                        raise

                self.m_scheduler.emit_status(
                    self.get_name(), "Unpacking archive, this might take a while", 100
                )

                # Émettre un statut avec une balise meta pour rafraîchir la page
                # Statut final avec balise meta pour rafraîchir la page
                message = (
                    "<meta http-equiv='refresh' content='5'>"
                    "<p>Unpacking completed successfully. The page will reload shortly.</p>"
                )
                self.m_scheduler.emit_status(self.get_name(), message, 103)

                time.sleep(7)
                self.m_scheduler.emit_status(
                    self.get_name(), "Unpacking archive success", 100
                )

            except Exception as e:
                self.m_logger.info("Unpacking failed: " + str(e))
                self.m_scheduler.emit_status(
                    self.get_name(),
                    "Unpacking archive, this might take a while",
                    101,
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
                    if data_raw[item] == "primary":
                        packager.set_file(item)
                packager.set_action("upload_package")

            elif "download" in data_in:
                packager.set_file(data_in["download_package"])
                packager.set_action("download_package")
            else:
                try:
                    for item in data_raw:
                        if data_raw[item] == "primary":
                            packager.set_file(item)
                    # f = request.files[".load_package_file"]
                    try:
                        os.mkdir(os.path.join("downloads"))
                    except FileExistsError:
                        pass

                    # f.save(os.path.join("downloads", f.filename))
                    # packager.set_file(f.filename)
                    packager.set_action("load_package_file")
                except Exception:
                    pass

            packager.start()

    disp = displayer.Displayer()
    disp.add_module(SETUP_Packager, display=False)
    disp.set_title(f"Binaries Package Manager")

    # Packager
    if access_manager.auth_object.authorize_group("admin") and not ((getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"))):
        disp.add_master_layout(
            displayer.DisplayerLayout(
                displayer.Layouts.VERTICAL,
                [3, 6, 3],
                subtitle="Package creation",
                alignment=[
                    displayer.BSalign.L,
                    displayer.BSalign.L,
                    displayer.BSalign.R,
                ],
            )
        )
        disp.add_display_item(displayer.DisplayerItemText("Create a new package"), 0)
        disp.add_display_item(displayer.DisplayerItemInputString("create_package"), 1)
        disp.add_display_item(
            displayer.DisplayerItemButton("pack", "Package creation"), 2
        )

        to_upload_files = utilities.util_dir_structure(
            os.path.join("packages"), inclusion=[".zip"]
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
        disp.add_display_item(displayer.DisplayerItemText("Upload package"), 0)
        disp.add_display_item(
            displayer.DisplayerItemInputFileExplorer(
                "upload_package",
                None,
                [to_upload_files],
                ["Files to upload"],
                ["file-upload"],
                ["primary"],
                [False],
            ),
            1,
        )
        disp.add_display_item(
            displayer.DisplayerItemButton("upload", "Package upload"), 2
        )

    disp.add_master_layout(
        displayer.DisplayerLayout(
            displayer.Layouts.VERTICAL,
            [3, 6, 3],
            subtitle="Package restoration",
            alignment=[
                displayer.BSalign.L,
                displayer.BSalign.L,
                displayer.BSalign.R,
            ],
        )
    )

    package_file = utilities.util_dir_structure(
            os.path.join("downloads"), inclusion=[".zip"]
        )
    disp.add_display_item(displayer.DisplayerItemText("Package available localy"), 0)
    # disp.add_display_item(displayer.DisplayerItemInputFile("load_package_file"), 1)
    disp.add_display_item(
            displayer.DisplayerItemInputFileExplorer(
                "load_package_file",
                None,
                [package_file],
                ["Package to unpack"],
                ["file-package"],
                ["primary"],
                [False],
            ),
            1,
        )
    disp.add_display_item(displayer.DisplayerItemButton("unpack", "Unpack"), 2)

    config = utilities.util_read_parameters()

    # Folder mode
    if config["updates"]["source"]["value"] == "Folder":
        if not os.path.exists(os.path.join(config["updates"]["folder"]["value"])):
            info = "Configured package folder doesn't exists"
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
                    "packages",
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
                displayer.DisplayerItemButton("download", "Install Package"), 2
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
            remote_dir = os.path.join(
                config["updates"]["path"]["value"],
                "packages",
                site_conf_obj.m_app["name"]
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
                displayer.DisplayerItemText("Select a package to download"), 0
            )
            disp.add_display_item(
                displayer.DisplayerItemInputSelect(
                    "download_package", None, None, content
                ),
                1,
            )
            disp.add_display_item(
                displayer.DisplayerItemButton("download", "Install package"), 2
            )

        except socket.gaierror:
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
        except Exception as e:
            info = "Unkown FTP error: " + str(e)
            disp.add_master_layout(
                displayer.DisplayerLayout(
                    displayer.Layouts.VERTICAL,
                    [12],
                    subtitle="",
                    alignment=[displayer.BSalign.C],
                )
            )
            disp.add_display_item(
                displayer.DisplayerItemAlert(info, displayer.BSstyle.WARNING), 0
            )

    return render_template(
        "base_content.j2", content=disp.display(), target="packager.packager"
    )

from flask import Blueprint, render_template, request

from submodules.framework.src import utilities
from submodules.framework.src import access_manager
from submodules.framework.src import site_conf
from submodules.framework.src import displayer
from submodules.framework.src import scheduler

import shutil
import socket
import datetime
from submodules.framework.src import threaded_action

import os
import ftplib


class SETUP_Packager(threaded_action.Threaded_action):
    m_default_name = "Binaries Package Manager"

    def set_file(self, file):
        self.m_file = file

    def set_action(self, action):
        self.m_action = action

    def action(self):
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
                shutil.make_archive(
                    os.path.join("packages", today.strftime("%y%m%d_" + self.m_file)),
                    "zip",
                    os.path.join("ressources"),
                )
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
            config = utilities.util_read_parameters()
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
                    session = ftplib.FTP(
                        config["updates"]["address"]["value"],
                        config["updates"]["user"]["value"],
                        config["updates"]["password"]["value"],
                    )

                    file = open(self.m_file, "rb")  # file to send
                    session.storbinary(
                        "STOR "
                        + config["updates"]["path"]["value"]
                        + "/packages/"
                        + site_conf_obj.m_app["name"]
                        + "/"
                        + self.m_file.split(os.path.sep)[-1],
                        file,
                    )  # send the file
                    file.close()  # close file and FTP
                    session.quit()
                except Exception as e:
                    self.m_logger.info("Package uploading failed: " + str(e))
                    self.m_scheduler.emit_status(
                        self.get_name(),
                        "Uploading package, this might take a while",
                        101,
                    )
                    return

            self.m_scheduler.emit_status(
                self.get_name(), "Uploading package, this might take a while", 100
            )

        elif (
            self.m_action == "download_package" or self.m_action == "load_package_file"
        ):
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
                    try:
                        session = ftplib.FTP(
                            config["updates"]["address"]["value"],
                            config["updates"]["user"]["value"],
                            config["updates"]["password"]["value"],
                        )
                        session.retrbinary(
                            "RETR "
                            + config["updates"]["path"]["value"]
                            + "/packages/"
                            + site_conf_obj.m_app["name"]
                            + "/"
                            + self.m_file,
                            open(os.path.join("downloads", self.m_file), "wb").write,
                        )  # send the file
                        session.quit()
                    except Exception as e:
                        self.m_logger.info("Download package failed: " + str(e))
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

            # Remove old binaries folder and add the new one
            self.m_scheduler.emit_status(self.get_name(), "Deleting old content", 0)
            try:
                shutil.rmtree(os.path.join("ressources"))
            except Exception:
                # Will except if it doesn't already exists
                pass
            os.mkdir(os.path.join("ressources"))

            self.m_scheduler.emit_status(self.get_name(), "Deleting old content", 100)

            self.m_scheduler.emit_status(
                self.get_name(), "Unpacking archive, this might take a while", 103
            )
            try:
                shutil.unpack_archive(
                    os.path.join("downloads", self.m_file),
                    os.path.join("ressources"),
                    "zip",
                )
                self.m_scheduler.emit_status(
                    self.get_name(), "Unpacking archive, this might take a while", 100
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
                    f = request.files[".load_package_file"]
                    try:
                        os.mkdir(os.path.join("downloads"))
                    except FileExistsError:
                        pass

                    f.save(os.path.join("downloads", f.filename))
                    packager.set_file(f.filename)
                    packager.set_action("load_package_file")
                except Exception:
                    pass

            packager.start()

    disp = displayer.Displayer()
    disp.add_module(SETUP_Packager)

    # Packager
    if access_manager.auth_object.authorize_group("admin"):
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
        disp.add_display_item(displayer.DisplayerItemText("Load package from file"), 0)
        disp.add_display_item(displayer.DisplayerItemInputFile("load_package_file"), 1)
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
                displayer.DisplayerItemButton("download", "Download"), 2
            )

    # FTP mode
    elif config["updates"]["source"]["value"] == "FTP":
        try:
            session = ftplib.FTP(
                config["updates"]["address"]["value"],
                config["updates"]["user"]["value"],
                config["updates"]["password"]["value"],
            )

            session.cwd(
                config["updates"]["path"]["value"]
                + "/packages/"
                + site_conf_obj.m_app["name"]
            )
            content = session.nlst()

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

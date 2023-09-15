from ctypes import util
from os import path
from flask import Blueprint, render_template, request, session

from framework import utilities
from framework import access_manager
from framework import site_conf
from framework import displayer

import json

from framework import threaded_action

from scp import SCPClient
import os
import zipfile
import pathlib
import importlib
import sys
import platform
import ftplib

class UPDATER_maker(threaded_action.Threaded_action):
    """Module to create and upload the update packages.
    
    Update package can be uploaded to FTP servers, provided that the correct credentials are given in the settings"""
    m_package = None
    m_action = None

    m_default_name = "Website engine update creation"

    def __init__(self):
        super().__init__() 

    def set_type(self, type: str) -> None:
        """Set the type of package to handle

        :param type: Can be the following values:

            * source (Only the python files)
            * distribution (PyInstaller distribution. Must be supported by the site_conf, see :meth:`Site_conf.create_distribuate`)
        :type type: str
        """
        self.m_package = type

    def set_action(self, action: str)  -> None:
        """Set the action to perform

        :param action: Can be the following values:

            * create (to create a new package)
            * upload (to upload a previously created package to the FTP server)
        :type action: str
        """
        self.m_action = action

    def action(self):
        """Execute the module
        """
        if self.m_action == "create":
            pass
            # Recover the site information
            site_conf_obj = site_conf.site_conf_obj
            
            # Create the udpate folder if needed
            try:
                os.makedirs(os.path.join("..", "updates"))
            except Exception as e:
                #Alread exists, no big deal
                pass
            
            self.m_scheduler.emit_status(self.get_name(), "Creation of the update package", 103)
            if self.m_package == "sources":
                directories=["templates", "assets", "framework", site_conf_obj.m_app["name"]]
            elif self.m_package == "distribution":
                # Create the package with pyinstaller
                try:
                    site_conf_obj.create_distribuate()
                except Exception as e:
                    self.m_scheduler.emit_status(self.get_name(), "Creation of the update package", 101, supplement=str(e))
                    return
                directories=[os.path.join("..", "updater", "dist")]

            extra = ""
            if self.m_package == "distribution":
                extra += "_" + platform.system()

            with zipfile.ZipFile(os.path.join("..", "updates", site_conf_obj.m_app["name"] + "_" + site_conf_obj.m_app["version"] + "_" + self.m_package + extra +".zip"), mode="w") as archive:
                for dir in directories:
                    directory = pathlib.Path(dir)
                    for file_path in directory.rglob("*"):
                        if self.m_package == "sources":
                            archive.write(file_path, arcname=os.path.join(dir, file_path.relative_to(directory)))
                        else:
                            archive.write(file_path, arcname=file_path.relative_to(directory))
                if self.m_package == "sources":
                    archive.write("main.py")
            self.m_scheduler.emit_status(self.get_name(), "Creation of the update package", 100)

        elif self.m_action == "upload":
            extra = ""
            if self.m_package == "distribution":
                extra += "_" + platform.system()

            # Recover the site information
            site_conf_obj = importlib.import_module("sites." + sys.argv[1] + ".site_conf").Site_conf()
            config = utilities.util_read_parameters()

            session = ftplib.FTP(config["updates"]["address"]["value"], config["updates"]["user"]["value"], config["updates"]["password"]["value"])
            file = open(os.path.join("..", "updates", site_conf_obj.m_app["name"] + "_" + site_conf_obj.m_app["version"] + "_" + self.m_package + extra +".zip"),'rb')                  # file to send
            self.m_scheduler.emit_status(self.get_name(), "Uploading update", 103)
            session.storbinary('STOR ' + config["updates"]["path"]["value"] + 'releases/' + site_conf_obj.m_app["name"] + "_" + site_conf_obj.m_app["version"] + "_" + self.m_package + extra +".zip", file)     # send the file
            self.m_scheduler.emit_status(self.get_name(), "Uploading update", 100)
            file.close()                                    # close file and FTP
            session.quit()
        

class UPDATER_exec(threaded_action.Threaded_action):
    """Module to handle updated and apply them
    
    Update package can be downlaoded from FTP servers, provided that the correct credentials are given in the settings"""

    m_action = None
    m_package = None

    m_default_name = "Website engine update"

    def __init__(self):
        super().__init__()

    def set_action(self, action: str) -> None:
        """Set the action to perform

        :param action: Can be the following values:

            * create (to create a new package)
            * upload (to upload a previously created package to the FTP server)
        :type action: str
        """

        self.m_action = action

    def set_package(self, package: str) -> None:
        """Set the target file for update

        :param package: The target file for update
        :type package: str
        """
        self.m_package = package

    def action(self):
        """Execute the module
        """
        if self.m_action == "update" or self.m_action == "load_update_file":
            self.m_scheduler.emit_status(self.get_name(), "Applying update", 103)
            current_param = utilities.util_read_parameters()
            with zipfile.ZipFile(os.path.join("..", "updates", self.m_package), mode='r') as zip:
                zip.extractall(path="../")

            # config file has been overwritten, we need to reapply current configuration
            new_param = utilities.util_read_parameters()

            # Add new topics
            for topic in new_param:
                if topic not in current_param:
                    current_param[topic] = new_param[topic]

            # Remove old ones
            to_remove = []
            for topic in current_param:
                if topic not in new_param:
                    to_remove.append(topic)

            for topic in to_remove:
                current_param.pop(topic)

            # and save
            utilities.util_write_parameters(current_param)

            self.m_scheduler.emit_status(self.get_name(), "Applying update", 100)
            if "distribution" in self.m_package:
                self.m_scheduler.emit_status(self.get_name(), "Please close application, run updater.bat and restart application", 102)
            else:
                self.m_scheduler.emit_status(self.get_name(), "Please restart application", 102)
        
        elif self.m_action == "download":
            config = utilities.util_read_parameters()

            try:
                os.mkdir(os.path.join("..", "updates"))
            except Exception as e:
                # Folder can already exists
                pass

            session = ftplib.FTP(config["updates"]["address"]["value"], config["updates"]["user"]["value"], config["updates"]["password"]["value"])
            self.m_scheduler.emit_status(self.get_name(), "Downloading update", 103)
            session.retrbinary('RETR ' + config["updates"]["path"]["value"] + 'releases/' + self.m_package, open(os.path.join("..", "updates", self.m_package), 'wb').write)     # send the file
            self.m_scheduler.emit_status(self.get_name(), "Downloading update", 100)
            session.quit()

            #Relist the package availables
            try:
                packages_total = os.listdir(os.path.join("..", "updates"))
                packages = []
                for pack in packages_total:
                    if "distribution" in pack and platform.system() in pack and sys.argv[1] in pack:
                        packages.append(pack)
                    if "sources" in pack and sys.argv[1] in pack:
                        packages.append(pack)
            except Exception as e:
                packages = []

            #Update the list of package since it has been changed
            inputs = []
            inputs.append({"label": "Select", "id": "extract_package", "value": "", "type": "select", "data": packages})
            reloader = utilities.util_view_reload_multi_input("extract_package", inputs)
            self.m_scheduler.emit_reload(reloader)


bp = Blueprint('updater', __name__, url_prefix='/updater')
@bp.route('/update', methods=['GET', 'POST'])
def update():
    """Update page to handle update package creation (if credential authorize it) or update package download and application
    """
    updater = utilities.util_view_init([UPDATER_maker, UPDATER_exec])
    data_in = None
    if request.method == "POST":
        data_in = utilities.util_post_to_json(request.form.to_dict())
        if UPDATER_maker.m_default_name in data_in:
            data_in = data_in[UPDATER_maker.m_default_name]
        elif UPDATER_exec.m_default_name in data_in:
            data_in = data_in[UPDATER_exec.m_default_name]

        try:
            f = request.files[".load_update_file"]
            try:
                os.mkdir("..", "ressources", sys.argv[1], "downloads")
            except Exception as e:
                pass
            f.save(os.path.join("..", "ressources", sys.argv[1], "downloads", f.filename))
            packager = UPDATER_exec()
            packager.set_action("load_update_file")
            packager.set_package(f.filename)
            packager.start()
        except Exception as e:
            pass

        if "create_package" in data_in:           
            packager = UPDATER_maker()
            packager.set_action("create")
            packager.set_type(data_in["create_package"].lower())
            packager.start()
        elif "upload_package" in data_in:
            packager = UPDATER_maker()
            packager.set_action("upload")
            packager.set_type(data_in["upload_package"].lower())
            packager.start()
        elif "extract_package" in data_in:
            packager = UPDATER_exec()
            packager.set_action("update")
            packager.set_package(data_in["extract_package"])
            packager.start()
        elif "download_package" in data_in:
            packager = UPDATER_exec()
            packager.set_action("download")
            packager.set_package(data_in["download_package"])
            packager.start()        
            
    disp = displayer.Displayer()
            
    disp.add_module(UPDATER_maker)
    
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [4, 6, 2], subtitle="", alignment = [displayer.BSalign.L, displayer.BSalign.L, displayer.BSalign.R]))

    disp.add_display_item(displayer.DisplayerItemText("Create a package of the program"), 0)  
    disp.add_display_item(displayer.DisplayerItemInputSelect("create_package", None, None, ["Sources", "Distribution"]), 1)
    disp.add_display_item(displayer.DisplayerItemButton("create", "Create"), 2)  

    if site_conf.site_conf_obj.p_updates_ftp:
        disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [4, 6, 2], subtitle="", alignment = [displayer.BSalign.L, displayer.BSalign.L, displayer.BSalign.R]))
        disp.add_display_item(displayer.DisplayerItemText("Upload a package of the program"), 0)  
        disp.add_display_item(displayer.DisplayerItemInputSelect("upload_package", None, None, ["Sources", "Distribution"]), 1)
        disp.add_display_item(displayer.DisplayerItemButton("upload", "Upload"), 2)  
        
    # List all the package availables
    try:
        packages_total = os.listdir(os.path.join("..", "updates"))
        packages = []
        for pack in packages_total:
            if "distribution" in pack and platform.system() in pack and sys.argv[1] in pack:
                packages.append(pack)
            if "sources" in pack and sys.argv[1] in pack:
                packages.append(pack)
    except Exception as e:
        packages = []

    disp.add_module(UPDATER_exec)
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [4, 6, 2], subtitle="", alignment = [displayer.BSalign.L, displayer.BSalign.L, displayer.BSalign.R]))

    disp.add_display_item(displayer.DisplayerItemText("Apply update"), 0)  
    disp.add_display_item(displayer.DisplayerItemInputSelect("extract_package", None, None, packages), 1)
    disp.add_display_item(displayer.DisplayerItemButton("apply", "Apply"), 2) 
    
    if site_conf.site_conf_obj.p_updates_ftp:
        try:
            config = utilities.util_read_parameters()

            session = ftplib.FTP(config["updates"]["address"]["value"], config["updates"]["user"]["value"], config["updates"]["password"]["value"])
            session.cwd(config["updates"]["path"]["value"] + 'releases')
            content = session.nlst()
            packages = []
            for pack in content:
                if "distribution" in pack and platform.system() in pack and sys.argv[1] in pack:
                    packages.append(pack)
                if "sources" in pack and sys.argv[1] in pack:
                    packages.append(pack)
            disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [4, 6, 2], subtitle="", alignment = [displayer.BSalign.L, displayer.BSalign.L, displayer.BSalign.R]))

            disp.add_display_item(displayer.DisplayerItemText("Doawnload update"), 0)  
            disp.add_display_item(displayer.DisplayerItemInputSelect("download_package", None, None, packages), 1)
            disp.add_display_item(displayer.DisplayerItemButton("download", "Download"), 2) 
        except Exception as e:
            warn = "OuFNis FTP server not accessible, please check your connection or use a zip file"
            disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12], subtitle=""))

            disp.add_display_item(displayer.DisplayerItemAlert(warn, displayer.BSstyle.WARNING), 0)

    
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [4, 6, 2], subtitle="", alignment = [displayer.BSalign.L, displayer.BSalign.L, displayer.BSalign.R]))
    disp.add_display_item(displayer.DisplayerItemText("Load package from file"), 0)  
    disp.add_display_item(displayer.DisplayerItemInputFile("load_update_file"), 1)
    disp.add_display_item(displayer.DisplayerItemButton("unpack", "Unpack"), 2)  
    
    return render_template('base_content_new.j2', content=disp.display(), target="updater.update")       

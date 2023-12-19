from ctypes import util
from os import path
from flask import Blueprint, render_template, request, session

from submodules.framework.src import utilities
from submodules.framework.src import access_manager
from submodules.framework.src import site_conf
from submodules.framework.src import displayer

import json
import socket

from submodules.framework.src import threaded_action

from scp import SCPClient
import os
import zipfile
import pathlib
import sys
import platform
import ftplib
import shutil

class SETUP_Updater(threaded_action.Threaded_action):
    """Module to create and upload the update packages.
    
    Update package can be uploaded to FTP servers, provided that the correct credentials are given in the settings"""
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

        # Recover the site information
        site_conf_obj = site_conf.site_conf_obj

        """Execute the module
        """
        if self.m_action == "update" or self.m_action == "load_update_file":
            self.m_scheduler.emit_status(self.get_name(), "Applying update", 103)
            current_param = utilities.util_read_parameters()
            with zipfile.ZipFile(os.path.join("..", "updates", self.m_file), mode='r') as zip:
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
            if "distribution" in self.m_file:
                self.m_scheduler.emit_status(self.get_name(), "Please close application, run updater.bat and restart application", 102)
            else:
                self.m_scheduler.emit_status(self.get_name(), "Please restart application", 102)
        
        elif self.m_action == "download":
            config = utilities.util_read_parameters()

            try:
                os.mkdir(os.path.join("updates"))
            except FileExistsError as e:
                pass

            # Folder mode
            self.m_scheduler.emit_status(self.get_name(), "Downloading archive, this might take a while", 103)
            config = utilities.util_read_parameters()
            if config["updates"]["source"]["value"] == "Folder":
                shutil.copyfile(os.path.join(config["updates"]["folder"]["value"], "updates", site_conf_obj.m_app["name"], self.m_file), os.path.join("downloads", self.m_file))

            # FTP mode
            elif config["updates"]["source"]["value"] == "FTP":
                try:
                    session = ftplib.FTP(config["updates"]["address"]["value"], config["updates"]["user"]["value"], config["updates"]["password"]["value"])
                    
                    session.retrbinary('RETR ' + config["updates"]["path"]["value"] +  '/updates/' + site_conf_obj.m_app["name"] + '/' + self.m_file, open(os.path.join("updates", self.m_file), 'wb').write)     # send the file
                    session.quit()
                except:
                    self.m_scheduler.emit_status(self.get_name(), "Downloading archive, this might take a while", 101)

            self.m_scheduler.emit_status(self.get_name(), "Downloading archive, this might take a while", 100)

            # session = ftplib.FTP(config["updates"]["address"]["value"], config["updates"]["user"]["value"], config["updates"]["password"]["value"])
            # self.m_scheduler.emit_status(self.get_name(), "Downloading update", 103)
            # session.retrbinary('RETR ' + config["updates"]["path"]["value"] + 'releases/' + self.m_file, open(os.path.join("..", "updates", self.m_file), 'wb').write)     # send the file
            # self.m_scheduler.emit_status(self.get_name(), "Downloading update", 100)
            # session.quit()

            #Relist the package availables
            try:
                packages_total = os.listdir(os.path.join("updates"))
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
        
        elif self.m_action == "create":
            pass
            
            # Create the udpate folder if needed
            try:
                os.makedirs(os.path.join("updates"))
            except Exception as e:
                #Alread exists, no big deal
                pass
            
            self.m_scheduler.emit_status(self.get_name(), "Creation of the update package", 103)
            # Create the package with pyinstaller
            try:
                site_conf_obj.create_distribuate()
            except Exception as e:
                self.m_scheduler.emit_status(self.get_name(), "Creation of the update package", 101, supplement=str(e))
                return
            directories=[os.path.join("updater", "dist")]

            with zipfile.ZipFile(os.path.join("updates", site_conf_obj.m_app["name"] + "_" + site_conf_obj.m_app["version"] + "_" + platform.system() +".zip"), mode="w") as archive:
                for dir in directories:
                    directory = pathlib.Path(dir)
                    for file_path in directory.rglob("*"):
                        if self.m_file == "sources":
                            archive.write(file_path, arcname=os.path.join(dir, file_path.relative_to(directory)))
                        else:
                            archive.write(file_path, arcname=file_path.relative_to(directory))
                if self.m_file == "sources":
                    archive.write("main.py")
            self.m_scheduler.emit_status(self.get_name(), "Creation of the update package", 100)

        elif self.m_action == "upload":
            self.m_file = os.path.join("updates", site_conf_obj.m_app["name"] + "_" + site_conf_obj.m_app["version"] + "_" + platform.system() +".zip")

            self.m_scheduler.emit_status(self.get_name(), "Uploading update, this might take a while", 103)

            # Folder mode
            config = utilities.util_read_parameters()

            if config["updates"]["source"]["value"] == "Folder":
                try:
                    os.mkdir(os.path.join(config["updates"]["folder"]["value"], "updates"))
                except FileExistsError as e:
                    pass

                try:
                    os.mkdir(os.path.join(config["updates"]["folder"]["value"], "updates", site_conf_obj.m_app["name"]))
                except FileExistsError as e:
                    pass
                
                shutil.copyfile(self.m_file, os.path.join(config["updates"]["folder"]["value"], "updates", site_conf_obj.m_app["name"], self.m_file.split(os.path.sep)[-1]))
                
            # FTP mode
            elif config["updates"]["source"]["value"] == "FTP":
                try:
                    session = ftplib.FTP(config["updates"]["address"]["value"], config["updates"]["user"]["value"], config["updates"]["password"]["value"])
                    
                    file = open(self.m_file,'rb')                  # file to send
                    session.storbinary('STOR ' + config["updates"]["path"]["value"] + "/updates/" + site_conf_obj.m_app["name"] + "/" + self.m_file.split(os.path.sep)[-1], file)     # send the file
                    file.close()                                    # close file and FTP
                    session.quit()  
                except:
                    self.m_scheduler.emit_status(self.get_name(), "Uploading update, this might take a while", 101)  
                    return


            self.m_scheduler.emit_status(self.get_name(), "Uploading update, this might take a while", 100)      

bp = Blueprint('updater', __name__, url_prefix='/updater')
@bp.route('/update', methods=['GET', 'POST'])
def update():
    """Update page to handle update package creation (if credential authorize it) or update package download and application
    """
    site_conf_obj = site_conf.site_conf_obj
    data_in = None
    if request.method == "POST":
        data_in = utilities.util_post_to_json(request.form.to_dict())
        data_in = data_in[SETUP_Updater.m_default_name]

        if "create" in data_in:           
            packager = SETUP_Updater()
            packager.set_action("create")
            packager.start()
        elif "upload" in data_in:
            packager = SETUP_Updater()
            packager.set_action("upload")
            packager.start()
        elif "apply" in data_in:
            packager = SETUP_Updater()
            packager.set_action("update")
            packager.set_file(data_in["extract_package"])
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
                except Exception as e:
                    pass
                f.save(os.path.join("downloads", f.filename))
                packager = SETUP_Updater()
                packager.set_action("load_update_file")
                packager.set_file(f.filename)
                packager.start()
            except Exception as e:
                pass    
            
    disp = displayer.Displayer()
    disp.add_module(SETUP_Updater)
    config = utilities.util_read_parameters()
    
    if access_manager.auth_object.authorize_group("admin"):
        disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [3, 6, 3], subtitle="Update Creation", alignment = [displayer.BSalign.L, displayer.BSalign.L, displayer.BSalign.R]))

        disp.add_display_item(displayer.DisplayerItemText("Create a new update with installer"), 0)  
        disp.add_display_item(displayer.DisplayerItemButton("create", "Create"), 2)  

        disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [3, 6, 3], subtitle="", alignment = [displayer.BSalign.L, displayer.BSalign.L, displayer.BSalign.R]))
        disp.add_display_item(displayer.DisplayerItemText("Upload the latested update"), 0)  
        disp.add_display_item(displayer.DisplayerItemButton("upload", "Upload"), 2)  
        
    
    to_apply = utilities.util_dir_structure(os.path.join("updates"), ".zip")
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [3, 6, 3], subtitle="Update Deployment", alignment = [displayer.BSalign.L, displayer.BSalign.L, displayer.BSalign.R]))
    disp.add_display_item(displayer.DisplayerItemText("Apply update"), 0)  
    disp.add_display_item(displayer.DisplayerItemInputSelect("update_package", None, None, to_apply), 1)
    disp.add_display_item(displayer.DisplayerItemButton("apply", "Apply"), 2) 
    
     # Folder mode
    if config["updates"]["source"]["value"] == "Folder":
        if not os.path.exists(os.path.join(config["updates"]["folder"]["value"])):
            info = "Configured update folder doesn't exists"
            disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12], subtitle="", alignment=[displayer.BSalign.C]))
            disp.add_display_item(displayer.DisplayerItemAlert(info, displayer.BSstyle.INFO), 0)
        else:
            content = utilities.util_dir_structure(os.path.join(config["updates"]["folder"]["value"], "updates", site_conf_obj.m_app["name"]), inclusion=[".zip"])
            disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [3, 6, 3], subtitle="", alignment = [displayer.BSalign.L, displayer.BSalign.L, displayer.BSalign.R]))
            disp.add_display_item(displayer.DisplayerItemText("Select a package to download"), 0)  
            disp.add_display_item(displayer.DisplayerItemInputSelect("download_package", None, None, content), 1)
            disp.add_display_item(displayer.DisplayerItemButton("download", "Download"), 2)   

    # FTP mode
    elif config["updates"]["source"]["value"] == "FTP":
        try:
            session = ftplib.FTP(config["updates"]["address"]["value"], config["updates"]["user"]["value"], config["updates"]["password"]["value"])
            
            session.cwd(config["updates"]["path"]["value"] + '/updates')
            content = session.nlst()

            disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [3, 6, 3], subtitle="", alignment = [displayer.BSalign.L, displayer.BSalign.L, displayer.BSalign.R]))
            disp.add_display_item(displayer.DisplayerItemText("Select a package to download"), 0)  
            disp.add_display_item(displayer.DisplayerItemInputSelect("download_package", None, None, content), 1)
            disp.add_display_item(displayer.DisplayerItemButton("download", "Download"), 2)    

        except socket.gaierror as e:
            info = "FTP server not accessible, please check your connection, use a zip file or use a local folder"
            disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12], subtitle="", alignment=[displayer.BSalign.C]))
            disp.add_display_item(displayer.DisplayerItemAlert(info, displayer.BSstyle.INFO), 0)
        except:
            info = "Unkown FTP error"
            disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [12], subtitle="", alignment=[displayer.BSalign.C]))
            disp.add_display_item(displayer.DisplayerItemAlert(info, displayer.BSstyle.WARNING), 0) 
    
    disp.add_master_layout(displayer.DisplayerLayout(displayer.Layouts.VERTICAL, [3, 6, 3], subtitle="", alignment = [displayer.BSalign.L, displayer.BSalign.L, displayer.BSalign.R]))
    disp.add_display_item(displayer.DisplayerItemText("Load package from file"), 0)  
    disp.add_display_item(displayer.DisplayerItemInputFile("load_update_file"), 1)
    disp.add_display_item(displayer.DisplayerItemButton("unpack", "Unpack"), 2)  
    
    return render_template('base_content_new.j2', content=disp.display(), target="updater.update")       

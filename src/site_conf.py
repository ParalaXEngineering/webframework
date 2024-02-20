from submodules.framework.src import access_manager
from submodules.framework.src import scheduler

import os

site_conf_obj = None
site_conf_app_path = None


class Site_conf:
    """Provides a set of function to configure the website"""

    m_app = {"name": "Default", "version": "0", "icon": "home"}
    """App information"""

    m_sidebar = []
    """Sidebar content"""

    m_topbar = {"display": False, "left": [], "center": [], "right": [], "login": False}
    """Topbar content"""

    m_javascripts = []
    """Custom javascripts"""

    m_scheduler_lt_functions = []
    """Functions that can be registered in the long term scheduler. Should be an array of arrays which are [func, period]"""

    def register_scheduler_lt_functions(self):
        """
        Register all the functions that are set in the m_scheduler_lt_functions, which must be populated by the child class
        """
        print(self.m_scheduler_lt_functions)
        for func in self.m_scheduler_lt_functions:
            scheduler.scheduler_ltobj.register_function(func[0], func[1])

    def add_sidebar_title(self, title: str):
        """Add a sidebar title, which can logically seperate several parts of the sidebar

        :param title: The title to add
        :type title: str
        """

        # Check if not already there
        for i in range(0, len(self.m_sidebar)):
            if "name" in self.m_sidebar[i] and self.m_sidebar[i]["name"] == title:
                return

        self.m_sidebar.append({"name": title, "isTitle": True})

    def add_sidebar_section(self, section: str, icon: str, endpoint: str):
        """Add a section to the sidebar. Sections are not clickable and are meant to host a submenu

        :param section: The section
        :type section: str
        :param icon: The section icon, from the mdi icon pack.
        :type icon: str
        :param endpoint: The endpoint address of the section.
        :type endpoint: str
        """
        for i in range(0, len(self.m_sidebar)):
            if "name" in self.m_sidebar[i] and self.m_sidebar[i]["name"] == section:
                return

        self.m_sidebar.append(
            {
                "name": section,
                "endpoint": endpoint,
                "icon": "mdi-" + icon,
                "cat": "",
                "submenu": [],
            }
        )

    def add_sidebar_page(self, name: str, icon: str, url: str):
        """Add a page to the sidebar

        :param name: The name of the page
        :type name: str
        :param icon: The page icon, from the mdi icon pack.
        :type icon: str
        :param url: The url of the page
        :type url: str
        """
        for i in range(0, len(self.m_sidebar)):
            if "name" in self.m_sidebar[i] and self.m_sidebar[i]["name"] == name:
                return

        self.m_sidebar.append(
            {
                "name": name,
                "endpoint": url,
                "url": url,
                "icon": "mdi-" + icon,
                "cat": "",
            }
        )

    def add_sidebar_submenu(
        self, name: str, url: str, parameter: str = None, endpoint: str = None
    ):
        """Add a submenu to the sidebar. It uses the url in order to extract the section. The url must be in the form endpoint.page

        :param name: The name of the submenu
        :type name: str
        :param url: The url of the submenu
        :type url: str
        :param parameter: Optional parameters for the page, that is the part of the GET url (e.g: topic=help), defaults to None
        :type parameter: str, optional
        :param endpoint: Optional endpoint override, instead of using the one in the url., defaults to None
        :type endpoint: str, optional
        """
        url_endpoint = url.split(".")[0]
        if not endpoint:
            endpoint = url_endpoint
        for i in range(0, len(self.m_sidebar)):
            if "submenu" in self.m_sidebar[i]:
                for j in range(0, len(self.m_sidebar[i]["submenu"])):
                    # if(self.m_sidebar[i]["submenu"][j]["name"] == name
                    #     and "endpoint" in self.m_sidebar[i]["submenu"][j]
                    #     and endpoint in self.m_sidebar[i]["submenu"][j]["endpoint"]):
                    if self.m_sidebar[i]["submenu"][j]["name"] == name:
                        return

            if (
                "endpoint" in self.m_sidebar[i]
                and self.m_sidebar[i]["endpoint"] == endpoint
            ):
                self.m_sidebar[i]["submenu"].append(
                    {"name": name, "url": url, "cat": ""}
                )

                if parameter:
                    self.m_sidebar[i]["submenu"][-1]["param"] = parameter

    def add_topbar_button(
        self, id: str, icon: str, text: str, area: str, link: str = None
    ):
        """Add a new button to the topbar

        :param id: The id (of the div) of the button
        :type id: str
        :param icon: The icon, from the mdi library
        :type icon: str
        :param text: The text of the button
        :type text: str
        :param area: The area of the topbar where the button lives (left, center or right)
        :type area: str
        :param link: Optional link where the button will point, defaults to None
        :type link: str, optional
        """
        self.m_topbar["display"] = True
        if area in self.m_topbar:
            for i in range(0, len(self.m_topbar[area])):
                if self.m_topbar[area][i]["id"] == id:
                    return

            self.m_topbar[area].append(
                {
                    "type": "button",
                    "icon": icon,
                    "text": text,
                    "id": id,
                    "color": "secondary",
                    "link": link,
                }
            )

    def add_topbar_thread_info(self, icon: str, area: str):
        """Add a zone where the thread are displayed. It can be skinned with an icon

        :param icon: The skin icon, mdi format
        :type icon: str
        :param area: The zone (center, left, right) where the status lives in the topbar
        :type area: str
        """
        self.m_topbar["display"] = True
        if area in self.m_topbar:
            for i in range(0, len(self.m_topbar[area])):
                if self.m_topbar[area][i]["id"] == "thread":
                    return

            self.m_topbar[area].append(
                {"type": "thread", "icon": icon, "color": "secondary", "id": "thread"}
            )

    def add_topbar_modal(
        self,
        id: str,
        icon: str,
        text: str,
        area: str,
        modal_text: str,
        modal_title: str,
        modal_footer: str,
        color: str,
    ):
        """Add a new button to the topbar that will display a modal information.

        Modal text content can be modified later on with the scheduler, or with the *update_topbar_modal* function

        :param id: The id (of the div) of the button
        :type id: str
        :param icon: The icon, from the mdi library
        :type icon: str
        :param text: The text of the button
        :type text: str
        :param area: The area of the topbar where the button lives (left, center or right)
        :type area: str
        :param modal_text: The content of the modal
        :type modal_text: str
        :param modal_title: _description_
        :type modal_title: str
        :param modal_footer: The title of the modal
        :type modal_footer: str
        :param color:  The footer of the modal
        :type color: str
        """

        self.m_topbar["display"] = True
        if area in self.m_topbar:
            for i in range(0, len(self.m_topbar[area])):
                if self.m_topbar[area][i]["id"] == id:
                    return

            self.m_topbar[area].append(
                {
                    "type": "modal",
                    "icon": icon,
                    "text": text,
                    "id": id,
                    "modal_text": modal_text,
                    "modal_title": modal_title,
                    "modal_footer": modal_footer,
                    "color": color,
                }
            )

    def update_topbar_button(
        self,
        id: str,
        icon: str,
        text: str,
        area: str,
        color: str = "secondary",
        link: str = None,
    ):
        """Update a new button to the topbar, works also for modals

        :param id: The id (of the div) of the button
        :type id: str
        :param icon: The icon, from the mdi library
        :type icon: str
        :param text: The text of the button
        :type text: str
        :param area: The area of the topbar where the button lives (left, center or right)
        :type area: str
        :param color: The color of the button, defaults to "secondary"
        :type color: str, optional
        :param link: Optionnal link, href on the button, defaults to None
        :type link: str, optional
        """

        self.m_topbar["display"] = True
        if area in self.m_topbar:
            for i in range(0, len(self.m_topbar[area])):
                if self.m_topbar[area][i]["id"] == id:
                    self.m_topbar[area][i]["icon"] = icon
                    self.m_topbar[area][i]["text"] = text
                    self.m_topbar[area][i]["color"] = color
                    self.m_topbar[area][i]["link"] = link

    def update_topbar_modal(self, id: str, text: str, area: str):
        """Update the content text of a modal

        :param id: The id (of the div) of the button
        :type id: str
        :param text: The text of the button
        :type text: str
        :param area: The area of the topbar where the button lives (left, center or right)
        :type area: str
        """
        self.m_topbar["display"] = True
        if area in self.m_topbar:
            for i in range(0, len(self.m_topbar[area])):
                if self.m_topbar[area][i]["id"] == id:
                    self.m_topbar[area][i]["modal_text"] = text

    def add_javascript(self, script: str):
        """Add a new script to load on the page

        :param script: A string with the path to the string, from assets/js
        :type script: str
        """
        self.m_javascripts.append(script)

    def use_login(self):
        """Indicate that this website uses login"""
        self.m_topbar["login"] = True
        access_manager.auth_object.use_login(True)
        return

    def app_details(self, name: str, version: str, icon: str):
        """Set the application details

        :param name: The name of the application
        :type name: str
        :param version: The version of the application
        :type version: str
        :param icon: The icon of the application, in mdi format
        :type icon: str
        """
        self.m_app["name"] = name
        self.m_app["icon"] = icon
        self.m_app["version"] = version

    def context_processor(self):
        """Function that is called before rendering any page, should be overwritten by the child object"""
        return

    def socketio_event(self, event, data):
        """Function called to respond to event, should be overwritten by the child object"""
        return

    def create_distribuate(self):
        """Function to create the distribuable package on this plateform, should be overwritten by the child object"""
        raise Exception("Distribuate creation not handled by this website")
        return False
    
    def get_statics(self, app_path) -> dict:
        """Function to store the other endpoints that must be registered by the application, for instance to serve images """
        return {"images": os.path.join(app_path, "website", "assets", "images")}

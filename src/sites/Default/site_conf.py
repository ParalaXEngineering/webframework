from submodules.framework.src.framework import site_conf
from submodules.framework.src.framework import utilities

import threading
import os

class Site_conf(site_conf.Site_conf):
    def __init__(self):
        # Setup sidebar
        self.add_sidebar_section("Settings", "cog", "settings")
        self.add_sidebar_submenu("Configuration", "settings.config_edit")

        self.add_sidebar_page("Hello", "hello world", "default.hello")

        # Configure app
        self.app_details("Default", "1.0", "chip")


    def context_processor(self) -> None:
       
        return super().context_processor()
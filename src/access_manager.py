from submodules.framework.src import utilities

import json

auth_object = None


class Access_manager:
    """Class that handle user management. It provide easy method to get the
    current user and its auhtorization on a given page or module.

    :warning: It is supposed that there is a correctly configured "config.json"
    pertinent to the application
    """

    def __init__(self):
        self.m_login = False
        self.m_user = ""

        self.m_users = {}
        self.m_groups = []
        self.m_modules = {}

        self.m_users_groups = {}

        self.load_authorizations()

    def load_authorizations(self):
        """Load the authorization file into the manager"""
        config = utilities.util_read_parameters()
    
        if "access" in config:
            self.m_users = config["access"]["users"]["value"]
            self.m_users_groups = config["access"]["users_groups"]["value"]
            self.m_groups = config["access"]["groups"]["value"]
            self.m_modules = config["access"]["modules"]["value"]

            if (
                "default_user" in config["access"]
                and config["access"]["default_user"]["value"] in self.m_users
            ):
                self.m_user = config["access"]["default_user"]["value"]

            # When creating a user, the user name is not in the authorization
            # file.Let's add it here, otherwise it will be too much a pain
            # to do elsewhere
            for user in config["access"]["users"]["value"]:
                if user not in config["access"]["users_password"]["value"]:
                    config["access"]["users_password"]["value"][user] = [""]

                if user not in config["access"]["users_groups"]["value"]:
                    config["access"]["users_groups"]["value"][user] = ["admin"]

    def get_login(self) -> bool:
        """Return the information as to if a user is logged

        :return: True if a user is logged
        :rtype: bool
        """
        return self.m_login

    def get_user(self) -> str:
        """Return the currently logged user, if any

        :return: The currently logged user
        :rtype: str
        """
        return self.m_user

    def use_login(self, login: bool):
        """Activate the login capabilities of the website

        :param login: True to activate the login capabilities, False otherwise
        :type login: bool
        """
        self.m_login = login

    def set_user(self, user: str, password: str):
        """Set the current user

        :param user: The user to set
        :type user: str
        :param password: The password of the user
        :type password: str
        """

        # Check if not already there
        if self.m_login:
            # Check password
            config = utilities.util_read_parameters()
            if user not in config["access"]["users_password"]["value"]:
                # No password
                self.m_user = user
                return True
            if (
                password in config["access"]["users_password"]["value"][user]
                or config["access"]["users_password"]["value"][user] == ""
            ):
                self.m_user = user
                config = utilities.util_read_parameters()
                return True
            else:
                return False

    def authorize_group(self, allowed_groups: list = None) -> bool:
        """Indicate if the current user is in an authorized group

        :param allowed_groups: A list of groups, defaults to None
        :type allowed_groups: list, optional
        :return: True if the current user is in the list, or if login
        is disabled, false otherwise
        :rtype: bool
        """
        if not self.m_login:
            return True

        # No identification was provided
        if not self.m_user:
            return False

        for user_group in self.m_users_groups[self.m_user]:
            if user_group in allowed_groups:
                return True

        return False

    def authorize_module(self, module: str) -> bool:
        """Indicate if the current user has access to the given module

        :param module: The module to check
        :type module: str
        :return: True if the current user is authorized to access the group
        :rtype: bool
        """

        if not self.m_login:
            return True

        # No identification was provided
        if not self.m_user:
            return False

        # print(self.m_modules[module])

        for user_group in self.m_users_groups[self.m_user]:
            if module not in self.m_modules:
                # Core modules are always in admin mode
                if user_group == "admin":
                    return True

            elif user_group in self.m_modules[module]:
                return True

        return False

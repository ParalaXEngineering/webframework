from submodules.framework.src import utilities
from submodules.framework.src.security_utils import failed_login_manager
from flask import session
import bcrypt
import logging

logger = logging.getLogger("website")
auth_object = None


class Access_manager:
    """Class that handle user management. It provide easy method to get the
    current user and its auhtorization on a given page or module.

    :warning: It is supposed that there is a correctly configured "config.json"
    pertinent to the application
    """

    def __init__(self):
        self.m_login = False

        self.m_users = {}
        self.m_groups = []
        self.m_modules = {}

        self.m_users_groups = {}

    def load_authorizations(self):
        """Load the authorization file into the manager"""
        config = utilities.util_read_parameters()

        if "access" in config:
            self.m_users = config["access"]["users"]["value"]
            self.m_users_groups = config["access"]["users_groups"]["value"]
            self.m_groups = config["access"]["groups"]["value"]
            self.m_modules = config["access"]["modules"]["value"]

            if "username" not in session:
                if ("default_user" in config["access"] and config["access"]["default_user"]["value"] in self.m_users):
                    session['username'] = config["access"]["default_user"]["value"]
                else:
                    session['username'] = "GUEST"

            # When creating a user, the user name is not in the authorization
            # file. Let's add it here, otherwise it will be too much a pain
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
        if 'username' not in session:
            session['username'] = "GUEST"
        return session['username']

    def use_login(self, login: bool):
        """Activate the login capabilities of the website

        :param login: True to activate the login capabilities, False otherwise
        :type login: bool
        """
        self.m_login = login

    def unlog(self):
        if 'username' in session:
            session['username'] = "GUEST"

    # def set_user(self, user: str, password: str):
    #     """Set the current user

    #     :param user: The user to set
    #     :type user: str
    #     :param password: The password of the user
    #     :type password: str
    #     """

    #     if not self.m_users_groups:
    #         self.load_authorizations()

    #     # Check if not already there
    #     if self.m_login:
    #         # Check password
    #         config = utilities.util_read_parameters()
    #         if user not in config["access"]["users_password"]["value"]:
    #             # No password
    #             session['username'] = user
    #             return True
    #         if (
    #             password in config["access"]["users_password"]["value"][user]
    #             or config["access"]["users_password"]["value"][user] == ""
    #         ):
    #             session['username'] = user
    #             return True
    #         else:
    #             session['username'] = "GUEST"
    #             return False
    def set_user(self, user: str, password_verified: bool):
        """Set the current user

        :param user: The user to set
        :type user: str
        :param password_verified: Indicate if the password has been verified
        :type password_verified: bool
        """

        if not self.m_users_groups:
            self.load_authorizations()

        # Si l'utilisateur est déjà connecté ou si le mot de passe a été vérifié, mettez à jour la session
        if self.m_login or password_verified:
            session['username'] = user
            return True
        else:
            session['username'] = "GUEST"
            return False

    def check_login_attempt(self, username: str, password: str):
        """Vérifie les identifiants et gère le verrouillage
        
        :param username: Le nom d'utilisateur
        :type username: str
        :param password: Le mot de passe à vérifier
        :type password: str
        :return: Tuple (succès, message_erreur)
        :rtype: tuple(bool, str)
        """
        config = utilities.util_read_parameters()
        users = config["access"]["users"]["value"]
        users_password = config["access"]["users_password"]["value"]
        
        # Vérifier si le compte est verrouillé
        is_locked, locked_until = failed_login_manager.is_locked(username)
        if is_locked:
            remaining_time = failed_login_manager.get_lockout_time_remaining(username)
            minutes = int(remaining_time // 60)
            seconds = int(remaining_time % 60)
            error_message = f"Account locked. Try again in {minutes}m {seconds}s"
            logger.warning(f"Blocked login attempt for locked user '{username}' (locked until {locked_until.strftime('%H:%M:%S')})")
            return False, error_message
        
        # Vérifier si l'utilisateur existe
        if username not in users:
            error_message = "User does not exist"
            logger.warning(f"Failed login attempt for non-existent user '{username}'")
            return False, error_message
        
        # Utilisateur sans mot de passe (accès toujours autorisé)
        if username not in users_password or users_password[username][0] == "":
            failed_login_manager.reset_attempts(username)
            logger.info(f"Successful login for user '{username}' (no password required)")
            return True, None
        
        # Vérifier le mot de passe avec bcrypt
        try:
            stored_password = users_password[username][0]
            stored_hash = stored_password.encode('utf-8')
            password_bytes = password.encode('utf-8')
            
            if bcrypt.checkpw(password_bytes, stored_hash):
                # Connexion réussie
                failed_login_manager.reset_attempts(username)
                logger.info(f"Successful login for user '{username}'")
                return True, None
            else:
                # Mot de passe incorrect
                count = failed_login_manager.increment_attempts(username)
                attempts_left = failed_login_manager.get_remaining_attempts(username)
                
                if count >= 5:
                    status = failed_login_manager.get_user_status(username)
                    error_message = "Too many failed attempts. Account locked for 5 minutes."
                    logger.warning(f"Account '{username}' LOCKED for 5 minutes (until {status['locked_until'].strftime('%H:%M:%S')})")
                else:
                    error_message = f"Bad Password for this user ({attempts_left} attempts remaining)"
                    logger.warning(f"Failed login attempt for user '{username}' ({attempts_left} attempts remaining)")
                
                return False, error_message
                
        except Exception as e:
            logger.error(f"CRITICAL: Exception during password verification for user '{username}': {e}")
            error_message = "Authentication error. Please contact administrator."
            return False, error_message

    def authorize_group(self, allowed_groups: list = None) -> bool:
        """Indicate if the current user is in an authorized group

        :param allowed_groups: A list of groups, defaults to None
        :type allowed_groups: list, optional
        :return: True if the current user is in the list, or if login
        is disabled, false otherwise
        :rtype: bool
        """
        if not self.m_users_groups:
            self.load_authorizations()

        if not self.m_login:
            return True

        # No identification was provided
        if 'username' not in session:
            self.load_authorizations()

        if not session['username']:
            return False

        if session['username'] not in self.m_users_groups:
            return False

        for user_group in self.m_users_groups[session['username']]:
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
        if 'username' not in session:
            # Check if we have a default user:
            self.load_authorizations()

        if not session['username']:
            self.load_authorizations()

        if session['username'] not in self.m_users_groups:
            self.load_authorizations()

        for user_group in self.m_users_groups[session['username']]:
            if module not in self.m_modules:
                # Core modules are always in admin mode
                if user_group == "admin":
                    return True

            elif user_group in self.m_modules[module]:
                return True

        return False

    def check_login_attempt(self, username: str, password: str) -> tuple:
        """Check login attempt with lockout management
        
        :param username: Username to check
        :type username: str
        :param password: Password to verify
        :type password: str
        :return: (success: bool, error_message: str or None)
        :rtype: tuple
        """
        config = utilities.util_read_parameters()
        users_password = config["access"]["users_password"]["value"]
        
        # Check if user is currently locked
        is_locked, locked_until = failed_login_manager.is_locked(username)
        if is_locked:
            remaining_time = failed_login_manager.get_lockout_time_remaining(username)
            minutes = int(remaining_time // 60)
            seconds = int(remaining_time % 60)
            error_message = f"Account locked. Try again in {minutes}m {seconds}s"
            logger.warning(f"Blocked login attempt for locked user '{username}' (locked until {locked_until.strftime('%H:%M:%S')})")
            return (False, error_message)
        
        # Check if user has no password (allowed)
        if username not in users_password:
            failed_login_manager.reset_attempts(username)
            logger.info(f"Successful login for user '{username}' (no password required)")
            return (True, None)
        
        # Verify password with bcrypt
        stored_password = users_password[username][0]
        stored_hash = stored_password.encode('utf-8')
        password_bytes = password.encode('utf-8')
        
        try:
            if bcrypt.checkpw(password_bytes, stored_hash):
                # Successful login - reset failed attempts
                failed_login_manager.reset_attempts(username)
                logger.info(f"Successful login for user '{username}'")
                return (True, None)
            else:
                # Failed login attempt
                count = failed_login_manager.increment_attempts(username)
                attempts_left = failed_login_manager.get_remaining_attempts(username)
                
                if count >= 5:
                    # Account is now locked for 5 minutes
                    status = failed_login_manager.get_user_status(username)
                    error_message = "Too many failed attempts. Account locked for 5 minutes."
                    logger.warning(f"Account '{username}' LOCKED for 5 minutes (until {status['locked_until'].strftime('%H:%M:%S')})")
                else:
                    error_message = f"Bad Password for this user ({attempts_left} attempts remaining)"
                    logger.warning(f"Failed login attempt for user '{username}' ({attempts_left} attempts remaining)")
                
                return (False, error_message)
        except Exception as e:
            logger.error(f"CRITICAL: Exception during password verification for user '{username}': {e}")
            return (False, "Authentication error. Please contact administrator.")

import paramiko
import socket

class SFTPConnection:
    def __init__(self, host, username, password, port=22):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.transport = None
        self.sftp = None

    def connect(self):
        """Établit une connexion SFTP si elle n'est pas déjà active."""
        if self.sftp is None:
            try:
                # Étape 1 : Créer un socket avec un timeout
                sock = socket.create_connection((self.host, self.port), timeout=0.5)  # timeout en secondes

                # Étape 2 : Créer le transport avec le socket
                self.transport = paramiko.Transport(sock)
                paramiko.util.logging.getLogger().setLevel(paramiko.util.logging.WARNING)

                # Étape 3 : Connexion
                self.transport.connect(username=self.username, password=self.password)

                # Étape 4 : Créer le client SFTP
                self.sftp = paramiko.SFTPClient.from_transport(self.transport)
            except Exception:
                # print(f"Erreur de connexion SFTP: {e}")
                self.sftp = None

    def listdir(self, remote_path):
        """Retourne la liste des fichiers d'un répertoire."""
        self.connect()
        if self.sftp:
            try:
                return self.sftp.listdir(remote_path)
            except FileNotFoundError:
                return []
        return []

    def download_file(self, remote_path, local_path):
        """Télécharge un fichier depuis le serveur SFTP."""
        self.connect()
        if self.sftp:
            try:
                self.sftp.get(remote_path, local_path)
            except Exception as e:
                print(f"Erreur lors du téléchargement: {e}")

    def upload_file(self, local_path, remote_path):
        """Envoie un fichier vers le serveur SFTP."""
        self.connect()
        if self.sftp:
            try:
                self.sftp.put(local_path, remote_path)
            except Exception as e:
                print(f"Erreur lors de l'envoi du fichier: {e}")

    def mkdir(self, remote_path):
        """Crée un répertoire distant s'il n'existe pas."""
        self.connect()
        if self.sftp:
            try:
                self.sftp.mkdir(remote_path)
            except OSError:
                pass  # Le répertoire existe déjà

    def close(self):
        """Ferme proprement la connexion SFTP."""
        if self.sftp:
            self.sftp.close()
            self.sftp = None
        if self.transport:
            self.transport.close()
            self.transport = None
            
    def exists(self, remote_path):
        """Vérifie si un fichier ou dossier existe sur le serveur distant."""
        self.connect()
        if self.sftp:
            try:
                self.sftp.stat(remote_path)
                return True
            except FileNotFoundError:
                return False
            except Exception as e:
                print(f"Erreur lors du test d'existence de {remote_path}: {e}")
                return False
        return False

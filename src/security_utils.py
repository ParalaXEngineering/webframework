"""
Module de gestion de la sécurité pour OuFNis DFDIG
Inclut: Stockage persistant des tentatives de connexion échouées
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timedelta

logger = logging.getLogger("website")

# Fichier de stockage persistant des tentatives échouées
LOCKOUT_FILE = Path("failed_logins.json")


class FailedLoginManager:
    """Gestionnaire persistant des tentatives de connexion échouées"""
    
    def __init__(self):
        self.attempts = self._load_attempts()
    
    def _load_attempts(self):
        """Charge les tentatives depuis le fichier JSON"""
        if LOCKOUT_FILE.exists():
            try:
                with open(LOCKOUT_FILE, 'r') as f:
                    data = json.load(f)
                    # Convertir les timestamps string en datetime
                    for username in data:
                        if data[username].get('locked_until'):
                            data[username]['locked_until'] = datetime.fromisoformat(
                                data[username]['locked_until']
                            )
                    return data
            except Exception as e:
                logger.error(f"Error loading failed login attempts: {e}")
                return {}
        return {}
    
    def _save_attempts(self):
        """Sauvegarde les tentatives dans le fichier JSON"""
        try:
            # Convertir les datetime en string pour JSON
            data = {}
            for username, info in self.attempts.items():
                data[username] = {
                    'count': info['count'],
                    'locked_until': info['locked_until'].isoformat() if info.get('locked_until') else None
                }
            
            with open(LOCKOUT_FILE, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving failed login attempts: {e}")
    
    def get_user_status(self, username):
        """Retourne le statut d'un utilisateur (count, locked_until)"""
        if username not in self.attempts:
            self.attempts[username] = {'count': 0, 'locked_until': None}
        return self.attempts[username]
    
    def is_locked(self, username):
        """Vérifie si un utilisateur est verrouillé"""
        status = self.get_user_status(username)
        locked_until = status.get('locked_until')
        
        if locked_until and datetime.now() < locked_until:
            return True, locked_until
        elif locked_until and datetime.now() >= locked_until:
            # Lock expiré, réinitialiser
            self.reset_attempts(username)
            return False, None
        
        return False, None
    
    def increment_attempts(self, username):
        """Incrémente le compteur de tentatives échouées"""
        status = self.get_user_status(username)
        status['count'] += 1
        
        if status['count'] >= 5:
            # Verrouiller pour 5 minutes
            status['locked_until'] = datetime.now() + timedelta(minutes=5)
            logger.warning(f"Account '{username}' locked until {status['locked_until'].strftime('%Y-%m-%d %H:%M:%S')}")
        
        self._save_attempts()
        return status['count']
    
    def reset_attempts(self, username):
        """Réinitialise les tentatives échouées (après connexion réussie)"""
        self.attempts[username] = {'count': 0, 'locked_until': None}
        self._save_attempts()
    
    def get_remaining_attempts(self, username):
        """Retourne le nombre de tentatives restantes"""
        status = self.get_user_status(username)
        return max(0, 5 - status['count'])
    
    def get_lockout_time_remaining(self, username):
        """Retourne le temps restant avant déverrouillage (en secondes)"""
        is_locked, locked_until = self.is_locked(username)
        if is_locked:
            remaining = (locked_until - datetime.now()).total_seconds()
            return max(0, remaining)
        return 0


# Instance globale
failed_login_manager = FailedLoginManager()

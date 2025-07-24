from ..base import BaseAPIClient
import logging
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger(__name__)

class Fail2BanClient(BaseAPIClient):
    """Client pour interagir avec l'API REST de Fail2Ban"""
    
    def __init__(self, base_url: str, username: str, password: str,
                 verify_ssl: bool = True, timeout: int = 10):
        """
        Initialise le client Fail2Ban.
        
        Args:
            base_url: URL de base de l'API Fail2Ban (ex: http://localhost:5000/api)
            username: Nom d'utilisateur pour l'authentification
            password: Mot de passe pour l'authentification
            verify_ssl: Vérifier les certificats SSL
            timeout: Délai d'attente en secondes pour les requêtes
        """
        super().__init__(base_url, username, password, None, verify_ssl, timeout)
    
    def test_connection(self) -> bool:
        """
        Teste la connexion à l'API Fail2Ban.
        
        Returns:
            True si la connexion est établie avec succès, False sinon
        """
        response = self.get("status")
        return response.get("success", False) and "version" in response
    
    def get_version(self) -> Dict[str, Any]:
        """
        Récupère la version de Fail2Ban.
        
        Returns:
            Informations sur la version
        """
        return self.get("version")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Récupère l'état du service Fail2Ban.
        
        Returns:
            État du service
        """
        return self.get("status")
    
    def get_jails(self) -> Dict[str, Any]:
        """
        Récupère la liste des jails.
        
        Returns:
            Liste des jails
        """
        return self.get("jails")
    
    def get_jail_info(self, jail_name: str) -> Dict[str, Any]:
        """
        Récupère les informations sur une jail spécifique.
        
        Args:
            jail_name: Nom de la jail
            
        Returns:
            Informations sur la jail
        """
        return self.get(f"jails/{jail_name}")
    
    def start_jail(self, jail_name: str) -> Dict[str, Any]:
        """
        Démarre une jail.
        
        Args:
            jail_name: Nom de la jail à démarrer
            
        Returns:
            Résultat de l'opération
        """
        return self.post(f"jails/{jail_name}/start")
    
    def stop_jail(self, jail_name: str) -> Dict[str, Any]:
        """
        Arrête une jail.
        
        Args:
            jail_name: Nom de la jail à arrêter
            
        Returns:
            Résultat de l'opération
        """
        return self.post(f"jails/{jail_name}/stop")
    
    def get_banned_ips(self, jail_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Récupère la liste des adresses IP bannies.
        
        Args:
            jail_name: Nom de la jail (si None, récupère pour toutes les jails)
            
        Returns:
            Liste des adresses IP bannies
        """
        if jail_name:
            return self.get(f"jails/{jail_name}/banned")
        else:
            return self.get("banned")
    
    def ban_ip(self, ip: str, jail_name: str, time: Optional[int] = None) -> Dict[str, Any]:
        """
        Banne une adresse IP dans une jail.
        
        Args:
            ip: Adresse IP à bannir
            jail_name: Nom de la jail
            time: Durée du bannissement en secondes (optionnel)
            
        Returns:
            Résultat de l'opération
        """
        data = {
            "ip": ip
        }
        
        if time:
            data["time"] = time
            
        return self.post(f"jails/{jail_name}/ban", json_data=data)
    
    def unban_ip(self, ip: str, jail_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Débanne une adresse IP.
        
        Args:
            ip: Adresse IP à débannir
            jail_name: Nom de la jail (si None, débanne de toutes les jails)
            
        Returns:
            Résultat de l'opération
        """
        data = {
            "ip": ip
        }
        
        if jail_name:
            return self.post(f"jails/{jail_name}/unban", json_data=data)
        else:
            return self.post("unban", json_data=data)
    
    def get_logs(self, jail_name: Optional[str] = None, limit: int = 100, 
                level: Optional[str] = None) -> Dict[str, Any]:
        """
        Récupère les logs de Fail2Ban.
        
        Args:
            jail_name: Nom de la jail (si None, récupère tous les logs)
            limit: Nombre maximum de logs à récupérer
            level: Niveau de log (DEBUG, INFO, WARNING, ERROR)
            
        Returns:
            Logs récupérés
        """
        params = {
            "limit": limit
        }
        
        if level:
            params["level"] = level
        
        if jail_name:
            return self.get(f"jails/{jail_name}/logs", params=params)
        else:
            return self.get("logs", params=params)
    
    def reload_config(self) -> Dict[str, Any]:
        """
        Recharge la configuration de Fail2Ban.
        
        Returns:
            Résultat de l'opération
        """
        return self.post("reload")
    
    def restart_service(self) -> Dict[str, Any]:
        """
        Redémarre le service Fail2Ban.
        
        Returns:
            Résultat de l'opération
        """
        return self.post("restart") 
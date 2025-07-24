from ..base import BaseAPIClient
import logging
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger(__name__)

class NtopngClient(BaseAPIClient):
    """Client pour interagir avec l'API REST de ntopng"""
    
    def __init__(self, base_url: str, username: str, password: str,
                 verify_ssl: bool = True, timeout: int = 10):
        """
        Initialise le client ntopng.
        
        Args:
            base_url: URL de base de l'API ntopng (ex: http://localhost:3000)
            username: Nom d'utilisateur pour l'authentification
            password: Mot de passe pour l'authentification
            verify_ssl: Vérifier les certificats SSL
            timeout: Délai d'attente en secondes pour les requêtes
        """
        super().__init__(base_url, username, password, None, verify_ssl, timeout)
    
    def test_connection(self) -> bool:
        """
        Teste la connexion à l'API ntopng.
        
        Returns:
            True si la connexion est établie avec succès, False sinon
        """
        response = self.get("lua/rest/v1/get/system/info.lua")
        return response.get("success", False) and "version" in response
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        Récupère les informations système de ntopng.
        
        Returns:
            Informations sur le système ntopng
        """
        return self.get("lua/rest/v1/get/system/info.lua")
    
    def get_interfaces(self) -> Dict[str, Any]:
        """
        Récupère la liste des interfaces réseau supervisées.
        
        Returns:
            Liste des interfaces
        """
        return self.get("lua/rest/v1/get/system/interfaces.lua")
    
    def get_interface_stats(self, interface_id: int) -> Dict[str, Any]:
        """
        Récupère les statistiques d'une interface.
        
        Args:
            interface_id: ID de l'interface
            
        Returns:
            Statistiques de l'interface
        """
        return self.get(f"lua/rest/v1/get/interface/{interface_id}/stats.lua")
    
    def get_hosts(self, interface_id: int) -> Dict[str, Any]:
        """
        Récupère la liste des hôtes détectés sur une interface.
        
        Args:
            interface_id: ID de l'interface
            
        Returns:
            Liste des hôtes
        """
        return self.get(f"lua/rest/v1/get/interface/{interface_id}/hosts.lua")
    
    def get_host_info(self, interface_id: int, host: str) -> Dict[str, Any]:
        """
        Récupère les informations d'un hôte.
        
        Args:
            interface_id: ID de l'interface
            host: Adresse IP ou nom de l'hôte
            
        Returns:
            Informations sur l'hôte
        """
        return self.get(f"lua/rest/v1/get/interface/{interface_id}/host/{host}/info.lua")
    
    def get_host_flows(self, interface_id: int, host: str) -> Dict[str, Any]:
        """
        Récupère les flux réseau d'un hôte.
        
        Args:
            interface_id: ID de l'interface
            host: Adresse IP ou nom de l'hôte
            
        Returns:
            Flux réseau de l'hôte
        """
        return self.get(f"lua/rest/v1/get/interface/{interface_id}/host/{host}/flows.lua")
    
    def get_flows(self, interface_id: int) -> Dict[str, Any]:
        """
        Récupère les flux réseau d'une interface.
        
        Args:
            interface_id: ID de l'interface
            
        Returns:
            Flux réseau de l'interface
        """
        return self.get(f"lua/rest/v1/get/interface/{interface_id}/flows.lua")
    
    def get_flow_details(self, interface_id: int, flow_id: str) -> Dict[str, Any]:
        """
        Récupère les détails d'un flux réseau.
        
        Args:
            interface_id: ID de l'interface
            flow_id: ID du flux
            
        Returns:
            Détails du flux
        """
        return self.get(f"lua/rest/v1/get/interface/{interface_id}/flow/{flow_id}/info.lua")
    
    def get_alerts(self) -> Dict[str, Any]:
        """
        Récupère la liste des alertes.
        
        Returns:
            Liste des alertes
        """
        return self.get("lua/rest/v1/get/alerts/alerts.lua")
    
    def get_timeseries(self, entity_type: str, entity_id: str, ts_key: str, 
                       epoch_begin: Optional[int] = None, epoch_end: Optional[int] = None) -> Dict[str, Any]:
        """
        Récupère les séries temporelles pour une entité donnée.
        
        Args:
            entity_type: Type d'entité (interface, host, etc.)
            entity_id: ID de l'entité
            ts_key: Clé de la série temporelle
            epoch_begin: Timestamp de début (optionnel)
            epoch_end: Timestamp de fin (optionnel)
            
        Returns:
            Données de la série temporelle
        """
        params = {}
        if epoch_begin:
            params["epoch_begin"] = epoch_begin
        if epoch_end:
            params["epoch_end"] = epoch_end
        
        return self.get(f"lua/rest/v1/get/timeseries/{entity_type}/{entity_id}/{ts_key}.lua", params=params) 
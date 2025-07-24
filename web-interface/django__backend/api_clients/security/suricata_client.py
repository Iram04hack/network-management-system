from ..base import BaseAPIClient
import logging
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger(__name__)

class SuricataClient(BaseAPIClient):
    """Client pour interagir avec l'API REST de Suricata via Eve-NG"""
    
    def __init__(self, base_url: str, token: Optional[str] = None,
                 username: Optional[str] = None, password: Optional[str] = None,
                 verify_ssl: bool = True, timeout: int = 10):
        """
        Initialise le client Suricata.
        
        Args:
            base_url: URL de base de l'API Suricata (ex: http://localhost:9200/suricata)
            token: Token d'authentification
            username: Nom d'utilisateur pour l'authentification (si pas de token)
            password: Mot de passe pour l'authentification (si pas de token)
            verify_ssl: Vérifier les certificats SSL
            timeout: Délai d'attente en secondes pour les requêtes
        """
        super().__init__(base_url, username, password, token, verify_ssl, timeout)
    
    def test_connection(self) -> bool:
        """
        Teste la connexion à l'API Suricata.
        
        Returns:
            True si la connexion est établie avec succès, False sinon
        """
        response = self.get("status")
        return response.get("success", False)
    
    def get_status(self) -> Dict[str, Any]:
        """
        Récupère l'état du service Suricata.
        
        Returns:
            État du service
        """
        return self.get("status")
    
    def get_version(self) -> Dict[str, Any]:
        """
        Récupère la version de Suricata.
        
        Returns:
            Informations sur la version
        """
        return self.get("info")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Récupère les statistiques de Suricata.
        
        Returns:
            Statistiques du service
        """
        return self.get("stats")
    
    def get_rules(self) -> Dict[str, Any]:
        """
        Récupère la liste des règles chargées.
        
        Returns:
            Liste des règles
        """
        return self.get("rules")
    
    def get_rule(self, rule_id: int) -> Dict[str, Any]:
        """
        Récupère une règle spécifique.
        
        Args:
            rule_id: ID de la règle
            
        Returns:
            Détails de la règle
        """
        return self.get(f"rules/{rule_id}")
    
    def update_rule(self, rule_id: int, enabled: bool) -> Dict[str, Any]:
        """
        Met à jour une règle (active/désactive).
        
        Args:
            rule_id: ID de la règle
            enabled: État d'activation de la règle
            
        Returns:
            Résultat de l'opération
        """
        data = {
            "enabled": enabled
        }
        return self.put(f"rules/{rule_id}", json_data=data)
    
    def get_alerts(self, limit: int = 100, offset: int = 0, 
                  severity: Optional[str] = None) -> Dict[str, Any]:
        """
        Récupère les alertes générées par Suricata.
        
        Args:
            limit: Nombre maximum d'alertes à récupérer
            offset: Offset pour la pagination
            severity: Filtre par niveau de sévérité (high, medium, low)
            
        Returns:
            Liste des alertes
        """
        params = {
            "limit": limit,
            "offset": offset
        }
        
        if severity:
            params["severity"] = severity
            
        return self.get("alerts", params=params)
    
    def get_alert(self, alert_id: str) -> Dict[str, Any]:
        """
        Récupère les détails d'une alerte spécifique.
        
        Args:
            alert_id: ID de l'alerte
            
        Returns:
            Détails de l'alerte
        """
        return self.get(f"alerts/{alert_id}")
    
    def get_flows(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """
        Récupère les flux réseau analysés par Suricata.
        
        Args:
            limit: Nombre maximum de flux à récupérer
            offset: Offset pour la pagination
            
        Returns:
            Liste des flux
        """
        params = {
            "limit": limit,
            "offset": offset
        }
        
        return self.get("flows", params=params)
    
    def reload_rules(self) -> Dict[str, Any]:
        """
        Recharge les règles Suricata.
        
        Returns:
            Résultat de l'opération
        """
        return self.post("reload")
    
    def restart_service(self) -> Dict[str, Any]:
        """
        Redémarre le service Suricata.
        
        Returns:
            Résultat de l'opération
        """
        return self.post("restart")
    
    def upload_ruleset(self, ruleset_content: str, name: str) -> Dict[str, Any]:
        """
        Télécharge un ensemble de règles personnalisées.
        
        Args:
            ruleset_content: Contenu des règles au format texte
            name: Nom du fichier de règles
            
        Returns:
            Résultat de l'opération
        """
        data = {
            "name": name,
            "content": ruleset_content
        }
        
        return self.post("rules/upload", json_data=data)
    
    def search_events(self, query: Dict[str, Any], 
                     from_time: Optional[str] = None, 
                     to_time: Optional[str] = None,
                     limit: int = 100) -> Dict[str, Any]:
        """
        Recherche les événements Suricata avec une requête personnalisée.
        
        Args:
            query: Requête de recherche
            from_time: Horodatage de début (format ISO)
            to_time: Horodatage de fin (format ISO)
            limit: Nombre maximum d'événements à récupérer
            
        Returns:
            Résultats de la recherche
        """
        data = {
            "query": query,
            "limit": limit
        }
        
        if from_time:
            data["from"] = from_time
            
        if to_time:
            data["to"] = to_time
        
        return self.post("events/search", json_data=data) 
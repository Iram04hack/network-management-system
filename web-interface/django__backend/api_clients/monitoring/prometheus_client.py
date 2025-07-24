from ..base import BaseAPIClient
import logging
from typing import Dict, Any, Optional, List, Union
import json

logger = logging.getLogger(__name__)

class PrometheusClient(BaseAPIClient):
    """Client pour interagir avec l'API REST de Prometheus"""
    
    def __init__(self, base_url: str, username: Optional[str] = None, 
                 password: Optional[str] = None, token: Optional[str] = None,
                 verify_ssl: bool = True, timeout: int = 10):
        """
        Initialise le client Prometheus.
        
        Args:
            base_url: URL de base de l'API Prometheus (ex: http://localhost:9090/api/v1)
            username: Nom d'utilisateur pour l'authentification basique
            password: Mot de passe pour l'authentification basique
            token: Token pour l'authentification Bearer
            verify_ssl: Vérifier les certificats SSL
            timeout: Délai d'attente en secondes pour les requêtes
        """
        super().__init__(base_url, username, password, token, verify_ssl, timeout)
    
    def test_connection(self) -> bool:
        """
        Teste la connexion à l'API Prometheus.
        
        Returns:
            True si la connexion est établie avec succès, False sinon
        """
        response = self.get("status/config")
        return response.get("success", False)
    
    def get_targets(self) -> Dict[str, Any]:
        """
        Récupère l'état de toutes les cibles de supervision.
        
        Returns:
            Dictionnaire contenant les informations sur les cibles
        """
        return self.get("targets")
    
    def get_alerts(self) -> Dict[str, Any]:
        """
        Récupère toutes les alertes actives.
        
        Returns:
            Dictionnaire contenant les informations sur les alertes
        """
        return self.get("alerts")
    
    def get_rules(self) -> Dict[str, Any]:
        """
        Récupère toutes les règles configurées.
        
        Returns:
            Dictionnaire contenant les informations sur les règles
        """
        return self.get("rules")
    
    def query(self, query: str, time: Optional[str] = None) -> Dict[str, Any]:
        """
        Exécute une requête PromQL instantanée.
        
        Args:
            query: Expression PromQL à exécuter
            time: Horodatage (format RFC3339 ou timestamp Unix) pour l'évaluation
            
        Returns:
            Résultat de la requête
        """
        params = {'query': query}
        if time:
            params['time'] = time
            
        return self.get("query", params=params)
    
    def query_range(self, query: str, start: str, end: str, step: str) -> Dict[str, Any]:
        """
        Exécute une requête PromQL sur une plage de temps.
        
        Args:
            query: Expression PromQL à exécuter
            start: Horodatage de début (format RFC3339 ou timestamp Unix)
            end: Horodatage de fin (format RFC3339 ou timestamp Unix)
            step: Intervalle de temps entre les points (ex: 15s, 1m, 1h)
            
        Returns:
            Résultat de la requête
        """
        params = {
            'query': query,
            'start': start,
            'end': end,
            'step': step
        }
        
        return self.get("query_range", params=params)
    
    def get_series(self, match: List[str], start: Optional[str] = None, 
                  end: Optional[str] = None) -> Dict[str, Any]:
        """
        Recherche les séries de données correspondant au sélecteur.
        
        Args:
            match: Liste d'expressions de sélection de séries
            start: Horodatage de début (format RFC3339 ou timestamp Unix)
            end: Horodatage de fin (format RFC3339 ou timestamp Unix)
            
        Returns:
            Liste de séries correspondantes
        """
        params = {'match[]': match}
        
        if start:
            params['start'] = start
            
        if end:
            params['end'] = end
            
        return self.get("series", params=params)
    
    def get_label_values(self, label_name: str) -> Dict[str, Any]:
        """
        Récupère les valeurs possibles pour un label donné.
        
        Args:
            label_name: Nom du label
            
        Returns:
            Liste des valeurs de label
        """
        return self.get(f"label/{label_name}/values") 
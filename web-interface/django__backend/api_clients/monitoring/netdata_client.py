from ..base import BaseAPIClient
import logging
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger(__name__)

class NetdataClient(BaseAPIClient):
    """Client pour interagir avec l'API REST de Netdata"""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None,
                 verify_ssl: bool = True, timeout: int = 10):
        """
        Initialise le client Netdata.
        
        Args:
            base_url: URL de base de l'API Netdata (ex: http://localhost:19999)
            api_key: Clé API pour l'authentification
            verify_ssl: Vérifier les certificats SSL
            timeout: Délai d'attente en secondes pour les requêtes
        """
        super().__init__(base_url, None, None, api_key, verify_ssl, timeout)
    
    def test_connection(self) -> bool:
        """
        Teste la connexion à l'API Netdata.
        
        Returns:
            True si la connexion est établie avec succès, False sinon
        """
        response = self.get("info")
        return response.get("success", False)
    
    def get_info(self) -> Dict[str, Any]:
        """
        Récupère les informations générales de Netdata.
        
        Returns:
            Informations sur l'instance Netdata
        """
        return self.get("info")
    
    def get_alarms(self) -> Dict[str, Any]:
        """
        Récupère la liste des alarmes actives.
        
        Returns:
            Liste des alarmes
        """
        return self.get("alarms")
    
    def get_allmetrics(self, format: str = "json") -> Dict[str, Any]:
        """
        Récupère toutes les métriques.
        
        Args:
            format: Format de réponse (json, prometheus, etc.)
            
        Returns:
            Toutes les métriques
        """
        return self.get("allmetrics", params={"format": format})
    
    def get_chart(self, chart_id: str, after: Optional[int] = None, 
                 before: Optional[int] = None, points: Optional[int] = None) -> Dict[str, Any]:
        """
        Récupère les données d'un graphique.
        
        Args:
            chart_id: ID du graphique
            after: Timestamp de début (en secondes)
            before: Timestamp de fin (en secondes)
            points: Nombre de points à récupérer
            
        Returns:
            Données du graphique
        """
        params = {}
        
        if after is not None:
            params["after"] = after
            
        if before is not None:
            params["before"] = before
            
        if points is not None:
            params["points"] = points
            
        return self.get(f"data?chart={chart_id}", params=params)
    
    def get_charts(self) -> Dict[str, Any]:
        """
        Récupère la liste des graphiques disponibles.
        
        Returns:
            Liste des graphiques
        """
        return self.get("charts")
    
    def get_chart_data(self, chart_id: str, dimension: Optional[str] = None,
                      after: Optional[int] = None, before: Optional[int] = None,
                      points: Optional[int] = None) -> Dict[str, Any]:
        """
        Récupère les données d'un graphique pour une dimension spécifique.
        
        Args:
            chart_id: ID du graphique
            dimension: Nom de la dimension
            after: Timestamp de début (en secondes)
            before: Timestamp de fin (en secondes)
            points: Nombre de points à récupérer
            
        Returns:
            Données du graphique pour la dimension spécifiée
        """
        params = {}
        
        if after is not None:
            params["after"] = after
            
        if before is not None:
            params["before"] = before
            
        if points is not None:
            params["points"] = points
            
        url = f"data?chart={chart_id}"
        
        if dimension:
            url += f"&dimension={dimension}"
            
        return self.get(url, params=params) 
from ..base import BaseAPIClient
import logging
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger(__name__)

class GrafanaClient(BaseAPIClient):
    """Client pour interagir avec l'API REST de Grafana"""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None,
                 username: Optional[str] = None, password: Optional[str] = None,
                 verify_ssl: bool = True, timeout: int = 10):
        """
        Initialise le client Grafana.
        
        Args:
            base_url: URL de base de l'API Grafana (ex: http://localhost:3000)
            api_key: Clé API pour l'authentification
            username: Nom d'utilisateur pour l'authentification basique (si pas de clé API)
            password: Mot de passe pour l'authentification basique (si pas de clé API)
            verify_ssl: Vérifier les certificats SSL
            timeout: Délai d'attente en secondes pour les requêtes
        """
        # Si une clé API est fournie, l'utiliser comme token Bearer
        token = api_key if api_key else None
        
        super().__init__(base_url, username, password, token, verify_ssl, timeout)
        
        # Configurer les en-têtes spécifiques à Grafana si API key est utilisée
        if api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {api_key}'
            })
    
    def _setup_session(self) -> None:
        """Configure la session HTTP avec les en-têtes et l'authentification par défaut"""
        super()._setup_session()
        
        # Ajouter l'en-tête Accept pour obtenir des réponses en JSON
        self.session.headers.update({
            'Accept': 'application/json'
        })
        
    def test_connection(self) -> bool:
        """
        Teste la connexion à l'API Grafana.
        
        Returns:
            True si la connexion est établie avec succès, False sinon
        """
        response = self.get("org")
        return response.get("success", False)
    
    def get_dashboards(self) -> Dict[str, Any]:
        """
        Récupère la liste des tableaux de bord.
        
        Returns:
            Liste des tableaux de bord
        """
        return self.get("search?type=dash-db")
    
    def get_dashboard(self, uid: str) -> Dict[str, Any]:
        """
        Récupère un tableau de bord par son UID.
        
        Args:
            uid: UID du tableau de bord
            
        Returns:
            Détails du tableau de bord
        """
        return self.get(f"dashboards/uid/{uid}")
    
    def get_datasources(self) -> Dict[str, Any]:
        """
        Récupère la liste des sources de données.
        
        Returns:
            Liste des sources de données
        """
        return self.get("datasources")
    
    def get_datasource(self, datasource_id: Union[int, str]) -> Dict[str, Any]:
        """
        Récupère une source de données par son ID ou son nom.
        
        Args:
            datasource_id: ID ou nom de la source de données
            
        Returns:
            Détails de la source de données
        """
        if isinstance(datasource_id, int) or datasource_id.isdigit():
            return self.get(f"datasources/{datasource_id}")
        else:
            return self.get(f"datasources/name/{datasource_id}")
    
    def get_alerts(self) -> Dict[str, Any]:
        """
        Récupère la liste des alertes.
        
        Returns:
            Liste des alertes
        """
        return self.get("alerts")
    
    def get_alert(self, alert_id: int) -> Dict[str, Any]:
        """
        Récupère une alerte par son ID.
        
        Args:
            alert_id: ID de l'alerte
            
        Returns:
            Détails de l'alerte
        """
        return self.get(f"alerts/{alert_id}")
    
    def create_dashboard(self, dashboard_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée ou met à jour un tableau de bord.
        
        Args:
            dashboard_json: JSON du tableau de bord
            
        Returns:
            Résultat de la création/mise à jour
        """
        return self.post("dashboards/db", json_data=dashboard_json)
    
    def create_datasource(self, datasource_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée une nouvelle source de données.
        
        Args:
            datasource_json: JSON de la source de données
            
        Returns:
            Résultat de la création
        """
        return self.post("datasources", json_data=datasource_json)
    
    def get_users(self) -> Dict[str, Any]:
        """
        Récupère la liste des utilisateurs.
        
        Returns:
            Liste des utilisateurs
        """
        return self.get("users")
    
    def get_current_user(self) -> Dict[str, Any]:
        """
        Récupère les informations de l'utilisateur actuel.
        
        Returns:
            Informations sur l'utilisateur actuel
        """
        return self.get("user") 
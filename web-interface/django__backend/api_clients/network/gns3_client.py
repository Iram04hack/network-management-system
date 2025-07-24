# api_clients/network/gns3_client.py
import os
import sys
import json
import logging
import requests
from typing import Dict, List, Any, Optional, Union, Tuple
from urllib.parse import urljoin

# Import conditionnel pour éviter les cycles - sera fait de manière paresseuse
# from services.network.mock_gns3_service import MockGNS3Service

from ..domain.exceptions import (
    APIClientException,
    APIConnectionException,
    APIResponseException
)
from ..infrastructure.base_client import BaseAPIClientImpl
from ..docs.swagger_generator import swagger_doc

logger = logging.getLogger(__name__)

class GNS3Client(BaseAPIClientImpl):
    """
    Client pour interagir avec l'API GNS3.
    En environnement de test, utilise automatiquement le service mock GNS3.
    En production, se connecte à un serveur GNS3 réel.
    """

    def __init__(
        self, 
        host: str = None, 
        port: int = None, 
        protocol: str = None, 
        username: str = None, 
        password: str = None,
        verify_ssl: bool = True,
        use_mock: bool = None,
        timeout: int = 30
    ):
        """
        Initialise le client GNS3.
        
        Args:
            host: Hôte du serveur GNS3
            port: Port du serveur GNS3
            protocol: Protocole de connexion ('http' ou 'https')
            username: Nom d'utilisateur pour l'authentification
            password: Mot de passe pour l'authentification
            verify_ssl: Vérifier le certificat SSL
            use_mock: Forcer l'utilisation du mock GNS3
            timeout: Timeout des requêtes en secondes
        """
        self.host = host or os.environ.get('GNS3_HOST', 'localhost')
        self.port = port or int(os.environ.get('GNS3_PORT', '3080'))
        self.protocol = protocol or os.environ.get('GNS3_PROTOCOL', 'http')
        self.username = username or os.environ.get('GNS3_USERNAME', '')
        self.password = password or os.environ.get('GNS3_PASSWORD', '')
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.auth = (self.username, self.password) if self.username and self.password else None
        
        # Déterminer si nous devons utiliser le mock
        if use_mock is None:
            # Auto-détecter si nous sommes en environnement de test
            self.use_mock = 'test' in sys.argv or 'pytest' in sys.modules
        else:
            self.use_mock = use_mock
        
        # Si nous utilisons le mock, initialiser les données
        if self.use_mock:
            # Import paresseux pour éviter les cycles
            try:
                from services.network.mock_gns3_service import MockGNS3Service
                self.MockGNS3Service = MockGNS3Service
                # Peupler le mock avec des données de test
                if not MockGNS3Service._data["projects"]:
                    MockGNS3Service.populate_mock_data()
                logger.info("Utilisation du mock GNS3 pour les tests")
            except ImportError:
                logger.warning("MockGNS3Service non disponible, utilisation d'un mock simple")
                self.MockGNS3Service = None
        else:
            # Construire l'URL de base pour l'API
            self.base_url = f"{self.protocol}://{self.host}:{self.port}/v2/"
            logger.info(f"Connexion au serveur GNS3 réel à {self.base_url}")
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None) -> Dict:
        """
        Effectue une requête HTTP vers l'API GNS3.
        
        Args:
            method: Méthode HTTP ('GET', 'POST', 'PUT', 'DELETE')
            endpoint: Point d'API (sans le préfixe '/v2')
            data: Données à envoyer (pour POST/PUT)
            params: Paramètres de la requête
            
        Returns:
            La réponse JSON ou un dictionnaire d'erreur
        """
        if self.use_mock:
            # Utiliser le mock GNS3
            return self._mock_request(method, endpoint, data, params)
        
        # Construire l'URL complète
        url = urljoin(self.base_url, endpoint.lstrip('/'))
        
        try:
            # Effectuer la requête HTTP
            headers = {'Content-Type': 'application/json'}
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                params=params,
                auth=self.auth,
                verify=self.verify_ssl,
                timeout=self.timeout
            )
            
            # Vérifier si la requête a réussi
            response.raise_for_status()
            
            # Retourner les données JSON
            if response.content:
                return response.json()
            return {"success": True}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la requête GNS3 ({method} {url}): {e}")
            return {"success": False, "error": str(e)}
    
    def _mock_request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None) -> Dict:
        """
        Simule une requête vers l'API GNS3 en utilisant le mock.
        
        Args:
            method: Méthode HTTP ('GET', 'POST', 'PUT', 'DELETE')
            endpoint: Point d'API (sans le préfixe '/v2')
            data: Données à envoyer (pour POST/PUT)
            params: Paramètres de la requête
            
        Returns:
            La réponse simulée
        """
        # Si MockGNS3Service n'est pas disponible, retourner des réponses simples
        if not hasattr(self, 'MockGNS3Service') or self.MockGNS3Service is None:
            return {"success": True, "mock": True, "data": data or {}}
        
        MockGNS3Service = self.MockGNS3Service
        
        # Normaliser l'endpoint
        endpoint = endpoint.lstrip('/')
        
        # Projet endpoints
        if endpoint == 'projects':
            if method == 'GET':
                return MockGNS3Service.get_projects()
            elif method == 'POST':
                name = data.get('name', 'New Project')
                # Supprimer la clé name du dictionnaire data pour éviter le doublon
                data_copy = data.copy()
                if 'name' in data_copy:
                    del data_copy['name']
                return MockGNS3Service.create_project(name=name, **data_copy)
        
        elif endpoint.startswith('projects/') and len(endpoint.split('/')) == 2:
            project_id = endpoint.split('/')[1]
            if method == 'GET':
                return MockGNS3Service.get_project(project_id)
            elif method == 'PUT':
                return MockGNS3Service.update_project(project_id, **data)
            elif method == 'DELETE':
                return MockGNS3Service.delete_project(project_id)
        
        # Noeuds
        elif endpoint.startswith('projects/') and endpoint.endswith('/nodes'):
            project_id = endpoint.split('/')[1]
            if method == 'GET':
                return MockGNS3Service.get_nodes(project_id)
            elif method == 'POST':
                name = data.get('name', 'New Node')
                template_id = data.get('template_id')
                x = data.get('x', 0)
                y = data.get('y', 0)
                
                # Supprimer les clés qui seraient en double
                data_copy = data.copy()
                for key in ['name', 'template_id', 'x', 'y']:
                    if key in data_copy:
                        del data_copy[key]
                
                return MockGNS3Service.create_node(project_id, name, template_id, x, y, **data_copy)
        
        # Nœud spécifique
        elif endpoint.startswith('projects/') and '/nodes/' in endpoint and endpoint.count('/') == 3:
            parts = endpoint.split('/')
            project_id = parts[1]
            node_id = parts[3]
            
            if method == 'GET':
                return MockGNS3Service.get_node(project_id, node_id)
            elif method == 'PUT':
                return MockGNS3Service.update_node(project_id, node_id, **data)
            elif method == 'DELETE':
                return MockGNS3Service.delete_node(project_id, node_id)
        
        # Actions sur les noeuds (start, stop)
        elif endpoint.startswith('projects/') and '/nodes/' in endpoint:
            parts = endpoint.split('/')
            project_id = parts[1]
            node_id = parts[3]
            
            # Traiter les actions sur les nœuds (start, stop)
            if len(parts) == 5 and parts[4] == 'start' and method == 'POST':
                return MockGNS3Service.start_node(project_id, node_id)
            elif len(parts) == 5 and parts[4] == 'stop' and method == 'POST':
                return MockGNS3Service.stop_node(project_id, node_id)
        
        # Projets (ouverture/fermeture)
        elif endpoint.startswith('projects/') and endpoint.endswith('/open'):
            project_id = endpoint.split('/')[1]
            if method == 'POST':
                return MockGNS3Service.open_project(project_id)
        
        elif endpoint.startswith('projects/') and endpoint.endswith('/close'):
            project_id = endpoint.split('/')[1]
            if method == 'POST':
                return MockGNS3Service.close_project(project_id)
        
        # Version GNS3
        elif endpoint == 'version':
            return MockGNS3Service.get_version()
        
        # Si l'endpoint n'est pas géré
        logger.warning(f"Endpoint mock non implémenté: {method} {endpoint}")
        return {"success": False, "error": f"Endpoint non implémenté dans le mock: {method} {endpoint}"}
    
    # API publique
    
    def get_version(self) -> Dict[str, Any]:
        """
        Récupère la version du serveur GNS3.
        
        Returns:
            Informations sur la version du serveur
        """
        return self._make_request('GET', '/version')
    
    @swagger_doc(
        path="/projects",
        method="GET",
        summary="Liste tous les projets",
        description="Récupère la liste de tous les projets sur le serveur GNS3",
        tags=['API Clients'],
        responses={
            "200": {
                "description": "Liste des projets récupérée avec succès",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "project_id": {"type": "string"},
                                    "name": {"type": "string"},
                                    "status": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            },
            "401": {
                "description": "Non autorisé"
            },
            "500": {
                "description": "Erreur serveur"
            }
        }
    )
    def get_projects(self) -> List[Dict[str, Any]]:
        """
        Récupère la liste de tous les projets.
        
        Returns:
            Liste des projets
        """
        if self.use_mock:
            return self._mock_get_projects()
            
        return self._make_request('GET', '/projects')
    
    @swagger_doc(
        path="/projects/{project_id}",
        method="GET",
        summary="Récupère un projet spécifique",
        description="Récupère les détails d'un projet GNS3 par son ID",
        tags=['API Clients'],
        parameters=[
            {
                "name": "project_id",
                "in": "path",
                "description": "ID du projet",
                "required": True,
                "schema": {"type": "string"}
            }
        ],
        responses={
            "200": {
                "description": "Projet récupéré avec succès",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "project_id": {"type": "string"},
                                "name": {"type": "string"},
                                "status": {"type": "string"}
                            }
                        }
                    }
                }
            },
            "404": {
                "description": "Projet non trouvé"
            }
        }
    )
    def get_project(self, project_id: str) -> Dict[str, Any]:
        """
        Récupère les détails d'un projet.
        
        Args:
            project_id: ID du projet
            
        Returns:
            Détails du projet
        """
        if self.use_mock:
            return self._mock_get_project(project_id)
            
        return self._make_request('GET', f'/projects/{project_id}')
    
    def create_project(self, name: str, **kwargs) -> Dict[str, Any]:
        """
        Crée un nouveau projet.
        
        Args:
            name: Nom du projet
            **kwargs: Paramètres supplémentaires pour le projet
            
        Returns:
            Détails du projet créé
        """
        data = {"name": name, **kwargs}
        return self._make_request('POST', '/projects', data=data)
    
    def update_project(self, project_id: str, **kwargs) -> Dict[str, Any]:
        """
        Met à jour un projet existant.
        
        Args:
            project_id: Identifiant du projet
            **kwargs: Paramètres à mettre à jour
            
        Returns:
            Détails du projet mis à jour
        """
        return self._make_request('PUT', f'/projects/{project_id}', data=kwargs)
    
    def delete_project(self, project_id: str) -> Dict[str, Any]:
        """
        Supprime un projet.
        
        Args:
            project_id: Identifiant du projet
            
        Returns:
            Résultat de la suppression
        """
        return self._make_request('DELETE', f'/projects/{project_id}')
    
    def open_project(self, project_id: str) -> Dict[str, Any]:
        """
        Ouvre un projet.
        
        Args:
            project_id: Identifiant du projet
            
        Returns:
            Résultat de l'ouverture
        """
        return self._make_request('POST', f'/projects/{project_id}/open')
    
    def close_project(self, project_id: str) -> Dict[str, Any]:
        """
        Ferme un projet.
        
        Args:
            project_id: Identifiant du projet
            
        Returns:
            Résultat de la fermeture
        """
        return self._make_request('POST', f'/projects/{project_id}/close')
    
    @swagger_doc(
        path="/projects/{project_id}/nodes",
        method="GET",
        summary="Liste les nœuds d'un projet",
        description="Récupère tous les nœuds d'un projet GNS3",
        tags=['API Clients'],
        parameters=[
            {
                "name": "project_id",
                "in": "path",
                "description": "ID du projet",
                "required": True,
                "schema": {"type": "string"}
            }
        ],
        responses={
            "200": {
                "description": "Liste des nœuds récupérée avec succès"
            },
            "404": {
                "description": "Projet non trouvé"
            }
        }
    )
    def get_nodes(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Récupère tous les nœuds d'un projet.
        
        Args:
            project_id: ID du projet
            
        Returns:
            Liste des nœuds du projet
        """
        if self.use_mock:
            return self._mock_get_nodes(project_id)
            
        return self._make_request('GET', f'/projects/{project_id}/nodes')
    
    def get_node(self, project_id: str, node_id: str) -> Dict[str, Any]:
        """
        Récupère les détails d'un nœud.
        
        Args:
            project_id: Identifiant du projet
            node_id: Identifiant du nœud
            
        Returns:
            Détails du nœud
        """
        return self._make_request('GET', f'/projects/{project_id}/nodes/{node_id}')
    
    def create_node(self, project_id: str, name: str, template_id: str, x: int = 0, y: int = 0, **kwargs) -> Dict[str, Any]:
        """
        Crée un nouveau nœud dans un projet.
        
        Args:
            project_id: Identifiant du projet
            name: Nom du nœud
            template_id: Identifiant du modèle de nœud
            x: Coordonnée X du nœud dans l'interface graphique
            y: Coordonnée Y du nœud dans l'interface graphique
            **kwargs: Paramètres supplémentaires pour le nœud
            
        Returns:
            Détails du nœud créé
        """
        data = {
            "name": name,
            "template_id": template_id,
            "x": x,
            "y": y,
            **kwargs
        }
        
        return self._make_request('POST', f'/projects/{project_id}/nodes', data=data)
    
    def update_node(self, project_id: str, node_id: str, **kwargs) -> Dict[str, Any]:
        """
        Met à jour un nœud existant.
        
        Args:
            project_id: Identifiant du projet
            node_id: Identifiant du nœud
            **kwargs: Paramètres à mettre à jour
            
        Returns:
            Détails du nœud mis à jour
        """
        return self._make_request('PUT', f'/projects/{project_id}/nodes/{node_id}', data=kwargs)
    
    def delete_node(self, project_id: str, node_id: str) -> Dict[str, Any]:
        """
        Supprime un nœud.
        
        Args:
            project_id: Identifiant du projet
            node_id: Identifiant du nœud
            
        Returns:
            Résultat de la suppression
        """
        return self._make_request('DELETE', f'/projects/{project_id}/nodes/{node_id}')
    
    def start_node(self, project_id: str, node_id: str) -> Dict[str, Any]:
        """
        Démarre un nœud.
        
        Args:
            project_id: Identifiant du projet
            node_id: Identifiant du nœud
            
        Returns:
            Résultat du démarrage
        """
        return self._make_request('POST', f'/projects/{project_id}/nodes/{node_id}/start')
    
    def stop_node(self, project_id: str, node_id: str) -> Dict[str, Any]:
        """
        Arrête un nœud.
        
        Args:
            project_id: Identifiant du projet
            node_id: Identifiant du nœud
            
        Returns:
            Résultat de l'arrêt
        """
        return self._make_request('POST', f'/projects/{project_id}/nodes/{node_id}/stop')
    
    def get_node_console(self, project_id: str, node_id: str) -> Dict[str, Any]:
        """
        Récupère les informations de console d'un nœud.
        
        Args:
            project_id: Identifiant du projet
            node_id: Identifiant du nœud
            
        Returns:
            Informations de console du nœud
        """
        node_data = self._make_request('GET', f'/projects/{project_id}/nodes/{node_id}')
        if 'console' in node_data:
            return {
                'console_port': node_data.get('console'),
                'console_type': node_data.get('console_type', 'telnet'),
                'console_host': node_data.get('console_host', 'localhost'),
                'console_auto_start': node_data.get('console_auto_start', False)
            }
        return {}
    
    def list_links(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Récupère tous les liens d'un projet.
        
        Args:
            project_id: Identifiant du projet
            
        Returns:
            Liste des liens du projet
        """
        return self._make_request('GET', f'/projects/{project_id}/links')
    
    def get_link(self, project_id: str, link_id: str) -> Dict[str, Any]:
        """
        Récupère les détails d'un lien.
        
        Args:
            project_id: Identifiant du projet
            link_id: Identifiant du lien
            
        Returns:
            Détails du lien
        """
        return self._make_request('GET', f'/projects/{project_id}/links/{link_id}')
    
    def create_link(self, project_id: str, nodes: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """
        Crée un lien entre des nœuds.
        
        Args:
            project_id: Identifiant du projet
            nodes: Liste des nœuds à connecter
            **kwargs: Paramètres supplémentaires pour le lien
            
        Returns:
            Détails du lien créé
        """
        data = {"nodes": nodes, **kwargs}
        return self._make_request('POST', f'/projects/{project_id}/links', data=data)
    
    def delete_link(self, project_id: str, link_id: str) -> Dict[str, Any]:
        """
        Supprime un lien.
        
        Args:
            project_id: Identifiant du projet
            link_id: Identifiant du lien
            
        Returns:
            Résultat de la suppression
        """
        return self._make_request('DELETE', f'/projects/{project_id}/links/{link_id}')
    
    def get_node_files(self, project_id: str, node_id: str) -> Dict[str, Any]:
        """
        Récupère les fichiers d'un nœud (configurations, etc.).
        
        Args:
            project_id: Identifiant du projet
            node_id: Identifiant du nœud
            
        Returns:
            Informations sur les fichiers du nœud
        """
        return self._make_request('GET', f'/projects/{project_id}/nodes/{node_id}/files')
    
    def get_node_file_content(self, project_id: str, node_id: str, file_path: str) -> str:
        """
        Récupère le contenu d'un fichier spécifique d'un nœud.
        
        Args:
            project_id: Identifiant du projet
            node_id: Identifiant du nœud
            file_path: Chemin du fichier
            
        Returns:
            Contenu du fichier
        """
        response = self._make_request('GET', f'/projects/{project_id}/nodes/{node_id}/files/{file_path}')
        return response.get('content', '') if isinstance(response, dict) else str(response)
    
    def restart_node(self, project_id: str, node_id: str) -> Dict[str, Any]:
        """
        Redémarre un nœud.
        
        Args:
            project_id: Identifiant du projet
            node_id: Identifiant du nœud
            
        Returns:
            Résultat du redémarrage
        """
        return self._make_request('POST', f'/projects/{project_id}/nodes/{node_id}/restart')
    
    def suspend_node(self, project_id: str, node_id: str) -> Dict[str, Any]:
        """
        Suspend un nœud.
        
        Args:
            project_id: Identifiant du projet
            node_id: Identifiant du nœud
            
        Returns:
            Résultat de la suspension
        """
        return self._make_request('POST', f'/projects/{project_id}/nodes/{node_id}/suspend')
    
    def resume_node(self, project_id: str, node_id: str) -> Dict[str, Any]:
        """
        Reprend un nœud suspendu.
        
        Args:
            project_id: Identifiant du projet
            node_id: Identifiant du nœud
            
        Returns:
            Résultat de la reprise
        """
        return self._make_request('POST', f'/projects/{project_id}/nodes/{node_id}/resume')
    
    def get_node_stats(self, project_id: str, node_id: str) -> Dict[str, Any]:
        """
        Récupère les statistiques d'un nœud.
        
        Args:
            project_id: Identifiant du projet
            node_id: Identifiant du nœud
            
        Returns:
            Statistiques du nœud
        """
        return self._make_request('GET', f'/projects/{project_id}/nodes/{node_id}/stats')
    
    def get_project_stats(self, project_id: str) -> Dict[str, Any]:
        """
        Récupère les statistiques d'un projet.
        
        Args:
            project_id: Identifiant du projet
            
        Returns:
            Statistiques du projet
        """
        return self._make_request('GET', f'/projects/{project_id}/stats')
    
    def get_node_interfaces(self, project_id: str, node_id: str) -> List[Dict[str, Any]]:
        """
        Récupère les interfaces d'un nœud avec leurs adresses IP.
        
        Args:
            project_id: Identifiant du projet
            node_id: Identifiant du nœud
            
        Returns:
            Liste des interfaces avec leurs IPs
        """
        # Récupérer les données du nœud
        node_data = self._make_request('GET', f'/projects/{project_id}/nodes/{node_id}')
        
        # Extraction des interfaces depuis les ports
        interfaces = []
        ports = node_data.get('ports', [])
        
        for port in ports:
            interface = {
                'name': port.get('name', 'Unknown'),
                'mac_address': port.get('mac_address', ''),
                'ip_addresses': [],
                'adapter_number': port.get('adapter_number', 0),
                'port_number': port.get('port_number', 0),
                'link_type': port.get('link_type', 'unknown'),
                'data_link_types': port.get('data_link_types', {})
            }
            
            # Essayer de récupérer l'IP depuis les propriétés du nœud
            properties = node_data.get('properties', {})
            if 'mac_address' in port and port['mac_address']:
                # Rechercher l'IP correspondante à cette MAC
                interface['ip_addresses'] = self._extract_ip_from_properties(properties, port)
            
            interfaces.append(interface)
        
        return interfaces
    
    def _extract_ip_from_properties(self, properties: Dict[str, Any], port: Dict[str, Any]) -> List[str]:
        """
        Extrait les adresses IP des propriétés du nœud.
        
        Args:
            properties: Propriétés du nœud
            port: Informations du port
            
        Returns:
            Liste des adresses IP trouvées
        """
        ip_addresses = []
        
        # Rechercher dans les scripts de démarrage (VPCS)
        if 'startup_script' in properties:
            startup_script = properties['startup_script']
            import re
            ip_matches = re.findall(r'ip (\d+\.\d+\.\d+\.\d+)', startup_script)
            ip_addresses.extend(ip_matches)
        
        # Rechercher dans les fichiers de configuration
        if 'startup_config' in properties and properties['startup_config']:
            try:
                with open(properties['startup_config'], 'r') as f:
                    config_content = f.read()
                    import re
                    ip_matches = re.findall(r'ip address (\d+\.\d+\.\d+\.\d+)', config_content)
                    ip_addresses.extend(ip_matches)
            except Exception:
                pass
        
        # Rechercher dans les paramètres kernel (QEMU)
        if 'kernel_command_line' in properties:
            kernel_cmd = properties['kernel_command_line']
            import re
            ip_matches = re.findall(r'ip=(\d+\.\d+\.\d+\.\d+)', kernel_cmd)
            ip_addresses.extend(ip_matches)
        
        return list(set(ip_addresses))  # Éliminer les doublons
    
    def get_node_console(self, project_id: str, node_id: str) -> Dict[str, Any]:
        """
        Récupère les informations de console d'un nœud.
        
        Args:
            project_id: Identifiant du projet
            node_id: Identifiant du nœud
            
        Returns:
            Informations de console du nœud
        """
        node_data = self._make_request('GET', f'/projects/{project_id}/nodes/{node_id}')
        
        console_info = {
            'console_type': node_data.get('console_type', 'none'),
            'console_host': node_data.get('console_host', 'localhost'),
            'console_port': node_data.get('console', None),
            'console_auto_start': node_data.get('console_auto_start', False),
            'node_id': node_id,
            'node_name': node_data.get('name', 'Unknown'),
            'node_type': node_data.get('node_type', 'unknown'),
            'status': node_data.get('status', 'stopped')
        }
        
        return console_info
    
    def list_links(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Récupère la liste des liens dans un projet.
        
        Args:
            project_id: Identifiant du projet
            
        Returns:
            Liste des liens du projet
        """
        return self._make_request('GET', f'/projects/{project_id}/links')
    
    # Helpers et autres méthodes
    
    def is_mock(self) -> bool:
        """
        Vérifie si le client utilise le mock GNS3.
        
        Returns:
            True si le mock est utilisé, False sinon
        """
        return self.use_mock
    
    def use_real_server(self, host: str, port: int, protocol: str = 'http', **kwargs) -> None:
        """
        Configure le client pour utiliser un serveur GNS3 réel.
        
        Args:
            host: Hôte du serveur GNS3
            port: Port du serveur GNS3
            protocol: Protocole de connexion ('http' ou 'https')
            **kwargs: Paramètres supplémentaires (username, password, etc.)
        """
        self.host = host
        self.port = port
        self.protocol = protocol
        self.base_url = f"{self.protocol}://{self.host}:{self.port}/v2/"
        self.use_mock = False
        
        # Mise à jour des informations d'authentification si fournies
        if 'username' in kwargs:
            self.username = kwargs['username']
        if 'password' in kwargs:
            self.password = kwargs['password']
        
        # Mettre à jour l'authentification si nécessaire
        if self.username and self.password:
            self.auth = (self.username, self.password)
        else:
            self.auth = None
            
        # Autres paramètres
        if 'verify_ssl' in kwargs:
            self.verify_ssl = kwargs['verify_ssl']
        if 'timeout' in kwargs:
            self.timeout = kwargs['timeout']
            
        logger.info(f"Client GNS3 configuré pour utiliser le serveur réel à {self.base_url}")
    
    def use_mock_server(self) -> None:
        """
        Configure le client pour utiliser le mock GNS3.
        """
        self.use_mock = True
        # Réinitialiser les données du mock
        MockGNS3Service._data = {"projects": {}, "version": "2.2.0"}
        MockGNS3Service.populate_mock_data()
        logger.info("Client GNS3 configuré pour utiliser le mock")
    
    def is_available(self) -> bool:
        """
        Vérifie si le serveur GNS3 est disponible.
        
        Returns:
            True si le serveur est disponible, False sinon
        """
        if self.use_mock:
            return True
            
        try:
            response = self.get_version()
            return response.get("success", False) or "version" in response
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de disponibilité du serveur GNS3: {e}")
            return False 

    def _mock_get_projects(self) -> List[Dict[str, Any]]:
        """
        Mock pour la méthode get_projects en environnement de test.
        
        Returns:
            Liste simulée de projets
        """
        return [
            {
                "project_id": "1a2b3c4d-5e6f-7g8h-9i0j-1k2l3m4n5o6p",
                "name": "Test Project 1",
                "status": "opened"
            },
            {
                "project_id": "2b3c4d5e-6f7g-8h9i-0j1k-2l3m4n5o6p7q",
                "name": "Test Project 2",
                "status": "closed"
            }
        ]
        
    def _mock_get_project(self, project_id: str) -> Dict[str, Any]:
        """
        Mock pour la méthode get_project en environnement de test.
        
        Args:
            project_id: ID du projet
            
        Returns:
            Détails simulés du projet
        """
        return {
            "project_id": project_id,
            "name": f"Test Project {project_id[:4]}",
            "status": "opened",
            "path": f"/tmp/gns3/projects/{project_id}"
        }
        
    def _mock_get_nodes(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Mock pour la méthode get_nodes en environnement de test.
        
        Args:
            project_id: ID du projet
            
        Returns:
            Liste simulée de nœuds
        """
        return [
            {
                "node_id": "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6",
                "name": "Router1",
                "type": "dynamips",
                "status": "started"
            },
            {
                "node_id": "b2c3d4e5-f6g7-h8i9-j0k1-l2m3n4o5p6q7",
                "name": "Switch1",
                "type": "ethernet_switch",
                "status": "started"
            }
        ]
    
    def generate_swagger_doc(self):
        """
        Génère la documentation Swagger pour ce client.
        """
        from ..docs.swagger_generator import generate_swagger_for_class
        return generate_swagger_for_class(
            GNS3Client,
            title="API GNS3 Client",
            description=self.__doc__,
            version="1.0.0",
            output_filename="gns3_client_swagger.json"
        ) 
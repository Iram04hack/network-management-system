"""
Implémentation du client GNS3.

Ce module contient l'implémentation concrète de l'interface GNS3ClientPort,
permettant d'interagir avec l'API GNS3 avec circuit breaker pour la résilience.
"""

import logging
import time
import requests
import json
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urljoin

from gns3_integration.domain.interfaces import GNS3ClientPort
from gns3_integration.domain.exceptions import (
    GNS3Exception, GNS3ConnectionError, GNS3AuthenticationError,
    GNS3ResourceNotFoundError, GNS3OperationError, GNS3TimeoutError
)
from api_clients.di_container import create_circuit_breaker
from api_clients.domain.exceptions import CircuitBreakerOpenException

logger = logging.getLogger(__name__)

class DefaultGNS3Client(GNS3ClientPort):
    """
    Implémentation par défaut du client GNS3 avec circuit breaker.
    
    Cette classe fournit l'implémentation concrète pour interagir avec l'API GNS3
    avec protection circuit breaker pour une meilleure résilience.
    """
    
    def __init__(self, host: str = None, port: int = None, 
                 protocol: str = None, username: str = None, 
                 password: str = None, verify_ssl: bool = None):
        """
        Initialise le client GNS3 avec les paramètres de connexion.
        
        Args:
            host: Nom d'hôte ou adresse IP du serveur GNS3
            port: Port de l'API GNS3
            protocol: Protocole de communication (http/https)
            username: Nom d'utilisateur pour l'authentification (optionnel)
            password: Mot de passe pour l'authentification (optionnel)
            verify_ssl: Vérifie les certificats SSL si True
        """
        # Utiliser les paramètres Django par défaut
        from django.conf import settings
        
        host = host or getattr(settings, 'GNS3_HOST', 'localhost')
        port = port or getattr(settings, 'GNS3_PORT', 3080)
        protocol = protocol or getattr(settings, 'GNS3_PROTOCOL', 'http')
        username = username or getattr(settings, 'GNS3_USERNAME', None)
        password = password or getattr(settings, 'GNS3_PASSWORD', None)
        verify_ssl = verify_ssl if verify_ssl is not None else getattr(settings, 'GNS3_VERIFY_SSL', True)
        
        self.base_url = f"{protocol}://{host}:{port}/v2/"
        
        logger.info(f"🔧 Client GNS3 initialisé avec {self.base_url}")
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "GNS3IntegrationClient/2.0"
        })
        
        # Authentification si fournie
        if username and password:
            self.session.auth = (username, password)
        
        # Vérification SSL
        self.session.verify = verify_ssl
        
        # Initialisation du circuit breaker
        self.circuit_breaker = create_circuit_breaker("gns3_api")
        
        # Configuration des timeouts (connect, read)
        self.session.timeout = (5, 30)
        
        # Métriques pour le monitoring
        self.request_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.last_request_time = 0
        
    def _execute_request(self, method: str, endpoint: str, 
                        payload: Optional[Dict[str, Any]] = None,
                        params: Optional[Dict[str, Any]] = None,
                        timeout: Optional[Tuple[int, int]] = None) -> Dict[str, Any]:
        """
        Exécute une requête API avec circuit breaker et métriques.
        
        Args:
            method: Méthode HTTP
            endpoint: Point d'accès API
            payload: Données à envoyer (optionnel)
            params: Paramètres de requête (optionnel)
            timeout: Timeout personnalisé (optionnel)
            
        Returns:
            Réponse de l'API
        
        Raises:
            GNS3ConnectionError: Si la connexion échoue
            GNS3AuthenticationError: Si l'authentification échoue
            GNS3ResourceNotFoundError: Si la ressource n'est pas trouvée
            GNS3OperationError: Si l'opération échoue
        """
        start_time = time.time()
        self.request_count += 1
        
        # Fonction à exécuter avec circuit breaker
        def _execute():
            try:
                url = self.base_url.rstrip('/') + '/' + endpoint.lstrip('/')
                logger.info(f"🔍 Requête {method} vers {url}")
                logger.debug(f"📋 Base URL: {self.base_url}, Endpoint: {endpoint}")
                
                response = self.session.request(
                    method=method,
                    url=url,
                    json=payload if method.lower() in ('post', 'put', 'patch') else None,
                    params=params,
                    timeout=timeout or self.session.timeout
                )
                
                logger.info(f"📊 Réponse: {response.status_code} pour {url}")
                
                # Analyser les erreurs HTTP
                if response.status_code >= 400:
                    if response.status_code == 401:
                        raise GNS3AuthenticationError(f"Erreur d'authentification: {response.text}")
                    elif response.status_code == 404:
                        raise GNS3ResourceNotFoundError(f"Ressource non trouvée: {response.text}")
                    elif response.status_code >= 500:
                        raise GNS3ConnectionError(f"Erreur serveur: {response.text}")
                    else:
                        raise GNS3OperationError(f"Opération échouée (HTTP {response.status_code}): {response.text}")
                
                # Tenter de décoder la réponse JSON
                try:
                    return response.json()
                except json.JSONDecodeError:
                    # Pour les endpoints qui ne retournent pas de JSON
                    return {"success": True, "status_code": response.status_code}
                
            except requests.exceptions.ConnectionError as e:
                raise GNS3ConnectionError(f"Impossible de se connecter au serveur GNS3: {e}")
            except requests.exceptions.Timeout as e:
                raise GNS3TimeoutError(f"Timeout lors de la connexion au serveur GNS3: {e}")
            except requests.exceptions.RequestException as e:
                raise GNS3ConnectionError(f"Erreur de requête HTTP: {e}")
            except (GNS3Exception, CircuitBreakerOpenException):
                # Réexposer les exceptions de domaine et circuit breaker
                raise
            except Exception as e:
                raise GNS3OperationError(f"Erreur inattendue: {e}")
        
        # Exécution avec circuit breaker
        try:
            result = self.circuit_breaker.execute(_execute)
            # Mise à jour des métriques en cas de succès
            self.last_request_time = time.time() - start_time
            self.success_count += 1
            return result
        except CircuitBreakerOpenException:
            logger.warning(f"Circuit breaker ouvert pour {method} {endpoint}")
            # Mise à jour des métriques en cas d'échec
            self.failure_count += 1
            raise
        except Exception as e:
            # Mise à jour des métriques en cas d'échec
            self.failure_count += 1
            logger.error(f"Erreur lors de {method} {endpoint}: {e}")
            raise
    
    def get_server_info(self) -> Dict[str, Any]:
        """
        Récupère les informations du serveur GNS3.
        
        Returns:
            Informations du serveur
        """
        return self._execute_request("GET", "/version")
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """
        Liste tous les projets GNS3.
        
        Returns:
            Liste des projets
        """
        return self._execute_request("GET", "/projects")
    
    def get_project(self, project_id: str) -> Dict[str, Any]:
        """
        Récupère les informations d'un projet GNS3.
        
        Args:
            project_id: Identifiant du projet
            
        Returns:
            Informations du projet
        """
        return self._execute_request("GET", f"/projects/{project_id}")
    
    def create_project(self, name: str, description: str = "") -> Dict[str, Any]:
        """
        Crée un projet GNS3.
        
        Args:
            name: Nom du projet
            description: Description du projet
            
        Returns:
            Projet créé
        """
        payload = {
            "name": name,
            "description": description
        }
        return self._execute_request("POST", "/projects", payload=payload)
    
    def delete_project(self, project_id: str) -> bool:
        """
        Supprime un projet GNS3.
        
        Args:
            project_id: Identifiant du projet
            
        Returns:
            Succès de la suppression
        """
        try:
            self._execute_request("DELETE", f"/projects/{project_id}")
            return True
        except GNS3ResourceNotFoundError:
            logger.warning(f"Tentative de suppression d'un projet inexistant: {project_id}")
            return False
        except Exception as e:
            logger.error(f"Échec de la suppression du projet {project_id}: {e}")
            return False
    
    def open_project(self, project_id: str) -> Dict[str, Any]:
        """
        Ouvre un projet GNS3.
        
        Args:
            project_id: Identifiant du projet
            
        Returns:
            Projet ouvert
        """
        return self._execute_request("POST", f"/projects/{project_id}/open")
    
    def close_project(self, project_id: str) -> Dict[str, Any]:
        """
        Ferme un projet GNS3.
        
        Args:
            project_id: Identifiant du projet
            
        Returns:
            Projet fermé
        """
        return self._execute_request("POST", f"/projects/{project_id}/close")
    
    def list_nodes(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Liste tous les nœuds d'un projet GNS3.
        
        Args:
            project_id: Identifiant du projet
            
        Returns:
            Liste des nœuds
        """
        return self._execute_request("GET", f"/projects/{project_id}/nodes")
    
    def get_node(self, project_id: str, node_id: str) -> Dict[str, Any]:
        """
        Récupère les informations d'un nœud GNS3.
        
        Args:
            project_id: Identifiant du projet
            node_id: Identifiant du nœud
            
        Returns:
            Informations du nœud
        """
        return self._execute_request("GET", f"/projects/{project_id}/nodes/{node_id}")
    
    def create_node(self, project_id: str, node_type: str, name: str, 
                    x: int = 0, y: int = 0, properties: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Crée un nœud GNS3.
        
        Args:
            project_id: Identifiant du projet
            node_type: Type de nœud
            name: Nom du nœud
            x: Position X
            y: Position Y
            properties: Propriétés du nœud
            
        Returns:
            Nœud créé
        """
        payload = {
            "name": name,
            "node_type": node_type,
            "compute_id": "local",  # Par défaut sur le serveur local
            "x": x,
            "y": y
        }
        
        # Ajouter les propriétés spécifiques si fournies
        if properties:
            payload.update(properties)
            
        return self._execute_request("POST", f"/projects/{project_id}/nodes", payload=payload)
    
    def delete_node(self, project_id: str, node_id: str) -> bool:
        """
        Supprime un nœud GNS3.
        
        Args:
            project_id: Identifiant du projet
            node_id: Identifiant du nœud
            
        Returns:
            Succès de la suppression
        """
        try:
            self._execute_request("DELETE", f"/projects/{project_id}/nodes/{node_id}")
            return True
        except GNS3ResourceNotFoundError:
            logger.warning(f"Tentative de suppression d'un nœud inexistant: {node_id}")
            return False
        except Exception as e:
            logger.error(f"Échec de la suppression du nœud {node_id}: {e}")
            return False
    
    def start_node(self, project_id: str, node_id: str) -> Dict[str, Any]:
        """
        Démarre un nœud GNS3.
        
        Args:
            project_id: Identifiant du projet
            node_id: Identifiant du nœud
            
        Returns:
            Résultat du démarrage
        """
        return self._execute_request("POST", f"/projects/{project_id}/nodes/{node_id}/start")
    
    def stop_node(self, project_id: str, node_id: str) -> Dict[str, Any]:
        """
        Arrête un nœud GNS3.
        
        Args:
            project_id: Identifiant du projet
            node_id: Identifiant du nœud
            
        Returns:
            Résultat de l'arrêt
        """
        return self._execute_request("POST", f"/projects/{project_id}/nodes/{node_id}/stop")
    
    def restart_node(self, project_id: str, node_id: str) -> Dict[str, Any]:
        """
        Redémarre un nœud GNS3.
        
        Args:
            project_id: Identifiant du projet
            node_id: Identifiant du nœud
            
        Returns:
            Résultat du redémarrage
        """
        # Implémentation avec stop puis start
        self.stop_node(project_id, node_id)
        time.sleep(1)  # Attente pour s'assurer que le nœud est complètement arrêté
        return self.start_node(project_id, node_id)
    
    def get_node_console(self, project_id: str, node_id: str) -> Dict[str, Any]:
        """
        Récupère les informations de console d'un nœud GNS3.
        
        Args:
            project_id: Identifiant du projet
            node_id: Identifiant du nœud
            
        Returns:
            Informations de console
        """
        node_info = self.get_node(project_id, node_id)
        
        if "console" not in node_info or node_info["console"] is None:
            return {
                "console_host": None,
                "console_port": None,
                "console_type": None
            }
        
        return {
            "console_host": node_info.get("console_host", "localhost"),
            "console_port": node_info.get("console", None),
            "console_type": node_info.get("console_type", "telnet")
        }
    
    def create_link(self, project_id: str, source_node_id: str, source_port: int, 
                    target_node_id: str, target_port: int) -> Dict[str, Any]:
        """
        Crée un lien GNS3.
        
        Args:
            project_id: Identifiant du projet
            source_node_id: Identifiant du nœud source
            source_port: Port du nœud source
            target_node_id: Identifiant du nœud cible
            target_port: Port du nœud cible
            
        Returns:
            Lien créé
        """
        # Récupérer les informations des ports des nœuds
        source_node = self.get_node(project_id, source_node_id)
        target_node = self.get_node(project_id, target_node_id)
        
        # Trouver les ports correspondants
        source_port_info = None
        target_port_info = None
        
        for port in source_node.get("ports", []):
            if port.get("port_number") == source_port:
                source_port_info = port
                break
                
        for port in target_node.get("ports", []):
            if port.get("port_number") == target_port:
                target_port_info = port
                break
        
        if not source_port_info or not target_port_info:
            raise GNS3OperationError("Ports spécifiés non trouvés")
        
        # Créer le lien
        payload = {
            "nodes": [
                {
                    "node_id": source_node_id,
                    "adapter_number": source_port_info.get("adapter_number", 0),
                    "port_number": source_port
                },
                {
                    "node_id": target_node_id,
                    "adapter_number": target_port_info.get("adapter_number", 0),
                    "port_number": target_port
                }
            ]
        }
        
        return self._execute_request("POST", f"/projects/{project_id}/links", payload=payload)
    
    def delete_link(self, project_id: str, link_id: str) -> bool:
        """
        Supprime un lien GNS3.
        
        Args:
            project_id: Identifiant du projet
            link_id: Identifiant du lien
            
        Returns:
            Succès de la suppression
        """
        try:
            self._execute_request("DELETE", f"/projects/{project_id}/links/{link_id}")
            return True
        except GNS3ResourceNotFoundError:
            logger.warning(f"Tentative de suppression d'un lien inexistant: {link_id}")
            return False
        except Exception as e:
            logger.error(f"Échec de la suppression du lien {link_id}: {e}")
            return False
    
    def get_link(self, project_id: str, link_id: str) -> Dict[str, Any]:
        """
        Récupère les informations d'un lien GNS3.
        
        Args:
            project_id: Identifiant du projet
            link_id: Identifiant du lien
            
        Returns:
            Informations du lien
        """
        return self._execute_request("GET", f"/projects/{project_id}/links/{link_id}")
    
    def list_links(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Liste tous les liens d'un projet GNS3.
        
        Args:
            project_id: Identifiant du projet
            
        Returns:
            Liste des liens
        """
        return self._execute_request("GET", f"/projects/{project_id}/links")

    def list_projects(self) -> List[Dict[str, Any]]:
        """
        Liste tous les projets disponibles sur le serveur GNS3.
        
        Returns:
            Liste des projets avec leurs informations
            
        Raises:
            GNS3ConnectionError: Si la connexion échoue
            GNS3OperationError: Si l'opération échoue
        """
        try:
            logger.info("🔍 Récupération de la liste des projets depuis le serveur GNS3...")
            projects = self._execute_request("GET", "/projects")
            logger.info(f"📋 {len(projects)} projets trouvés sur le serveur GNS3")
            return projects
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des projets: {e}")
            raise GNS3OperationError(f"Impossible de récupérer la liste des projets: {e}")

    def get_project(self, project_id: str) -> Dict[str, Any]:
        """
        Récupère les détails d'un projet spécifique.
        
        Args:
            project_id: Identifiant du projet
            
        Returns:
            Informations détaillées du projet
            
        Raises:
            GNS3ConnectionError: Si la connexion échoue
            GNS3ResourceNotFoundError: Si le projet n'est pas trouvé
            GNS3OperationError: Si l'opération échoue
        """
        try:
            return self._execute_request("GET", f"/projects/{project_id}")
        except Exception as e:
            if "404" in str(e):
                raise GNS3ResourceNotFoundError(f"Projet {project_id} non trouvé")
            else:
                raise GNS3OperationError(f"Impossible de récupérer le projet {project_id}: {e}")
    
    def create_snapshot(self, project_id: str, name: str = None) -> Dict[str, Any]:
        """
        Crée un snapshot d'un projet GNS3.
        
        Args:
            project_id: Identifiant du projet
            name: Nom du snapshot
            
        Returns:
            Snapshot créé
        """
        payload = {}
        if name:
            payload = {"name": name}
            
        return self._execute_request("POST", f"/projects/{project_id}/snapshots", payload=payload)
    
    def restore_snapshot(self, project_id: str, snapshot_id: str) -> Dict[str, Any]:
        """
        Restaure un snapshot d'un projet GNS3.
        
        Args:
            project_id: Identifiant du projet
            snapshot_id: Identifiant du snapshot
            
        Returns:
            Résultat de la restauration
        """
        return self._execute_request("POST", f"/projects/{project_id}/snapshots/{snapshot_id}/restore")
    
    def list_snapshots(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Liste tous les snapshots d'un projet GNS3.
        
        Args:
            project_id: Identifiant du projet
            
        Returns:
            Liste des snapshots
        """
        return self._execute_request("GET", f"/projects/{project_id}/snapshots")
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Récupère les métriques d'utilisation du client.
        
        Returns:
            Métriques d'utilisation
        """
        success_rate = 0
        if self.request_count > 0:
            success_rate = (self.success_count / self.request_count) * 100
            
        return {
            "request_count": self.request_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": success_rate,
            "last_request_time": self.last_request_time,
            "circuit_breaker_state": self.circuit_breaker.state.name
        }
    
    def reset_metrics(self) -> None:
        """Réinitialise les métriques du client."""
        self.request_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.last_request_time = 0


# Alias pour la compatibilité avec l'ancien code
GNS3ClientImpl = DefaultGNS3Client

"""
Module de conteneur pour les clients API.

Ce module contient la classe APIClientContainer qui gère les clients API.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class APIClientContainer:
    """
    Conteneur pour les clients API.
    
    Cette classe gère les clients API et permet de les récupérer par leur nom.
    """
    
    def __init__(self):
        """
        Initialise le conteneur de clients API.
        """
        self._clients = {}
        self._initialize_clients()
    
    def _initialize_clients(self):
        """
        Initialise les clients API.

        Cette méthode est appelée lors de l'initialisation du conteneur.
        Elle crée et configure les clients API.
        """
        # Initialisation sécurisée des clients avec gestion d'erreurs
        self._clients = {
            # Clients d'exemple toujours disponibles
            "example": ExampleAPIClient(),
            "network": NetworkAPIClient(),
        }

        # Tentative d'ajout des vrais clients API
        self._try_add_real_clients()

        logger.info(f"Conteneur initialisé avec {len(self._clients)} clients API")

    def _try_add_real_clients(self):
        """Tente d'ajouter les vrais clients API avec gestion d'erreurs."""

        # Clients réseau
        try:
            from .network import SNMPClient
            self._clients["snmp"] = SNMPClient(host="localhost")
        except Exception as e:
            logger.warning(f"Impossible d'initialiser SNMPClient: {e}")

        try:
            from .network import NetflowClient
            self._clients["netflow"] = NetflowClient(base_url="http://localhost:9995")
        except Exception as e:
            logger.warning(f"Impossible d'initialiser NetflowClient: {e}")

        try:
            from .network import GNS3Client
            self._clients["gns3"] = GNS3Client(host="localhost", port=3080)
        except Exception as e:
            logger.warning(f"Impossible d'initialiser GNS3Client: {e}")

        # Clients monitoring
        try:
            from .monitoring import PrometheusClient
            self._clients["prometheus"] = PrometheusClient(base_url="http://localhost:9090")
        except Exception as e:
            logger.warning(f"Impossible d'initialiser PrometheusClient: {e}")

        try:
            from .monitoring import GrafanaClient
            self._clients["grafana"] = GrafanaClient(base_url="http://localhost:3000")
        except Exception as e:
            logger.warning(f"Impossible d'initialiser GrafanaClient: {e}")

        try:
            from .monitoring import ElasticsearchClient
            self._clients["elasticsearch"] = ElasticsearchClient(
                base_url="http://localhost:9200",
                username="elastic",
                password="changeme",
                api_key=None
            )
        except Exception as e:
            logger.warning(f"Impossible d'initialiser ElasticsearchClient: {e}")

        try:
            from .monitoring import NetdataClient
            self._clients["netdata"] = NetdataClient(base_url="http://localhost:19999")
        except Exception as e:
            logger.warning(f"Impossible d'initialiser NetdataClient: {e}")

        try:
            from .monitoring import NtopngClient
            self._clients["ntopng"] = NtopngClient(
                base_url="http://localhost:3000",
                username="admin",
                password="admin"
            )
        except Exception as e:
            logger.warning(f"Impossible d'initialiser NtopngClient: {e}")

        # Clients infrastructure
        try:
            from .infrastructure import HAProxyClient
            self._clients["haproxy"] = HAProxyClient(stats_socket="/var/run/haproxy.sock")
        except Exception as e:
            logger.warning(f"Impossible d'initialiser HAProxyClient: {e}")

        try:
            from .security import Fail2BanClient
            self._clients["fail2ban"] = Fail2BanClient(
                base_url="http://localhost:8080",
                username="admin",
                password="admin"
            )
        except Exception as e:
            logger.warning(f"Impossible d'initialiser Fail2BanClient: {e}")

        try:
            from .security import SuricataClient
            self._clients["suricata"] = SuricataClient(base_url="http://localhost:8081")
        except Exception as e:
            logger.warning(f"Impossible d'initialiser SuricataClient: {e}")
    
    def get_client(self, client_name: str) -> Optional[Any]:
        """
        Récupère un client API par son nom.
        
        Args:
            client_name: Le nom du client API.
            
        Returns:
            Le client API ou None si le client n'existe pas.
        """
        return self._clients.get(client_name)
    
    def get_all_clients(self) -> Dict[str, Any]:
        """
        Récupère tous les clients API.
        
        Returns:
            Un dictionnaire contenant tous les clients API.
        """
        return self._clients


class BaseAPIClient:
    """
    Classe de base pour les clients API.
    
    Cette classe définit l'interface commune à tous les clients API.
    """
    
    def get_swagger_doc(self) -> Dict[str, Any]:
        """
        Récupère la documentation OpenAPI du client.
        
        Returns:
            La documentation OpenAPI au format JSON.
        """
        raise NotImplementedError("Cette méthode doit être implémentée par les sous-classes")
    
    def check_health(self) -> bool:
        """
        Vérifie la santé du client.
        
        Returns:
            True si le client est en bonne santé, False sinon.
        """
        raise NotImplementedError("Cette méthode doit être implémentée par les sous-classes")


class ExampleAPIClient(BaseAPIClient):
    """
    Client API d'exemple pour les tests.
    """
    
    def get_swagger_doc(self) -> Dict[str, Any]:
        """
        Récupère la documentation OpenAPI du client.
        
        Returns:
            La documentation OpenAPI au format JSON.
        """
        return {
            "openapi": "3.0.0",
            "info": {
                "title": "Example API",
                "version": "1.0.0",
                "description": "API d'exemple pour les tests"
            },
            "paths": {
                "/example": {
                    "get": {
                        "summary": "Récupère un exemple",
                        "responses": {
                            "200": {
                                "description": "Succès",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "id": {"type": "integer"},
                                                "name": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    
    def check_health(self) -> bool:
        """
        Vérifie la santé du client.
        
        Returns:
            True si le client est en bonne santé, False sinon.
        """
        return True


class NetworkAPIClient(BaseAPIClient):
    """
    Client API pour les services réseau.
    """
    
    def get_swagger_doc(self) -> Dict[str, Any]:
        """
        Récupère la documentation OpenAPI du client.
        
        Returns:
            La documentation OpenAPI au format JSON.
        """
        return {
            "openapi": "3.0.0",
            "info": {
                "title": "Network API",
                "version": "1.0.0",
                "description": "API pour les services réseau"
            },
            "paths": {
                "/devices": {
                    "get": {
                        "summary": "Récupère la liste des appareils réseau",
                        "responses": {
                            "200": {
                                "description": "Succès",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "id": {"type": "integer"},
                                                    "name": {"type": "string"},
                                                    "ip": {"type": "string"},
                                                    "status": {"type": "string"}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    
    def check_health(self) -> bool:
        """
        Vérifie la santé du client.
        
        Returns:
            True si le client est en bonne santé, False sinon.
        """
        return True 
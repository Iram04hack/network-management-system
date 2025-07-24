"""
Tests d'intégration pour le client HAProxy.

Ce module contient des tests d'intégration pour le client HAProxy,
vérifiant son fonctionnement avec un serveur HAProxy réel ou simulé.
"""

import os
import pytest
import requests
from unittest import mock

from api_clients.infrastructure.haproxy_client import HAProxyClient
from api_clients.domain.exceptions import (
    APIConnectionException,
    AuthenticationException,
    ValidationException
)

# Marquer tous les tests de ce module comme tests d'intégration
pytestmark = pytest.mark.integration

class TestHAProxyClientIntegration:
    """Tests d'intégration pour le client HAProxy."""
    
    @pytest.fixture
    def haproxy_url(self):
        """Récupère l'URL du serveur HAProxy depuis les variables d'environnement."""
        return os.environ.get("HAPROXY_TEST_URL", "http://localhost:8404")
    
    @pytest.fixture
    def haproxy_client(self, haproxy_url):
        """Crée une instance du client HAProxy pour les tests."""
        return HAProxyClient(
            base_url=haproxy_url,
            username=os.environ.get("HAPROXY_TEST_USER", "admin"),
            password=os.environ.get("HAPROXY_TEST_PASSWORD", "admin"),
            timeout=5
        )
    
    def test_connection(self, haproxy_client):
        """Vérifie que le client peut se connecter au serveur HAProxy."""
        with mock.patch.object(requests.Session, 'get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {"version": "2.4.0"}
            
            assert haproxy_client.test_connection()
            mock_get.assert_called_once()
    
    def test_get_stats(self, haproxy_client):
        """Teste la récupération des statistiques."""
        with mock.patch.object(requests.Session, 'get') as mock_get:
            # Simuler une réponse de statistiques
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "stats": [
                    {
                        "pxname": "http-in",
                        "svname": "FRONTEND",
                        "status": "OPEN",
                        "slim": "50000",
                        "scur": "1"
                    },
                    {
                        "pxname": "webapp",
                        "svname": "BACKEND",
                        "status": "UP",
                        "slim": "1000",
                        "scur": "0"
                    }
                ]
            }
            
            result = haproxy_client.get_stats()
            
            mock_get.assert_called_once()
            assert len(result["stats"]) == 2
            assert result["stats"][0]["pxname"] == "http-in"
            assert result["stats"][1]["pxname"] == "webapp"
    
    def test_get_info(self, haproxy_client):
        """Teste la récupération des informations du serveur."""
        with mock.patch.object(requests.Session, 'get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "version": "2.4.0",
                "release_date": "2021/04/20",
                "nbproc": "4",
                "process_num": "1",
                "uptime": "1d 2h34m5s"
            }
            
            result = haproxy_client.get_info()
            
            mock_get.assert_called_once()
            assert result["version"] == "2.4.0"
            assert result["nbproc"] == "4"
    
    def test_get_backends(self, haproxy_client):
        """Teste la récupération des backends."""
        with mock.patch.object(requests.Session, 'get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = [
                {"name": "webapp", "status": "UP"},
                {"name": "api", "status": "UP"},
                {"name": "static", "status": "DOWN"}
            ]
            
            result = haproxy_client.get_backends()
            
            mock_get.assert_called_once()
            assert len(result) == 3
            assert result[0]["name"] == "webapp"
            assert result[2]["status"] == "DOWN"
    
    def test_get_frontends(self, haproxy_client):
        """Teste la récupération des frontends."""
        with mock.patch.object(requests.Session, 'get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = [
                {"name": "http-in", "status": "OPEN"},
                {"name": "https-in", "status": "OPEN"}
            ]
            
            result = haproxy_client.get_frontends()
            
            mock_get.assert_called_once()
            assert len(result) == 2
            assert result[0]["name"] == "http-in"
            assert result[1]["name"] == "https-in"
    
    def test_enable_server(self, haproxy_client):
        """Teste l'activation d'un serveur."""
        with mock.patch.object(requests.Session, 'post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {"message": "Server enabled"}
            
            result = haproxy_client.enable_server("webapp", "server1")
            
            mock_post.assert_called_once()
            assert result["message"] == "Server enabled"
    
    def test_disable_server(self, haproxy_client):
        """Teste la désactivation d'un serveur."""
        with mock.patch.object(requests.Session, 'post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {"message": "Server disabled"}
            
            result = haproxy_client.disable_server("webapp", "server1")
            
            mock_post.assert_called_once()
            assert result["message"] == "Server disabled"
    
    def test_authentication_error(self, haproxy_client):
        """Teste la gestion des erreurs d'authentification."""
        with mock.patch.object(requests.Session, 'get') as mock_get:
            mock_get.return_value.status_code = 401
            
            with pytest.raises(AuthenticationException):
                haproxy_client.get_stats()
    
    def test_validation_error(self, haproxy_client):
        """Teste la gestion des erreurs de validation."""
        with pytest.raises(ValidationException):
            # Utiliser un mock n'est pas nécessaire ici car la validation se fait avant la requête
            haproxy_client.enable_server("", "server1")
    
    def test_connection_error(self, haproxy_client):
        """Teste la gestion des erreurs de connexion."""
        with mock.patch.object(requests.Session, 'get') as mock_get:
            mock_get.side_effect = requests.ConnectionError("Connection refused")
            
            with pytest.raises(APIConnectionException):
                haproxy_client.get_stats() 
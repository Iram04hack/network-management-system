"""
Tests d'intégration pour le client Prometheus.

Ce module contient des tests d'intégration pour le client Prometheus,
vérifiant son fonctionnement avec un serveur Prometheus réel ou simulé.
"""

import os
import pytest
import requests
from unittest import mock
from datetime import datetime, timedelta

from api_clients.monitoring.prometheus_client import PrometheusClient
from api_clients.monitoring.metrics.performance import PerformanceMetrics
from api_clients.domain.exceptions import APIConnectionException

# Marquer tous les tests de ce module comme tests d'intégration
pytestmark = pytest.mark.integration

class TestPrometheusClientIntegration:
    """Tests d'intégration pour le client Prometheus."""
    
    @pytest.fixture
    def prometheus_url(self):
        """Récupère l'URL du serveur Prometheus depuis les variables d'environnement."""
        # Utiliser une URL de test par défaut si aucune n'est spécifiée
        return os.environ.get("PROMETHEUS_TEST_URL", "http://localhost:9090")
    
    @pytest.fixture
    def prometheus_client(self, prometheus_url):
        """Crée une instance du client Prometheus pour les tests."""
        return PrometheusClient(base_url=prometheus_url, timeout=5)
    
    def test_connection(self, prometheus_client):
        """Vérifie que le client peut se connecter au serveur Prometheus."""
        # Utiliser un mock pour éviter de dépendre d'un serveur réel
        with mock.patch.object(requests.Session, 'get') as mock_get:
            # Simuler une réponse HTTP 200
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {"status": "success", "data": {}}
            
            # Vérifier que la connexion fonctionne
            assert prometheus_client.test_connection()
    
    def test_query(self, prometheus_client):
        """Teste la fonctionnalité de requête PromQL."""
        with mock.patch.object(requests.Session, 'get') as mock_get:
            # Simuler une réponse de requête PromQL
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "status": "success",
                "data": {
                    "resultType": "vector",
                    "result": [
                        {
                            "metric": {"__name__": "up", "job": "prometheus"},
                            "value": [1618501548.467, "1"]
                        }
                    ]
                }
            }
            
            # Exécuter une requête PromQL simple
            result = prometheus_client.query("up{job='prometheus'}")
            
            # Vérifier que la requête a été bien formée
            mock_get.assert_called_once()
            assert "query=" in mock_get.call_args[1]["params"]
            
            # Vérifier le résultat
            assert result["status"] == "success"
            assert len(result["data"]["result"]) == 1
            assert result["data"]["result"][0]["metric"]["job"] == "prometheus"
    
    def test_query_range(self, prometheus_client):
        """Teste la fonctionnalité de requête PromQL sur une plage de temps."""
        with mock.patch.object(requests.Session, 'get') as mock_get:
            # Simuler une réponse de requête PromQL range
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "status": "success",
                "data": {
                    "resultType": "matrix",
                    "result": [
                        {
                            "metric": {"__name__": "up", "job": "prometheus"},
                            "values": [
                                [1618501458.467, "1"],
                                [1618501518.467, "1"],
                                [1618501578.467, "1"]
                            ]
                        }
                    ]
                }
            }
            
            # Calculer les timestamps pour la plage
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=1)
            
            # Exécuter une requête de plage
            result = prometheus_client.query_range(
                "up{job='prometheus'}",
                start=int(start_time.timestamp()),
                end=int(end_time.timestamp()),
                step=60
            )
            
            # Vérifier que la requête a été bien formée
            mock_get.assert_called_once()
            assert "query=" in mock_get.call_args[1]["params"]
            assert "start=" in mock_get.call_args[1]["params"]
            assert "end=" in mock_get.call_args[1]["params"]
            assert "step=" in mock_get.call_args[1]["params"]
            
            # Vérifier le résultat
            assert result["status"] == "success"
            assert len(result["data"]["result"]) == 1
            assert len(result["data"]["result"][0]["values"]) == 3
    
    def test_alerts(self, prometheus_client):
        """Teste la récupération des alertes actives."""
        with mock.patch.object(requests.Session, 'get') as mock_get:
            # Simuler une réponse d'alertes
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "status": "success",
                "data": {
                    "alerts": [
                        {
                            "labels": {
                                "alertname": "InstanceDown",
                                "severity": "critical"
                            },
                            "annotations": {
                                "description": "Instance is down",
                                "summary": "Instance down"
                            },
                            "state": "firing",
                            "activeAt": "2023-01-01T00:00:00Z",
                            "value": "1"
                        }
                    ]
                }
            }
            
            # Récupérer les alertes
            result = prometheus_client.get_alerts()
            
            # Vérifier la requête
            mock_get.assert_called_once()
            
            # Vérifier le résultat
            assert result["status"] == "success"
            assert len(result["data"]["alerts"]) == 1
            assert result["data"]["alerts"][0]["labels"]["alertname"] == "InstanceDown"
    
    def test_error_handling(self, prometheus_client):
        """Teste la gestion des erreurs de connexion."""
        with mock.patch.object(requests.Session, 'get') as mock_get:
            # Simuler une erreur de connexion
            mock_get.side_effect = requests.ConnectionError("Connection refused")
            
            # Vérifier que l'exception appropriée est levée
            with pytest.raises(APIConnectionException):
                prometheus_client.query("up")
    
    def test_metrics_collection(self, prometheus_client):
        """Vérifie que les métriques de performance sont collectées."""
        # Effacer les métriques existantes
        metrics = PerformanceMetrics()
        metrics.clear_metrics()
        
        with mock.patch.object(requests.Session, 'get') as mock_get:
            # Simuler une réponse réussie
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {"status": "success", "data": {}}
            
            # Exécuter une requête
            prometheus_client.query("up")
            
            # Vérifier que des métriques ont été collectées
            summaries = metrics.get_metrics_summary()
            
            # Il devrait y avoir au moins une métrique pour la méthode "query"
            assert any(s.endpoint == "query" for s in summaries) 
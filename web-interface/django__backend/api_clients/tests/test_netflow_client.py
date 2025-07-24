"""
Tests unitaires pour le client NetFlow.

Ces tests couvrent l'analyse des flux réseau, la validation sécurisée,
la détection d'anomalies et les cas d'usage avancés.
"""

import pytest
import time
from datetime import datetime
from unittest.mock import Mock, patch

from api_clients.network.netflow_client import NetflowClient
from api_clients.infrastructure.input_validator import ValidationException
from api_clients.domain.exceptions import APIClientDataException


class TestNetflowClientInitialization:
    """Tests pour l'initialisation du client NetFlow."""
    
    def test_netflow_client_basic_init(self):
        """Test l'initialisation de base du client."""
        client = NetflowClient(
            base_url="http://netflow.example.com",
            collector_host="192.168.1.100",
            collector_port=2055
        )
        
        assert client.base_url == "http://netflow.example.com"
        assert client.collector_host == "192.168.1.100"
        assert client.collector_port == 2055
        assert client.timeout == 30  # Timeout par défaut
    
    def test_netflow_client_with_credentials(self):
        """Test l'initialisation avec credentials."""
        client = NetflowClient(
            base_url="https://netflow.example.com",
            username="admin",
            password="secret",
            api_key="test-key"
        )
        
        assert client.username == "admin"
        assert client.password == "secret"
        assert client.api_key == "test-key"
    
    def test_netflow_client_validators_initialization(self):
        """Test l'initialisation des validateurs."""
        client = NetflowClient("http://netflow.example.com")
        
        # Vérifier que les validateurs sont initialisés
        assert hasattr(client, 'validators')
        assert 'src_ip' in client.validators.validators
        assert 'dst_ip' in client.validators.validators
        assert 'src_port' in client.validators.validators
        assert 'dst_port' in client.validators.validators


class TestNetflowClientValidation:
    """Tests pour la validation des paramètres NetFlow."""
    
    def test_validate_time_range_valid(self):
        """Test la validation d'une plage temporelle valide."""
        client = NetflowClient("http://netflow.example.com")
        
        start_time = datetime.now().timestamp() - 3600  # Il y a 1 heure
        end_time = datetime.now().timestamp()
        
        validated = client._validate_time_range(start_time, end_time)
        
        assert 'start_time' in validated
        assert 'end_time' in validated
    
    def test_validate_time_range_invalid_order(self):
        """Test la validation avec ordre temporel invalide."""
        client = NetflowClient("http://netflow.example.com")
        
        start_time = datetime.now().timestamp()
        end_time = datetime.now().timestamp() - 3600  # Dans le passé
        
        with pytest.raises(ValidationException):
            client._validate_time_range(start_time, end_time)
    
    def test_validate_time_range_too_large(self):
        """Test la validation avec plage temporelle trop large."""
        client = NetflowClient("http://netflow.example.com")
        
        start_time = datetime.now().timestamp() - (8 * 24 * 3600)  # Il y a 8 jours
        end_time = datetime.now().timestamp()
        
        with pytest.raises(ValidationException):
            client._validate_time_range(start_time, end_time)
    
    def test_normalize_protocol_valid(self):
        """Test la normalisation des protocoles valides."""
        client = NetflowClient("http://netflow.example.com")
        
        # Test avec noms
        assert client._normalize_protocol("TCP") == 6
        assert client._normalize_protocol("UDP") == 17
        assert client._normalize_protocol("ICMP") == 1
        
        # Test avec numéros
        assert client._normalize_protocol(6) == 6
        assert client._normalize_protocol("17") == 17
    
    def test_normalize_protocol_invalid(self):
        """Test la normalisation avec protocoles invalides."""
        client = NetflowClient("http://netflow.example.com")
        
        with pytest.raises(ValidationException):
            client._normalize_protocol("INVALID")
        
        with pytest.raises(ValidationException):
            client._normalize_protocol(999)  # Protocole non supporté
    
    def test_validate_query_params_comprehensive(self):
        """Test la validation complète des paramètres de requête."""
        client = NetflowClient("http://netflow.example.com")
        
        current_time = datetime.now().timestamp()
        params = {
            'start_time': current_time - 3600,
            'end_time': current_time,
            'src_ip': '192.168.1.1',
            'dst_ip': '10.0.0.1',
            'src_port': 80,
            'dst_port': 443,
            'protocol': 'TCP',
            'interface': 'eth0'
        }
        
        validated = client._validate_query_params(**params)
        
        assert validated['src_ip'] == '192.168.1.1'
        assert validated['dst_ip'] == '10.0.0.1'
        assert validated['src_port'] == 80
        assert validated['dst_port'] == 443
        assert validated['protocol'] == 6  # TCP normalisé
        assert validated['interface'] == 'eth0'


class TestNetflowClientQueries:
    """Tests pour les requêtes NetFlow."""
    
    @patch('api_clients.network.netflow_client.NetflowClient.get')
    def test_query_flows_basic(self, mock_get):
        """Test la requête de base des flux."""
        mock_get.return_value = {
            "success": True,
            "flows": [
                {
                    "src_ip": "192.168.1.1",
                    "dst_ip": "10.0.0.1",
                    "src_port": 80,
                    "dst_port": 443,
                    "protocol": 6,
                    "bytes": 1024,
                    "first_switched": 1640995200,
                    "last_switched": 1640995260
                }
            ]
        }
        
        client = NetflowClient("http://netflow.example.com")
        
        start_time = datetime.now().timestamp() - 3600
        end_time = datetime.now().timestamp()
        
        result = client.query_flows(start_time, end_time)
        
        assert result["success"] is True
        assert "flows" in result
        assert len(result["flows"]) == 1
        
        # Vérifier l'enrichissement des données
        flow = result["flows"][0]
        assert "protocol_name" in flow
        assert flow["protocol_name"] == "TCP"
        assert "duration_seconds" in flow
        assert "bitrate_bps" in flow
    
    @patch('api_clients.network.netflow_client.NetflowClient.get')
    def test_query_flows_with_filters(self, mock_get):
        """Test la requête avec filtres."""
        mock_get.return_value = {"success": True, "flows": []}
        
        client = NetflowClient("http://netflow.example.com")
        
        start_time = datetime.now().timestamp() - 3600
        end_time = datetime.now().timestamp()
        
        result = client.query_flows(
            start_time=start_time,
            end_time=end_time,
            src_ip="192.168.1.1",
            dst_ip="10.0.0.1",
            protocol="TCP",
            limit=500
        )
        
        # Vérifier que les paramètres ont été transmis
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        params = call_args[1]['params']
        
        assert params['src_ip'] == "192.168.1.1"
        assert params['dst_ip'] == "10.0.0.1"
        assert params['protocol'] == 6  # TCP normalisé
        assert params['limit'] == 500
    
    @patch('api_clients.network.netflow_client.NetflowClient.get')
    def test_get_top_talkers(self, mock_get):
        """Test la récupération des top talkers."""
        mock_get.return_value = {
            "success": True,
            "data": [
                {
                    "ip_address": "192.168.1.100",
                    "bytes": 1048576,
                    "packets": 1000,
                    "flows": 50
                },
                {
                    "ip_address": "8.8.8.8",
                    "bytes": 524288,
                    "packets": 500,
                    "flows": 25
                }
            ]
        }
        
        client = NetflowClient("http://netflow.example.com")
        
        start_time = datetime.now().timestamp() - 3600
        end_time = datetime.now().timestamp()
        
        result = client.get_top_talkers(start_time, end_time, top_n=10)
        
        assert result["success"] is True
        assert "data" in result
        assert len(result["data"]) == 2
        
        # Vérifier l'enrichissement
        talker1 = result["data"][0]
        assert "ip_type" in talker1
        assert "is_private" in talker1
        assert talker1["is_private"] is True  # 192.168.x.x est privée
        
        talker2 = result["data"][1]
        assert talker2["is_private"] is False  # 8.8.8.8 est publique
    
    @patch('api_clients.network.netflow_client.NetflowClient.get')
    def test_get_protocol_distribution(self, mock_get):
        """Test l'analyse de distribution des protocoles."""
        mock_get.return_value = {
            "success": True,
            "data": [
                {"protocol_number": 6, "bytes": 1048576, "flows": 100},
                {"protocol_number": 17, "bytes": 524288, "flows": 50},
                {"protocol_number": 1, "bytes": 1024, "flows": 5}
            ]
        }
        
        client = NetflowClient("http://netflow.example.com")
        
        start_time = datetime.now().timestamp() - 3600
        end_time = datetime.now().timestamp()
        
        result = client.get_protocol_distribution(start_time, end_time)
        
        assert result["success"] is True
        assert "data" in result
        
        # Vérifier l'enrichissement avec noms de protocoles
        protocols = result["data"]
        assert protocols[0]["protocol_name"] == "TCP"
        assert protocols[1]["protocol_name"] == "UDP"
        assert protocols[2]["protocol_name"] == "ICMP"
    
    @patch('api_clients.network.netflow_client.NetflowClient.get')
    def test_detect_anomalies(self, mock_get):
        """Test la détection d'anomalies."""
        mock_get.return_value = {
            "success": True,
            "anomalies": [
                {
                    "type": "volume_spike",
                    "flow_count": 1000,
                    "baseline_flow_count": 100,
                    "timestamp": 1640995200,
                    "affected_hosts": ["192.168.1.100"]
                },
                {
                    "type": "new_destination",
                    "flow_count": 50,
                    "baseline_flow_count": 0,
                    "timestamp": 1640995300,
                    "destination": "suspicious.com"
                }
            ]
        }
        
        client = NetflowClient("http://netflow.example.com")
        
        start_time = datetime.now().timestamp() - 3600
        end_time = datetime.now().timestamp()
        
        result = client.detect_anomalies(start_time, end_time)
        
        assert result["success"] is True
        assert "anomalies" in result
        
        # Vérifier l'enrichissement des anomalies
        anomalies = result["anomalies"]
        assert len(anomalies) == 2
        
        # Première anomalie (volume spike)
        anomaly1 = anomalies[0]
        assert anomaly1["severity"] == "high"  # Ratio > 5
        assert "investigation_hints" in anomaly1
        assert any("bande passante" in hint for hint in anomaly1["investigation_hints"])
        
        # Deuxième anomalie (new destination)
        anomaly2 = anomalies[1]
        assert "investigation_hints" in anomaly2
        assert any("destination" in hint for hint in anomaly2["investigation_hints"])
    
    @patch('api_clients.network.netflow_client.NetflowClient.get')
    def test_get_traffic_matrix(self, mock_get):
        """Test la génération de matrice de trafic."""
        mock_get.return_value = {
            "success": True,
            "matrix": {
                "192.168.1.0/24": {
                    "10.0.0.0/24": 1048576,
                    "8.8.8.0/24": 524288
                }
            }
        }
        
        client = NetflowClient("http://netflow.example.com")
        
        start_time = datetime.now().timestamp() - 3600
        end_time = datetime.now().timestamp()
        
        result = client.get_traffic_matrix(start_time, end_time, subnet_mask=24)
        
        assert result["success"] is True
        assert "matrix" in result
    
    def test_get_traffic_matrix_invalid_mask(self):
        """Test la matrice de trafic avec masque invalide."""
        client = NetflowClient("http://netflow.example.com")
        
        start_time = datetime.now().timestamp() - 3600
        end_time = datetime.now().timestamp()
        
        # Masque trop petit
        result = client.get_traffic_matrix(start_time, end_time, subnet_mask=5)
        assert result["success"] is False
        
        # Masque trop grand
        result = client.get_traffic_matrix(start_time, end_time, subnet_mask=35)
        assert result["success"] is False


class TestNetflowClientEnrichment:
    """Tests pour l'enrichissement des données NetFlow."""
    
    def test_enrich_flow_data(self):
        """Test l'enrichissement des données de flux."""
        client = NetflowClient("http://netflow.example.com")
        
        response = {
            "success": True,
            "flows": [
                {
                    "src_ip": "192.168.1.1",
                    "dst_ip": "10.0.0.1",
                    "protocol": 6,
                    "bytes": 1024,
                    "first_switched": 1640995200,
                    "last_switched": 1640995260  # 60 secondes plus tard
                },
                {
                    "src_ip": "192.168.1.2",
                    "dst_ip": "10.0.0.2",
                    "protocol": 17,
                    "bytes": 512,
                    "first_switched": 1640995200,
                    "last_switched": 1640995200  # Même timestamp
                }
            ]
        }
        
        enriched = client._enrich_flow_data(response)
        
        assert enriched["success"] is True
        flows = enriched["flows"]
        
        # Premier flux
        flow1 = flows[0]
        assert flow1["protocol_name"] == "TCP"
        assert flow1["duration_seconds"] == 60
        assert "bitrate_bps" in flow1
        # bitrate = (1024 bytes * 8 bits) / 60 seconds = 136.53 bps
        assert flow1["bitrate_bps"] == pytest.approx(136.53, rel=0.1)
        
        # Deuxième flux
        flow2 = flows[1]
        assert flow2["protocol_name"] == "UDP"
        assert flow2["duration_seconds"] == 0  # Même timestamp
        # Pas de bitrate car durée = 0
        assert "bitrate_bps" not in flow2
    
    def test_enrich_top_talkers(self):
        """Test l'enrichissement des top talkers."""
        client = NetflowClient("http://netflow.example.com")
        
        response = {
            "success": True,
            "data": [
                {"ip_address": "192.168.1.1", "bytes": 1024},
                {"ip_address": "2001:db8::1", "bytes": 512},
                {"ip_address": "224.0.0.1", "bytes": 256},
                {"ip_address": "invalid_ip", "bytes": 128}
            ]
        }
        
        enriched = client._enrich_top_talkers(response)
        
        talkers = enriched["data"]
        
        # IPv4 privée
        assert talkers[0]["ip_type"] == "IPv4"
        assert talkers[0]["is_private"] is True
        assert talkers[0]["is_multicast"] is False
        
        # IPv6
        assert talkers[1]["ip_type"] == "IPv6"
        assert talkers[1]["is_private"] is False
        
        # IPv4 multicast
        assert talkers[2]["ip_type"] == "IPv4"
        assert talkers[2]["is_multicast"] is True
        
        # IP invalide - pas d'enrichissement
        assert "ip_type" not in talkers[3]
    
    def test_enrich_protocol_data(self):
        """Test l'enrichissement des données de protocoles."""
        client = NetflowClient("http://netflow.example.com")
        
        response = {
            "success": True,
            "data": [
                {"protocol_number": 6, "bytes": 1024},
                {"protocol_number": 17, "bytes": 512},
                {"protocol_number": 999, "bytes": 256}  # Protocole inconnu
            ]
        }
        
        enriched = client._enrich_protocol_data(response)
        
        protocols = enriched["data"]
        
        assert protocols[0]["protocol_name"] == "TCP"
        assert protocols[1]["protocol_name"] == "UDP"
        assert protocols[2]["protocol_name"] == "Unknown(999)"
    
    def test_enrich_anomaly_data(self):
        """Test l'enrichissement des données d'anomalies."""
        client = NetflowClient("http://netflow.example.com")
        
        response = {
            "success": True,
            "anomalies": [
                {
                    "type": "volume_spike",
                    "flow_count": 1000,
                    "baseline_flow_count": 100
                },
                {
                    "type": "volume_spike",
                    "flow_count": 300,
                    "baseline_flow_count": 100
                },
                {
                    "type": "new_destination",
                    "flow_count": 50,
                    "baseline_flow_count": 0
                },
                {
                    "type": "unknown_type",
                    "flow_count": 200,
                    "baseline_flow_count": 100
                }
            ]
        }
        
        enriched = client._enrich_anomaly_data(response)
        
        anomalies = enriched["anomalies"]
        
        # Première anomalie : ratio = 10 (high)
        assert anomalies[0]["severity"] == "high"
        
        # Deuxième anomalie : ratio = 3 (medium)
        assert anomalies[1]["severity"] == "medium"
        
        # Troisième anomalie : type new_destination
        assert "investigation_hints" in anomalies[2]
        hints = anomalies[2]["investigation_hints"]
        assert any("destination" in hint for hint in hints)
        
        # Quatrième anomalie : type inconnu, pas d'hints spéciaux
        assert "investigation_hints" not in anomalies[3]


class TestNetflowClientErrorHandling:
    """Tests pour la gestion d'erreur du client NetFlow."""
    
    def test_query_flows_validation_error(self):
        """Test la gestion d'erreur de validation."""
        client = NetflowClient("http://netflow.example.com")
        
        # IP invalide
        result = client.query_flows(
            start_time=datetime.now().timestamp() - 3600,
            end_time=datetime.now().timestamp(),
            src_ip="invalid_ip"
        )
        
        assert result["success"] is False
        assert "Paramètres invalides" in result["error"]
    
    def test_query_flows_invalid_time_range(self):
        """Test avec plage temporelle invalide."""
        client = NetflowClient("http://netflow.example.com")
        
        # Ordre inversé
        result = client.query_flows(
            start_time=datetime.now().timestamp(),
            end_time=datetime.now().timestamp() - 3600
        )
        
        assert result["success"] is False
        assert "Paramètres invalides" in result["error"]
    
    @patch('api_clients.network.netflow_client.NetflowClient.get')
    def test_query_flows_api_error(self, mock_get):
        """Test la gestion d'erreur API."""
        mock_get.side_effect = Exception("API Error")
        
        client = NetflowClient("http://netflow.example.com")
        
        result = client.query_flows(
            start_time=datetime.now().timestamp() - 3600,
            end_time=datetime.now().timestamp()
        )
        
        assert result["success"] is False
        assert "API Error" in result["error"]
    
    @patch('api_clients.network.netflow_client.NetflowClient.get')
    def test_test_connection_failure(self, mock_get):
        """Test l'échec de test de connexion."""
        mock_get.return_value = {"success": False}
        
        client = NetflowClient("http://netflow.example.com")
        
        assert client.test_connection() is False
    
    @patch('api_clients.network.netflow_client.NetflowClient.get')
    def test_test_connection_exception(self, mock_get):
        """Test l'exception lors du test de connexion."""
        mock_get.side_effect = Exception("Connection failed")
        
        client = NetflowClient("http://netflow.example.com")
        
        assert client.test_connection() is False


class TestNetflowClientPerformance:
    """Tests de performance pour le client NetFlow."""
    
    @patch('api_clients.network.netflow_client.NetflowClient.get')
    @pytest.mark.performance
    def test_query_performance(self, mock_get):
        """Test de performance des requêtes."""
        # Simuler une réponse avec beaucoup de flux
        large_response = {
            "success": True,
            "flows": [
                {
                    "src_ip": f"192.168.1.{i % 255}",
                    "dst_ip": f"10.0.0.{i % 255}",
                    "protocol": 6,
                    "bytes": 1024 + i,
                    "first_switched": 1640995200 + i,
                    "last_switched": 1640995200 + i + 60
                }
                for i in range(1000)
            ]
        }
        
        mock_get.return_value = large_response
        
        client = NetflowClient("http://netflow.example.com")
        
        start_time = time.time()
        result = client.query_flows(
            start_time=datetime.now().timestamp() - 3600,
            end_time=datetime.now().timestamp()
        )
        end_time = time.time()
        
        # Vérifier que l'enrichissement de 1000 flux reste rapide
        assert end_time - start_time < 1.0  # Moins d'1 seconde
        assert len(result["flows"]) == 1000
        assert all("protocol_name" in flow for flow in result["flows"])
    
    @patch('api_clients.network.netflow_client.NetflowClient.get')
    @pytest.mark.performance
    def test_validation_performance(self, mock_get):
        """Test de performance de la validation."""
        mock_get.return_value = {"success": True, "flows": []}
        
        client = NetflowClient("http://netflow.example.com")
        
        start_time = time.time()
        
        # Effectuer de nombreuses validations
        for _ in range(100):
            client.query_flows(
                start_time=datetime.now().timestamp() - 3600,
                end_time=datetime.now().timestamp(),
                src_ip="192.168.1.1",
                dst_ip="10.0.0.1",
                protocol="TCP"
            )
        
        end_time = time.time()
        
        # 100 validations devraient être rapides
        assert end_time - start_time < 0.5  # Moins de 500ms


class TestNetflowClientIntegration:
    """Tests d'intégration pour le client NetFlow."""
    
    @patch('api_clients.network.netflow_client.NetflowClient.get')
    def test_realistic_workflow(self, mock_get):
        """Test un workflow réaliste d'analyse NetFlow."""
        
        # Simuler différentes réponses selon l'endpoint
        def mock_get_side_effect(endpoint, params=None):
            if endpoint == "status":
                return {"success": True, "version": "1.0"}
            elif endpoint == "collector/status":
                return {"success": True, "status": "active", "flows_per_second": 1000}
            elif endpoint == "flows/query":
                return {
                    "success": True,
                    "flows": [
                        {
                            "src_ip": "192.168.1.100",
                            "dst_ip": "8.8.8.8",
                            "protocol": 6,
                            "src_port": 12345,
                            "dst_port": 80,
                            "bytes": 2048,
                            "first_switched": 1640995200,
                            "last_switched": 1640995260
                        }
                    ]
                }
            elif endpoint == "analytics/top_talkers":
                return {
                    "success": True,
                    "data": [
                        {"ip_address": "192.168.1.100", "bytes": 1048576}
                    ]
                }
            elif endpoint == "analytics/anomalies":
                return {
                    "success": True,
                    "anomalies": [
                        {
                            "type": "volume_spike",
                            "flow_count": 500,
                            "baseline_flow_count": 100
                        }
                    ]
                }
            else:
                return {"success": False, "error": "Unknown endpoint"}
        
        mock_get.side_effect = mock_get_side_effect
        
        client = NetflowClient("http://netflow.example.com")
        
        # 1. Test de connexion
        assert client.test_connection() is True
        
        # 2. Vérification du statut du collecteur
        status = client.get_collector_status()
        assert status["success"] is True
        assert status["status"] == "active"
        
        # 3. Requête de flux
        current_time = datetime.now().timestamp()
        flows = client.query_flows(
            start_time=current_time - 3600,
            end_time=current_time
        )
        assert flows["success"] is True
        assert len(flows["flows"]) == 1
        
        # 4. Analyse des top talkers
        top_talkers = client.get_top_talkers(
            start_time=current_time - 3600,
            end_time=current_time
        )
        assert top_talkers["success"] is True
        
        # 5. Détection d'anomalies
        anomalies = client.detect_anomalies(
            start_time=current_time - 3600,
            end_time=current_time
        )
        assert anomalies["success"] is True
        assert anomalies["anomalies"][0]["severity"] == "high"
    
    def test_security_parameter_validation(self):
        """Test la validation sécurisée des paramètres."""
        client = NetflowClient("http://netflow.example.com")
        
        current_time = datetime.now().timestamp()
        
        # Test injection dans IP
        result = client.query_flows(
            start_time=current_time - 3600,
            end_time=current_time,
            src_ip="192.168.1.1'; DROP TABLE flows; --"
        )
        assert result["success"] is False
        
        # Test injection dans interface
        result = client.query_flows(
            start_time=current_time - 3600,
            end_time=current_time,
            interface="eth0; rm -rf /"
        )
        assert result["success"] is False
        
        # Test port invalide
        result = client.query_flows(
            start_time=current_time - 3600,
            end_time=current_time,
            src_port=99999  # Port trop élevé
        )
        assert result["success"] is False
    
    def test_edge_cases_handling(self):
        """Test la gestion des cas limites."""
        client = NetflowClient("http://netflow.example.com")
        
        # Test avec timestamp au format ISO
        iso_time = "2022-01-01T00:00:00Z"
        future_iso = "2022-01-01T01:00:00Z"
        
        # Cette validation devrait passer
        validated = client._validate_time_range(iso_time, future_iso)
        assert 'start_time' in validated
        assert 'end_time' in validated
        
        # Test avec protocole en string numérique
        assert client._normalize_protocol("6") == 6
        
        # Test enrichissement avec données manquantes
        incomplete_response = {
            "success": True,
            "flows": [
                {"src_ip": "192.168.1.1"},  # Données incomplètes
                {"protocol": "invalid"}      # Protocole invalide
            ]
        }
        
        enriched = client._enrich_flow_data(incomplete_response)
        assert enriched["success"] is True
        assert len(enriched["flows"]) == 2 
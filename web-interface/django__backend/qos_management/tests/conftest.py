"""
Configuration pour les tests pytest du module QoS Management.
"""
import pytest
from django.conf import settings

# Configuration globale pour les tests
def pytest_configure(config):
    """Configuration globale pour pytest."""
    # Marquer tous les tests comme appartenant au module qos_management
    config.addinivalue_line("markers", "qos_management: marque les tests du module QoS Management")
    
# Fixtures communes pour les tests
@pytest.fixture
def sample_qos_policy_data():
    """Fournit des données d'exemple pour une politique QoS."""
    return {
        "name": "Politique Test",
        "description": "Description de test",
        "is_active": True,
        "traffic_classes": [
            {
                "name": "VoIP",
                "description": "Trafic VoIP",
                "dscp": "ef",
                "priority": 10,
                "min_bandwidth": 1000,
                "max_bandwidth": 5000
            },
            {
                "name": "Vidéo",
                "description": "Trafic vidéo",
                "dscp": "af41",
                "priority": 8,
                "min_bandwidth": 10000,
                "max_bandwidth": 20000
            }
        ]
    } 
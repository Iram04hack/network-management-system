"""
Configuration spécifique au module Dashboard.

Ce fichier définit les paramètres par défaut et la configuration du module Dashboard.
"""

from django.conf import settings

# Configuration par défaut du dashboard
DEFAULT_DASHBOARD_SETTINGS = {
    'CACHE_TTL': 120,  # Durée de vie du cache en secondes (2 minutes)
    'DEFAULT_UPDATE_INTERVAL': 60,  # Intervalle de mise à jour en secondes (1 minute)
    'MAX_ALERTS': 50,  # Nombre maximum d'alertes à afficher
    'NETWORK_HEALTH_THRESHOLD': {
        'CRITICAL': 0.5,  # Seuil critique pour la santé du réseau
        'WARNING': 0.8,  # Seuil d'avertissement pour la santé du réseau
    },
    'ENABLE_WEBSOCKET': True,  # Activer les mises à jour en temps réel via WebSockets
    'CUSTOM_DASHBOARDS_ENABLED': True,  # Activer les tableaux de bord personnalisés
    'DATA_RETENTION_DAYS': 30,  # Durée de conservation des données historiques en jours
    'LOG_LEVEL': 'INFO',  # Niveau de journalisation
    'ENABLE_PROMETHEUS': True,  # Activer l'intégration Prometheus
}

# Récupérer la configuration utilisateur (si définie)
USER_DASHBOARD_SETTINGS = getattr(settings, 'DASHBOARD_SETTINGS', {})

# Fusionner les configurations par défaut et utilisateur
DASHBOARD_SETTINGS = {**DEFAULT_DASHBOARD_SETTINGS, **USER_DASHBOARD_SETTINGS}

# Fonctions d'accès aux paramètres
def get_cache_ttl():
    """Récupère la durée de vie du cache."""
    return DASHBOARD_SETTINGS['CACHE_TTL']

def get_update_interval():
    """Récupère l'intervalle de mise à jour."""
    return DASHBOARD_SETTINGS['DEFAULT_UPDATE_INTERVAL']

def get_max_alerts():
    """Récupère le nombre maximum d'alertes à afficher."""
    return DASHBOARD_SETTINGS['MAX_ALERTS']

def get_network_health_thresholds():
    """Récupère les seuils de santé du réseau."""
    return DASHBOARD_SETTINGS['NETWORK_HEALTH_THRESHOLD']

def is_websocket_enabled():
    """Vérifie si les WebSockets sont activés."""
    return DASHBOARD_SETTINGS['ENABLE_WEBSOCKET']

def are_custom_dashboards_enabled():
    """Vérifie si les tableaux de bord personnalisés sont activés."""
    return DASHBOARD_SETTINGS['CUSTOM_DASHBOARDS_ENABLED']

def get_data_retention_days():
    """Récupère la durée de conservation des données historiques."""
    return DASHBOARD_SETTINGS['DATA_RETENTION_DAYS']

def get_log_level():
    """Récupère le niveau de journalisation."""
    return DASHBOARD_SETTINGS['LOG_LEVEL']

def is_prometheus_enabled():
    """Vérifie si l'intégration Prometheus est activée."""
    return DASHBOARD_SETTINGS['ENABLE_PROMETHEUS'] 
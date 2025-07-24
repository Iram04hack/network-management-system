# Dashboard module initialization 
"""
Module Dashboard pour le système de gestion de réseau.

Ce module implémente les fonctionnalités du tableau de bord
principal du système, permettant la visualisation des données
réseau, des alertes et des métriques de performance.
"""

import logging
from django.conf import settings

# Configuration du logger
logger = logging.getLogger(__name__)

# Nom de l'application pour Django
default_app_config = 'dashboard.apps.DashboardConfig'

# Valeurs par défaut pour la configuration
DEFAULT_CACHE_TTL = 300  # 5 minutes
DEFAULT_REFRESH_INTERVAL = 60  # 1 minute
DEFAULT_THEME = 'light'
DEFAULT_LAYOUT = 'grid'


def get_cache_ttl():
    """
    Récupère la durée de vie du cache depuis les paramètres.
    
    Returns:
        int: Durée de vie du cache en secondes
    """
    return getattr(settings, 'DASHBOARD_CACHE_TTL', DEFAULT_CACHE_TTL)


def get_refresh_interval():
    """
    Récupère l'intervalle de rafraîchissement depuis les paramètres.
    
    Returns:
        int: Intervalle de rafraîchissement en secondes
    """
    return getattr(settings, 'DASHBOARD_REFRESH_INTERVAL', DEFAULT_REFRESH_INTERVAL)


def get_default_theme():
    """
    Récupère le thème par défaut depuis les paramètres.
    
    Returns:
        str: Thème par défaut
    """
    return getattr(settings, 'DASHBOARD_DEFAULT_THEME', DEFAULT_THEME)


def get_default_layout():
    """
    Récupère la disposition par défaut depuis les paramètres.
    
    Returns:
        str: Disposition par défaut
    """
    return getattr(settings, 'DASHBOARD_DEFAULT_LAYOUT', DEFAULT_LAYOUT)

# Version du module
__version__ = '1.0.0'

# Rendre la configuration accessible
from .conf import (
    DASHBOARD_SETTINGS,
    get_cache_ttl,
    get_update_interval,
    get_max_alerts,
    get_network_health_thresholds,
    is_websocket_enabled,
    are_custom_dashboards_enabled,
    get_data_retention_days,
    get_log_level,
    is_prometheus_enabled
)

__all__ = [
    'DASHBOARD_SETTINGS',
    'get_cache_ttl',
    'get_update_interval',
    'get_max_alerts',
    'get_network_health_thresholds',
    'is_websocket_enabled',
    'are_custom_dashboards_enabled',
    'get_data_retention_days',
    'get_log_level',
    'is_prometheus_enabled'
] 
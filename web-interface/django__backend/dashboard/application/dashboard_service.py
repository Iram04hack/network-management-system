"""
Implémentation du service de données du tableau de bord.

Ce module fournit une implémentation du service de données du tableau de bord
qui utilise les adaptateurs pour le monitoring et le réseau.
"""

import logging
from typing import Dict, Any, List, Optional

from ..domain.interfaces import IDashboardDataService, IMonitoringDataProvider, INetworkDataProvider

logger = logging.getLogger(__name__)


class DashboardDataServiceHexagonal(IDashboardDataService):
    """
    Implémentation du service de données du tableau de bord suivant l'architecture hexagonale.
    
    Cette classe utilise des fournisseurs de données injectés pour récupérer
    les informations nécessaires au tableau de bord.
    """
    
    def __init__(
        self,
        monitoring_provider: IMonitoringDataProvider,
        network_provider: INetworkDataProvider
    ):
        """
        Initialise le service avec les fournisseurs de données.
        
        Args:
            monitoring_provider: Fournisseur de données de monitoring
            network_provider: Fournisseur de données réseau
        """
        self._monitoring_provider = monitoring_provider
        self._network_provider = network_provider
    
    def get_dashboard_overview(self) -> Dict[str, Any]:
        """
        Récupère les données de vue d'ensemble pour le tableau de bord.
        
        Returns:
            Dictionnaire contenant les données agrégées du tableau de bord
        """
        try:
            # Récupérer les données de réseau
            device_stats = self._network_provider.get_device_summary()
            
            # Récupérer les alertes récentes
            security_alerts = self._get_security_alerts()
            system_alerts = self._monitoring_provider.get_system_alerts(limit=5)
            
            # Récupérer les métriques de performances
            performance_metrics = self._monitoring_provider.get_performance_metrics()
            
            return {
                'devices': device_stats,
                'security_alerts': security_alerts,
                'system_alerts': system_alerts,
                'performance': performance_metrics,
                'health_metrics': self.get_system_health_metrics(),
                'qos_summary': self._network_provider.get_qos_summary()
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données du tableau de bord: {str(e)}", exc_info=True)
            return {
                'devices': {},
                'security_alerts': [],
                'system_alerts': [],
                'performance': {},
                'health_metrics': self.get_system_health_metrics(),
                'qos_summary': {}
            }
    
    def get_system_health_metrics(self) -> Dict[str, float]:
        """
        Récupère les métriques de santé du système.
        
        Returns:
            Dictionnaire contenant les métriques de santé système
        """
        try:
            # Récupérer les statistiques d'équipements
            device_stats = self._network_provider.get_device_summary()
            total_devices = device_stats.get('total', 0)
            
            if total_devices == 0:
                return {'system_health': 0, 'network_health': 0, 'security_health': 0}
            
            # Santé du réseau basée sur le statut des équipements
            healthy_devices = device_stats.get('active', 0)
            warning_devices = device_stats.get('warning', 0)
            
            # Formule pondérée: les équipements en warning comptent pour moitié
            network_health = (healthy_devices + warning_devices * 0.5) / total_devices if total_devices > 0 else 0
            
            # Récupérer les alertes pour calculer la santé de la sécurité
            security_alerts = self._get_security_alerts()
            total_alerts = len(security_alerts)
            
            # Plus il y a d'alertes, plus le score est bas (formule arbitraire)
            security_health = 1.0 / (1 + 0.1 * total_alerts) if total_alerts else 1.0
            
            # Combiner les scores
            system_health = (network_health * 0.6) + (security_health * 0.4)
            
            return {
                'system_health': round(system_health, 2),
                'network_health': round(network_health, 2),
                'security_health': round(security_health, 2)
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des métriques de santé: {str(e)}", exc_info=True)
            return {
                'system_health': 0.5,  # Valeurs par défaut
                'network_health': 0.5,
                'security_health': 0.5
            }
    
    def _get_security_alerts(self) -> List[Dict[str, Any]]:
        """
        Récupère les alertes de sécurité.
        
        Dans une implémentation complète, cela pourrait venir d'un autre adaptateur
        dédié à la sécurité.
        
        Returns:
            Liste des alertes de sécurité
        """
        # Dans cet exemple, nous utilisons simplement les alertes système
        # qui correspondent à la catégorie "security"
        system_alerts = self._monitoring_provider.get_system_alerts(limit=10)
        
        # Filtrer pour ne garder que les alertes de sécurité
        return [
            alert for alert in system_alerts 
            if 'security' in alert.get('metric_name', '').lower() or 
               'security' in alert.get('message', '').lower()
        ]
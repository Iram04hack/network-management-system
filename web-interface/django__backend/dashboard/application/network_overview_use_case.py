"""
Cas d'utilisation pour la vue d'ensemble du réseau.

Ce module fournit un cas d'utilisation pour obtenir une vue d'ensemble
consolidée du réseau à travers les différents adaptateurs.
"""

import logging
from typing import Dict, Any, List, Optional

from ..domain.interfaces import INetworkDataProvider, IMonitoringDataProvider

logger = logging.getLogger(__name__)


class GetNetworkOverviewUseCase:
    """
    Cas d'utilisation pour obtenir une vue d'ensemble du réseau.
    
    Ce cas d'utilisation coordonne l'accès aux données de plusieurs fournisseurs
    pour construire une vue d'ensemble complète du réseau.
    """
    
    def __init__(
        self,
        network_provider: INetworkDataProvider,
        monitoring_provider: IMonitoringDataProvider
    ):
        """
        Initialise le cas d'utilisation avec les fournisseurs de données.
        
        Args:
            network_provider: Fournisseur de données réseau
            monitoring_provider: Fournisseur de données de monitoring
        """
        self._network_provider = network_provider
        self._monitoring_provider = monitoring_provider
    
    def execute(self) -> Dict[str, Any]:
        """
        Exécute le cas d'utilisation pour obtenir la vue d'ensemble du réseau.
        
        Returns:
            Dictionnaire contenant la vue d'ensemble du réseau
        """
        try:
            # Récupérer les informations sur les équipements
            device_summary = self._network_provider.get_device_summary()
            
            # Récupérer les informations sur les interfaces
            interface_summary = self._network_provider.get_interface_summary()
            
            # Récupérer les informations sur les politiques QoS
            qos_summary = self._network_provider.get_qos_summary()
            
            # Récupérer les alertes réseau récentes
            network_alerts = self._monitoring_provider.get_system_alerts(
                limit=10, 
                status_filter=['new', 'acknowledged']
            )
            
            # Filtrer pour ne garder que les alertes réseau
            network_alerts = [
                alert for alert in network_alerts
                if 'network' in alert.get('metric_name', '').lower() or
                   'interface' in alert.get('metric_name', '').lower() or
                   'bandwidth' in alert.get('metric_name', '').lower() or
                   'latency' in alert.get('metric_name', '').lower()
            ]
            
            # Construire la vue d'ensemble
            return {
                'devices': device_summary,
                'interfaces': interface_summary,
                'qos': qos_summary,
                'alerts': network_alerts,
                'health_indicators': self._calculate_health_indicators(
                    device_summary,
                    interface_summary,
                    network_alerts
                )
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la vue d'ensemble du réseau: {str(e)}", exc_info=True)
            return {
                'devices': {},
                'interfaces': {},
                'qos': {},
                'alerts': [],
                'health_indicators': {
                    'network_health': 0.5,
                    'critical_alerts_count': 0,
                    'degraded_interfaces_percentage': 0
                }
            }
    
    def _calculate_health_indicators(
        self,
        device_summary: Dict[str, Any],
        interface_summary: Dict[str, Any],
        alerts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calcule les indicateurs de santé du réseau.
        
        Args:
            device_summary: Résumé des équipements
            interface_summary: Résumé des interfaces
            alerts: Liste des alertes réseau
            
        Returns:
            Dictionnaire contenant les indicateurs de santé
        """
        # Calculer la santé du réseau basée sur le statut des équipements
        total_devices = device_summary.get('total', 0)
        healthy_devices = device_summary.get('active', 0)
        warning_devices = device_summary.get('warning', 0)
        
        # Formule pondérée: les équipements en warning comptent pour moitié
        network_health = (healthy_devices + warning_devices * 0.5) / total_devices if total_devices > 0 else 0
        
        # Compter les alertes critiques
        critical_alerts = [alert for alert in alerts if alert.get('severity') == 'critical']
        
        # Calculer le pourcentage d'interfaces dégradées
        total_interfaces = interface_summary.get('total', 0)
        down_interfaces = interface_summary.get('down', 0)
        degraded_interfaces_percentage = (down_interfaces / total_interfaces * 100) if total_interfaces > 0 else 0
        
        return {
            'network_health': round(network_health, 2),
            'critical_alerts_count': len(critical_alerts),
            'degraded_interfaces_percentage': round(degraded_interfaces_percentage, 2)
        }
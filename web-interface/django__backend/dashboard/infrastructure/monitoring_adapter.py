"""
Adaptateur de monitoring pour le module Dashboard.

Ce fichier implémente l'interface IMonitoringDataProvider pour
connecter le tableau de bord aux données de surveillance du système.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from django.db.models import Q, Count, Avg
from asgiref.sync import sync_to_async

from django.conf import settings
from django.utils import timezone

# Import des vrais modèles Django
from monitoring.models import Alert, DeviceMetric, MetricValue
# from network_management.models import NetworkDevice  # Temporairement désactivé

from ..domain.interfaces import IMonitoringDataProvider
from ..domain.entities import AlertInfo, AlertSeverity, SystemHealthMetrics

logger = logging.getLogger(__name__)


class MonitoringAdapter(IMonitoringDataProvider):
    """
    Adaptateur connectant le tableau de bord au système de surveillance.
    
    Cette classe implémente l'interface IMonitoringDataProvider pour récupérer
    les données de surveillance et les convertir en entités du domaine dashboard.
    """
    
    def __init__(self):
        """Initialise l'adaptateur de monitoring."""
        # On utilisera ces services pour récupérer des données réelles
        # dans une implémentation ultérieure
        self._monitoring_service = None
        self._alert_service = None
        self._metrics_service = None
        
        # Essayer d'importer les services si disponibles
        try:
            from monitoring.services import MonitoringService
            from security_management.services import AlertService
            from reporting.services import MetricsService
            
            # On les initialiserait ici dans une implémentation complète
            # self._monitoring_service = MonitoringService()
            # self._alert_service = AlertService()
            # self._metrics_service = MetricsService()
            logger.info("Services de monitoring importés avec succès")
        except ImportError:
            logger.warning("Services de monitoring non disponibles. Utilisation de données simulées.")
            
    async def get_system_alerts(self, limit: int = 5, status_filter: Optional[List[str]] = None) -> List[AlertInfo]:
        """
        Récupère les alertes système récentes depuis la base de données réelle.

        Args:
            limit: Nombre maximum d'alertes à récupérer
            status_filter: Liste des statuts pour filtrer les alertes

        Returns:
            Liste des alertes système
        """
        try:
            logger.info(f"Récupération des alertes réelles depuis la base de données (limit: {limit})")

            # Construire la requête avec filtres
            query = Alert.objects.select_related('device')

            if status_filter:
                query = query.filter(status__in=status_filter)

            # Récupérer les alertes récentes
            alerts_data = await sync_to_async(
                lambda: list(query.order_by('-created_at')[:limit])
            )()

            # Convertir en objets AlertInfo
            alerts = []
            for alert_obj in alerts_data:
                # Mapper les sévérités
                severity_mapping = {
                    'critical': AlertSeverity.CRITICAL,
                    'high': AlertSeverity.HIGH,
                    'medium': AlertSeverity.MEDIUM,
                    'low': AlertSeverity.LOW,
                    'info': AlertSeverity.LOW
                }

                severity = severity_mapping.get(alert_obj.severity, AlertSeverity.MEDIUM)

                alert_info = AlertInfo(
                    id=alert_obj.id,
                    message=alert_obj.message,
                    severity=severity,
                    timestamp=alert_obj.created_at,
                    status=alert_obj.status,
                    source=f"monitoring.{alert_obj.alert_type}",
                    metric_name=alert_obj.metric_name,
                    affected_devices=[alert_obj.device.id] if alert_obj.device else []
                )
                alerts.append(alert_info)

            logger.info(f"Alertes réelles récupérées: {len(alerts)} alertes")
            return alerts

        except Exception as e:
            logger.error(f"Erreur lors de la récupération des alertes système: {e}")
            # Fallback vers des données simulées en cas d'erreur
            logger.warning("Fallback vers des données simulées")
            return await self._get_simulated_alerts(limit, "system", status_filter)
    
    async def get_performance_metrics(self, time_range: Optional[Tuple[datetime, datetime]] = None) -> Dict[str, Any]:
        """
        Récupère les données de performance agrégées.
        
        Args:
            time_range: Plage de temps pour les métriques (début, fin)
            
        Returns:
            Dictionnaire contenant les métriques de performance
        """
        try:
            # Dans une implémentation réelle, on récupérerait les métriques depuis le service
            # if self._metrics_service:
            #     return await self._metrics_service.get_aggregated_metrics(time_range=time_range)
            
            # Utilisation temporaire de données simulées
            return await self._get_simulated_performance_metrics(time_range)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des métriques de performance: {e}")
            return {}
    
    async def get_device_metrics(self, device_id: int) -> Dict[str, Any]:
        """
        Récupère les métriques spécifiques à un équipement depuis la base de données réelle.

        Args:
            device_id: ID de l'équipement

        Returns:
            Dictionnaire contenant les métriques de l'équipement
        """
        try:
            logger.info(f"Récupération des métriques réelles pour l'équipement {device_id}")

            # Vérifier que l'équipement existe
            device_exists = await sync_to_async(
                lambda: NetworkDevice.objects.filter(id=device_id).exists()
            )()

            if not device_exists:
                logger.warning(f"Équipement {device_id} non trouvé")
                return {"error": f"Device {device_id} not found"}

            # Récupérer les métriques récentes pour cet équipement
            device_metrics = await sync_to_async(
                lambda: list(DeviceMetric.objects.filter(device_id=device_id).select_related('metric_definition'))
            )()

            # Récupérer les valeurs les plus récentes pour chaque métrique
            metrics_data = {}
            for device_metric in device_metrics:
                latest_value = await sync_to_async(
                    lambda dm=device_metric: MetricValue.objects.filter(device_metric=dm).order_by('-timestamp').first()
                )()

                if latest_value:
                    metric_name = device_metric.metric_definition.name
                    metrics_data[metric_name] = {
                        'value': latest_value.value,
                        'timestamp': latest_value.timestamp.isoformat(),
                        'unit': device_metric.metric_definition.unit
                    }

            # Normaliser les noms de métriques pour compatibilité
            normalized_metrics = {}
            metric_mapping = {
                'cpu_utilization': 'cpu_usage',
                'memory_utilization': 'memory_usage',
                'disk_utilization': 'disk_usage',
                'temperature': 'temperature',
                'uptime': 'uptime',
                'interface_throughput': 'throughput_mbps'
            }

            for original_name, normalized_name in metric_mapping.items():
                if original_name in metrics_data:
                    normalized_metrics[normalized_name] = metrics_data[original_name]['value']
                else:
                    # Valeur par défaut si la métrique n'est pas disponible
                    normalized_metrics[normalized_name] = 0

            # Ajouter des métadonnées
            normalized_metrics.update({
                "last_update": timezone.now().isoformat(),
                "data_source": "real_database",
                "metrics_count": len(metrics_data)
            })

            logger.info(f"Métriques réelles récupérées pour l'équipement {device_id}: {len(metrics_data)} métriques")
            return normalized_metrics

        except Exception as e:
            logger.error(f"Erreur lors de la récupération des métriques de l'équipement {device_id}: {e}")
            # Fallback vers des données simulées
            logger.warning("Fallback vers des données simulées")
            return {
                "cpu_usage": round(35 + (device_id % 10) * 5, 1),
                "memory_usage": round(45 + (device_id % 15) * 2, 1),
                "disk_usage": round(30 + (device_id % 20), 1),
                "temperature": 40 + (device_id % 5) * 2,
                "uptime": 86400 * (3 + (device_id % 10)),
                "throughput_mbps": 120 + (device_id % 100) * 5,
                "last_update": timezone.now().isoformat(),
                "data_source": "simulated_fallback"
            }
    
    async def get_system_health_metrics(self) -> SystemHealthMetrics:
        """
        Récupère les métriques de santé du système depuis les données réelles.

        Returns:
            Objet contenant les métriques de santé système
        """
        try:
            logger.info("Calcul des métriques de santé système depuis les données réelles")

            # Calculer la santé système basée sur les alertes actives
            total_devices = await sync_to_async(NetworkDevice.objects.count)()
            if total_devices == 0:
                logger.warning("Aucun équipement trouvé, utilisation de valeurs par défaut")
                return SystemHealthMetrics(
                    system_health=0.8,
                    network_health=0.8,
                    security_health=0.8
                )

            # Santé système basée sur les alertes critiques
            critical_alerts = await sync_to_async(
                lambda: Alert.objects.filter(severity='critical', status='active').count()
            )()

            high_alerts = await sync_to_async(
                lambda: Alert.objects.filter(severity='high', status='active').count()
            )()

            # Calculer le score de santé système (0.0 à 1.0)
            # Formule: 1.0 - (critical_alerts * 0.1 + high_alerts * 0.05) / total_devices
            system_health = max(0.0, 1.0 - (critical_alerts * 0.1 + high_alerts * 0.05) / max(total_devices, 1))

            # Santé réseau basée sur le statut des équipements
            active_devices = await sync_to_async(
                lambda: NetworkDevice.objects.filter(status='active').count()
            )()

            network_health = active_devices / total_devices if total_devices > 0 else 0.8

            # Santé sécurité basée sur les alertes de sécurité
            security_alerts = await sync_to_async(
                lambda: Alert.objects.filter(
                    Q(alert_type__icontains='security') | Q(message__icontains='security'),
                    status='active'
                ).count()
            )()

            security_health = max(0.0, 1.0 - (security_alerts * 0.05) / max(total_devices, 1))

            # S'assurer que les valeurs sont dans la plage [0.0, 1.0]
            system_health = min(1.0, max(0.0, system_health))
            network_health = min(1.0, max(0.0, network_health))
            security_health = min(1.0, max(0.0, security_health))

            result = SystemHealthMetrics(
                system_health=round(system_health, 2),
                network_health=round(network_health, 2),
                security_health=round(security_health, 2)
            )

            logger.info(f"Métriques de santé calculées: système={result.system_health}, réseau={result.network_health}, sécurité={result.security_health}")
            return result

        except Exception as e:
            logger.error(f"Erreur lors de la récupération des métriques de santé: {e}")
            # Valeurs par défaut en cas d'erreur
            return SystemHealthMetrics(
                system_health=0.8,
                network_health=0.8,
                security_health=0.8
            )

    async def get_network_alerts(self, limit: int = 5) -> List[AlertInfo]:
        """
        Récupère les alertes réseau spécifiques depuis la base de données réelle.

        Args:
            limit: Nombre maximum d'alertes à récupérer

        Returns:
            Liste des alertes réseau
        """
        try:
            logger.info(f"Récupération des alertes réseau réelles (limit: {limit})")

            # Récupérer les alertes liées au réseau
            network_alerts = await sync_to_async(
                lambda: list(Alert.objects.filter(
                    Q(alert_type__icontains='network') |
                    Q(message__icontains='network') |
                    Q(message__icontains='interface') |
                    Q(message__icontains='link')
                ).select_related('device').order_by('-created_at')[:limit])
            )()

            # Convertir en objets AlertInfo
            alerts = []
            for alert_obj in network_alerts:
                severity_mapping = {
                    'critical': AlertSeverity.CRITICAL,
                    'high': AlertSeverity.HIGH,
                    'medium': AlertSeverity.MEDIUM,
                    'low': AlertSeverity.LOW,
                    'info': AlertSeverity.LOW
                }

                severity = severity_mapping.get(alert_obj.severity, AlertSeverity.MEDIUM)

                alert_info = AlertInfo(
                    id=alert_obj.id,
                    message=alert_obj.message,
                    severity=severity,
                    timestamp=alert_obj.created_at,
                    status=alert_obj.status,
                    source="network.monitoring",
                    metric_name=alert_obj.metric_name,
                    affected_devices=[alert_obj.device.id] if alert_obj.device else []
                )
                alerts.append(alert_info)

            logger.info(f"Alertes réseau réelles récupérées: {len(alerts)} alertes")
            return alerts

        except Exception as e:
            logger.error(f"Erreur lors de la récupération des alertes réseau: {e}")
            # Fallback vers des données simulées
            return await self._get_simulated_alerts(limit, "network", None)

    # Méthodes privées pour générer des données simulées
    
    async def _get_simulated_alerts(self, limit: int, alert_type: str, status_filter: Optional[List[str]] = None) -> List[AlertInfo]:
        """Génère des alertes simulées pour les tests."""
        # Les statuts par défaut si aucun filtre n'est fourni
        statuses = status_filter or ["active", "acknowledged", "resolved"]
        
        # Simuler un délai réseau réaliste
        await asyncio.sleep(0.1)
        
        alerts = []
        base_time = timezone.now()
        
        severity_options = [AlertSeverity.LOW, AlertSeverity.MEDIUM, AlertSeverity.HIGH, AlertSeverity.CRITICAL]
        type_prefix = "System" if alert_type == "system" else "Security"
        
        for i in range(limit):
            severity = severity_options[i % len(severity_options)]
            status = statuses[i % len(statuses)]
            
            alert = AlertInfo(
                id=1000 + i,
                message=f"{type_prefix} alert: {severity.value.capitalize()} issue detected",
                severity=severity,
                timestamp=base_time - timedelta(minutes=i*15),
                status=status,
                source=f"monitoring.{alert_type}",
                metric_name=f"{alert_type}.health" if i % 2 == 0 else None,
                affected_devices=[100 + i, 200 + i] if i % 3 == 0 else []
            )
            alerts.append(alert)
        
        return alerts
    
    async def _get_simulated_performance_metrics(self, time_range: Optional[Tuple[datetime, datetime]] = None) -> Dict[str, Any]:
        """Génère des métriques de performance simulées pour les tests."""
        # Simuler un délai réseau réaliste
        await asyncio.sleep(0.2)
        
        # Utiliser la plage de temps si fournie, sinon utiliser les dernières 24 heures
        if time_range:
            start_time, end_time = time_range
        else:
            end_time = timezone.now()
            start_time = end_time - timedelta(hours=24)
        
        # Générer des points de données toutes les heures dans la plage
        time_points = []
        current = start_time
        while current <= end_time:
            time_points.append(current)
            current += timedelta(hours=1)
        
        # Simuler des métriques de CPU, mémoire et réseau
        import random
        
        cpu_usage = [round(random.uniform(30, 85), 1) for _ in time_points]
        memory_usage = [round(random.uniform(40, 75), 1) for _ in time_points]
        network_throughput = [round(random.uniform(100, 500), 1) for _ in time_points]
        
        return {
            "time_points": [t.isoformat() for t in time_points],
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "network_throughput": network_throughput,
            "average_cpu": round(sum(cpu_usage) / len(cpu_usage), 1),
            "average_memory": round(sum(memory_usage) / len(memory_usage), 1),
            "average_network": round(sum(network_throughput) / len(network_throughput), 1),
            "peak_cpu": max(cpu_usage),
            "peak_memory": max(memory_usage),
            "peak_network": max(network_throughput),
        } 
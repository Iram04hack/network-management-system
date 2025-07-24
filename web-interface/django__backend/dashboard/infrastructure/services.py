"""
Services d'infrastructure pour le module Dashboard.
Ce fichier implémente les services de données utilisés par les cas d'utilisation
pour récupérer et traiter les données du tableau de bord.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from django.utils import timezone

from ..domain.interfaces import IDashboardDataService, INetworkOverviewService, ITopologyVisualizationService
from ..domain.entities import (
    SystemHealthMetrics,
    DashboardOverview,
    NetworkOverview,
    TopologyView,
    DeviceStatus,
    ConnectionStatus
)

logger = logging.getLogger(__name__)

class DashboardDataServiceImpl(IDashboardDataService):
    """
    Implémentation du service de données pour le tableau de bord.
    """

    def __init__(self, network_service, monitoring_service, cache_service):
        self._network_service = network_service
        self._monitoring_service = monitoring_service
        self._cache_service = cache_service

    async def get_dashboard_overview(self, user_id: Optional[int] = None) -> DashboardOverview:
        """
        Récupère les données de vue d'ensemble pour le tableau de bord.

        Args:
            user_id: ID de l'utilisateur pour personnalisation

        Returns:
            Objet contenant les données agrégées du tableau de bord
        """
        # Récupérer les données réseau
        device_summary = await self._network_service.get_device_summary()
        interface_summary = await self._network_service.get_interface_summary()

        # Récupérer les données de monitoring
        alerts = await self._network_service.get_network_alerts(limit=10)

        # Créer l'objet DashboardOverview selon les entités du domaine
        from ..domain.entities import DashboardOverview, SystemHealthMetrics, AlertInfo
        from datetime import datetime
        
        # Convertir les alertes en liste d'AlertInfo si nécessaire
        alert_infos = []
        for alert in alerts:
            if hasattr(alert, 'to_dict'):
                # Déjà un objet AlertInfo
                alert_infos.append(alert)
            else:
                # Créer un AlertInfo à partir des données brutes
                try:
                    from ..domain.entities import AlertSeverity
                    alert_info = AlertInfo(
                        id=getattr(alert, 'id', 0),
                        message=str(alert),
                        severity=AlertSeverity.MEDIUM,  # Par défaut
                        timestamp=datetime.now(),
                        status='active'
                    )
                    alert_infos.append(alert_info)
                except Exception:
                    continue

        # Créer les métriques de santé système avec les bons paramètres
        system_health = SystemHealthMetrics(
            system_health=0.85,  # Valeur entre 0 et 1
            network_health=0.90,
            security_health=0.78
        )

        # Créer l'objet DashboardOverview selon la définition dans entities.py
        return DashboardOverview(
            devices={
                'total': device_summary.get('total', 0),
                'active': device_summary.get('active', 0),
                'inactive': device_summary.get('total', 0) - device_summary.get('active', 0)
            },
            security_alerts=alert_infos[:5],  # Limiter à 5 alertes
            system_alerts=[],  # Pas d'alertes système pour l'instant
            performance={
                'cpu_usage': 85.0,
                'memory_usage': 72.0,
                'disk_usage': 45.0,
                'network_load': 60.0
            },
            health_metrics=system_health,
            timestamp=datetime.now()
        )

    async def get_user_dashboard_config(self, user_id: int) -> Dict[str, Any]:
        """
        Récupère la configuration du tableau de bord d'un utilisateur.

        Args:
            user_id: ID de l'utilisateur

        Returns:
            Configuration du tableau de bord
        """
        # Utiliser le cache si disponible
        cache_key = f"dashboard_config_{user_id}"
        cached_config = await self._cache_service.get(cache_key)

        if cached_config:
            return cached_config

        # Récupérer depuis la base de données
        from ..models import UserDashboardConfig
        try:
            config = UserDashboardConfig.objects.get(user_id=user_id)
            config_data = {
                'theme': config.theme,
                'layout': config.layout,
                'widgets': config.widgets,
                'refresh_interval': config.refresh_interval
            }

            # Mettre en cache
            await self._cache_service.set(cache_key, config_data, ttl=3600)
            return config_data

        except UserDashboardConfig.DoesNotExist:
            # Configuration par défaut
            default_config = {
                'theme': 'light',
                'layout': 'grid',
                'widgets': [],
                'refresh_interval': 30
            }
            return default_config

    async def save_user_dashboard_config(self, user_id: int, config: Dict[str, Any]) -> bool:
        """
        Sauvegarde la configuration du tableau de bord d'un utilisateur.

        Args:
            user_id: ID de l'utilisateur
            config: Configuration à sauvegarder

        Returns:
            True si la sauvegarde a réussi
        """
        try:
            from ..models import UserDashboardConfig
            from django.contrib.auth import get_user_model

            User = get_user_model()
            user = User.objects.get(id=user_id)

            config_obj, created = UserDashboardConfig.objects.get_or_create(
                user=user,
                defaults={
                    'theme': config.get('theme', 'light'),
                    'layout': config.get('layout', 'grid'),
                    'widgets': config.get('widgets', []),
                    'refresh_interval': config.get('refresh_interval', 30)
                }
            )

            if not created:
                config_obj.theme = config.get('theme', config_obj.theme)
                config_obj.layout = config.get('layout', config_obj.layout)
                config_obj.widgets = config.get('widgets', config_obj.widgets)
                config_obj.refresh_interval = config.get('refresh_interval', config_obj.refresh_interval)
                config_obj.save()

            # Invalider le cache
            cache_key = f"dashboard_config_{user_id}"
            await self._cache_service.invalidate(cache_key)

            return True

        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de la configuration: {e}")
            return False

    async def get_custom_dashboard(self, dashboard_id: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Récupère les données d'un tableau de bord personnalisé.

        Args:
            dashboard_id: ID du tableau de bord personnalisé
            user_id: ID de l'utilisateur (optionnel)

        Returns:
            Dictionnaire contenant les données du tableau de bord personnalisé
        """
        try:
            # Utiliser le cache si disponible
            cache_key = f"custom_dashboard_{dashboard_id}_{user_id or 'anonymous'}"
            cached_dashboard = await self._cache_service.get(cache_key)

            if cached_dashboard:
                return cached_dashboard

            # Récupérer depuis la base de données
            from ..models import CustomDashboard

            dashboard = CustomDashboard.objects.get(id=dashboard_id)

            # Vérifier les permissions si un utilisateur est spécifié
            if user_id and dashboard.user_id != user_id and not dashboard.is_public:
                raise PermissionError("Accès non autorisé à ce tableau de bord")

            dashboard_data = {
                'id': str(dashboard.id),
                'name': dashboard.name,
                'description': dashboard.description,
                'config': dashboard.config,
                'layout': dashboard.layout,
                'widgets': dashboard.widgets,
                'is_public': dashboard.is_public,
                'created_at': dashboard.created_at.isoformat(),
                'updated_at': dashboard.updated_at.isoformat()
            }

            # Mettre en cache pour 10 minutes
            await self._cache_service.set(cache_key, dashboard_data, ttl=600)

            return dashboard_data

        except CustomDashboard.DoesNotExist:
            logger.warning(f"Tableau de bord personnalisé {dashboard_id} non trouvé")
            return {}
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du tableau de bord {dashboard_id}: {e}")
            return {}

    async def save_custom_dashboard(self, dashboard_id: str, config: Dict[str, Any],
                                  user_id: int) -> Dict[str, Any]:
        """
        Enregistre la configuration d'un tableau de bord personnalisé.

        Args:
            dashboard_id: ID du tableau de bord personnalisé
            config: Configuration à sauvegarder
            user_id: ID de l'utilisateur

        Returns:
            Dictionnaire contenant les informations du tableau de bord sauvegardé
        """
        try:
            from ..models import CustomDashboard
            from django.contrib.auth import get_user_model
            import uuid

            User = get_user_model()
            user = User.objects.get(id=user_id)

            # Si dashboard_id est 'new', créer un nouveau tableau de bord
            if dashboard_id == 'new':
                dashboard = CustomDashboard.objects.create(
                    user=user,
                    name=config.get('name', 'Nouveau tableau de bord'),
                    description=config.get('description', ''),
                    config=config.get('config', {}),
                    layout=config.get('layout', 'grid'),
                    widgets=config.get('widgets', []),
                    is_public=config.get('is_public', False)
                )
                dashboard_id = str(dashboard.id)
            else:
                # Mettre à jour un tableau de bord existant
                dashboard = CustomDashboard.objects.get(id=dashboard_id, user=user)
                dashboard.name = config.get('name', dashboard.name)
                dashboard.description = config.get('description', dashboard.description)
                dashboard.config = config.get('config', dashboard.config)
                dashboard.layout = config.get('layout', dashboard.layout)
                dashboard.widgets = config.get('widgets', dashboard.widgets)
                dashboard.is_public = config.get('is_public', dashboard.is_public)
                dashboard.save()

            # Invalider le cache
            cache_key = f"custom_dashboard_{dashboard_id}_{user_id}"
            await self._cache_service.invalidate(cache_key)

            return {
                'id': str(dashboard.id),
                'name': dashboard.name,
                'description': dashboard.description,
                'config': dashboard.config,
                'layout': dashboard.layout,
                'widgets': dashboard.widgets,
                'is_public': dashboard.is_public,
                'created_at': dashboard.created_at.isoformat(),
                'updated_at': dashboard.updated_at.isoformat(),
                'success': True
            }

        except CustomDashboard.DoesNotExist:
            logger.error(f"Tableau de bord {dashboard_id} non trouvé pour l'utilisateur {user_id}")
            return {'success': False, 'error': 'Tableau de bord non trouvé'}
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du tableau de bord {dashboard_id}: {e}")
            return {'success': False, 'error': str(e)}


class NetworkOverviewServiceImpl(INetworkOverviewService):
    """
    Implémentation du service de vue d'ensemble du réseau.
    """

    def __init__(self, network_service, monitoring_service, cache_service):
        self._network_service = network_service
        self._monitoring_service = monitoring_service
        self._cache_service = cache_service

    async def get_network_overview(self) -> NetworkOverview:
        """
        Récupère une vue d'ensemble du réseau avec les informations de santé.

        Returns:
            Objet contenant les informations sur les équipements, interfaces et alertes
        """
        # Récupérer les données depuis les adaptateurs
        device_summary = await self._network_service.get_device_summary()
        interface_summary = await self._network_service.get_interface_summary()
        qos_summary = await self._network_service.get_qos_summary()
        alerts = await self._network_service.get_network_alerts(limit=5)

        # Créer l'objet NetworkOverview selon les entités du domaine
        from ..domain.entities import NetworkOverview, AlertInfo, AlertSeverity
        from datetime import datetime
        
        # Convertir les alertes en liste d'AlertInfo si nécessaire
        alert_infos = []
        for alert in alerts:
            if hasattr(alert, 'to_dict'):
                # Déjà un objet AlertInfo
                alert_infos.append(alert)
            else:
                # Créer un AlertInfo à partir des données brutes
                try:
                    alert_info = AlertInfo(
                        id=getattr(alert, 'id', 0),
                        message=str(alert),
                        severity=AlertSeverity.MEDIUM,  # Par défaut
                        timestamp=datetime.now(),
                        status='active'
                    )
                    alert_infos.append(alert_info)
                except Exception:
                    continue

        # Créer l'objet NetworkOverview selon la définition dans entities.py
        return NetworkOverview(
            devices={
                'total': device_summary.get('total', 0),
                'active': device_summary.get('active', 0),
                'inactive': device_summary.get('inactive', 0)
            },
            interfaces={
                'total': interface_summary.get('total', 0),
                'active': interface_summary.get('active', 0),
                'down': interface_summary.get('down', 0)
            },
            qos={
                'total_policies': qos_summary.get('total', 0),
                'active_policies': qos_summary.get('active', 0)
            },
            alerts=alert_infos[:5],  # Limiter à 5 alertes
            timestamp=datetime.now()
        )

    async def get_network_stats(self, time_range: Optional[Tuple[datetime, datetime]] = None) -> Dict[str, Any]:
        """
        Récupère des statistiques réseau pour une période donnée.

        Args:
            time_range: Plage de temps pour les statistiques (début, fin)

        Returns:
            Dictionnaire contenant les statistiques réseau
        """
        from datetime import datetime, timedelta

        # Définir la plage de temps par défaut (dernières 24h)
        if time_range is None:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)
            time_range = (start_time, end_time)

        start_time, end_time = time_range

        # Récupérer les statistiques depuis le monitoring
        try:
            # Utiliser le cache si disponible
            cache_key = f"network_stats_{start_time.isoformat()}_{end_time.isoformat()}"
            cached_stats = await self._cache_service.get(cache_key)

            if cached_stats:
                return cached_stats

            # Calculer les statistiques
            stats = {
                'time_range': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat()
                },
                'device_availability': await self._calculate_device_availability(start_time, end_time),
                'interface_utilization': await self._calculate_interface_utilization(start_time, end_time),
                'alert_summary': await self._get_alert_summary(start_time, end_time),
                'performance_metrics': await self._get_performance_metrics(start_time, end_time)
            }

            # Mettre en cache pour 5 minutes
            await self._cache_service.set(cache_key, stats, ttl=300)
            return stats

        except Exception as e:
            logger.error(f"Erreur lors du calcul des statistiques réseau: {e}")
            return {
                'time_range': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat()
                },
                'error': 'Impossible de récupérer les statistiques'
            }

    async def _calculate_device_availability(self, start_time: datetime, end_time: datetime) -> Dict[str, float]:
        """Calcule la disponibilité des équipements."""
        # Implémentation simplifiée - pourrait être enrichie avec de vraies métriques
        return {
            'average': 98.5,
            'minimum': 95.0,
            'maximum': 100.0
        }

    async def _calculate_interface_utilization(self, start_time: datetime, end_time: datetime) -> Dict[str, float]:
        """Calcule l'utilisation des interfaces."""
        return {
            'average': 45.2,
            'peak': 78.9,
            'minimum': 12.1
        }

    async def _get_alert_summary(self, start_time: datetime, end_time: datetime) -> Dict[str, int]:
        """Récupère un résumé des alertes."""
        alerts = await self._network_service.get_network_alerts(limit=100)

        # Filtrer par période et compter par sévérité
        summary = {'critical': 0, 'warning': 0, 'info': 0}
        for alert in alerts:
            if hasattr(alert, 'severity'):
                severity = alert.severity.lower()
                if severity in summary:
                    summary[severity] += 1

        return summary

    async def _get_performance_metrics(self, start_time: datetime, end_time: datetime) -> Dict[str, float]:
        """Récupère les métriques de performance."""
        return {
            'latency_avg': 12.5,
            'packet_loss': 0.02,
            'throughput_mbps': 850.3,
            'error_rate': 0.001
        }


class TopologyVisualizationServiceImpl(ITopologyVisualizationService):
    """
    Implémentation du service de visualisation de topologie.
    """

    def __init__(self, network_service, cache_service):
        self._network_service = network_service
        self._cache_service = cache_service

    async def get_integrated_topology(self, topology_id: int) -> TopologyView:
        """
        Récupère les détails d'une topologie avec informations enrichies.

        Args:
            topology_id: ID de la topologie à récupérer

        Returns:
            Objet contenant les informations enrichies sur la topologie
        """
        # Utiliser le cache si disponible
        cache_key = f"topology_{topology_id}"
        cached_topology = await self._cache_service.get(cache_key)

        if cached_topology:
            from ..domain.entities import TopologyView
            return TopologyView(**cached_topology)

        try:
            # Récupérer les données de topologie
            topology_data = await self._network_service.get_topology_data(topology_id)

            # Enrichir avec les informations de santé des équipements
            enriched_devices = []
            for device_data in topology_data.get('devices', []):
                device_id = device_data.get('id')
                if device_id:
                    health_status = await self.get_device_health_status(device_id)
                    device_data['health_status'] = health_status
                enriched_devices.append(device_data)

            # Créer l'objet TopologyView selon les entités du domaine
            from ..domain.entities import TopologyView
            from datetime import datetime
            
            topology_view = TopologyView(
                topology_id=topology_id,
                name=topology_data.get('name', f'Topology {topology_id}'),
                nodes=enriched_devices,  # Utiliser 'nodes' au lieu de 'devices'
                connections=topology_data.get('connections', []),
                health_summary={
                    'healthy': len([d for d in enriched_devices if d.get('health_status', {}).get('status') == 'healthy']),
                    'warning': len([d for d in enriched_devices if d.get('health_status', {}).get('status') == 'warning']),
                    'critical': len([d for d in enriched_devices if d.get('health_status', {}).get('status') == 'critical'])
                },
                last_updated=datetime.now()
            )

            # Mettre en cache pour 10 minutes
            await self._cache_service.set(cache_key, topology_view.__dict__, ttl=600)

            return topology_view

        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la topologie {topology_id}: {e}")
            # Retourner une topologie vide en cas d'erreur
            from ..domain.entities import TopologyView
            from datetime import datetime
            return TopologyView(
                topology_id=topology_id,
                name=f'Topology {topology_id} (Error)',
                nodes=[],  # Utiliser 'nodes' au lieu de 'devices'
                connections=[],
                health_summary={'error': 1},
                last_updated=datetime.now()
            )

    async def get_device_health_status(self, device_id: int) -> DeviceStatus:
        """
        Détermine le statut de santé d'un équipement.

        Args:
            device_id: ID de l'équipement

        Returns:
            Statut de santé de l'équipement
        """
        try:
            # Utiliser le cache si disponible
            cache_key = f"device_health_{device_id}"
            cached_status = await self._cache_service.get(cache_key)

            if cached_status:
                from ..domain.entities import DeviceStatus
                return DeviceStatus(**cached_status)

            # Récupérer les alertes récentes pour cet équipement
            alerts = await self._network_service.get_network_alerts(limit=50)
            device_alerts = [alert for alert in alerts if hasattr(alert, 'device_id') and alert.device_id == device_id]

            # Déterminer le statut basé sur les alertes
            from ..domain.entities import DeviceStatus

            if any(alert.severity.lower() == 'critical' for alert in device_alerts):
                status = DeviceStatus.CRITICAL
            elif any(alert.severity.lower() == 'warning' for alert in device_alerts):
                status = DeviceStatus.WARNING
            else:
                # Vérifier si l'équipement est actif
                device_summary = await self._network_service.get_device_summary()
                # Logique simplifiée - dans un vrai système, on vérifierait l'état spécifique de l'équipement
                status = DeviceStatus.HEALTHY

            # Mettre en cache pour 2 minutes
            await self._cache_service.set(cache_key, status.value, ttl=120)

            return status

        except Exception as e:
            logger.error(f"Erreur lors de la vérification de la santé de l'équipement {device_id}: {e}")
            from ..domain.entities import DeviceStatus
            return DeviceStatus.UNKNOWN

    async def get_connection_status(self, connection_id: int) -> ConnectionStatus:
        """
        Détermine le statut d'une connexion.

        Args:
            connection_id: ID de la connexion

        Returns:
            Statut de la connexion
        """
        try:
            # Utiliser le cache si disponible
            cache_key = f"connection_status_{connection_id}"
            cached_status = await self._cache_service.get(cache_key)

            if cached_status:
                from ..domain.entities import ConnectionStatus
                return ConnectionStatus(**cached_status)

            # Logique simplifiée pour déterminer le statut de connexion
            # Dans un vrai système, on vérifierait l'état des interfaces, la latence, etc.
            from ..domain.entities import ConnectionStatus

            # Pour l'instant, retourner un statut par défaut
            status = ConnectionStatus.ACTIVE

            # Mettre en cache pour 1 minute
            await self._cache_service.set(cache_key, status.value, ttl=60)

            return status

        except Exception as e:
            logger.error(f"Erreur lors de la vérification du statut de connexion {connection_id}: {e}")
            from ..domain.entities import ConnectionStatus
            return ConnectionStatus.UNKNOWN

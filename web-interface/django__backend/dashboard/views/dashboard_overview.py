from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

from django.utils import timezone
from datetime import timedelta

from network_management.models import NetworkDevice
# from security_management.models import SecurityAlertModel as SecurityAlert, TrafficAnomalyModel as TrafficAnomaly  # Module désactivé
from qos_management.models import QoSPolicy, InterfaceQoSPolicy

from dashboard.di_container import container

logger = logging.getLogger(__name__)

class DashboardOverviewView(APIView):
    """
    Vue principale pour le tableau de bord intégré
    
    Cette vue fournit les données consolidées de tous les sous-systèmes
    pour afficher une vue d'ensemble cohérente de l'état du réseau.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.dashboard_overview_use_case = container.get_service('dashboard_service')
            self.system_health_use_case = container.get_service('monitoring_adapter')
        except Exception as e:
            logger.warning(f"Erreur lors de l'initialisation des services: {e}")
            self.dashboard_overview_use_case = None
            self.system_health_use_case = None
    
    @swagger_auto_schema(
        operation_description="Récupère les données consolidées du tableau de bord",
        
        operation_summary="Vue d'ensemble du tableau de bord",
        tags=['Dashboard'],
        responses={
            200: openapi.Response(
                description="Données du tableau de bord récupérées avec succès",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'devices': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'total_devices': openapi.Schema(type=openapi.TYPE_INTEGER, description='Nombre total d\'équipements'),
                                'device_types': openapi.Schema(type=openapi.TYPE_OBJECT, description='Répartition par type d\'équipement'),
                                'status': openapi.Schema(type=openapi.TYPE_OBJECT, description='Répartition par statut'),
                                'connections': openapi.Schema(type=openapi.TYPE_OBJECT, description='Statistiques de connexions')
                            }
                        ),
                        'security_alerts': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'severity': openapi.Schema(type=openapi.TYPE_STRING, enum=['low', 'medium', 'high', 'critical']),
                                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                                    'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format='date-time')
                                }
                            ),
                            description='Alertes de sécurité récentes'
                        ),
                        'system_alerts': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_OBJECT),
                            description='Alertes système récentes'
                        ),
                        'health_metrics': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'system_health': openapi.Schema(type=openapi.TYPE_NUMBER, minimum=0, maximum=1, description='Santé globale du système'),
                                'network_health': openapi.Schema(type=openapi.TYPE_NUMBER, minimum=0, maximum=1, description='Santé du réseau'),
                                'security_health': openapi.Schema(type=openapi.TYPE_NUMBER, minimum=0, maximum=1, description='Santé de la sécurité')
                            },
                            description='Métriques de santé du système'
                        ),
                        'qos_summary': openapi.Schema(type=openapi.TYPE_OBJECT, description='Résumé des politiques QoS'),
                        'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time', description='Horodatage de dernière mise à jour')
                    }
                )
            ),
            401: openapi.Response(description="Non authentifié"),
            500: openapi.Response(description="Erreur serveur interne")
        }
    )
    def get(self, request):
        """
        Obtenir les données globales pour le tableau de bord

        Returns:
            Données consolidées du tableau de bord incluant:
            - Statistiques des équipements
            - Alertes de sécurité récentes
            - Anomalies de trafic récentes
            - Statistiques QoS
            - Indicateurs de santé système
        """
        try:
            # Essayer d'utiliser le service si disponible
            if self.dashboard_overview_use_case:
                import asyncio
                
                # Utiliser les méthodes correctes du service
                async def get_dashboard_data():
                    return await self.dashboard_overview_use_case.get_dashboard_overview(user_id=request.user.id)
                
                result = asyncio.run(get_dashboard_data())
                
                # Convertir l'objet DashboardOverview en dictionnaire pour la réponse JSON
                dashboard_dict = {
                    'total_devices': getattr(result, 'total_devices', 0),
                    'active_devices': getattr(result, 'active_devices', 0),
                    'total_interfaces': getattr(result, 'total_interfaces', 0),
                    'active_interfaces': getattr(result, 'active_interfaces', 0),
                    'recent_alerts': getattr(result, 'recent_alerts', []),
                    'system_health': {
                        'cpu_usage': getattr(result.system_health, 'cpu_usage', 0) if hasattr(result, 'system_health') else 0,
                        'memory_usage': getattr(result.system_health, 'memory_usage', 0) if hasattr(result, 'system_health') else 0,
                        'disk_usage': getattr(result.system_health, 'disk_usage', 0) if hasattr(result, 'system_health') else 0,
                        'network_load': getattr(result.system_health, 'network_load', 0) if hasattr(result, 'system_health') else 0
                    }
                }

                return Response(dashboard_dict)
            else:
                # Fallback: collecter les données manuellement
                result = self._collect_dashboard_data()
                return Response(result)

        except Exception as e:
            logger.exception(f"Erreur lors de la récupération des données du tableau de bord: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _collect_dashboard_data(self):
        """
        Collecte manuellement les données du tableau de bord
        
        Returns:
            Dictionnaire contenant les données agrégées du tableau de bord
        """
        # Statistiques des équipements
        devices_count = NetworkDevice.objects.count()
        active_devices_count = NetworkDevice.objects.filter(is_active=True).count()
        
        # Période pour les données récentes - 7 derniers jours
        recent_period = timezone.now() - timedelta(days=7)
        
        # Alertes récentes
        recent_alerts = SecurityAlert.objects.filter(
            detection_time__gte=recent_period
        ).order_by('-detection_time')[:10]

        # Anomalies récentes
        recent_anomalies = TrafficAnomaly.objects.filter(
            timestamp__gte=recent_period
        ).order_by('-timestamp')[:10]
        
        # Politiques QoS actives
        active_qos_policies = QoSPolicy.objects.filter(is_active=True).count()
        
        # Construire la structure de données complète
        return {
            "device_stats": {
                "total": devices_count,
                "active": active_devices_count,
                "inactive": devices_count - active_devices_count
            },
            "security_stats": {
                "recent_alerts_count": recent_alerts.count(),
                "recent_alerts": self._format_alerts(recent_alerts),
                "recent_anomalies_count": recent_anomalies.count(),
                "recent_anomalies": self._format_anomalies(recent_anomalies)
            },
            "qos_stats": {
                "active_policies": active_qos_policies,
                "applied_policies": InterfaceQoSPolicy.objects.filter(is_active=True).count()
            },
            "system_health": self._get_system_health()
        }
    
    def _format_alerts(self, alerts):
        """
        Formate les alertes de sécurité pour la réponse API

        Args:
            alerts: QuerySet d'alertes à formater

        Returns:
            Liste d'alertes formatées
        """
        return [{
            "id": alert.id,
            "severity": alert.severity,
            "message": alert.title,  # Le modèle utilise 'title' au lieu de 'message'
            "source": alert.source_ip or "Unknown",  # Le modèle utilise 'source_ip'
            "timestamp": alert.detection_time
        } for alert in alerts]
    
    def _format_anomalies(self, anomalies):
        """
        Formate les anomalies de trafic pour la réponse API

        Args:
            anomalies: QuerySet d'anomalies à formater

        Returns:
            Liste d'anomalies formatées
        """
        return [{
            "id": anomaly.id,
            "type": anomaly.anomaly_type,
            "deviation": f"{anomaly.deviation_percent:.2f}%",
            "detected_at": anomaly.timestamp  # Le modèle utilise 'timestamp'
        } for anomaly in anomalies]
    
    def _get_system_health(self):
        """
        Récupère des indicateurs de santé du système
        
        Dans une implémentation réelle, ces données proviendraient 
        d'un service de monitoring (Prometheus, etc.)
        
        Returns:
            Dictionnaire contenant les métriques de santé système
        """
        try:
            # Si un service de monitoring est disponible, l'utiliser
            if self.system_health_use_case:
                import asyncio
                
                async def get_health_metrics():
                    return await self.system_health_use_case.get_system_health_metrics()
                
                health_data = asyncio.run(get_health_metrics())
                return {
                    "cpu_load": getattr(health_data, 'cpu_usage', 45.2),
                    "memory_usage": getattr(health_data, 'memory_usage', 68.7),
                    "disk_usage": getattr(health_data, 'disk_usage', 72.3),
                    "network_load": getattr(health_data, 'network_load', 38.9)
                }
        except Exception as e:
            logger.warning(f"Erreur lors de la récupération des métriques système: {e}")
        
        # Valeurs simulées par défaut
        return {
            "cpu_load": 45.2,
            "memory_usage": 68.7,
            "disk_usage": 72.3,
            "network_load": 38.9
        }
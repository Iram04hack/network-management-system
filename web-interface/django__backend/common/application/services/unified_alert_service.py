"""
Service unifié pour la gestion des alertes.
"""
import logging
from typing import Dict, Any, List, Optional
from django.apps import apps
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User

# from security_management.models import SecurityAlert  # Module désactivé
from monitoring.models import Alert
from network_management.models import NetworkDevice
from ...domain.interfaces.unified_alert import UnifiedAlertInterface

logger = logging.getLogger(__name__)

class UnifiedAlertService(UnifiedAlertInterface):
    """Implémentation du service pour centraliser les alertes de différentes sources."""
    
    def get_all_alerts(
        self, 
        days: int = 7, 
        filter_by: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None, 
        device_ids: Optional[List[int]] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Récupère toutes les alertes de toutes les sources.
        
        Args:
            days: Nombre de jours en arrière pour la recherche
            filter_by: Filtres à appliquer (severity, status, etc.)
            user_id: ID de l'utilisateur pour filtrer les alertes ack
            device_ids: Liste des IDs d'équipements à filtrer
            limit: Nombre maximum d'alertes à retourner
            
        Returns:
            Alertes consolidées de toutes les sources
        """
        try:
            # Récupérer les modèles via lazy loading
            SecurityAlert = apps.get_model('security_management', 'SecurityAlert')
            Alert = apps.get_model('monitoring', 'Alert')
            
            since_date = timezone.now() - timedelta(days=days)
            
            # Récupérer les alertes de sécurité
            security_alerts_query = SecurityAlert.objects.filter(
                timestamp__gte=since_date
            ).select_related('device', 'acknowledged_by')
            
            # Récupérer les alertes de monitoring
            monitoring_alerts_query = Alert.objects.filter(
                timestamp__gte=since_date
            ).select_related('device', 'acknowledged_by', 'metric', 'service_check')
            
            # Appliquer les filtres
            if filter_by:
                if 'severity' in filter_by:
                    security_alerts_query = security_alerts_query.filter(severity__in=filter_by['severity'])
                    monitoring_alerts_query = monitoring_alerts_query.filter(severity__in=filter_by['severity'])
                
                if 'status' in filter_by:
                    security_alerts_query = security_alerts_query.filter(status__in=filter_by['status'])
                    monitoring_alerts_query = monitoring_alerts_query.filter(status__in=filter_by['status'])
                    
                if 'source' in filter_by:
                    if 'security' in filter_by['source'] and 'monitoring' not in filter_by['source']:
                        monitoring_alerts_query = monitoring_alerts_query.none()
                    elif 'monitoring' in filter_by['source'] and 'security' not in filter_by['source']:
                        security_alerts_query = security_alerts_query.none()
            
            # Filtrer par utilisateur ayant acquitté
            if user_id is not None:
                security_alerts_query = security_alerts_query.filter(acknowledged_by__id=user_id)
                monitoring_alerts_query = monitoring_alerts_query.filter(acknowledged_by__id=user_id)
            
            # Filtrer par équipement
            if device_ids:
                security_alerts_query = security_alerts_query.filter(device__id__in=device_ids)
                monitoring_alerts_query = monitoring_alerts_query.filter(device__id__in=device_ids)
            
            # Convertir en format unifié
            unified_alerts = []
            
            # Traiter les alertes de sécurité
            for alert in security_alerts_query:
                unified_alerts.append({
                    'id': f"security-{alert.id}",
                    'type': 'security',
                    'source': alert.source,
                    'event_type': alert.event_type,
                    'severity': alert.severity,
                    'status': alert.status,
                    'device_id': alert.device.id if alert.device else None,
                    'device_name': alert.device.name if alert.device else "N/A",
                    'message': alert.message,
                    'timestamp': alert.timestamp.isoformat(),
                    'acknowledged_by': alert.acknowledged_by.username if alert.acknowledged_by else None,
                    'acknowledged_at': alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                    'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None,
                    'details': {
                        'source_ip': alert.source_ip,
                        'destination_ip': alert.destination_ip,
                    }
                })
            
            # Traiter les alertes de monitoring
            for alert in monitoring_alerts_query:
                unified_alerts.append({
                    'id': f"monitoring-{alert.id}",
                    'type': 'monitoring',
                    'source': 'monitoring',
                    'event_type': alert.service_check.name if alert.service_check else 'metric_alert',
                    'severity': alert.severity,
                    'status': alert.status,
                    'device_id': alert.device.id if alert.device else None,
                    'device_name': alert.device.name if alert.device else "N/A",
                    'message': alert.message,
                    'timestamp': alert.timestamp.isoformat(),
                    'acknowledged_by': alert.acknowledged_by.username if alert.acknowledged_by else None,
                    'acknowledged_at': alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                    'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None,
                    'details': {
                        'metric': alert.metric.name if alert.metric else None,
                        'value': alert.value,
                        'service': alert.service_check.name if alert.service_check else None,
                    }
                })
            
            # Trier par date (les plus récentes d'abord)
            unified_alerts.sort(key=lambda x: x['timestamp'], reverse=True)
            
            # Limiter le nombre de résultats
            if limit and len(unified_alerts) > limit:
                unified_alerts = unified_alerts[:limit]
            
            return {
                'success': True,
                'count': len(unified_alerts),
                'alerts': unified_alerts
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des alertes unifiées: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def acknowledge_alert(self, alert_id: str, user_id: int) -> Dict[str, Any]:
        """
        Acquitte une alerte.
        
        Args:
            alert_id: ID de l'alerte au format "type-id"
            user_id: ID de l'utilisateur qui acquitte
            
        Returns:
            Résultat de l'opération
        """
        try:
            # Récupérer les modèles via lazy loading
            SecurityAlert = apps.get_model('security_management', 'SecurityAlert')
            Alert = apps.get_model('monitoring', 'Alert')
            
            # Récupérer l'utilisateur
            user = User.objects.get(id=user_id)
            
            # Déterminer le type d'alerte
            if not alert_id or '-' not in alert_id:
                return {
                    'success': False,
                    'error': "Format d'ID d'alerte invalide"
                }
            
            alert_type, alert_numeric_id = alert_id.split('-', 1)
            
            if alert_type == 'security':
                # Acquitter une alerte de sécurité
                alert = SecurityAlert.objects.get(id=alert_numeric_id)
                alert.acknowledge(user)
                result = {
                    'success': True,
                    'message': 'Alerte de sécurité acquittée',
                    'alert_id': alert_id,
                    'acknowledged_by': user.username,
                    'acknowledged_at': alert.acknowledged_at.isoformat()
                }
            elif alert_type == 'monitoring':
                # Acquitter une alerte de monitoring
                alert = Alert.objects.get(id=alert_numeric_id)
                alert.acknowledge(user)
                result = {
                    'success': True,
                    'message': 'Alerte de monitoring acquittée',
                    'alert_id': alert_id,
                    'acknowledged_by': user.username,
                    'acknowledged_at': alert.acknowledged_at.isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': f"Type d'alerte inconnu: {alert_type}"
                }
            
            return result
            
        except (SecurityAlert.DoesNotExist, Alert.DoesNotExist):
            return {
                'success': False,
                'error': f"Alerte {alert_id} non trouvée"
            }
        except Exception as e:
            logger.error(f"Erreur lors de l'acquittement de l'alerte {alert_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def resolve_alert(self, alert_id: str, user_id: int) -> Dict[str, Any]:
        """
        Résoud une alerte.
        
        Args:
            alert_id: ID de l'alerte au format "type-id"
            user_id: ID de l'utilisateur qui résoud
            
        Returns:
            Résultat de l'opération
        """
        try:
            # Récupérer les modèles via lazy loading
            SecurityAlert = apps.get_model('security_management', 'SecurityAlert')
            Alert = apps.get_model('monitoring', 'Alert')
            
            # Récupérer l'utilisateur
            user = User.objects.get(id=user_id)
            
            # Déterminer le type d'alerte
            if not alert_id or '-' not in alert_id:
                return {
                    'success': False,
                    'error': "Format d'ID d'alerte invalide"
                }
            
            alert_type, alert_numeric_id = alert_id.split('-', 1)
            
            if alert_type == 'security':
                # Résoudre une alerte de sécurité
                alert = SecurityAlert.objects.get(id=alert_numeric_id)
                alert.resolve(user)
                result = {
                    'success': True,
                    'message': 'Alerte de sécurité résolue',
                    'alert_id': alert_id,
                    'resolved_at': alert.resolved_at.isoformat()
                }
            elif alert_type == 'monitoring':
                # Résoudre une alerte de monitoring
                alert = Alert.objects.get(id=alert_numeric_id)
                alert.resolve(user)
                result = {
                    'success': True,
                    'message': 'Alerte de monitoring résolue',
                    'alert_id': alert_id,
                    'resolved_at': alert.resolved_at.isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': f"Type d'alerte inconnu: {alert_type}"
                }
            
            return result
            
        except (SecurityAlert.DoesNotExist, Alert.DoesNotExist):
            return {
                'success': False,
                'error': f"Alerte {alert_id} non trouvée"
            }
        except Exception as e:
            logger.error(f"Erreur lors de la résolution de l'alerte {alert_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_alert_statistics(self, days: int = 7, device_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Récupère des statistiques sur les alertes.
        
        Args:
            days: Nombre de jours en arrière pour la recherche
            device_ids: Liste des IDs d'équipements à filtrer
            
        Returns:
            Statistiques sur les alertes
        """
        try:
            # Récupérer les modèles via lazy loading
            SecurityAlert = apps.get_model('security_management', 'SecurityAlert')
            Alert = apps.get_model('monitoring', 'Alert')
            
            since_date = timezone.now() - timedelta(days=days)
            
            # Base des requêtes
            security_alerts = SecurityAlert.objects.filter(timestamp__gte=since_date)
            monitoring_alerts = Alert.objects.filter(timestamp__gte=since_date)
            
            # Filtrer par équipement
            if device_ids:
                security_alerts = security_alerts.filter(device__id__in=device_ids)
                monitoring_alerts = monitoring_alerts.filter(device__id__in=device_ids)
            
            # Statistiques par sévérité
            security_by_severity = {
                severity: security_alerts.filter(severity=severity).count()
                for severity in ['critical', 'high', 'medium', 'low']
            }
            
            monitoring_by_severity = {
                severity: monitoring_alerts.filter(severity=severity).count()
                for severity in ['critical', 'high', 'medium', 'low']
            }
            
            # Statistiques par statut
            security_by_status = {
                status: security_alerts.filter(status=status).count()
                for status in ['new', 'acknowledged', 'resolved', 'false_positive']
            }
            
            monitoring_by_status = {
                status: monitoring_alerts.filter(status=status).count()
                for status in ['new', 'acknowledged', 'resolved', 'false_positive']
            }
            
            # Statistiques par source (pour les alertes de sécurité)
            security_by_source = {}
            for source in security_alerts.values_list('source', flat=True).distinct():
                security_by_source[source] = security_alerts.filter(source=source).count()
            
            # Total des alertes
            total_security = security_alerts.count()
            total_monitoring = monitoring_alerts.count()
            total_all = total_security + total_monitoring
            
            return {
                'success': True,
                'period_days': days,
                'total_alerts': total_all,
                'security_alerts': total_security,
                'monitoring_alerts': total_monitoring,
                'by_severity': {
                    'security': security_by_severity,
                    'monitoring': monitoring_by_severity,
                    'total': {
                        severity: security_by_severity.get(severity, 0) + monitoring_by_severity.get(severity, 0)
                        for severity in ['critical', 'high', 'medium', 'low']
                    }
                },
                'by_status': {
                    'security': security_by_status,
                    'monitoring': monitoring_by_status,
                    'total': {
                        status: security_by_status.get(status, 0) + monitoring_by_status.get(status, 0)
                        for status in ['new', 'acknowledged', 'resolved', 'false_positive']
                    }
                },
                'security_by_source': security_by_source
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des statistiques d'alertes: {e}")
            return {
                'success': False,
                'error': str(e)
            } 
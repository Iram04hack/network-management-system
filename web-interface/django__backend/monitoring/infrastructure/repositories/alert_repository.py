"""
Implémentation concrète du repository pour les alertes.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from django.db.models import Q, Count

from ...domain.interfaces.repositories import AlertRepository as AlertRepositoryInterface
from ...models import Alert, AlertComment, AlertHistory
from .base_repository import BaseRepository

# Configuration du logger
logger = logging.getLogger(__name__)


class AlertRepository(BaseRepository[Alert], AlertRepositoryInterface):
    """
    Repository pour les alertes.
    """
    
    def __init__(self):
        """
        Initialise le repository avec le modèle Alert.
        """
        super().__init__(Alert)
    
    def create_alert(self, device_id: int, message: str, severity: str, 
                     metric_id: Optional[int] = None, 
                     service_check_id: Optional[int] = None,
                     source: str = "system", status: str = "active",
                     details: Dict[str, Any] = None) -> Alert:
        """
        Crée une nouvelle alerte.
        
        Args:
            device_id: ID de l'équipement concerné
            message: Message d'alerte
            severity: Sévérité de l'alerte ('critical', 'warning', 'info')
            metric_id: ID de la métrique associée (optionnel)
            service_check_id: ID de la vérification de service associée (optionnel)
            source: Source de l'alerte ('system', 'user', 'external')
            status: Statut initial de l'alerte ('active', 'acknowledged', 'resolved')
            details: Détails supplémentaires de l'alerte (optionnel)
            
        Returns:
            L'alerte créée
        """
        try:
            alert = Alert(
                device_id=device_id,
                message=message,
                severity=severity,
                status=status,
                source=source,
                details=details or {},
                created_at=datetime.now(timezone.utc)
            )
            
            if metric_id:
                alert.metric_id = metric_id
                
            if service_check_id:
                alert.service_check_id = service_check_id
            
            alert.save()
            logger.info(f"Alerte créée: {alert.id} - {message}")
            return alert
        except Exception as e:
            logger.error(f"Erreur lors de la création d'une alerte: {e}")
            raise
    
    def update_alert_status(self, alert_id: int, status: str, 
                           acknowledged_by: Optional[int] = None,
                           resolved_by: Optional[int] = None,
                           resolution_note: Optional[str] = None) -> Optional[Alert]:
        """
        Met à jour le statut d'une alerte.
        
        Args:
            alert_id: ID de l'alerte
            status: Nouveau statut de l'alerte ('active', 'acknowledged', 'resolved')
            acknowledged_by: ID de l'utilisateur qui a accusé réception (optionnel)
            resolved_by: ID de l'utilisateur qui a résolu l'alerte (optionnel)
            resolution_note: Note de résolution (optionnel)
            
        Returns:
            L'alerte mise à jour ou None si elle n'existe pas
        """
        alert = self.get_by_id(alert_id)
        if not alert:
            return None
        
        try:
            alert.status = status
            
            if status == "acknowledged" and acknowledged_by:
                alert.acknowledged_by_id = acknowledged_by
                alert.acknowledged_at = datetime.now(timezone.utc)
                
            if status == "resolved":
                alert.resolved_at = datetime.now(timezone.utc)
                
                if resolved_by:
                    alert.resolved_by_id = resolved_by
                    
                if resolution_note:
                    alert.resolution_note = resolution_note
            
            alert.save()
            logger.info(f"Alerte {alert_id} mise à jour avec le statut: {status}")
            return alert
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du statut de l'alerte {alert_id}: {e}")
            raise
    
    def get_alerts_by_device(self, device_id: int, status: Optional[str] = None, 
                            severity: Optional[str] = None,
                            limit: int = 100) -> List[Alert]:
        """
        Récupère les alertes pour un équipement donné.
        
        Args:
            device_id: ID de l'équipement
            status: Filtrer par statut (optionnel)
            severity: Filtrer par sévérité (optionnel)
            limit: Nombre maximum d'alertes à récupérer
            
        Returns:
            Liste des alertes filtrées
        """
        query = Q(device_id=device_id)
        
        if status:
            query &= Q(status=status)
            
        if severity:
            query &= Q(severity=severity)
        
        return list(Alert.objects.filter(query).order_by('-created_at')[:limit])
    
    def get_active_alerts_count(self) -> int:
        """
        Récupère le nombre d'alertes actives.
        
        Returns:
            Nombre d'alertes actives
        """
        return Alert.objects.filter(status='active').count()
    
    def get_alerts_summary_by_device(self) -> List[Dict[str, Any]]:
        """
        Récupère un résumé des alertes par équipement.
        
        Returns:
            Liste de résumés d'alertes par équipement
        """
        return list(Alert.objects.filter(status='active').values(
            'device_id', 'device__name'
        ).annotate(
            alert_count=Count('id'),
            critical_count=Count('id', filter=Q(severity='critical')),
            warning_count=Count('id', filter=Q(severity='warning')),
            info_count=Count('id', filter=Q(severity='info'))
        ).order_by('-critical_count', '-warning_count', '-info_count'))
    
    def get_similar_alerts(self, alert_id: int, limit: int = 5) -> List[Alert]:
        """
        Récupère des alertes similaires à une alerte donnée.
        
        Args:
            alert_id: ID de l'alerte de référence
            limit: Nombre maximum d'alertes à récupérer
            
        Returns:
            Liste des alertes similaires
        """
        alert = self.get_by_id(alert_id)
        if not alert:
            return []
        
        query = Q(message=alert.message) & Q(device_id=alert.device_id) & ~Q(id=alert_id)
        return list(Alert.objects.filter(query).order_by('-created_at')[:limit])
    
    def get_unresolved_alerts_by_metric(self, metric_id: int) -> List[Alert]:
        """
        Récupère les alertes non résolues pour une métrique donnée.
        
        Args:
            metric_id: ID de la métrique
            
        Returns:
            Liste des alertes non résolues
        """
        query = Q(metric_id=metric_id) & ~Q(status='resolved')
        return list(Alert.objects.filter(query).order_by('-created_at'))
    
    def get_unresolved_alerts_by_service_check(self, service_check_id: int) -> List[Alert]:
        """
        Récupère les alertes non résolues pour une vérification de service donnée.
        
        Args:
            service_check_id: ID de la vérification de service
            
        Returns:
            Liste des alertes non résolues
        """
        query = Q(service_check_id=service_check_id) & ~Q(status='resolved')
        return list(Alert.objects.filter(query).order_by('-created_at')) 

    def list_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Récupère une liste d'alertes filtrées.
        Cette méthode est requise par l'interface abstraite.
        
        Args:
            filters: Filtres à appliquer (optionnel)
            
        Returns:
            Liste des alertes correspondant aux filtres
        """
        try:
            queryset = Alert.objects.all()
            
            if filters:
                if 'status' in filters:
                    queryset = queryset.filter(status=filters['status'])
                if 'severity' in filters:
                    queryset = queryset.filter(severity=filters['severity'])
                if 'device_id' in filters:
                    queryset = queryset.filter(device_id=filters['device_id'])
                if 'created_after' in filters:
                    queryset = queryset.filter(created_at__gte=filters['created_after'])
                if 'created_before' in filters:
                    queryset = queryset.filter(created_at__lte=filters['created_before'])
            
            # Convertir les objets Django en dictionnaires
            alerts = []
            for alert in queryset.order_by('-created_at'):
                alert_dict = {
                    'id': alert.id,
                    'message': alert.message,
                    'severity': alert.severity,
                    'status': alert.status,
                    'source': alert.source,
                    'device_id': alert.device_id,
                    'metric_id': alert.metric_id,
                    'service_check_id': alert.service_check_id,
                    'details': alert.details or {},
                    'created_at': alert.created_at.isoformat() if alert.created_at else None,
                    'acknowledged_at': alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                    'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None,
                    'acknowledged_by_id': alert.acknowledged_by_id,
                    'resolved_by_id': alert.resolved_by_id,
                    'resolution_note': alert.resolution_note
                }
                alerts.append(alert_dict)
            
            return alerts
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des alertes: {e}")
            return []

    def update_status(self, alert_id: int, status: str, user_id: Optional[int], 
                     comment: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Met à jour le statut d'une alerte.
        Cette méthode est requise par l'interface abstraite.
        
        Args:
            alert_id: ID de l'alerte
            status: Nouveau statut
            user_id: ID de l'utilisateur qui effectue la mise à jour
            comment: Commentaire optionnel
            
        Returns:
            L'alerte mise à jour ou None si elle n'existe pas
        """
        try:
            alert = Alert.objects.get(id=alert_id)
            
            alert.status = status
            
            if status == "acknowledged" and user_id:
                alert.acknowledged_by_id = user_id
                alert.acknowledged_at = datetime.now(timezone.utc)
                
            if status == "resolved":
                alert.resolved_at = datetime.now(timezone.utc)
                if user_id:
                    alert.resolved_by_id = user_id
                if comment:
                    alert.resolution_note = comment
            
            alert.save()
            
            # Convertir en dictionnaire pour respecter l'interface
            alert_dict = {
                'id': alert.id,
                'message': alert.message,
                'severity': alert.severity,
                'status': alert.status,
                'source': alert.source,
                'device_id': alert.device_id,
                'metric_id': alert.metric_id,
                'service_check_id': alert.service_check_id,
                'details': alert.details or {},
                'created_at': alert.created_at.isoformat() if alert.created_at else None,
                'acknowledged_at': alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None,
                'acknowledged_by_id': alert.acknowledged_by_id,
                'resolved_by_id': alert.resolved_by_id,
                'resolution_note': alert.resolution_note
            }
            
            logger.info(f"Alerte {alert_id} mise à jour avec le statut: {status}")
            return alert_dict
        except Alert.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du statut de l'alerte {alert_id}: {e}")
            raise

    def get_by_id(self, alert_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère une alerte par son ID.
        Méthode requise par l'interface abstraite.
        
        Args:
            alert_id: ID de l'alerte
            
        Returns:
            L'alerte ou None si elle n'existe pas
        """
        try:
            alert = Alert.objects.get(id=alert_id)
            return {
                'id': alert.id,
                'message': alert.message,
                'severity': alert.severity,
                'status': alert.status,
                'source': alert.source,
                'device_id': alert.device_id,
                'metric_id': alert.metric_id,
                'service_check_id': alert.service_check_id,
                'details': alert.details or {},
                'created_at': alert.created_at.isoformat() if alert.created_at else None,
                'acknowledged_at': alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None,
                'acknowledged_by_id': alert.acknowledged_by_id,
                'resolved_by_id': alert.resolved_by_id,
                'resolution_note': alert.resolution_note
            }
        except Alert.DoesNotExist:
            return None

    def create(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée une nouvelle alerte.
        Méthode requise par l'interface abstraite.
        
        Args:
            alert_data: Données de l'alerte à créer
            
        Returns:
            L'alerte créée
        """
        alert = Alert.objects.create(**alert_data)
        return {
            'id': alert.id,
            'message': alert.message,
            'severity': alert.severity,
            'status': alert.status,
            'source': alert.source,
            'device_id': alert.device_id,
            'metric_id': alert.metric_id,
            'service_check_id': alert.service_check_id,
            'details': alert.details or {},
            'created_at': alert.created_at.isoformat() if alert.created_at else None,
            'acknowledged_at': alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
            'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None,
            'acknowledged_by_id': alert.acknowledged_by_id,
            'resolved_by_id': alert.resolved_by_id,
            'resolution_note': alert.resolution_note
        }

    def update(self, alert_id: int, alert_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Met à jour une alerte.
        Méthode requise par l'interface abstraite.
        
        Args:
            alert_id: ID de l'alerte
            alert_data: Nouvelles données
            
        Returns:
            L'alerte mise à jour ou None si elle n'existe pas
        """
        try:
            alert = Alert.objects.get(id=alert_id)
            for key, value in alert_data.items():
                setattr(alert, key, value)
            alert.save()
            
            return {
                'id': alert.id,
                'message': alert.message,
                'severity': alert.severity,
                'status': alert.status,
                'source': alert.source,
                'device_id': alert.device_id,
                'metric_id': alert.metric_id,
                'service_check_id': alert.service_check_id,
                'details': alert.details or {},
                'created_at': alert.created_at.isoformat() if alert.created_at else None,
                'acknowledged_at': alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None,
                'acknowledged_by_id': alert.acknowledged_by_id,
                'resolved_by_id': alert.resolved_by_id,
                'resolution_note': alert.resolution_note
            }
        except Alert.DoesNotExist:
            return None

    def delete(self, alert_id: int) -> bool:
        """
        Supprime une alerte.
        Méthode requise par l'interface abstraite.
        
        Args:
            alert_id: ID de l'alerte
            
        Returns:
            True si supprimée, False sinon
        """
        try:
            alert = Alert.objects.get(id=alert_id)
            alert.delete()
            return True
        except Alert.DoesNotExist:
            return False

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Compte les alertes selon les filtres.
        Méthode requise par l'interface abstraite.
        
        Args:
            filters: Filtres à appliquer
            
        Returns:
            Nombre d'alertes
        """
        queryset = Alert.objects.all()
        
        if filters:
            if 'status' in filters:
                queryset = queryset.filter(status=filters['status'])
            if 'severity' in filters:
                queryset = queryset.filter(severity=filters['severity'])
            if 'device_id' in filters:
                queryset = queryset.filter(device_id=filters['device_id'])
        
        return queryset.count()


class AlertCommentRepository(BaseRepository[AlertComment]):
    """
    Repository pour les commentaires d'alertes.
    """
    
    def __init__(self):
        """
        Initialise le repository avec le modèle AlertComment.
        """
        super().__init__(AlertComment)
    
    def create(self, alert_id: int, user_id: int, comment: str,
               is_internal: bool = False) -> AlertComment:
        """
        Crée un nouveau commentaire d'alerte.
        """
        try:
            alert_comment = AlertComment(
                alert_id=alert_id,
                user_id=user_id,
                comment=comment,
                is_internal=is_internal,
                created_at=datetime.now(timezone.utc)
            )
            
            alert_comment.save()
            logger.info(f"Commentaire d'alerte créé: {alert_comment.id}")
            return alert_comment
        except Exception as e:
            logger.error(f"Erreur lors de la création d'un commentaire d'alerte: {e}")
            raise
    
    def get_by_alert(self, alert_id: int) -> List[AlertComment]:
        """
        Récupère les commentaires pour une alerte.
        """
        return list(AlertComment.objects.filter(alert_id=alert_id).order_by('created_at'))


class AlertHistoryRepository(BaseRepository[AlertHistory]):
    """
    Repository pour l'historique des alertes.
    """
    
    def __init__(self):
        """
        Initialise le repository avec le modèle AlertHistory.
        """
        super().__init__(AlertHistory)
    
    def create(self, alert_id: int, action: str, description: str = "",
               user_id: Optional[int] = None, old_value: Optional[Dict[str, Any]] = None,
               new_value: Optional[Dict[str, Any]] = None,
               metadata: Optional[Dict[str, Any]] = None) -> AlertHistory:
        """
        Crée un nouvel élément d'historique d'alerte.
        """
        try:
            history_item = AlertHistory(
                alert_id=alert_id,
                action=action,
                description=description,
                user_id=user_id,
                old_value=old_value,
                new_value=new_value,
                metadata=metadata or {},
                timestamp=datetime.now(timezone.utc)
            )
            
            history_item.save()
            logger.info(f"Historique d'alerte créé: {history_item.id}")
            return history_item
        except Exception as e:
            logger.error(f"Erreur lors de la création d'un historique d'alerte: {e}")
            raise
    
    def get_by_alert(self, alert_id: int) -> List[AlertHistory]:
        """
        Récupère l'historique pour une alerte.
        """
        return list(AlertHistory.objects.filter(alert_id=alert_id).order_by('timestamp'))

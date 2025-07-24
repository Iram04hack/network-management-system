"""
Cas d'utilisation pour la gestion des alertes.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional

class AlertUseCase:
    """Cas d'utilisation pour la gestion des alertes."""
    
    def __init__(self, alert_repository, notification_service):
        self.alert_repository = alert_repository
        self.notification_service = notification_service
    
    def list_alerts(self, filters=None):
        """Liste toutes les alertes avec filtres optionnels."""
        if filters is None:
            filters = {}
            
        # Utiliser la méthode list_all avec filtres
        return self.alert_repository.list_all(filters)
    
    def get_alert(self, alert_id):
        """Récupère une alerte par son ID."""
        alert = self.alert_repository.get_by_id(alert_id)
        if alert is None:
            raise ValueError(f"Alert with ID {alert_id} not found")
        return alert
    
    def create_alert(self, title, severity, status="active", description=None, 
                    source_type=None, source_id=None, device_id=None, details=None):
        """Crée une nouvelle alerte."""
        # Créer les données de l'alerte
        alert_data = {
            'message': title,  # title devient message
            'severity': severity,
            'status': status,
            'details': details or {},
            'device_id': device_id
        }
        
        # Créer l'alerte
        alert = self.alert_repository.create(alert_data)
        
        # Envoyer des notifications pour l'alerte (si le service est disponible)
        try:
            if hasattr(self.notification_service, 'send_alert_notifications'):
                self.notification_service.send_alert_notifications(alert)
        except Exception:
            pass  # Ignorer les erreurs de notification pour l'instant
        
        return alert
    
    def update_status(self, alert_id, status, user_id=None, comment=None):
        """Met à jour le statut d'une alerte."""
        alert = self.get_alert(alert_id)
        
        # Mettre à jour le statut de l'alerte
        updated_alert = self.alert_repository.update_status(
            alert_id,
            status=status,
            user_id=user_id,
            comment=comment
        )
        
        # Envoyer des notifications pour le changement de statut (si disponible)
        try:
            if status != alert.get('status') and hasattr(self.notification_service, 'send_alert_status_change_notifications'):
                self.notification_service.send_alert_status_change_notifications(updated_alert)
        except Exception:
            pass  # Ignorer les erreurs de notification pour l'instant
        
        return updated_alert
    
    def acknowledge_alert(self, alert_id, user_id, comment=None):
        """Reconnaît une alerte."""
        return self.update_status(alert_id, "acknowledged", user_id, comment)
    
    def resolve_alert(self, alert_id, user_id, comment=None):
        """Résout une alerte."""
        return self.update_status(alert_id, "resolved", user_id, comment)
    
    def get_active_alerts_count(self):
        """Récupère le nombre d'alertes actives."""
        # Utiliser la méthode count avec filtre
        return self.alert_repository.count({'status': 'active'})
    
    def get_alerts_summary(self):
        """Récupère un résumé des alertes par sévérité et statut."""
        return {
            "by_severity": {
                "critical": self.alert_repository.count({'severity': 'critical'}),
                "high": self.alert_repository.count({'severity': 'high'}),
                "medium": self.alert_repository.count({'severity': 'medium'}),
                "low": self.alert_repository.count({'severity': 'low'}),
                "info": self.alert_repository.count({'severity': 'info'})
            },
            "by_status": {
                "active": self.alert_repository.count({'status': 'active'}),
                "acknowledged": self.alert_repository.count({'status': 'acknowledged'}),
                "resolved": self.alert_repository.count({'status': 'resolved'})
            }
        }
    
    def delete_alert(self, alert_id):
        """Supprime une alerte."""
        alert = self.get_alert(alert_id)
        return self.alert_repository.delete(alert_id)
    
    def bulk_update_status(self, alert_ids, status, user_id=None, comment=None):
        """Met à jour le statut de plusieurs alertes en une seule opération."""
        updated_alerts = []
        for alert_id in alert_ids:
            try:
                updated_alert = self.update_status(alert_id, status, user_id, comment)
                updated_alerts.append(updated_alert)
            except ValueError:
                # Ignorer les alertes qui n'existent pas
                pass
        
        return updated_alerts 
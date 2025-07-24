"""
Tâches Celery pour le module Security Management.

Ce module contient les tâches asynchrones pour la détection automatique
des alertes de sécurité et le déclenchement des rapports.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from celery import shared_task
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def monitor_security_alerts(self):
    """
    Tâche qui monitore automatiquement Elasticsearch pour les nouvelles alertes Suricata.
    
    Cette tâche est exécutée toutes les 2 minutes par Celery Beat pour détecter
    les nouvelles alertes de sécurité et déclencher automatiquement la génération
    de rapports et l'envoi de notifications.
    """
    try:
        logger.info("🔍 Démarrage monitoring automatique des alertes de sécurité")
        
        from .services.elasticsearch_monitor import ElasticsearchMonitor
        from reporting.tasks import generate_security_report_from_alerts
        from .signals import security_alert_detected
        
        # Initialiser le moniteur Elasticsearch
        es_monitor = ElasticsearchMonitor()
        
        # Récupérer les nouvelles alertes depuis le dernier scan
        last_scan_key = "security_monitor_last_scan"
        last_scan_time = cache.get(last_scan_key, timezone.now() - timedelta(minutes=2))
        
        # Scanner les nouvelles alertes
        new_alerts = es_monitor.get_new_alerts_since(last_scan_time)
        
        if not new_alerts:
            logger.debug("✅ Aucune nouvelle alerte détectée")
            cache.set(last_scan_key, timezone.now(), timeout=3600)
            return {"status": "success", "new_alerts": 0}
        
        logger.warning(f"🚨 {len(new_alerts)} nouvelles alertes de sécurité détectées!")
        
        # Analyser la criticité des alertes
        critical_alerts = []
        high_alerts = []
        medium_alerts = []
        
        for alert in new_alerts:
            severity = alert.get('severity', 'medium').lower()
            
            if severity in ['critical', 'high']:
                if severity == 'critical':
                    critical_alerts.append(alert)
                else:
                    high_alerts.append(alert)
                    
                # Émettre signal pour alertes critiques/élevées
                security_alert_detected.send(
                    sender=self.__class__,
                    alert={
                        'id': alert.get('alert_id'),
                        'title': alert.get('signature', 'Alerte de sécurité'),
                        'description': alert.get('message', ''),
                        'severity': severity,
                        'source_ip': alert.get('src_ip'),
                        'destination_ip': alert.get('dest_ip'),
                        'detection_time': alert.get('@timestamp'),
                        'raw_data': alert
                    }
                )
            else:
                medium_alerts.append(alert)
        
        # Déclencher génération automatique de rapport si alertes critiques/élevées
        report_triggered = False
        if critical_alerts or high_alerts:
            logger.info(f"🚨 Déclenchement automatique du rapport de sécurité: {len(critical_alerts)} critiques, {len(high_alerts)} élevées")
            
            # Lancer génération asynchrone du rapport
            report_task = generate_security_report_from_alerts.delay({
                'critical_alerts': critical_alerts,
                'high_alerts': high_alerts,
                'medium_alerts': medium_alerts,
                'detection_time': timezone.now().isoformat(),
                'auto_generated': True,
                'trigger_source': 'security_monitoring'
            })
            
            report_triggered = True
            
            # Sauvegarder info du rapport en cours
            cache.set(f"security_report_task_{report_task.id}", {
                'task_id': report_task.id,
                'started_at': timezone.now().isoformat(),
                'alert_counts': {
                    'critical': len(critical_alerts),
                    'high': len(high_alerts),
                    'medium': len(medium_alerts)
                }
            }, timeout=3600)
        
        # Mettre à jour métriques de monitoring
        cache.set("security_monitoring_stats", {
            'last_scan': timezone.now().isoformat(),
            'alerts_processed': len(new_alerts),
            'critical_alerts': len(critical_alerts),
            'high_alerts': len(high_alerts),
            'medium_alerts': len(medium_alerts),
            'report_triggered': report_triggered,
            'scan_success': True
        }, timeout=86400)
        
        # Mettre à jour timestamp du dernier scan
        cache.set(last_scan_key, timezone.now(), timeout=3600)
        
        logger.info(f"✅ Monitoring terminé - {len(new_alerts)} alertes traitées, rapport {'déclenché' if report_triggered else 'non requis'}")
        
        return {
            "status": "success",
            "new_alerts": len(new_alerts),
            "critical_alerts": len(critical_alerts),
            "high_alerts": len(high_alerts),
            "medium_alerts": len(medium_alerts),
            "report_triggered": report_triggered
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du monitoring des alertes de sécurité: {e}")
        
        # Mettre à jour métriques d'erreur
        cache.set("security_monitoring_stats", {
            'last_scan': timezone.now().isoformat(),
            'scan_success': False,
            'error': str(e)
        }, timeout=86400)
        
        # Retry avec backoff exponentiel
        try:
            raise self.retry(countdown=30 * (2 ** self.request.retries))
        except self.MaxRetriesExceededError:
            logger.error("⚠️ Nombre maximum de tentatives atteint pour le monitoring de sécurité")


@shared_task
def process_security_event(event_data: Dict[str, Any]):
    """
    Traite un événement de sécurité en temps réel.
    
    Args:
        event_data: Données de l'événement de sécurité
    """
    try:
        logger.info(f"🔒 Traitement événement de sécurité: {event_data.get('event_type', 'unknown')}")
        
        # Analyser le type d'événement
        event_type = event_data.get('event_type')
        source_ip = event_data.get('source_ip')
        destination_ip = event_data.get('destination_ip')
        severity = event_data.get('severity', 'medium')
        
        # Action automatique selon la sévérité
        if severity == 'critical':
            # Notification immédiate pour événements critiques
            from .services.notification_service import send_immediate_alert
            send_immediate_alert({
                'title': f"🚨 ALERTE CRITIQUE - {event_type}",
                'message': f"Source: {source_ip} → Destination: {destination_ip}",
                'event_data': event_data
            })
            
        # Loguer l'événement pour corrélation future
        from .models import SecurityEvent
        SecurityEvent.objects.create(
            event_type=event_type,
            source_ip=source_ip,
            destination_ip=destination_ip,
            severity=severity,
            event_data=event_data,
            processed_at=timezone.now()
        )
        
        logger.info(f"✅ Événement de sécurité traité avec succès")
        
    except Exception as e:
        logger.error(f"❌ Erreur traitement événement de sécurité: {e}")


@shared_task
def fetch_suricata_alerts():
    """
    Récupère les alertes Suricata depuis Elasticsearch.
    
    Cette tâche est exécutée toutes les 5 minutes pour synchroniser
    les alertes Suricata avec la base de données Django.
    """
    try:
        logger.info("📥 Récupération des alertes Suricata")
        
        from .services.suricata_client import SuricataClient
        
        suricata_client = SuricataClient()
        
        # Récupérer les alertes depuis le dernier fetch
        last_fetch_key = "suricata_last_fetch"
        last_fetch_time = cache.get(last_fetch_key, timezone.now() - timedelta(minutes=5))
        
        alerts = suricata_client.get_alerts_since(last_fetch_time)
        
        alerts_processed = 0
        for alert_data in alerts:
            try:
                # Créer ou mettre à jour l'alerte en DB
                from .models import SuricataAlert
                
                alert, created = SuricataAlert.objects.get_or_create(
                    alert_id=alert_data.get('alert_id', alert_data.get('_id')),
                    defaults={
                        'signature': alert_data.get('alert', {}).get('signature', ''),
                        'category': alert_data.get('alert', {}).get('category', ''),
                        'severity': alert_data.get('alert', {}).get('severity', 1),
                        'source_ip': alert_data.get('src_ip', ''),
                        'destination_ip': alert_data.get('dest_ip', ''),
                        'source_port': alert_data.get('src_port', 0),
                        'destination_port': alert_data.get('dest_port', 0),
                        'protocol': alert_data.get('proto', ''),
                        'timestamp': alert_data.get('@timestamp'),
                        'raw_data': alert_data
                    }
                )
                
                if created:
                    alerts_processed += 1
                    
                    # Déclencher signal pour nouvelle alerte
                    from .signals import security_alert_detected
                    security_alert_detected.send(
                        sender=SuricataAlert,
                        alert=alert
                    )
                    
            except Exception as e:
                logger.error(f"Erreur traitement alerte Suricata: {e}")
                continue
        
        # Mettre à jour timestamp
        cache.set(last_fetch_key, timezone.now(), timeout=3600)
        
        logger.info(f"✅ {alerts_processed} nouvelles alertes Suricata traitées")
        
        return {
            "status": "success",
            "alerts_processed": alerts_processed,
            "total_alerts": len(alerts)
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur récupération alertes Suricata: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@shared_task
def sync_suricata_rules():
    """
    Synchronise les règles Suricata.
    """
    try:
        logger.info("🔄 Synchronisation des règles Suricata")
        
        from .services.suricata_rules_manager import SuricataRulesManager
        
        rules_manager = SuricataRulesManager()
        result = rules_manager.sync_rules()
        
        if result['success']:
            logger.info(f"✅ Règles Suricata synchronisées: {result['rules_updated']} mises à jour")
        else:
            logger.warning(f"⚠️ Problème synchronisation règles: {result.get('error', 'Unknown')}")
            
        return result
        
    except Exception as e:
        logger.error(f"❌ Erreur synchronisation règles Suricata: {e}")
        return {"success": False, "error": str(e)}


@shared_task
def cleanup_old_security_data():
    """
    Nettoie les anciennes données de sécurité.
    """
    try:
        logger.info("🧹 Nettoyage des anciennes données de sécurité")
        
        # Paramètres de rétention
        alert_retention_days = getattr(settings, 'SECURITY_ALERT_RETENTION_DAYS', 30)
        event_retention_days = getattr(settings, 'SECURITY_EVENT_RETENTION_DAYS', 90)
        
        cutoff_alert_date = timezone.now() - timedelta(days=alert_retention_days)
        cutoff_event_date = timezone.now() - timedelta(days=event_retention_days)
        
        # Nettoyer les alertes anciennes
        from .models import SuricataAlert, SecurityEvent
        
        old_alerts = SuricataAlert.objects.filter(timestamp__lt=cutoff_alert_date)
        alerts_deleted = old_alerts.count()
        old_alerts.delete()
        
        # Nettoyer les événements anciens
        old_events = SecurityEvent.objects.filter(processed_at__lt=cutoff_event_date)
        events_deleted = old_events.count()
        old_events.delete()
        
        logger.info(f"✅ Nettoyage terminé: {alerts_deleted} alertes, {events_deleted} événements supprimés")
        
        return {
            "alerts_deleted": alerts_deleted,
            "events_deleted": events_deleted
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur nettoyage données de sécurité: {e}")
        return {"error": str(e)}
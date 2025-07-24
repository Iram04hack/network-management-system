"""
Tâches périodiques pour le module monitoring.
Ces tâches sont exécutées par Celery selon une planification définie.
"""

import logging
from datetime import datetime, timedelta
from celery import shared_task
from django.conf import settings
from django.utils import timezone

from .di_container import resolve

# Configuration du logger
logger = logging.getLogger(__name__)


@shared_task
def collect_metrics():
    """
    Tâche périodique pour collecter les métriques.
    Collecte les métriques pour tous les équipements actifs.
    """
    try:
        logger.info("Démarrage de la collecte des métriques")
        collect_metrics_use_case = resolve('CollectMetricsUseCase')
        result = collect_metrics_use_case.execute()
        
        success_count = result.get('success_count', 0)
        error_count = result.get('error_count', 0)
        
        logger.info(f"Collecte des métriques terminée: {success_count} succès, {error_count} erreurs")
        return result
    except Exception as e:
        logger.error(f"Erreur lors de la collecte des métriques: {e}")
        raise


@shared_task
def check_services():
    """
    Tâche périodique pour exécuter les vérifications de service.
    Exécute les vérifications de service pour tous les équipements actifs.
    """
    try:
        logger.info("Démarrage des vérifications de service")
        check_services_use_case = resolve('CheckServicesUseCase')
        result = check_services_use_case.execute()
        
        success_count = result.get('success_count', 0)
        error_count = result.get('error_count', 0)
        warning_count = result.get('warning_count', 0)
        critical_count = result.get('critical_count', 0)
        
        logger.info(f"Vérifications de service terminées: {success_count} succès, {warning_count} avertissements, {critical_count} critiques, {error_count} erreurs")
        return result
    except Exception as e:
        logger.error(f"Erreur lors des vérifications de service: {e}")
        raise


@shared_task
def clean_old_data():
    """
    Tâche périodique pour nettoyer les anciennes données.
    Supprime les données plus anciennes que la durée de rétention configurée.
    """
    try:
        logger.info("Démarrage du nettoyage des anciennes données")
        
        # Récupérer les paramètres de rétention
        metrics_retention_days = getattr(settings, 'MONITORING', {}).get('metrics_retention_days', 30)
        check_results_retention_days = getattr(settings, 'MONITORING', {}).get('check_results_retention_days', 30)
        
        # Nettoyer les anciennes valeurs de métriques
        metric_value_repository = resolve('IMetricValueRepository')
        cutoff_date = timezone.now() - timedelta(days=metrics_retention_days)
        
        from .models import DeviceMetric
        device_metrics = DeviceMetric.objects.all()
        
        metrics_deleted = 0
        for device_metric in device_metrics:
            count = metric_value_repository.clean_old_values(
                device_metric.id, 
                retention_days=metrics_retention_days
            )
            metrics_deleted += count
        
        # Nettoyer les anciens résultats de vérification
        check_result_repository = resolve('ICheckResultRepository')
        cutoff_date = timezone.now() - timedelta(days=check_results_retention_days)
        
        from .models import DeviceServiceCheck
        device_checks = DeviceServiceCheck.objects.all()
        
        results_deleted = 0
        for device_check in device_checks:
            count = check_result_repository.clean_old_results(
                device_check.id, 
                retention_days=check_results_retention_days
            )
            results_deleted += count
        
        logger.info(f"Nettoyage terminé: {metrics_deleted} valeurs de métriques et {results_deleted} résultats de vérification supprimés")
        
        return {
            'metrics_deleted': metrics_deleted,
            'results_deleted': results_deleted
        }
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage des anciennes données: {e}")
        raise


@shared_task
def detect_anomalies():
    """
    Tâche périodique pour détecter les anomalies dans les métriques.
    Analyse les métriques pour détecter des comportements anormaux.
    """
    try:
        logger.info("Démarrage de la détection d'anomalies")
        detect_anomalies_use_case = resolve('DetectAnomaliesUseCase')
        
        # Récupérer les métriques actives
        from .models import DeviceMetric
        device_metrics = DeviceMetric.objects.filter(is_active=True)
        
        anomalies_detected = 0
        for device_metric in device_metrics:
            try:
                result = detect_anomalies_use_case.execute(device_metric_id=device_metric.id)
                if result.get('anomalies_detected', 0) > 0:
                    anomalies_detected += result.get('anomalies_detected', 0)
            except Exception as e:
                logger.error(f"Erreur lors de la détection d'anomalies pour la métrique {device_metric.id}: {e}")
        
        logger.info(f"Détection d'anomalies terminée: {anomalies_detected} anomalies détectées")
        
        return {
            'anomalies_detected': anomalies_detected
        }
    except Exception as e:
        logger.error(f"Erreur lors de la détection d'anomalies: {e}")
        raise


@shared_task
def send_pending_notifications():
    """
    Tâche périodique pour envoyer les notifications en attente.
    """
    try:
        logger.info("Démarrage de l'envoi des notifications en attente")
        notification_delivery_use_case = resolve('NotificationDeliveryUseCase')
        
        result = notification_delivery_use_case.execute()
        
        sent_count = result.get('sent_count', 0)
        error_count = result.get('error_count', 0)
        
        logger.info(f"Envoi des notifications terminé: {sent_count} envoyées, {error_count} erreurs")
        
        return result
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi des notifications en attente: {e}")
        raise


@shared_task
def update_business_kpis():
    """
    Tâche périodique pour mettre à jour les KPIs métier.
    """
    try:
        logger.info("Démarrage de la mise à jour des KPIs métier")
        
        from .models import BusinessKPI
        
        # Calculer les KPIs
        kpis_updated = 0
        
        # KPI: Disponibilité des équipements
        try:
            from django.db.models import Avg, Count, Q
            from .models import DeviceServiceCheck, CheckResult
            
            # Calculer la disponibilité sur les dernières 24 heures
            start_time = timezone.now() - timedelta(hours=24)
            
            # Récupérer tous les équipements avec des vérifications
            from network_management.models import NetworkDevice
            devices = NetworkDevice.objects.filter(deviceservicecheck__isnull=False).distinct()
            
            for device in devices:
                # Récupérer les résultats de vérification pour cet équipement
                results = CheckResult.objects.filter(
                    device_service_check__device=device,
                    timestamp__gte=start_time
                )
                
                if results.exists():
                    # Calculer le pourcentage de résultats OK
                    total_results = results.count()
                    ok_results = results.filter(status='ok').count()
                    
                    if total_results > 0:
                        availability = (ok_results / total_results) * 100
                    else:
                        availability = 0
                    
                    # Mettre à jour ou créer le KPI
                    kpi, created = BusinessKPI.objects.update_or_create(
                        name=f"device_availability_{device.id}",
                        defaults={
                            'value': availability,
                            'unit': '%',
                            'label': f"Disponibilité de {device.name}",
                            'category': 'availability',
                            'updated_at': timezone.now()
                        }
                    )
                    
                    kpis_updated += 1
        except Exception as e:
            logger.error(f"Erreur lors du calcul des KPIs de disponibilité: {e}")
        
        # KPI: Nombre d'alertes actives
        try:
            from .models import Alert
            
            active_alerts = Alert.objects.filter(status='active').count()
            critical_alerts = Alert.objects.filter(status='active', severity='critical').count()
            
            # Mettre à jour ou créer les KPIs
            kpi, created = BusinessKPI.objects.update_or_create(
                name="active_alerts",
                defaults={
                    'value': active_alerts,
                    'unit': 'count',
                    'label': "Alertes actives",
                    'category': 'alerts',
                    'updated_at': timezone.now()
                }
            )
            
            kpi, created = BusinessKPI.objects.update_or_create(
                name="critical_alerts",
                defaults={
                    'value': critical_alerts,
                    'unit': 'count',
                    'label': "Alertes critiques",
                    'category': 'alerts',
                    'updated_at': timezone.now()
                }
            )
            
            kpis_updated += 2
        except Exception as e:
            logger.error(f"Erreur lors du calcul des KPIs d'alertes: {e}")
        
        logger.info(f"Mise à jour des KPIs terminée: {kpis_updated} KPIs mis à jour")
        
        return {
            'kpis_updated': kpis_updated
        }
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des KPIs métier: {e}")
        raise 
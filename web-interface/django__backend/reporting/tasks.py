# reporting/tasks.py
from celery import shared_task
import logging
from typing import Dict, Any, List, Optional
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta

from .models import Report, ScheduledReport, ReportTemplate
from .di_container import get_container

logger = logging.getLogger(__name__)

@shared_task
def generate_report_async(report_id: int) -> Dict[str, Any]:
    """
    Génère un rapport de manière asynchrone.
    
    Args:
        report_id: ID du rapport à générer
        
    Returns:
        Résultat de la génération
    """
    logger.info(f"Début de la génération asynchrone du rapport {report_id}")
    
    try:
        # Récupérer le rapport
        report = Report.objects.get(pk=report_id)
        
        # Marquer comme en cours de traitement
        report.status = 'processing'
        report.save(update_fields=['status'])
        
        # Utiliser le conteneur DI pour obtenir le service de génération
        container = get_container()
        generation_service = container.report_generation_service()
        
        # Générer le rapport
        success = generation_service.generate_report(report_id)
        
        if success:
            logger.info(f"Rapport {report_id} généré avec succès")
            return {
                "success": True,
                "report_id": report_id,
                "timestamp": timezone.now().isoformat()
            }
        else:
            # Marquer comme échoué
            report.status = 'failed'
            report.save(update_fields=['status'])
            
            logger.error(f"Échec de la génération du rapport {report_id}")
            return {
                "success": False,
                "report_id": report_id,
                "error": "Échec de la génération",
                "timestamp": timezone.now().isoformat()
            }
            
    except Report.DoesNotExist:
        logger.error(f"Rapport {report_id} introuvable")
        return {
            "success": False,
            "report_id": report_id,
            "error": "Rapport introuvable",
            "timestamp": timezone.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erreur lors de la génération du rapport {report_id}: {e}")
        
        # Marquer comme échoué si le rapport existe
        try:
            report = Report.objects.get(pk=report_id)
            report.status = 'failed'
            report.save(update_fields=['status'])
        except:
            pass
            
        return {
            "success": False,
            "report_id": report_id,
            "error": str(e),
            "timestamp": timezone.now().isoformat()
        }

@shared_task
def distribute_report_async(report_id: int, distribution_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Distribue un rapport de manière asynchrone.
    
    Args:
        report_id: ID du rapport à distribuer
        distribution_config: Configuration de distribution
        
    Returns:
        Résultat de la distribution
    """
    logger.info(f"Début de la distribution asynchrone du rapport {report_id}")
    
    try:
        # Utiliser le conteneur DI pour obtenir le cas d'utilisation de distribution
        container = get_container()
        distribute_use_case = container.distribute_report_use_case()
        
        # Distribuer le rapport
        result = distribute_use_case.execute(report_id, distribution_config)
        
        logger.info(f"Rapport {report_id} distribué avec succès")
        return {
            "success": True,
            "report_id": report_id,
            "distribution_result": result,
            "timestamp": timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la distribution du rapport {report_id}: {e}")
        return {
            "success": False,
            "report_id": report_id,
            "error": str(e),
            "timestamp": timezone.now().isoformat()
        }

@shared_task
def process_scheduled_reports() -> Dict[str, Any]:
    """
    Traite les rapports planifiés qui doivent être générés.
    """
    logger.info("Début du traitement des rapports planifiés")
    
    try:
        now = timezone.now()
        
        # Récupérer les rapports planifiés actifs qui doivent être exécutés
        scheduled_reports = ScheduledReport.objects.filter(
            is_active=True
        )
        
        processed_count = 0
        success_count = 0
        
        for scheduled_report in scheduled_reports:
            try:
                # Vérifier si le rapport doit être exécuté selon sa fréquence
                should_run = _should_run_scheduled_report(scheduled_report, now)
                
                if not should_run:
                    continue
                
                # Créer une instance de rapport
                if scheduled_report.report:
                    # Dupliquer un rapport existant
                    original_report = scheduled_report.report
                    report = Report.objects.create(
                        title=f"{original_report.title} - {now.strftime('%Y-%m-%d %H:%M')}",
                        description=original_report.description,
                        report_type=original_report.report_type,
                        template=original_report.template,
                        content=original_report.content,
                        status='processing'
                    )
                elif scheduled_report.template:
                    # Créer un rapport à partir d'un template
                    template = scheduled_report.template
                    report = Report.objects.create(
                        title=f"{template.name} - {now.strftime('%Y-%m-%d %H:%M')}",
                        description=f"Rapport généré automatiquement à partir du template {template.name}",
                        report_type='custom',  # Type par défaut pour les templates
                        template=template,
                        content=template.content,
                        status='processing'
                    )
                else:
                    logger.warning(f"Rapport planifié {scheduled_report.id} sans rapport ni template associé")
                    continue
                
                # Lancer la génération asynchrone
                generate_report_async.delay(report.id)
                
                # Mettre à jour la prochaine exécution
                _update_next_run(scheduled_report, now)
                
                logger.info(f"Rapport planifié {report.id} créé pour la planification {scheduled_report.id}")
                processed_count += 1
                success_count += 1
                
            except Exception as e:
                logger.error(f"Erreur lors du traitement du rapport planifié {scheduled_report.id}: {e}")
                processed_count += 1
        
        return {
            "success": True,
            "reports_processed": processed_count,
            "reports_success": success_count,
            "timestamp": now.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erreur globale lors du traitement des rapports planifiés: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": timezone.now().isoformat()
        }

@shared_task
def cleanup_old_reports(days_to_keep: int = 90) -> Dict[str, Any]:
    """
    Nettoie les anciens rapports selon la politique de rétention.
    
    Args:
        days_to_keep: Nombre de jours à conserver
        
    Returns:
        Résultat du nettoyage
    """
    logger.info(f"Début du nettoyage des rapports de plus de {days_to_keep} jours")
    
    try:
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)
        
        # Récupérer les rapports anciens
        old_reports = Report.objects.filter(
            created_at__lt=cutoff_date,
            status='completed'
        )
        
        deleted_count = 0
        for report in old_reports:
            try:
                # Supprimer le fichier physique si il existe
                if hasattr(report, 'file') and report.file:
                    report.file.delete(save=False)
                
                # Supprimer l'entrée en base
                report.delete()
                deleted_count += 1
                
            except Exception as e:
                logger.error(f"Erreur lors de la suppression du rapport {report.id}: {e}")
        
        logger.info(f"Nettoyage terminé: {deleted_count} rapports supprimés")
        return {
            "success": True,
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date.isoformat(),
            "timestamp": timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage des rapports: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": timezone.now().isoformat()
        }

def _should_run_scheduled_report(scheduled_report: ScheduledReport, reference_time: datetime) -> bool:
    """
    Détermine si un rapport planifié doit être exécuté.
    
    Args:
        scheduled_report: Rapport planifié
        reference_time: Temps de référence
        
    Returns:
        True si le rapport doit être exécuté
    """
    if not scheduled_report.is_active:
        return False
    
    if scheduled_report.start_date and reference_time < scheduled_report.start_date:
        return False
    
    # Logique basée sur la fréquence
    if scheduled_report.frequency == 'daily':
        # Exécuter une fois par jour
        if not hasattr(scheduled_report, 'last_run') or not scheduled_report.last_run:
            return True
        
        # Vérifier si c'est un nouveau jour
        last_run_date = scheduled_report.last_run.date() if scheduled_report.last_run else None
        current_date = reference_time.date()
        return last_run_date != current_date
    
    elif scheduled_report.frequency == 'weekly':
        # Exécuter une fois par semaine (lundi)
        if reference_time.weekday() == 0:  # Lundi
            if not hasattr(scheduled_report, 'last_run') or not scheduled_report.last_run:
                return True
            
            # Vérifier si c'est une nouvelle semaine
            days_since_last_run = (reference_time.date() - scheduled_report.last_run.date()).days
            return days_since_last_run >= 7
    
    elif scheduled_report.frequency == 'monthly':
        # Exécuter le premier jour du mois
        if reference_time.day == 1:
            if not hasattr(scheduled_report, 'last_run') or not scheduled_report.last_run:
                return True
            
            # Vérifier si c'est un nouveau mois
            last_run_month = scheduled_report.last_run.month if scheduled_report.last_run else None
            current_month = reference_time.month
            return last_run_month != current_month
    
    elif scheduled_report.frequency == 'quarterly':
        # Exécuter le premier jour du trimestre (janvier, avril, juillet, octobre)
        quarterly_months = [1, 4, 7, 10]
        if reference_time.month in quarterly_months and reference_time.day == 1:
            if not hasattr(scheduled_report, 'last_run') or not scheduled_report.last_run:
                return True
            
            # Vérifier si c'est un nouveau trimestre
            days_since_last_run = (reference_time.date() - scheduled_report.last_run.date()).days
            return days_since_last_run >= 90
    
    return False

def _update_next_run(scheduled_report: ScheduledReport, current_time: datetime) -> None:
    """
    Met à jour la prochaine exécution d'un rapport planifié.
    
    Args:
        scheduled_report: Rapport planifié
        current_time: Temps actuel
    """
    # Mettre à jour last_run
    if hasattr(scheduled_report, 'last_run'):
        scheduled_report.last_run = current_time
        scheduled_report.save(update_fields=['last_run'])


@shared_task
def generate_security_report_from_alerts(alerts_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Génère automatiquement un rapport de sécurité basé sur les alertes détectées.
    
    Cette tâche est déclenchée automatiquement par le monitoring des alertes
    et génère un rapport complet avec notifications email/Telegram.
    
    Args:
        alerts_data: Données des alertes (critiques, élevées, moyennes)
        
    Returns:
        Résultat de la génération du rapport
    """
    logger.info("🚨 Génération automatique du rapport de sécurité")
    
    try:
        from datetime import datetime
        import os
        import tempfile
        
        # Extraire les données d'alertes
        critical_alerts = alerts_data.get('critical_alerts', [])
        high_alerts = alerts_data.get('high_alerts', [])
        medium_alerts = alerts_data.get('medium_alerts', [])
        
        total_alerts = len(critical_alerts) + len(high_alerts) + len(medium_alerts)
        
        # Générer ID de session unique
        session_id = f"auto_security_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Créer les données du rapport
        report_data = {
            'session_id': session_id,
            'start_time': alerts_data.get('detection_time', timezone.now().isoformat()),
            'duration_formatted': 'Temps réel',
            'project_name': 'Monitoring Automatique NMS',
            'total_scenarios': 1,
            'total_attacks': total_alerts,
            'detection_rate': 100,  # Toutes les alertes sont détectées
            'alerts_generated': total_alerts,
            'modules_tested': [
                'Security Management',
                'Monitoring',
                'Network Management', 
                'Reporting',
                'AI Assistant'
            ],
            'scenarios': [
                {
                    'name': 'Détection Automatique d\'Alertes',
                    'status': 'completed',
                    'criticality': 'critical' if critical_alerts else 'high',
                    'alerts_count': total_alerts,
                    'details': f'{len(critical_alerts)} critiques, {len(high_alerts)} élevées, {len(medium_alerts)} moyennes'
                }
            ],
            'auto_generated': True,
            'trigger_source': alerts_data.get('trigger_source', 'automatic_monitoring'),
            'alert_breakdown': {
                'critical': len(critical_alerts),
                'high': len(high_alerts), 
                'medium': len(medium_alerts)
            },
            'raw_alerts_data': {
                'critical_alerts': critical_alerts,
                'high_alerts': high_alerts,
                'medium_alerts': medium_alerts
            }
        }
        
        # Utiliser le générateur de rapport amélioré
        enhanced_report_path = '/home/adjada/network-management-system/security_testing/reporting/enhanced_report_generator.py'
        
        if os.path.exists(enhanced_report_path):
            # Importer et utiliser le générateur existant
            import sys
            import importlib.util
            
            spec = importlib.util.spec_from_file_location("enhanced_report_generator", enhanced_report_path)
            enhanced_report = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(enhanced_report)
            
            # Générer le rapport HTML
            generator = enhanced_report.EnhancedSecurityReportGenerator()
            report_html = generator.generate_comprehensive_report(report_data)
            
            # Sauvegarder le rapport
            report_filename = f"rapport_securite_auto_{session_id}.html"
            report_path = f"/tmp/{report_filename}"
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_html)
            
            logger.info(f"✅ Rapport HTML généré: {report_path}")
            
            # Déclencher les notifications automatiques
            notification_task = send_security_notifications.delay(report_data, report_path)
            
            logger.info(f"📤 Notifications déclenchées (Task ID: {notification_task.id})")
            
            # Créer entrée en base de données
            report = Report.objects.create(
                title=f"Rapport Sécurité Automatique - {session_id}",
                description=f"Rapport généré automatiquement suite à {total_alerts} alertes de sécurité",
                report_type='security_auto',
                status='completed',
                content=f"Fichier généré: {report_path}",
                created_at=timezone.now()
            )
            
            return {
                'success': True,
                'report_id': report.id,
                'session_id': session_id,
                'report_path': report_path,
                'total_alerts': total_alerts,
                'critical_alerts': len(critical_alerts),
                'high_alerts': len(high_alerts),
                'medium_alerts': len(medium_alerts),
                'notification_task_id': notification_task.id,
                'timestamp': timezone.now().isoformat()
            }
            
        else:
            logger.error(f"❌ Générateur de rapport introuvable: {enhanced_report_path}")
            return {
                'success': False,
                'error': 'Enhanced report generator not found'
            }
            
    except Exception as e:
        logger.error(f"❌ Erreur génération rapport de sécurité automatique: {e}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }


@shared_task
def generate_emergency_system_report(system_health: Dict[str, Any]) -> Dict[str, Any]:
    """
    Génère un rapport d'urgence système quand des problèmes critiques sont détectés.
    
    Args:
        system_health: Données de santé système avec problèmes critiques
        
    Returns:
        Résultat de la génération du rapport d'urgence
    """
    logger.warning("🚨 Génération rapport d'urgence système critique")
    
    try:
        from django.core.cache import cache
        
        # Créer données du rapport d'urgence
        emergency_data = {
            'session_id': f"emergency_{timezone.now().strftime('%Y%m%d_%H%M%S')}",
            'severity': 'CRITICAL',
            'global_status': system_health.get('status', 'unknown'),
            'modules_status': system_health.get('modules', {}),
            'issues': system_health.get('issues', []),
            'health_score': system_health.get('health_score', 0),
            'timestamp': timezone.now().isoformat(),
            'recommendations': _generate_system_recovery_recommendations(system_health)
        }
        
        # Sauvegarder dans le cache pour accès immédiat
        cache.set('emergency_system_report', emergency_data, timeout=3600)
        
        # Créer entrée en base
        report = Report.objects.create(
            title=f"Rapport d'Urgence Système - {emergency_data['session_id']}",
            description=f"Système en état critique: {len(emergency_data['issues'])} problème(s) détecté(s)",
            report_type='emergency_system',
            status='completed',
            content=f"Statut global: {emergency_data['global_status']}, Score: {emergency_data['health_score']}%",
            created_at=timezone.now()
        )
        
        logger.warning(f"✅ Rapport d'urgence généré: {report.id}")
        
        return {
            'success': True,
            'report_id': report.id,
            'emergency_data': emergency_data,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur génération rapport d'urgence système: {e}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }


@shared_task
def distribute_unified_report(unified_report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Distribue le rapport unifié système à tous les canaux configurés.
    
    Args:
        unified_report: Données du rapport unifié
        
    Returns:
        Résultat de la distribution
    """
    logger.info("📤 Distribution rapport unifié système")
    
    try:
        from django.core.cache import cache
        from django.core.mail import send_mail
        
        # Générer un résumé pour notifications
        summary = {
            'global_status': unified_report.get('global_status', 'unknown'),
            'total_modules': unified_report.get('summary', {}).get('total_modules', 0),
            'healthy_modules': unified_report.get('summary', {}).get('healthy_modules', 0),
            'warning_modules': unified_report.get('summary', {}).get('warning_modules', 0),
            'critical_modules': unified_report.get('summary', {}).get('critical_modules', 0),
            'generated_at': unified_report.get('generated_at', timezone.now().isoformat())
        }
        
        # Sauvegarder pour distribution web
        cache.set('distributed_unified_report', {
            'report': unified_report,
            'summary': summary,
            'distributed_at': timezone.now().isoformat()
        }, timeout=7200)
        
        # Envoyer notification email si configuré
        notifications_sent = {'email': False, 'websocket': False}
        
        try:
            if hasattr(settings, 'ADMIN_EMAIL') and settings.ADMIN_EMAIL:
                email_content = f"""
Rapport Unifié NMS - {summary['generated_at']}

Statut Global: {summary['global_status'].upper()}

Modules:
- Total: {summary['total_modules']}
- Fonctionnels: {summary['healthy_modules']}
- Avertissements: {summary['warning_modules']}  
- Critiques: {summary['critical_modules']}

Rapport complet disponible dans l'interface NMS.
                """
                
                send_mail(
                    subject=f"📊 Rapport Unifié NMS - {summary['global_status'].upper()}",
                    message=email_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.ADMIN_EMAIL],
                    fail_silently=True
                )
                notifications_sent['email'] = True
                
        except Exception as e:
            logger.warning(f"⚠️ Erreur envoi email rapport unifié: {e}")
        
        # Diffuser via WebSocket si disponible
        try:
            from common.infrastructure.realtime_event_system import broadcast_system_event
            broadcast_system_event({
                'type': 'unified_report_update',
                'data': summary,
                'timestamp': timezone.now().isoformat()
            })
            notifications_sent['websocket'] = True
            
        except Exception as e:
            logger.warning(f"⚠️ Erreur diffusion WebSocket rapport unifié: {e}")
        
        # Créer entrée en base
        report = Report.objects.create(
            title=f"Rapport Unifié Système - {summary['generated_at'][:19]}",
            description=f"Statut global: {summary['global_status']}, {summary['total_modules']} modules",
            report_type='unified_system',
            status='completed',
            content=f"Modules fonctionnels: {summary['healthy_modules']}/{summary['total_modules']}",
            created_at=timezone.now()
        )
        
        logger.info(f"✅ Rapport unifié distribué: {report.id}")
        
        return {
            'success': True,
            'report_id': report.id,
            'notifications_sent': notifications_sent,
            'summary': summary,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur distribution rapport unifié: {e}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }


@shared_task 
def generate_qos_performance_report(trigger_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Génère un rapport de performance QoS basé sur la congestion détectée.
    
    Args:
        trigger_data: Données de déclenchement avec interfaces congestionées
        
    Returns:
        Résultat de la génération du rapport QoS
    """
    logger.info("📊 Génération rapport performance QoS")
    
    try:
        from django.core.cache import cache
        
        # Récupérer données QoS depuis le cache
        qos_stats = cache.get('qos_traffic_statistics', {})
        qos_status = cache.get('qos_monitoring_status', {})
        recent_optimizations = cache.get('qos_recent_optimizations', {})
        
        # Analyser les données de congestion
        congested_interfaces = trigger_data.get('interfaces', [])
        trigger_type = trigger_data.get('trigger', 'unknown')
        
        # Compiler le rapport QoS
        qos_report = {
            'session_id': f"qos_{timezone.now().strftime('%Y%m%d_%H%M%S')}",
            'trigger_type': trigger_type,
            'detection_time': trigger_data.get('timestamp', timezone.now().isoformat()),
            'summary': {
                'total_interfaces': qos_status.get('interfaces_monitored', 0),
                'congested_interfaces': len(congested_interfaces),
                'critical_congestion': len([i for i in congested_interfaces if i.get('congestion_level') == 'critical']),
                'optimizations_applied': recent_optimizations.get('total_applied', 0)
            },
            'congestion_details': congested_interfaces,
            'current_statistics': qos_stats,
            'recent_optimizations': recent_optimizations.get('optimizations', []),
            'recommendations': _generate_qos_recommendations(congested_interfaces, qos_stats),
            'performance_impact': _calculate_performance_impact(congested_interfaces)
        }
        
        # Sauvegarder pour consultation
        cache.set('qos_performance_report', qos_report, timeout=3600)
        
        # Créer entrée en base
        report = Report.objects.create(
            title=f"Rapport Performance QoS - {qos_report['session_id']}",
            description=f"Congestion détectée: {len(congested_interfaces)} interface(s), Type: {trigger_type}",
            report_type='qos_performance',
            status='completed',
            content=f"Interfaces critiques: {qos_report['summary']['critical_congestion']}, Optimisations: {qos_report['summary']['optimizations_applied']}",
            created_at=timezone.now()
        )
        
        logger.info(f"✅ Rapport QoS généré: {report.id}")
        
        return {
            'success': True,
            'report_id': report.id,
            'qos_summary': qos_report['summary'],
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur génération rapport QoS: {e}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }


@shared_task
def generate_monitoring_health_report(monitoring_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Génère un rapport de santé du monitoring basé sur les métriques collectées.
    
    Args:
        monitoring_data: Données de monitoring collectées
        
    Returns:
        Résultat de la génération du rapport monitoring
    """
    logger.info("📈 Génération rapport santé monitoring")
    
    try:
        from django.core.cache import cache
        
        # Récupérer données monitoring depuis le cache
        monitoring_stats = cache.get('monitoring_stats', {})
        alerts_processed = cache.get('monitoring_alerts_processed', [])
        
        # Analyser la santé du monitoring
        monitoring_health = {
            'session_id': f"monitoring_{timezone.now().strftime('%Y%m%d_%H%M%S')}",
            'collection_success': monitoring_data.get('success', False),
            'last_scan': monitoring_stats.get('last_scan'),
            'devices_monitored': monitoring_data.get('devices_monitored', 0),
            'metrics_collected': monitoring_data.get('metrics_collected', 0),
            'alerts_generated': len(alerts_processed),
            'critical_alerts': len([a for a in alerts_processed if a.get('severity') == 'critical']),
            'scan_duration': monitoring_data.get('scan_duration_ms', 0),
            'health_score': _calculate_monitoring_health_score(monitoring_data, monitoring_stats),
            'recommendations': _generate_monitoring_recommendations(monitoring_data, alerts_processed)
        }
        
        # Sauvegarder pour consultation
        cache.set('monitoring_health_report', monitoring_health, timeout=3600)
        
        # Créer entrée en base
        report = Report.objects.create(
            title=f"Rapport Santé Monitoring - {monitoring_health['session_id']}",
            description=f"Dispositifs: {monitoring_health['devices_monitored']}, Alertes: {monitoring_health['alerts_generated']}",
            report_type='monitoring_health',
            status='completed',
            content=f"Score santé: {monitoring_health['health_score']}%, Alertes critiques: {monitoring_health['critical_alerts']}",
            created_at=timezone.now()
        )
        
        logger.info(f"✅ Rapport monitoring généré: {report.id}")
        
        return {
            'success': True,
            'report_id': report.id,
            'health_score': monitoring_health['health_score'],
            'alerts_count': monitoring_health['alerts_generated'],
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur génération rapport monitoring: {e}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }


@shared_task
def generate_gns3_integration_report(gns3_metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Génère un rapport d'intégration GNS3 basé sur les métriques collectées.
    
    Args:
        gns3_metrics: Métriques GNS3 collectées
        
    Returns:
        Résultat de la génération du rapport GNS3
    """
    logger.info("🔧 Génération rapport intégration GNS3")
    
    try:
        from django.core.cache import cache
        
        # Récupérer données GNS3 complémentaires
        gns3_health_report = cache.get('gns3_health_report', {})
        gns3_projects_sync = cache.get('gns3_projects_sync', {})
        
        # Compiler le rapport GNS3
        gns3_report = {
            'session_id': f"gns3_{timezone.now().strftime('%Y%m%d_%H%M%S')}",
            'server_available': gns3_metrics.get('is_available', False),
            'server_version': gns3_metrics.get('version', 'N/A'),
            'response_time_ms': gns3_metrics.get('response_time_ms', 0),
            'projects_count': gns3_metrics.get('projects_count', 0),
            'last_check': gns3_metrics.get('last_check'),
            'consecutive_failures': gns3_metrics.get('consecutive_failures', 0),
            'health_score': gns3_health_report.get('availability_score', 0),
            'performance_score': gns3_health_report.get('performance_score', 0),
            'sync_status': {
                'last_sync': gns3_projects_sync.get('timestamp'),
                'projects_synced': gns3_projects_sync.get('projects_count', 0)
            },
            'recommendations': gns3_health_report.get('recommendations', []),
            'status_trend': _analyze_gns3_status_trend(gns3_metrics)
        }
        
        # Déterminer statut global
        if gns3_report['server_available'] and gns3_report['consecutive_failures'] == 0:
            gns3_report['global_status'] = 'healthy'
        elif gns3_report['consecutive_failures'] > 3:
            gns3_report['global_status'] = 'critical'
        else:
            gns3_report['global_status'] = 'degraded'
        
        # Sauvegarder pour consultation
        cache.set('gns3_integration_report', gns3_report, timeout=3600)
        
        # Créer entrée en base
        report = Report.objects.create(
            title=f"Rapport Intégration GNS3 - {gns3_report['session_id']}",
            description=f"Serveur: {'Disponible' if gns3_report['server_available'] else 'Indisponible'}, Projets: {gns3_report['projects_count']}",
            report_type='gns3_integration',
            status='completed',
            content=f"Statut: {gns3_report['global_status']}, Score santé: {gns3_report['health_score']}%",
            created_at=timezone.now()
        )
        
        logger.info(f"✅ Rapport GNS3 généré: {report.id}")
        
        return {
            'success': True,
            'report_id': report.id,
            'server_status': gns3_report['global_status'],
            'projects_count': gns3_report['projects_count'],
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur génération rapport GNS3: {e}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }


# Fonctions utilitaires pour les rapports

def _generate_system_recovery_recommendations(system_health: Dict[str, Any]) -> List[str]:
    """Génère des recommandations de récupération système."""
    recommendations = []
    
    if system_health.get('health_score', 0) < 50:
        recommendations.append("Redémarrage des services critiques recommandé")
    
    for issue in system_health.get('issues', []):
        if 'monitoring' in issue.lower():
            recommendations.append("Vérifier la connectivité des dispositifs réseau")
        elif 'security' in issue.lower():
            recommendations.append("Examiner les logs de sécurité immédiatement")
        elif 'qos' in issue.lower():
            recommendations.append("Analyser la congestion réseau et optimiser les politiques QoS")
    
    return recommendations


def _generate_qos_recommendations(congested_interfaces: List[Dict], qos_stats: Dict) -> List[str]:
    """Génère des recommandations QoS basées sur la congestion."""
    recommendations = []
    
    critical_count = len([i for i in congested_interfaces if i.get('congestion_level') == 'critical'])
    
    if critical_count > 0:
        recommendations.append(f"Intervention immédiate requise: {critical_count} interface(s) critique(s)")
        recommendations.append("Considérer l'augmentation de la bande passante")
    
    for interface in congested_interfaces:
        if interface.get('recommended_action') == 'traffic_shaping':
            recommendations.append(f"Appliquer traffic shaping sur {interface.get('interface')}")
    
    return recommendations


def _calculate_performance_impact(congested_interfaces: List[Dict]) -> Dict[str, Any]:
    """Calcule l'impact performance de la congestion."""
    if not congested_interfaces:
        return {'severity': 'none', 'affected_traffic': 0}
    
    critical_interfaces = [i for i in congested_interfaces if i.get('congestion_level') == 'critical']
    
    if critical_interfaces:
        return {
            'severity': 'high',
            'affected_traffic': len(critical_interfaces) * 25,  # Estimation %
            'user_impact': 'Dégradation significative des performances'
        }
    else:
        return {
            'severity': 'medium', 
            'affected_traffic': len(congested_interfaces) * 10,
            'user_impact': 'Ralentissements occasionnels'
        }


def _calculate_monitoring_health_score(monitoring_data: Dict, monitoring_stats: Dict) -> int:
    """Calcule le score de santé du monitoring."""
    score = 100
    
    if not monitoring_data.get('success', False):
        score -= 50
    
    devices_monitored = monitoring_data.get('devices_monitored', 0)
    if devices_monitored == 0:
        score -= 30
    elif devices_monitored < 5:
        score -= 10
    
    scan_duration = monitoring_data.get('scan_duration_ms', 0)
    if scan_duration > 30000:  # > 30 secondes
        score -= 20
    
    return max(0, score)


def _generate_monitoring_recommendations(monitoring_data: Dict, alerts: List) -> List[str]:
    """Génère des recommandations pour le monitoring."""
    recommendations = []
    
    if not monitoring_data.get('success', False):
        recommendations.append("Vérifier la connectivité réseau et les permissions SNMP")
    
    if monitoring_data.get('devices_monitored', 0) == 0:
        recommendations.append("Configurer les dispositifs à monitorer")
    
    critical_alerts = [a for a in alerts if a.get('severity') == 'critical']
    if len(critical_alerts) > 5:
        recommendations.append("Investiguer les alertes critiques en priorité")
    
    return recommendations


def _analyze_gns3_status_trend(gns3_metrics: Dict) -> Dict[str, Any]:
    """Analyse la tendance du statut GNS3."""
    consecutive_failures = gns3_metrics.get('consecutive_failures', 0)
    
    if consecutive_failures == 0:
        return {'trend': 'stable', 'direction': 'positive'}
    elif consecutive_failures <= 2:
        return {'trend': 'fluctuating', 'direction': 'neutral'}
    else:
        return {'trend': 'declining', 'direction': 'negative'}


@shared_task
def send_security_notifications(report_data: Dict[str, Any], report_file_path: str) -> Dict[str, Any]:
    """
    Envoie les notifications de sécurité par email et Telegram.
    
    Args:
        report_data: Données du rapport de sécurité
        report_file_path: Chemin vers le fichier de rapport
        
    Returns:
        Résultat de l'envoi des notifications
    """
    logger.info("📤 Envoi des notifications de sécurité automatiques")
    
    try:
        # Utiliser le gestionnaire de notifications existant
        notification_manager_path = '/home/adjada/network-management-system/security_testing/notifications/notification_manager.py'
        
        if os.path.exists(notification_manager_path):
            import sys
            import importlib.util
            import asyncio
            
            # Importer le gestionnaire de notifications
            spec = importlib.util.spec_from_file_location("notification_manager", notification_manager_path)
            notification_manager = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(notification_manager)
            
            # Créer le gestionnaire
            manager = notification_manager.NotificationManager()
            
            # Envoyer les notifications de manière asynchrone
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    manager.send_security_report_notifications(report_data, report_file_path)
                )
                
                logger.info(f"✅ Notifications envoyées: Email={result['email']['success']}, Telegram={result['telegram']['success']}")
                
                return {
                    'success': True,
                    'email_sent': result['email']['success'],
                    'telegram_sent': result['telegram']['success'],
                    'email_result': result['email'],
                    'telegram_result': result['telegram'],
                    'timestamp': timezone.now().isoformat()
                }
                
            finally:
                loop.close()
                
        else:
            logger.warning(f"⚠️ Gestionnaire de notifications introuvable: {notification_manager_path}")
            
            # Fallback: notification Django simple
            from django.core.mail import send_mail
            
            try:
                send_mail(
                    subject=f"🚨 Rapport Sécurité NMS - {report_data.get('session_id', 'Auto')}",
                    message=f"Rapport de sécurité automatique généré.\n\n"
                           f"Alertes détectées: {report_data.get('total_attacks', 0)}\n"
                           f"Critiques: {report_data.get('alert_breakdown', {}).get('critical', 0)}\n"
                           f"Élevées: {report_data.get('alert_breakdown', {}).get('high', 0)}\n"
                           f"Moyennes: {report_data.get('alert_breakdown', {}).get('medium', 0)}\n\n"
                           f"Rapport disponible: {report_file_path}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=['admin@localhost'],  # Configuration par défaut
                    fail_silently=False,
                )
                
                logger.info("✅ Email de notification basique envoyé")
                
                return {
                    'success': True,
                    'email_sent': True,
                    'telegram_sent': False,
                    'fallback_mode': True,
                    'timestamp': timezone.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"❌ Erreur envoi email fallback: {e}")
                return {
                    'success': False,
                    'error': f'Email fallback failed: {str(e)}',
                    'timestamp': timezone.now().isoformat()
                }
            
    except Exception as e:
        logger.error(f"❌ Erreur envoi notifications de sécurité: {e}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }

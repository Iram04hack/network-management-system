# nms_backend/celery.py
import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# Définir la variable d'environnement pour les paramètres Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nms_backend.settings')

# Créer l'application Celery
app = Celery('nms_backend')

# Utiliser les paramètres de Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Découvrir automatiquement les tâches
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# Définir les tâches périodiques
app.conf.beat_schedule = {
    # Tâches pour le monitoring
    'collect-metrics': {
        'task': 'monitoring.tasks.collect_metrics',
        'schedule': crontab(minute='*/1'),  # Toutes les minutes
    },
    'check-services': {
        'task': 'monitoring.tasks.check_services',
        'schedule': crontab(minute='*/5'),  # Toutes les 5 minutes
    },
    'check-device-status': {
        'task': 'monitoring.tasks.check_device_status',
        'schedule': crontab(minute='*/10'),  # Toutes les 10 minutes
    },
    'collect-prometheus-metrics': {
        'task': 'monitoring.tasks.collect_prometheus_metrics',
        'schedule': crontab(minute='*/5'),  # Toutes les 5 minutes
    },
    'check-prometheus-alerts': {
        'task': 'monitoring.tasks.check_prometheus_alerts',
        'schedule': crontab(minute='*/2'),  # Toutes les 2 minutes
    },
    'sync-fail2ban-bans': {
        'task': 'monitoring.tasks.sync_fail2ban_bans',
        'schedule': crontab(minute='*/10'),  # Toutes les 10 minutes
    },
    'check-haproxy-backends': {
        'task': 'monitoring.tasks.check_haproxy_backends',
        'schedule': crontab(minute='*/5'),  # Toutes les 5 minutes
    },
    'generate-security-report': {
        'task': 'monitoring.tasks.generate_security_report',
        'schedule': crontab(hour=6, minute=0),  # Tous les jours à 6h
    },
    'cleanup-old-metrics': {
        'task': 'monitoring.tasks.cleanup_old_data',
        'schedule': crontab(hour=1, minute=0),  # Tous les jours à 1h
    },
    'cleanup-old-alerts': {
        'task': 'monitoring.tasks.cleanup_old_data',
        'schedule': crontab(hour=1, minute=30),  # Tous les jours à 1h30
    },
    
    # Tâches pour la sécurité
    'monitor-security-alerts': {
        'task': 'security_management.tasks.monitor_security_alerts',
        'schedule': crontab(minute='*/2'),  # Toutes les 2 minutes - DÉCLENCHEUR AUTOMATIQUE
    },
    'sync-suricata-rules': {
        'task': 'security_management.tasks.sync_suricata_rules',
        'schedule': crontab(minute=0, hour='*/6'),  # Toutes les 6 heures
    },
    'fetch-suricata-alerts': {
        'task': 'security_management.tasks.fetch_suricata_alerts',
        'schedule': crontab(minute='*/5'),  # Toutes les 5 minutes
    },
    'cleanup-old-security-data': {
        'task': 'security_management.tasks.cleanup_old_security_data',
        'schedule': crontab(hour=3, minute=30),  # Tous les jours à 3h30
    },
    
    # Tâches pour les rapports
    'process-scheduled-reports': {
        'task': 'reporting.tasks.process_scheduled_reports',
        'schedule': crontab(minute=0, hour='*/1'),  # Toutes les heures
    },
    
    # Tâches pour l'assistant IA
    'cleanup-old-conversations': {
        'task': 'ai_assistant.tasks.cleanup_old_conversations',
        'schedule': crontab(hour=2, minute=0),  # Tous les jours à 2h
    },
    'update-knowledge-base-embeddings': {
        'task': 'ai_assistant.tasks.update_knowledge_base_embeddings',
        'schedule': crontab(hour=3, minute=0),  # Tous les jours à 3h
    },
    'generate-daily-summary': {
        'task': 'ai_assistant.tasks.generate_daily_summary',
        'schedule': crontab(hour=6, minute=0),  # Tous les jours à 6h
    },
    
    # Tâches pour GNS3 Integration
    'monitor-gns3-server': {
        'task': 'gns3_integration.tasks.monitor_gns3_server',
        'schedule': crontab(minute='*/2'),  # Toutes les 2 minutes
    },
    'sync-gns3-projects': {
        'task': 'gns3_integration.tasks.sync_gns3_projects',
        'schedule': crontab(minute='*/15'),  # Toutes les 15 minutes
    },
    'cleanup-gns3-cache': {
        'task': 'gns3_integration.tasks.cleanup_gns3_cache',
        'schedule': crontab(hour=1, minute=45),  # Tous les jours à 1h45
    },
    'generate-gns3-health-report': {
        'task': 'gns3_integration.tasks.generate_gns3_health_report',
        'schedule': crontab(minute='*/30'),  # Toutes les 30 minutes
    },
    
    # === TÂCHES MULTI-PROJETS GNS3 ===
    # Surveillance automatique du trafic et basculement
    'monitor-multi-projects-traffic': {
        'task': 'gns3_integration.tasks.monitor_multi_projects_traffic',
        'schedule': crontab(minute='*/2'),  # Toutes les 2 minutes - DÉTECTION TRAFIC AUTOMATIQUE
    },
    
    # Synchronisation projets sélectionnés
    'sync-all-selected-projects': {
        'task': 'gns3_integration.tasks.sync_all_selected_projects',
        'schedule': crontab(minute='*/10'),  # Toutes les 10 minutes
    },
    
    # Nettoyage cache multi-projets
    'cleanup-multi-project-cache': {
        'task': 'gns3_integration.tasks.cleanup_multi_project_cache',
        'schedule': crontab(minute=30, hour='*/2'),  # Toutes les 2 heures
    },
    
    # Tâches pour Network Management
    'sync-network-topology': {
        'task': 'network_management.tasks.sync_network_topology',
        'schedule': crontab(minute='*/10'),  # Toutes les 10 minutes
    },
    'discover-network-devices': {
        'task': 'network_management.tasks.discover_network_devices',
        'schedule': crontab(minute=0, hour='*/6'),  # Toutes les 6 heures
    },
    'collect-interface-statistics': {
        'task': 'network_management.tasks.collect_interface_statistics',
        'schedule': crontab(minute='*/5'),  # Toutes les 5 minutes
    },
    'update-device-statuses': {
        'task': 'network_management.tasks.update_device_statuses',
        'schedule': crontab(minute='*/15'),  # Toutes les 15 minutes
    },
    'cleanup-old-topology-data': {
        'task': 'network_management.tasks.cleanup_old_topology_data',
        'schedule': crontab(hour=2, minute=30),  # Tous les jours à 2h30
    },
    'generate-topology-health-report': {
        'task': 'network_management.tasks.generate_topology_health_report',
        'schedule': crontab(minute='*/20'),  # Toutes les 20 minutes
    },
    
    # === ORCHESTRATION CENTRALE ===
    # Tâche maîtresse qui coordonne tous les modules
    'orchestrate-system-monitoring': {
        'task': 'common.tasks.orchestrate_system_monitoring',
        'schedule': crontab(minute='*/5'),  # Toutes les 5 minutes - ORCHESTRATEUR PRINCIPAL
    },
    
    # Communication inter-modules
    'coordinate-inter-module-communication': {
        'task': 'common.tasks.coordinate_inter_module_communication',
        'schedule': crontab(minute='*/3'),  # Toutes les 3 minutes
    },
    
    # Synchronisation globale des configurations
    'sync-modules-configuration': {
        'task': 'common.tasks.sync_modules_configuration',
        'schedule': crontab(minute=0, hour='*/2'),  # Toutes les 2 heures
    },
    
    # Rapport unifié système
    'generate-unified-system-report': {
        'task': 'common.tasks.generate_unified_system_report',
        'schedule': crontab(minute=0, hour='*/1'),  # Toutes les heures
    },
    
    # Nettoyage cache système global
    'cleanup-system-cache': {
        'task': 'common.tasks.cleanup_system_cache',
        'schedule': crontab(hour=4, minute=0),  # Tous les jours à 4h
    },
    
    # === TÂCHES QoS MANAGEMENT ===
    # Collecte statistiques trafic en temps réel
    'collect-traffic-statistics': {
        'task': 'qos_management.tasks.collect_traffic_statistics',
        'schedule': crontab(minute='*/2'),  # Toutes les 2 minutes - TEMPS RÉEL
    },
    
    # Monitoring conformité QoS
    'monitor-qos-compliance': {
        'task': 'qos_management.tasks.monitor_qos_compliance',
        'schedule': crontab(minute='*/10'),  # Toutes les 10 minutes
    },
    
    # Génération recommandations QoS automatiques
    'generate-qos-recommendations': {
        'task': 'qos_management.tasks.generate_qos_recommendations',
        'schedule': crontab(minute=0, hour='*/4'),  # Toutes les 4 heures
    },
    
    # Nettoyage données QoS anciennes
    'cleanup-qos-data': {
        'task': 'qos_management.tasks.cleanup_qos_data',
        'schedule': crontab(hour=3, minute=0),  # Tous les jours à 3h
    },
    
    # === TÂCHES REPORTING UNIFIÉES ===
    # Nettoyage rapports anciens
    'cleanup-old-reports': {
        'task': 'reporting.tasks.cleanup_old_reports',
        'schedule': crontab(hour=5, minute=0),  # Tous les jours à 5h
        'kwargs': {'days_to_keep': 30}
    },
    
    # === TÂCHES DASHBOARD TEMPS RÉEL ===
    # Collecte métriques système en temps réel
    'collect-system-metrics': {
        'task': 'dashboard.tasks.collect_system_metrics',
        'schedule': crontab(minute='*/1'),  # Toutes les minutes - TEMPS RÉEL
    },
    
    # Mise à jour topologie réseau
    'update-network-topology': {
        'task': 'dashboard.tasks.update_network_topology',
        'schedule': crontab(minute='*/2'),  # Toutes les 2 minutes
    },
    
    # Surveillance projets GNS3
    'monitor-gns3-projects': {
        'task': 'dashboard.tasks.monitor_gns3_projects',
        'schedule': crontab(minute='*/3'),  # Toutes les 3 minutes
    },
    
    # Mise à jour widgets dashboard
    'update-dashboard-widgets': {
        'task': 'dashboard.tasks.update_dashboard_widgets',
        'schedule': crontab(minute='*/2'),  # Toutes les 2 minutes
    },
    
    # Nettoyage métriques anciennes
    'cleanup-old-metrics': {
        'task': 'dashboard.tasks.cleanup_old_metrics',
        'schedule': crontab(hour=4, minute=30),  # Tous les jours à 4h30
    },
}

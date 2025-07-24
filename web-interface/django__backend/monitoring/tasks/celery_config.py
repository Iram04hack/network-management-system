"""
Configuration Celery pour le module monitoring.
"""

from celery import Celery
from celery.schedules import crontab
import os

# Définir les variables d'environnement pour Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nms_backend.settings')

# Créer l'application Celery
app = Celery('monitoring')

# Charger la configuration depuis les paramètres Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Découverte automatique des tâches dans les applications Django
app.autodiscover_tasks()

# Configuration des tâches périodiques
app.conf.beat_schedule = {
    'collect-metrics-every-minute': {
        'task': 'monitoring.tasks.metrics_tasks.collect_all_metrics',
        'schedule': 60.0,  # Toutes les minutes
    },
    'run-service-checks-every-5-minutes': {
        'task': 'monitoring.tasks.service_check_tasks.run_all_service_checks',
        'schedule': 300.0,  # Toutes les 5 minutes
    },
    'cleanup-old-metrics-daily': {
        'task': 'monitoring.tasks.maintenance_tasks.cleanup_old_metrics',
        'schedule': crontab(hour=2, minute=0),  # Tous les jours à 2h00
    },
    'generate-daily-reports': {
        'task': 'monitoring.tasks.reporting_tasks.generate_daily_reports',
        'schedule': crontab(hour=5, minute=0),  # Tous les jours à 5h00
    },
    'check-alert-thresholds-every-minute': {
        'task': 'monitoring.tasks.alert_tasks.check_alert_thresholds',
        'schedule': 60.0,  # Toutes les minutes
    },
    'process-pending-notifications-every-minute': {
        'task': 'monitoring.tasks.notification_tasks.process_pending_notifications',
        'schedule': 30.0,  # Toutes les 30 secondes
    },
}

# Configuration des files d'attente
app.conf.task_routes = {
    'monitoring.tasks.metrics_tasks.*': {'queue': 'metrics'},
    'monitoring.tasks.service_check_tasks.*': {'queue': 'service_checks'},
    'monitoring.tasks.alert_tasks.*': {'queue': 'alerts'},
    'monitoring.tasks.notification_tasks.*': {'queue': 'notifications'},
    'monitoring.tasks.maintenance_tasks.*': {'queue': 'maintenance'},
    'monitoring.tasks.reporting_tasks.*': {'queue': 'reporting'},
}

# Configuration des priorités
app.conf.task_queue_max_priority = 10
app.conf.task_default_priority = 5

# Configuration des délais d'expiration
app.conf.task_soft_time_limit = 300  # 5 minutes
app.conf.task_time_limit = 600  # 10 minutes

# Configuration de la journalisation
app.conf.worker_log_format = "[%(asctime)s: %(levelname)s/%(processName)s] %(message)s"
app.conf.worker_task_log_format = "[%(asctime)s: %(levelname)s/%(processName)s] [%(task_name)s(%(task_id)s)] %(message)s"

# Configuration des tentatives en cas d'échec
app.conf.task_acks_late = True
app.conf.task_reject_on_worker_lost = True
app.conf.task_default_retry_delay = 60  # 1 minute
app.conf.task_max_retries = 3

# Configuration de la concurrence
app.conf.worker_concurrency = 8  # Nombre de processus de travail

# Configuration des résultats de tâches
app.conf.result_expires = 86400  # 24 heures

# Configuration de la compression
app.conf.task_compression = 'gzip'

# Configuration de la sérialisation
app.conf.task_serializer = 'json'
app.conf.result_serializer = 'json'
app.conf.accept_content = ['json'] 
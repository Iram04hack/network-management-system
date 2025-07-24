"""
Tâches Celery pour les vérifications de service.

Ce module contient les tâches asynchrones pour la vérification
de l'état des services sur les équipements réseau.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from celery import shared_task
from django.utils import timezone

from ..use_cases.service_check_use_cases import (
    ExecuteServiceCheckUseCase,
    AnalyzeServiceHealthUseCase
)
from ..di_container import get_container

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def execute_service_check(
    self,
    service_check_id: int,
    device_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Exécute une vérification de service.
    
    Args:
        service_check_id: ID de la vérification de service
        device_id: ID de l'équipement (optionnel)
        
    Returns:
        Résultat de la vérification
    """
    logger.info(f"Exécution vérification service {service_check_id} pour équipement {device_id}")
    
    try:
        # Résoudre les dépendances
        container = get_container()
        use_case = container.resolve(ExecuteServiceCheckUseCase)
        
        # Exécuter la vérification
        result = use_case.execute(
            service_check_id=service_check_id,
            device_id=device_id
        )
        
        if result.get("success"):
            status = result.get("status", "unknown")
            logger.info(f"Vérification réussie: statut {status}")
        else:
            logger.warning(f"Vérification échouée: {result.get('error', 'Erreur inconnue')}")
        
        return result
        
    except Exception as exc:
        logger.error(f"Erreur lors de la vérification de service: {exc}")
        
        try:
            raise self.retry(countdown=30 * (2 ** self.request.retries))
        except self.MaxRetriesExceededError:
            return {
                "success": False,
                "error": f"Échec après {self.max_retries} tentatives: {str(exc)}",
                "timestamp": timezone.now().isoformat()
            }


@shared_task(
    name="monitoring.tasks.service_check_tasks.run_all_service_checks",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    queue="service_checks",
    priority=5
)
def run_all_service_checks(self, device_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Exécute toutes les vérifications de service actives.
    
    Args:
        device_id: ID de l'équipement spécifique (optionnel)
        
    Returns:
        Résultat des vérifications
    """
    logger.info(f"Exécution de toutes les vérifications pour équipement {device_id or 'tous'}")
    
    try:
        # Résoudre les dépendances
        container = get_container()
        use_case = container.resolve(ExecuteServiceCheckUseCase)
        
        # Exécuter toutes les vérifications
        result = use_case.execute_all(device_id=device_id)
        
        if result.get("success"):
            executed = result.get("executed", 0)
            total = result.get("total", 0)
            logger.info(f"Vérifications réussies: {executed}/{total}")
        else:
            logger.warning(f"Vérifications échouées: {result.get('error', 'Erreur inconnue')}")
        
        return result
        
    except Exception as exc:
        logger.error(f"Erreur lors des vérifications de service: {exc}")
        self.retry(exc=exc)


@shared_task(
    name="monitoring.tasks.service_check_tasks.run_device_service_checks",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    queue="service_checks",
    priority=5
)
def run_device_service_checks(self, device_id: int) -> Dict[str, Any]:
    """Exécute toutes les vérifications de service pour un équipement spécifique."""
    logger.info(f"Starting execution of service checks for device {device_id}")
    
    return run_all_service_checks(device_id=device_id)


@shared_task(
    name="monitoring.tasks.service_check_tasks.run_service_check",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    queue="service_checks",
    priority=5
)
def run_service_check(self, device_service_check_id: int) -> Dict[str, Any]:
    """Exécute une vérification de service spécifique."""
    logger.info(f"Starting execution of service check {device_service_check_id}")
    
    return execute_service_check(service_check_id=device_service_check_id)


@shared_task
def analyze_service_health(device_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Analyse la santé des services.
    
    Args:
        device_id: ID de l'équipement spécifique (optionnel)
        
    Returns:
        Analyse de la santé des services
    """
    logger.info(f"Analyse de santé des services pour équipement {device_id or 'tous'}")
    
    try:
        # Résoudre les dépendances
        container = get_container()
        use_case = container.resolve(AnalyzeServiceHealthUseCase)
        
        # Effectuer l'analyse
        result = use_case.execute(device_id=device_id)
        
        if result.get("success"):
            healthy = result.get("healthy_services", 0)
            total = result.get("total_services", 0)
            logger.info(f"Analyse terminée: {healthy}/{total} services en bonne santé")
        else:
            logger.warning(f"Analyse échouée: {result.get('error', 'Erreur inconnue')}")
        
        return result
        
    except Exception as exc:
        logger.error(f"Erreur lors de l'analyse de santé: {exc}")
        return {
            "success": False,
            "error": str(exc),
            "timestamp": timezone.now().isoformat()
        }


@shared_task(
    name="monitoring.tasks.service_check_tasks.check_service_check_timeouts",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
    queue="service_checks",
    priority=4
)
def check_service_check_timeouts(self):
    """Vérifie les vérifications de service qui ont dépassé leur délai d'exécution."""
    logger.info("Checking for service check timeouts")
    
    try:
        # Cette fonctionnalité nécessiterait un use case dédié
        # Pour l'instant, simulation
        result = {
            "success": True,
            "message": "Vérification des timeouts terminée",
            "timeout_checks": 0,
            "timestamp": timezone.now().isoformat()
        }
        
        logger.info("Vérification des timeouts terminée")
        return result
    
    except Exception as e:
        logger.error(f"Error in check_service_check_timeouts task: {str(e)}", exc_info=True)
        self.retry(exc=e)


@shared_task(
    name="monitoring.tasks.service_check_tasks.cleanup_old_check_results",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
    queue="maintenance",
    priority=3
)
def cleanup_old_check_results(self, days_to_keep=30):
    """Nettoie les anciens résultats de vérification."""
    logger.info(f"Cleaning up check results older than {days_to_keep} days")
    
    try:
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)
        
        # Cette fonctionnalité nécessiterait un use case dédié pour le nettoyage
        # Pour l'instant, simulation
        deleted_count = 0  # Sera remplacé par la vraie logique
        
        result = {
            "success": True,
            "message": f"Nettoyage terminé: {deleted_count} résultats supprimés",
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date.isoformat(),
            "days_to_keep": days_to_keep,
            "timestamp": timezone.now().isoformat()
        }
        
        logger.info(f"Nettoyage réussi: {deleted_count} résultats supprimés")
        return result
    
    except Exception as e:
        logger.error(f"Error in cleanup_old_check_results task: {str(e)}", exc_info=True)
        self.retry(exc=e)


@shared_task
def periodic_service_monitoring() -> Dict[str, Any]:
    """
    Surveillance périodique de tous les services.
    
    Tâche planifiée pour exécuter régulièrement toutes les vérifications.
    
    Returns:
        Résultat de la surveillance périodique
    """
    logger.info("Démarrage surveillance périodique des services")
    
    try:
        # Exécuter toutes les vérifications
        check_result = run_all_service_checks.delay()
        check_data = check_result.get()
        
        # Analyser la santé des services
        health_result = analyze_service_health.delay()
        health_data = health_result.get()
        
        # Consolider les résultats
        result = {
            "success": True,
            "timestamp": timezone.now().isoformat(),
            "service_checks": check_data,
            "health_analysis": health_data,
            "summary": {
                "checks_executed": check_data.get("executed", 0),
                "checks_total": check_data.get("total", 0),
                "healthy_services": health_data.get("healthy_services", 0),
                "total_services": health_data.get("total_services", 0)
            }
        }
        
        logger.info("Surveillance périodique terminée avec succès")
        return result
        
    except Exception as exc:
        logger.error(f"Erreur lors de la surveillance périodique: {exc}")
        return {
            "success": False,
            "error": str(exc),
            "timestamp": timezone.now().isoformat()
        } 
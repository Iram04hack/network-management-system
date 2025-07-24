"""
Tâches Celery pour la collecte et l'analyse de métriques.

Ce module contient les tâches asynchrones pour la gestion
des métriques de surveillance.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from celery import shared_task
from django.utils import timezone

from ..use_cases.metrics_use_cases import (
    CollectMetricsUseCase,
    AnalyzeMetricsUseCase, 
    CleanupMetricsUseCase
)
from ..use_cases.anomaly_detection_use_cases import DetectAnomaliesUseCase
from ..di_container import get_container

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def collect_device_metrics(self, device_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Collecte les métriques pour un équipement spécifique ou tous les équipements.
    
    Args:
        device_id: ID de l'équipement (optionnel, None pour tous)
        
    Returns:
        Résultat de la collecte
    """
    logger.info(f"Démarrage collecte métriques pour équipement {device_id or 'tous'}")
    
    try:
        # Résoudre les dépendances
        container = get_container()
        use_case = container.resolve(CollectMetricsUseCase)
        
        # Exécuter la collecte
        result = use_case.execute(device_id=device_id)
        
        if result.get("success"):
            collected = result.get("collected", 0)
            total = result.get("total", 0)
            logger.info(f"Collecte réussie: {collected}/{total} métriques collectées")
        else:
            logger.warning(f"Collecte échouée: {result.get('error', 'Erreur inconnue')}")
        
        return result
        
    except Exception as exc:
        logger.error(f"Erreur lors de la collecte de métriques: {exc}")
        
        # Réessayer avec backoff exponentiel
        try:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        except self.MaxRetriesExceededError:
            return {
                "success": False,
                "error": f"Échec après {self.max_retries} tentatives: {str(exc)}",
                "timestamp": timezone.now().isoformat()
            }


@shared_task(bind=True, max_retries=2)
def analyze_metrics_trends(
    self,
    metric_id: int,
    analysis_type: str = "trend",
    days_back: int = 7
) -> Dict[str, Any]:
    """
    Analyse les tendances des métriques.
    
    Args:
        metric_id: ID de la métrique à analyser
        analysis_type: Type d'analyse ("basic", "advanced", "trend")
        days_back: Nombre de jours d'historique à analyser
        
    Returns:
        Résultat de l'analyse
    """
    logger.info(f"Analyse de tendance pour métrique {metric_id}")
    
    try:
        # Résoudre les dépendances
        container = get_container()
        use_case = container.resolve(AnalyzeMetricsUseCase)
        
        # Définir la période d'analyse
        end_time = timezone.now()
        start_time = end_time - timedelta(days=days_back)
        
        # Exécuter l'analyse
        result = use_case.execute(
            metric_id=metric_id,
            start_time=start_time,
            end_time=end_time,
            analysis_type=analysis_type
        )
        
        if result.get("success"):
            data_points = result.get("data_points", 0)
            logger.info(f"Analyse réussie: {data_points} points de données analysés")
        else:
            logger.warning(f"Analyse échouée: {result.get('error', 'Erreur inconnue')}")
        
        return result
        
    except Exception as exc:
        logger.error(f"Erreur lors de l'analyse de métriques: {exc}")
        
        try:
            raise self.retry(countdown=30 * (2 ** self.request.retries))
        except self.MaxRetriesExceededError:
            return {
                "success": False,
                "error": f"Échec après {self.max_retries} tentatives: {str(exc)}",
                "timestamp": timezone.now().isoformat()
            }


@shared_task(bind=True)
def detect_metric_anomalies(
    self,
    metric_id: Optional[int] = None,
    device_id: Optional[int] = None,
    algorithm: str = "statistical",
    sensitivity: float = 0.95
) -> Dict[str, Any]:
    """
    Détecte les anomalies dans les métriques.
    
    Args:
        metric_id: ID de la métrique spécifique (optionnel)
        device_id: ID de l'équipement spécifique (optionnel)
        algorithm: Algorithme de détection
        sensitivity: Sensibilité de la détection
        
    Returns:
        Résultat de la détection d'anomalies
    """
    logger.info(f"Détection d'anomalies - métrique:{metric_id}, équipement:{device_id}")
    
    try:
        # Résoudre les dépendances
        container = get_container()
        use_case = container.resolve(DetectAnomaliesUseCase)
        
        # Exécuter la détection
        result = use_case.execute(
            metric_id=metric_id,
            device_id=device_id,
            algorithm=algorithm,
            sensitivity=sensitivity
        )
        
        if result.get("success"):
            anomalies = result.get("anomalies_found", 0)
            alerts = result.get("alerts_created", 0)
            logger.info(f"Détection réussie: {anomalies} anomalies trouvées, {alerts} alertes créées")
        else:
            logger.warning(f"Détection échouée: {result.get('error', 'Erreur inconnue')}")
        
        return result
        
    except Exception as exc:
        logger.error(f"Erreur lors de la détection d'anomalies: {exc}")
        return {
            "success": False,
            "error": str(exc),
            "timestamp": timezone.now().isoformat()
        }


@shared_task(bind=True)
def cleanup_old_metrics(self, retention_days: int = 30) -> Dict[str, Any]:
    """
    Nettoie les anciennes données de métriques.
    
    Args:
        retention_days: Nombre de jours de rétention
        
    Returns:
        Résultat du nettoyage
    """
    logger.info(f"Nettoyage des métriques anciennes (rétention: {retention_days} jours)")
    
    try:
        # Résoudre les dépendances
        container = get_container()
        use_case = container.resolve(CleanupMetricsUseCase)
        
        # Exécuter le nettoyage
        result = use_case.execute(retention_days=retention_days)
        
        if result.get("success"):
            deleted = result.get("deleted_count", 0)
            logger.info(f"Nettoyage réussi: {deleted} enregistrements supprimés")
        else:
            logger.warning(f"Nettoyage échoué: {result.get('error', 'Erreur inconnue')}")
        
        return result
        
    except Exception as exc:
        logger.error(f"Erreur lors du nettoyage: {exc}")
        return {
            "success": False,
            "error": str(exc),
            "timestamp": timezone.now().isoformat()
        }


@shared_task(
    name="monitoring.tasks.metrics_tasks.collect_all_metrics",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    queue="metrics",
    priority=5
)
def collect_all_metrics(self) -> Dict[str, Any]:
    """
    Collecte toutes les métriques de tous les équipements en une fois.
    
    Tâche optimisée pour les collectes périodiques massives.
    
    Returns:
        Résultat de la collecte globale
    """
    logger.info("Démarrage collecte massive de toutes les métriques")
    
    try:
        # Utiliser la tâche de collecte sans device_id pour tous les équipements
        result = collect_device_metrics.delay()
        return result.get()
        
    except Exception as exc:
        logger.error(f"Erreur lors de la collecte massive: {exc}")
        self.retry(exc=exc)


@shared_task
def periodic_anomaly_detection() -> Dict[str, Any]:
    """
    Détection périodique d'anomalies sur toutes les métriques actives.
    
    Exécutée régulièrement pour surveiller automatiquement les anomalies.
    
    Returns:
        Résultat de la détection globale
    """
    logger.info("Démarrage détection périodique d'anomalies")
    
    try:
        # Lancer la détection pour toutes les métriques
        result = detect_metric_anomalies.delay()
        return result.get()
        
    except Exception as exc:
        logger.error(f"Erreur lors de la détection périodique: {exc}")
        return {
            "success": False,
            "error": str(exc),
            "timestamp": timezone.now().isoformat()
        }


@shared_task
def generate_metrics_report(days_back: int = 7) -> Dict[str, Any]:
    """
    Génère un rapport consolidé des métriques.
    
    Args:
        days_back: Nombre de jours à inclure dans le rapport
        
    Returns:
        Rapport des métriques
    """
    logger.info(f"Génération rapport métriques ({days_back} jours)")
    
    try:
        # Cette tâche nécessiterait un use case dédié pour les rapports
        # Pour l'instant, retourner un placeholder
        
        end_time = timezone.now()
        start_time = end_time - timedelta(days=days_back)
        
        report = {
            "success": True,
            "period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "days": days_back
            },
            "generated_at": timezone.now().isoformat(),
            "note": "Rapport détaillé nécessite implémentation complète"
        }
        
        logger.info("Rapport métriques généré avec succès")
        return report
        
    except Exception as exc:
        logger.error(f"Erreur lors de la génération du rapport: {exc}")
        return {
            "success": False,
            "error": str(exc),
            "timestamp": timezone.now().isoformat()
        }